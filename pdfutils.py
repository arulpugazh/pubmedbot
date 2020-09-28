import subprocess
import re
from functools import partial, reduce
from itertools import chain
from bs4 import BeautifulSoup
import requests
import os
from gcputils import upload_blob

bucket_name = os.environ['TEXT_BUCKET_NAME']

def get_scihub_urls():
    urls = []
    res = requests.get('https://sci-hub.now.sh/')
    s = BeautifulSoup(res.content, 'html.parser')
    for a in s.find_all('a', href=True):
        if 'sci-hub.' in a['href']:
            urls.append(a['href'])
    # print("URLS", urls)
    if len(urls) != 0:
        return urls
    else:
        return ['https://sci-hub.st']

def download_pdf(base_url, pmid, sess):
    try:
        data = {'request': str(pmid)}
        res = sess.post(base_url, data)
        if 'article not found' in str(res.content):
            return 404
        else:
            s = BeautifulSoup(res.content, 'html.parser')
        with open('test.html', 'wb+') as f:
            f.write(res.content)
        iframe = s.find('iframe')
        if not iframe.get('src').startswith('//'):
            url = iframe.get('src')
        else:
            url = 'http:' + iframe.get('src')
        # print("Detected URL:", url)
        res = sess.get(url)
        pdf = res.content
        with open(str(pmid) + '.pdf', 'wb+') as f:
            f.write(pdf)
    except Exception as e:
        print(e)
        return 503
    return 200

def ngram(seq, n):
    # In order to maintain the original whitespace, but still consider \n and \t for n-gram tokenization,
    # we add a space here and remove it after creation of the ngrams again (see below)
    seq = seq.replace("\n", " \n")
    seq = seq.replace("\t", " \t")

    words = seq.split(" ")
    ngrams = (
        " ".join(words[i: i + n]).replace(" \n", "\n").replace(" \t", "\t") for i in range(0, len(words) - n + 1)
    )
    return ngrams


def allngram(seq, min_ngram, max_ngram):
    lengths = range(min_ngram, max_ngram) if max_ngram else range(min_ngram, len(seq))
    ngrams = map(partial(ngram, seq), lengths)
    res = set(chain.from_iterable(ngrams))
    return res


def find_longest_common_ngram(sequences, max_ngram=30, min_ngram=3):
    sequences = [s for s in sequences if s]  # filter empty sequences
    if not sequences:
        return None
    seqs_ngrams = map(partial(allngram, min_ngram=min_ngram, max_ngram=max_ngram), sequences)
    intersection = reduce(set.intersection, seqs_ngrams)

    try:
        longest = max(intersection, key=len)
    except ValueError:
        # no common sequence found
        longest = ""
    return longest if longest.strip() else None


def parse_pdf(pmid):
    file_path = str(pmid) + '.pdf'
    command = ["pdftotext", str(file_path), "-"]
    output = subprocess.run(command, stdout=subprocess.PIPE, shell=False)
    document = output.stdout.decode(errors="ignore")
    pages = document.split("\f")
    pages = pages[:-1]  # the last page in the split is always empty.
    # print("No of pages", len(pages))
    cleaned_pages = []

    for page in pages:
        lines = page.splitlines()
        cleaned_lines = []
        for line in lines:
            words = line.split()
            digits = [word for word in words if any(i.isdigit() for i in word)]
            # remove lines having > 40% of words as digits AND not ending with a period(.)
            if words and len(digits) / len(words) > 0.4 and not line.strip().endswith("."):
                continue
            line = line.strip()
            cleaned_lines.append(line)
        page = "\n".join(cleaned_lines)
        page = re.sub(r"\n\n+", "\n\n", page)
        cleaned_pages.append(page)

    n_chars = 300
    n_first_pages_to_ignore = 1
    n_last_pages_to_ignore = 1

    start_of_pages = [p[:n_chars] for p in pages[n_first_pages_to_ignore:-n_last_pages_to_ignore]]
    found_header = find_longest_common_ngram(start_of_pages)
    if found_header:
        cleaned_pages = [page.replace(found_header, "") for page in cleaned_pages]

    # footer
    end_of_pages = [p[-n_chars:] for p in pages[n_first_pages_to_ignore:-n_last_pages_to_ignore]]
    found_footer = find_longest_common_ngram(end_of_pages)
    if found_footer:
        cleaned_pages = [page.replace(found_footer, "") for page in cleaned_pages]
    text = "\n".join(cleaned_pages)
    # print("No of chars:", len(cleaned_pages))
    with open(str(pmid)+'.txt', 'w+') as f:
        f.write(text)
    upload_blob(bucket_name, str(pmid)+'.txt', str(pmid)+'.txt')
    os.remove(str(pmid)+'.txt')
    os.remove(str(pmid)+'.pdf')