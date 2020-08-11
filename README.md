# Question-Answering Bot on PubMed

This is a closed-domain question-answering bot that can answer any questions about medical research with answers from PubMed articles.

I am developing this as part of my mentorship with SharpestMinds. 
# Scraping PubMed articles

### Extract article ID and URL
I extract the article information from [nih baseline files](https://ftp.ncbi.nlm.nih.gov/pubmed/baseline/) . They are XML files and we extract the article id, PubMed URL and abstract from them and store them in SQLite for later use.

### Scrape article texts
PubMed articles are paywalled and will need institutional credentials for access. So we use SciHub to scrape the articles. We forked the [scihub.py repo](https://github.com/zaytoun/scihub.py) and made some changes to handle our application specific exceptions. 
We download the PDF of the articles and use PyMuPDF to extract the text and index them in an ElasticSearch server.

### ElasticSearch Server
We hosted a simple ElasticServer in a GCP Compute Engine machine. This serves two purposes: First to store the article texts and secondly to serve as document store for HayStack

To host an ElasticSearch server and to index it, follow the below steps. This is for a Ubuntu 20.04 instance:

```
curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-7.x.list
sudo apt update
sudo apt install elasticsearch
```
After installing elasticsearch, we will need to modify the config file. 
```
sudo nano /etc/elasticsearch/elasticsearch.yml
```
Change the network.host parameter to below:

```
network.host: 0.0.0.0
```
After that, run the below commands
```
sudo systemctl start elasticsearch
sudo systemctl enable elasticsearch
sudo ufw allow 9200
sudo ufw allow 22
sudo ufw enable
```
After this, read the article texts from CSV file and index them
For example, here I will be downloading 10,000 articles from a GCS bucket

```
gsutil cp gs://pubmedbot/10k_articles.csv .
```
and index them in a Python shell:
```
from elasticsearch import Elasticsearch
import pandas as pd

df = pd.read_csv('10k_articles.csv')

es = Elasticsearch(hosts=[{'host'='', 'port'='9200','username'='', 'password'='', 'index'='main'}])
dicts = []
id =1
for c in df['article'].values:
    doc = {'article': c}
    es.index(index='main', id=id, body=doc)
    id = id+1

es.count(index='main')
```

## Choosing Model

We use [HayStack](https://github.com/deepset-ai/haystack) to choose the best model for the application.

### Fine-tuning
We did not do fine-tuning as of now since it will require labeling significant number of articles with question, answer and contexts. 
We intend to use the pretrained models as such.

### Validation
We drafted about 50 questions from different articles with answers and context. All of these questions will be passed to different models for inference and the responses will be recorded. 

### Metrics
1. USE Similarity: We use spacy and Universal Sentence Encoder to measure the similarity of the labels and the predictions
2. BLEU score: We also use Bilingual Evaluation Understudy Score to measure the correctness
3. Manual Validation: For some iterations, we use manual check and mark the accuracy by hand.

## Deployment

### Web Page
TO-DO
### Slack Bot
TO-DO
### Voice Bot
TO-DO