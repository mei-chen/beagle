import csv
import os

from django.template.loader import render_to_string
from weasyprint import HTML

# Load licenses risks from file on django start
lic_risks_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'data', 'LicensesRisks.csv'
)
LICENSES_RISKS = {}

with open(lic_risks_path) as csvfile:
    csvreader = csv.reader(csvfile, dialect=csv.excel,
                           delimiter=';', quotechar='"')
    data = [[cell.decode('utf8') for cell in row] for row in csvreader]

    for row in data[1:-2]:
        LICENSES_RISKS[row[0]] = {
            'commercial_description': row[5],
            'commercial_score': int(row[6]),
            'ip_description': row[7],
            'ip_score': int(row[8]),
            'source': row[4]
        }


def render_to_pdf(template, base_url, context):
    html = render_to_string(template, context)
    return HTML(string=html, base_url=base_url).write_pdf()
