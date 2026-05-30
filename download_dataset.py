"""
download_dataset.py  —  Bulk download Wikipedia articles into data/

Run:
    python download_dataset.py

Edit the ARTICLES list below to choose your topic.
"""

import os
import wikipediaapi

# Wikipedia requires a user-agent string (just a name for your app)
wiki = wikipediaapi.Wikipedia(
    user_agent="CS382-RAG-Lab/1.0 (student project)",
    language="en"
)

os.makedirs("data", exist_ok=True)

# -----------------------------------------------------------------------
# EDIT THIS LIST to match your chosen topic.
# -----------------------------------------------------------------------

# --- Study Buddy Bot (AI / CS topics) ---
ARTICLES = [
    "Machine learning",
    "Artificial neural network",
    "Natural language processing",
    "Deep learning",
    "Transformer (deep learning architecture)",
    "Large language model",
    "Information retrieval",
    "Vector space model",
    "Cosine similarity",
    "Knowledge base",
]

# --- Movie Recommendation Bot (uncomment to use instead) ---
ARTICLES = [
    "Inception (film)",
    "Interstellar (film)",
    "The Dark Knight",
    "Spirited Away",
    "Your Name (film)",
    "Attack on Titan",
    "Demon Slayer: Kimetsu no Yaiba",
    "Princess Mononoke",
    "Parasite (2019 film)",
    "Everything Everywhere All at Once",
]

# --- Relationship Bot (uncomment to use instead) ---
ARTICLES = [
    "Attachment theory",
    "Emotional intelligence",
    "Communication",
    "Interpersonal relationship",
    "Love languages",
    "Conflict resolution",
    "Empathy",
    "Active listening",
    "Psychological manipulation",
    "Self-esteem",
]

# -----------------------------------------------------------------------

total_words = 0

for title in ARTICLES:
    page = wiki.page(title)
    if not page.exists():
        print(f"  ✗ NOT FOUND: {title}")
        continue

    # Use only the main text (no references section)
    text = page.text
    words = len(text.split())
    total_words += words

    # Save as a clean .txt file
    filename = title.replace(" ", "_").replace("/", "-").replace(":", "") + ".txt"
    filepath = os.path.join("data", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"TITLE: {title}\n")
        f.write(f"SOURCE: {page.fullurl}\n\n")
        f.write(text)

    print(f"  ✓ {title:45s} ({words:,} words) → data/{filename}")

print(f"\nDone! {len(ARTICLES)} articles, ~{total_words:,} words total "
      f"(≈ {total_words // 250} pages)")
print("\nNext step: python ingest.py")
