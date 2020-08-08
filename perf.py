from timeit import default_timer as timer
from pdfminer.high_level import extract_text
import fitz

print("mupdf")
start = timer()
doc = fitz.open('out.pdf')
article = " "
for page in doc:
    article = article + " " + page.getText()
end = timer()
print(end - start)

print("pdfminer")

start = timer()
article = extract_text('out.pdf')
end = timer()
print(end - start)