import xml.etree.ElementTree as ET
import pandas as pd
import sqlite3
from scihub import SciHub
import os
from pdfminer.high_level import extract_text


# tree = ET.parse('pubmed20n0001.xml')
# root = tree.getroot()
# abstracts = tree.findall("./PubmedArticle/MedlineCitation/Article/Abstract/AbstractText")
# print(len(abstracts))


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file, timeout=60)
    except Exception as e:
        print(e)
    return conn


def write_to_db(abstract, article, url, cur):
    # print(type(text))
    cur.execute('''INSERT INTO abstracts(abstract, article,url) VALUES(?,?,?)''', [abstract, article, url])


def download_parse_pdf(url):
    sh = SciHub()
    result = sh.download(url, path="out.pdf")
    if result:
        article = extract_text(pdf_file="out.pdf")
    return article


def parse_abstract_article(row, cur):
    for col in ['deep_learning', 'covid_19', 'human_connectome',
                'virtual_reality', 'brain_machine_interfaces', 'electroactive_polymers',
                'pedot_electrodes', 'neuroprosthetics']:
        url = row[col + "_links"]
        # article = download_parse_pdf(url)
        write_to_db(row[col], "", url, cur)


def transform_abstract_one():
    df = pd.read_csv('pubmed_abstracts.csv')

    conn = create_connection("pubmed.sqlite")
    cur = conn.cursor()

    df.apply(parse_abstract_article, args=(cur,), axis=1)

    conn.commit()
    conn.close()


def transform_abstract_two():
    df = pd.read_csv('fibro_abstracts.csv')

    conn = create_connection("pubmed.sqlite")
    cur = conn.cursor()

    df['abstract'].apply(write_to_db, args=("", "", cur,))
    conn.commit()
    conn.close()


def transform_abstract_three():
    tree = ET.parse('pubmed20n0001.xml')
    root = tree.getroot()
    abstracts = tree.findall("./PubmedArticle/MedlineCitation/Article/Abstract/AbstractText")

    conn = create_connection("pubmed.sqlite")
    cur = conn.cursor()

    for abs in abstracts:
        write_to_db(abs.text, "", "", cur)
    conn.commit()
    conn.close()


def update_articles():
    conn = create_connection("pubmed.sqlite")
    cur = conn.cursor()

    cur.execute('''SELECT id, url FROM abstracts WHERE article="" AND url!= "" ''')
    rows = cur.fetchall()
    print(f"Number of articles yet to be updated: {len(rows)}")
    for row_id, url in rows:
        print(row_id, url)
        article = download_parse_pdf(url)
        cur.execute('''UPDATE abstracts SET article=? WHERE id=?''', [article, row_id])
        conn.commit()
    conn.close()


if __name__ == '__main__':
    # transform_abstract_one()
    # transform_abstract_two()
    # transform_abstract_three()
    update_articles()
