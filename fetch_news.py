"""Collect UNO News headlines, descriptions, and links into news.csv."""
import csv
import re
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

SOURCE = "https://www.unomaha.edu/news/"
FIELDS = ["title", "description", "url"]
MAX_ARTICLES = 20
session = requests.Session()
session.headers.update({"User-Agent": "UNO-News-Feed/1.0 (public news RSS aggregator)"})


def get_soup(url):
    response = session.get(url, timeout=25)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def article_description(url):
    """Prefer the publisher's summary; fall back to a substantial article paragraph."""
    try:
        soup = get_soup(url)
        for attrs in (
            {"name": "description"},
            {"property": "og:description"},
            {"name": "twitter:description"},
        ):
            tag = soup.find("meta", attrs=attrs)
            if tag and clean(tag.get("content")):
                return clean(tag["content"])
        article = soup.find("article") or soup.find("main") or soup
        for p in article.find_all("p"):
            text = clean(p.get_text(" ", strip=True))
            if len(text) >= 60:
                return text
    except requests.RequestException as exc:
        print(f"Description unavailable for {url}: {exc}")
    return ""


def main():
    soup = get_soup(SOURCE)
    heading = next(
        (h for h in soup.find_all(re.compile(r"^h[1-6]$"))
         if clean(h.get_text(" ", strip=True)).lower() == "recent news"),
        None,
    )
    if heading is None:
        raise RuntimeError("Recent News heading not found; preserving existing news.csv")

    headlines = []
    seen = set()
    for element in heading.next_elements:
        if getattr(element, "name", None) in ("h1", "h2"):
            break
        if getattr(element, "name", None) != "a":
            continue
        title = clean(element.get_text(" ", strip=True))
        href = element.get("href")
        if not href or not title:
            continue
        url = urldefrag(urljoin(SOURCE, href)).url
        parsed = urlparse(url)
        if (parsed.netloc != "www.unomaha.edu"
                or not parsed.path.startswith("/news/")
                or not parsed.path.endswith(".php")
                or url in seen):
            continue
        seen.add(url)
        headlines.append({"title": title, "description": article_description(url), "url": url})
        if len(headlines) >= MAX_ARTICLES:
            break

    if not headlines:
        raise RuntimeError("No UNO news articles found; preserving existing news.csv")
    with open("news.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(headlines)
    print(f"Collected {len(headlines)} headlines; {sum(bool(a['description']) for a in headlines)} descriptions")


if __name__ == "__main__":
    main()
