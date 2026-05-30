"""
download_dataset.py  —  Bulk download Wikipedia articles into data/

Streams the wikimedia/structured-wikipedia dataset from Hugging Face,
extracts plain text from each article, and writes one .txt file per article
to data/. Then run `python ingest.py` to build the vector store.

Setup:
    pip install datasets

Run:
    python download_dataset.py
"""

import json
import os
import re
from datasets import load_dataset

DATA_DIR = "data"
NUM_ARTICLES = 500
MIN_WORDS = 200


def extract_sections(sections_json: str | None) -> str:
    """Walk the section tree pulling headings, paragraphs, lists, and table captions."""
    if not sections_json:
        return ""
    parts = []

    def walk(node, depth=0):
        if isinstance(node, dict):
            t = node.get("type")
            if t == "section" and node.get("name"):
                parts.append(("#" * max(depth, 1)) + " " + node["name"])
            elif t == "paragraph" and node.get("value"):
                parts.append(node["value"])
            elif t == "list":
                for item in node.get("has_parts", []) or []:
                    if isinstance(item, dict) and item.get("value"):
                        parts.append("- " + item["value"])
            elif t == "table" and node.get("name"):
                parts.append(f"[table: {node['name']}]")
            for child in node.get("has_parts", []) or []:
                walk(child, depth + 1 if t == "section" else depth)
        elif isinstance(node, list):
            for item in node:
                walk(item, depth)

    walk(json.loads(sections_json))
    return "\n\n".join(parts).strip()


def extract_infoboxes(infoboxes_json: str | None) -> str:
    """Flatten infobox key/value pairs into 'key: value' lines."""
    if not infoboxes_json:
        return ""
    lines = []

    def walk(node):
        if isinstance(node, dict):
            name = node.get("name")
            value = node.get("value")
            if name and value and isinstance(value, str):
                lines.append(f"{name}: {value}")
            for child in node.get("has_parts", []) or []:
                walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(json.loads(infoboxes_json))
    return "\n".join(lines).strip()


def extract_text(row: dict) -> str:
    sections = extract_sections(row.get("sections"))
    infoboxes = extract_infoboxes(row.get("infoboxes"))
    if infoboxes:
        return f"{sections}\n\n## Key facts\n{infoboxes}"
    return sections


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")
    return cleaned[:100] or "untitled"


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    ds = load_dataset(
        "wikimedia/structured-wikipedia",
        "enwiki_namespace_0",
        split="train",
        streaming=True,
    )

    saved = 0
    for row in ds:
        if saved >= NUM_ARTICLES:
            break
        text = extract_text(row)
        if len(text.split()) < MIN_WORDS:
            continue
        path = os.path.join(DATA_DIR, safe_filename(row["name"]) + ".txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        saved += 1
        print(f"  + {row['name']} ({len(text.split())} words)")

    print(f"\nDone. Saved {saved} articles to '{DATA_DIR}/'.")


if __name__ == "__main__":
    main()
