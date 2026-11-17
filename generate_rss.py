import csv
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

CSV_PATH = Path(__file__).resolve().parent / 'news.csv'
OUTPUT_PATH = Path(__file__).resolve().parent / 'news.xml'
SITE = 'https://www.unomaha.edu/news/'

if not CSV_PATH.exists():
    raise SystemExit('news.csv not found. Run fetch_news.py first.')

with CSV_PATH.open('r', encoding='utf-8-sig', newline='') as file:
    rows = list(csv.DictReader(file))

items = [r for r in rows if (r.get('title') or '').strip() and (r.get('url') or '').startswith('https://www.unomaha.edu/news/')]
if not items:
    raise SystemExit('No valid UNO headlines found; existing RSS feed preserved.')

rss = ET.Element('rss', {'version': '2.0'})
channel = ET.SubElement(rss, 'channel')
for tag, value in [
    ('title', 'UNO News Center'),
    ('link', SITE),
    ('description', 'Latest headlines from the University of Nebraska at Omaha News Center.'),
    ('language', 'en-us'),
    ('lastBuildDate', datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')),
]:
    ET.SubElement(channel, tag).text = value

for row in items[:30]:
    item = ET.SubElement(channel, 'item')
    title = row['title'].strip()
    url = row['url'].strip()
    for tag, value in [('title', title), ('link', url), ('guid', url)]:
        element = ET.SubElement(item, tag)
        element.text = value
        if tag == 'guid':
            element.set('isPermaLink', 'true')
    if (row.get('description') or '').strip():
        ET.SubElement(item, 'description').text = row['description'].strip()

ET.indent(rss, space='  ')
ET.ElementTree(rss).write(OUTPUT_PATH, encoding='utf-8', xml_declaration=True)
print(f'Generated {OUTPUT_PATH.name} with {len(items[:30])} headlines')
