import requests
from bs4 import BeautifulSoup
import csv

url = "https://services.ecourts.gov.in/ecourtindia_v6/"
response = requests.get(url)
htmlContent = response.content

soup = BeautifulSoup(htmlContent, 'html.parser')

lists = soup.find_all('li', class_='list-group-item')

points = []
link = ""

for li in lists:
    if li.a:  
        link = li.a.get('href')
        link_text = li.a.get_text(strip=True)
        points.append(f"1. {link_text} ({url}{link})")
    else:
        points.append(f"{len(points) + 1}. {li.get_text(strip=True)}")

formatted_points = " ".join(points)

csv_file = 'case_status_info.csv'
with open(csv_file, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["How to know your case status", formatted_points])

print(f"Data has been written to {csv_file}")
