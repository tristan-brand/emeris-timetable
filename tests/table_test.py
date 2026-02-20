import camelot
from pandas import DataFrame

pdf_path = "./bin/resrc/pas.pdf"

tables = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")
for i, t in enumerate(tables):
    print(i, t.shape, t.parsing_report)

print(tables[0].df)