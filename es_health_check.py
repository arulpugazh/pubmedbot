from gcputils import download_blob, list_blobs_with_prefix
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError
import re
import os
import logging
from datetime import datetime

logging.basicConfig(filename='log/es_health_check' + datetime.now().strftime('%M:%H %d%b%Y') + '.log',
                    level=logging.INFO,
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')


def clean_unidentified_characters(text):
    words_list = ['', '', '', '', '', '', '',
                  'Chemical Reviews', 'Frontiers in Endocrinology | www.frontiersin.org',
                  'ACS Applied Materials & Interfaces',
                  '1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n16\n17\n18\n19\n20\n21\n22\n23\n24\n25\n26\n27\n28\n29\n30\n31\n32\n33\n34\n35\n36\n37\n38\n39\n40\n41\n42\n43\n44\n45\n46\n47\n48\n49\n50\n51\n52\n53\n54\n55\n56\n57\n58\n59\n60\n']
    p = re.compile('|'.join(map(re.escape, words_list)))
    article = re.sub(p, '', text)
    return article


index_name = 'articles'
es = Elasticsearch(timeout=1000)
indices = es.indices.get_alias("*")
if not (index_name in indices.keys()):
    logging.info("Index not found. Creating index")
    es.indices.create(index=index_name)
count = es.count(index=index_name)['count']
logging.info("Document Count: %s", str(count))
article_id = 1
if not (count > 0):
    logging.info("Documents deleted. Commencing re-indexing..")
    doc_list = list_blobs_with_prefix('pubmedbot', 'txt/')
    for doc in doc_list:
        file_name = doc.name
        download_blob('pubmedbot', file_name, file_name)
        pmid = file_name.split('.')[0]
        with open(file_name, 'r') as f:
            text = f.read()
        new_text = re.sub(r'\n\n.*et al\n', "", text)
        new_text = re.sub(r'\.\n\n', "\.\n", new_text)
        new_text = re.sub(r'Page [0-9]+ of [0-9]+\n', "", new_text)
        new_text = clean_unidentified_characters(new_text)
        new_text = re.sub(r'(\n )+', "\n", new_text).strip()
        new_text = re.sub(r'\n+', "\n", new_text).strip()
        paragraphs = re.split(r'\.( )*\n', new_text)
        dicts = []
        for para in paragraphs:
            article = {'pmid': pmid, 'text': para}
            try:
                es.index(index=index_name, id=article_id, body=article)
            except RequestError as e:
                with open('error.log', 'a+') as f:
                    f.write(e)
                continue
            article_id = article_id + 1
        os.remove(file_name)
