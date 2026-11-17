
import csv
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SOURCE = "https://www.unomaha.edu/news/"
HEADERS = {"User-Agent": "UNO-News-Feed/1.0"}
FIELDS = ["title", "description", "image", "url", "date"]

response = requests.get(SOURCE, headers=HEADERS, timeout=30)
response.raise_for_status()
soup = BeautifulSoup(response.text, "html.parser")

heading = next(
    (h for h in soup.find_all(re.compile("^h[1-6]$"))
     if h.get_text(" ", strip=True).lower() == "recent news"),
    None
)

if heading is None:
    raise RuntimeError("Recent News section not found")

articles = []
seen = set()

# Collect article links following the Recent News heading.
for element in heading.next_elements:
    if getattr(element, "name", None) == "h2":
        break

    if getattr(element, "name", None) != "a":
        continue

    title = element.get_text(" ", strip=True)
    href = element.get("href", "")
    url = urljoin(SOURCE, href)

    if not title or url in seen:
        continue

    parsed = urlparse(url)
    if parsed.netloc != "www.unomaha.edu":
        continue
    if not parsed.path.startswith("/news/"):
        continue
    if not parsed.path.endswith(".php"):
        continue

    container = element
    for _ in range(4):
        if container.parent is None:
            break
        container = container.parent
        if container.find("img") and container.find("p"):
            break

    image_tag = container.find("img")
    image = ""
    if image_tag:
        image = image_tag.get("src") or image_tag.get("data-src") or ""
        image = urljoin(SOURCE, image)

    paragraph = container.find("p")
    description = paragraph.get_text(" ", strip=True) if paragraph else ""

    articles.append({
        "title": title,
        "description": description,
        "image": image,
        "url": url,
        "date": ""
    })
    seen.add(url)

    if len(articles) >= 30:
        break

if not articles:
    raise RuntimeError("No articles found; keeping previous feed")

with open("news.csv", "w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(articles)

print(f"Published {len(articles)} UNO news articles")
