"""Convert UNO news.csv into a valid RSS 2.0 news.xml feed."""
import csv
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.etree import ElementTree as ET

SOURCE = "https://www.unomaha.edu/news/"
OUTPUT = "news.xml"


def main():
    with open("news.csv", newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise RuntimeError("CSV contains no news stories; preserving previous RSS")

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    for tag, value in (
        ("title", "University of Nebraska Omaha News"),
        ("link", SOURCE),
        ("description", "Latest news and headlines from the UNO News Center"),
        ("language", "en-us"),
        ("lastBuildDate", format_datetime(datetime.now(timezone.utc))),
    ):
        ET.SubElement(channel, tag).text = value

    for row in rows:
        title = (row.get("title") or "").strip()
        url = (row.get("url") or "").strip()
        if not title or not url:
            continue
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = url
        ET.SubElement(item, "guid", isPermaLink="true").text = url
        ET.SubElement(item, "description").text = (row.get("description") or "").strip()

    ET.indent(rss, space="  ")
    ET.ElementTree(rss).write(OUTPUT, encoding="utf-8", xml_declaration=True)
    print(f"Generated {OUTPUT} from {len(rows)} CSV rows")


if __name__ == "__main__":
    main()
