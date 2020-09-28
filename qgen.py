from question_generator import QuestionGenerator
from nltk.tokenize import sent_tokenize
import re
import json


def clean_unidentified_characters(text):
    words_list = ['', '', '', '', '', '', '',
                  'Chemical Reviews', 'Frontiers in Endocrinology | www.frontiersin.org',
                  'ACS Applied Materials & Interfaces',
                  '1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15\n16\n17\n18\n19\n20\n21\n22\n23\n24\n25\n26\n27\n28\n29\n30\n31\n32\n33\n34\n35\n36\n37\n38\n39\n40\n41\n42\n43\n44\n45\n46\n47\n48\n49\n50\n51\n52\n53\n54\n55\n56\n57\n58\n59\n60\n']
    p = re.compile('|'.join(map(re.escape, words_list)))
    article = re.sub(p, '', text)
    return article


def article_to_paragraphs(file_name):
    with open('/Users/arul/Projects/pubmedbot/txt/' + file_name, 'r') as f:
        text = f.read()
    new_text = re.sub(r'\n\n.*et al\n', "", text)
    new_text = re.sub(r'\.\n\n', "\.\n", new_text)
    new_text = re.sub(r'Page [0-9]+ of [0-9]+\n', "", new_text)
    new_text = clean_unidentified_characters(new_text)
    new_text = re.sub(r'(\n )+', "\n", new_text).strip()
    new_text = re.sub(r'\n+', "\n", new_text).strip()
    paragraphs = re.split(r'\.( )*\n', new_text)
    return paragraphs


qgen = QuestionGenerator()
file_name = '12113563.txt'
paras = article_to_paragraphs(file_name)

qa_id = 1
doc_id = 1
data_vec = []
paragraphs_vec = []
for para in paras:
    sentences = sent_tokenize(para)
    qas_vec = []
    for sent in sentences:
        if sent is not None:
            qa_pairs = qgen.generate_question(sent, ['Wh', 'Are', 'Who', 'Do'])
            for qa_pair in qa_pairs:
                answer_start = para.find(qa_pair['A'])
                answers_vec = [{"text": qa_pair['A'],
                                "answer_start": answer_start,
                                "answer_category": None}]

                qas_vec.append({"question": qa_pair['Q'],
                                "id": qa_id,
                                "answers": answers_vec,
                                "is_impossible": False})
    paragraphs_vec.append({"qas": qas_vec,
                           "context": para,
                           "document_id": doc_id})

body = {"data": paragraphs_vec}
print(body)
squad = json.dumps(body)
with open('squad.json', 'w+') as f:
    f.write(squad)
