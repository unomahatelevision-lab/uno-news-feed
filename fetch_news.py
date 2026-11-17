
import csv
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

SOURCE = "https://www.unomaha.edu/news/"

response = requests.get(
    SOURCE,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30
)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

heading = next(
    (
        h for h in soup.find_all(["h2", "h3"])
        if h.get_text(" ", strip=True).lower() == "recent news"
    ),
    None
)

if heading is None:
    raise RuntimeError("Recent News section not found")

headlines = []
seen = set()

for element in heading.next_elements:
    if getattr(element, "name", None) == "h3":
        break

    if getattr(element, "name", None) != "a":
        continue

    title = element.get_text(" ", strip=True)
    url = urljoin(SOURCE, element.get("href", ""))

    parsed = urlparse(url)

    if (
        not title
        or title.lower() == "complete archive"
        or url in seen
        or parsed.netloc != "www.unomaha.edu"
        or not parsed.path.startswith("/news/")
        or not parsed.path.endswith(".php")
    ):
        continue

    headlines.append({"title": title, "url": url})
    seen.add(url)

    if len(headlines) >= 20:
        break

if not headlines:
    raise RuntimeError("No headlines found; previous feed preserved")

with open("news.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=["title", "url"])
    writer.writeheader()
    writer.writerows(headlines)

print(f"Collected {len(headlines)} headlines")
