import xml.etree.ElementTree as ET
import pandas as pd
from dbutils import get_new_db_connection
import os
from random import uniform
from time import sleep
from multiprocessing import Pool
from pdfutils import download_pdf, parse_pdf, get_scihub_urls
import requests
import gzip
from tqdm import tqdm

def write_to_db(url, pmid, cur, conn):
    cur.execute('''INSERT INTO articles(pmid, url, downloaded) VALUES(?,?,?)''',
                [pmid, url, 0])
    conn.commit()


def clean_unidentified_characters(text):
    words_list = ['', '', '', '', '', '', '',
                  'Chemical Reviews', 'Frontiers in Endocrinology | www.frontiersin.org',
                  'ACS Applied Materials & Interfaces',
                  '1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n16\n17\n18\n19\n20\n21\n22\n23\n24\n25\n26\n27\n28\n29\n30\n31\n32\n33\n34\n35\n36\n37\n38\n39\n40\n41\n42\n43\n44\n45\n46\n47\n48\n49\n50\n51\n52\n53\n54\n55\n56\n57\n58\n59\n60\n']


def download_parse_pdf(pmid):
    try:
        HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0',
                   "x-rapidapi-host": os.environ['RAPIDAPI_HOST'],
                   "x-rapidapi-key": os.environ['RAPIDAPI_KEY'],
                   "useQueryString": 'true'}
        sess = requests.Session()
        sess.headers = HEADERS
        urls = get_scihub_urls()
        for url in urls:
            print("Trying", pmid, "with URL", url)
            dl_status = download_pdf(url, pmid, sess, 'pdf/')
            if dl_status == 404:
                return 404
            elif dl_status == 200:
                parse_pdf(pmid)
                return 200
            else:
                break
    except Exception as e:
        print(str(e))
        with open('errors.log', 'a+') as f:
            f.write(str(e))
        return 503
    return 503


def parse_abstract_article(row, cur, conn):
    for col in ['deep_learning', 'covid_19', 'human_connectome',
                'virtual_reality', 'brain_machine_interfaces', 'electroactive_polymers',
                'pedot_electrodes', 'neuroprosthetics']:
        url = row[col + "_links"]
        # article = download_parse_pdf(url)
        write_to_db(row[col], "", url, cur, conn)


def transform_abstract_one():
    df = pd.read_csv('pubmed_abstracts.csv')
    conn, cur = get_new_db_connection()
    df.apply(parse_abstract_article, args=(cur, conn), axis=1)
    conn.close()


def transform_abstract_two():
    df = pd.read_csv('fibro_abstracts.csv')
    conn, cur = get_new_db_connection()
    df['abstract'].apply(write_to_db, args=("", "", cur, conn))
    conn.close()


def transform_abstract_three(file):
    input = gzip.open(file, 'r')
    tree = ET.parse(input)
    root = tree.getroot()

    conn, cur = get_new_db_connection()
    for e in root.findall('PubmedArticle/MedlineCitation'):
        try:
            abstract = e.find('Article/Abstract/AbstractText').text
            pmid = e.find('PMID').text
            url = "https://www.ncbi.nlm.nih.gov/pubmed/" + pmid
            write_to_db(url, pmid, cur, conn)
        except AttributeError:
            continue
    conn.commit()
    conn.close()


def extract_medline_base():
    folder_path = 'baseline/'
    for file_name in tqdm(os.listdir(folder_path)):
        transform_abstract_three(folder_path + file_name)


def update_article(row):
    conn, cur = get_new_db_connection()
    sleep(uniform(0.0, 1.0))
    status = download_parse_pdf(row[0])
    # print(status)
    cur.execute('''UPDATE abstracts SET downloaded=? WHERE pmid=?''', [status, row[0]])
    conn.commit()
    conn.close()


def update_articles():
    conn, cur = get_new_db_connection()
    cur.execute('''SELECT pmid FROM abstracts WHERE downloaded = 503 AND pmid is not null''')
    rows = cur.fetchall()
    conn.close()
    print(f"Number of articles yet to be updated: {len(rows)}")
    pool = Pool(15)
    pool.map(update_article, rows)


def clean_article(text):
    return text.encode('ascii', 'ignore')


# 16953 articles on morning
if __name__ == '__main__':
    # transform_abstract_one()
    # transform_abstract_two()
    # transform_abstract_three()
    # update_articles()
    extract_medline_base()
