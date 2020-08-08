import xml.etree.ElementTree as ET
import pandas as pd
import sqlite3
from dbutils import get_new_db_connection
from scihub import SciHub
import os
import fitz
from random import uniform
from time import sleep
from requests.exceptions import TooManyRedirects
from multiprocessing import Pool
from urllib.parse import urlparse
from pathlib import Path


def write_to_db(abstract, article, url, cur, conn):
    cur.execute('''INSERT INTO abstracts(abstract, article, url) VALUES(%s,%s,%s)''',
                [abstract, article, url])
    conn.commit()


def download_parse_pdf(url):
    f = urlparse(url)
    f = Path(f.path).name
    try:
        sh = SciHub()
        result = sh.download(url, path=f)
        if result:
            doc = fitz.open(f)
            article = " "
            for page in doc:
                article = article + " " + page.getText()
    except (TooManyRedirects, RuntimeError):
        return "None"
    os.remove(f)
    return clean_article(article)


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


def transform_abstract_three():
    tree = ET.parse('pubmed20n0001.xml')
    root = tree.getroot()

    conn, cur = get_new_db_connection()
    for e in root.findall('PubmedArticle/MedlineCitation'):
        try:
            abstract = e.find('Article/Abstract/AbstractText').text
            pmid = e.find('PMID').text
            url = "https://www.ncbi.nlm.nih.gov/pubmed/" + pmid
            write_to_db(abstract, "", url, cur)
        except AttributeError:
            continue
    conn.commit()
    conn.close()


def update_article(row):
    row_id, url = row
    print(row_id, url)

    conn, cur = get_new_db_connection()
    sleep(uniform(0.0, 1.0))
    article = download_parse_pdf(url)
    cur.execute('''UPDATE abstracts SET article=%s WHERE id=%s''', [article, row_id])
    conn.commit()
    conn.close()


def update_articles():
    conn, cur = get_new_db_connection()
    cur.execute('''SELECT id, url FROM abstracts WHERE article='' AND url!= '' ''')
    rows = cur.fetchall()
    conn.close()
    print(f"Number of articles yet to be updated: {len(rows)}")
    pool = Pool(5)
    pool.map(update_article, rows)


def clean_article(text):
    return text.encode('ascii', 'ignore')


if __name__ == '__main__':
    # transform_abstract_one()
    # transform_abstract_two()
    # transform_abstract_three()
    update_articles()
