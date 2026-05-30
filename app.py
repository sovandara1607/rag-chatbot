"""
app.py — Study Buddy chat UI.

Run it with:
    streamlit run app.py
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st
from rag_core import answer

CHATS_FILE = Path(__file__).parent / "chats.json"


def load_chats() -> dict:
    if not CHATS_FILE.exists():
        return {}
    try:
        return json.loads(CHATS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_chats(convs: dict) -> None:
    try:
        CHATS_FILE.write_text(json.dumps(convs, indent=2))
    except OSError:
        pass

st.set_page_config(
    page_title="Study Buddy",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design tokens — dark scheme (consistent in both empty + chat states)
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
      :root {
        --bg: #111111;
        --card: #191919;
        --muted: #222222;
        --accent: #2a2a2a;
        --border: #2a2a2a;
        --input-border: #333333;
        --ring: #ffe0c2;
        --primary: #ffe0c2;
        --primary-fg: #1a1208;
        --fg: #eeeeee;
        --fg-muted: #a1a1a1;
        --sidebar-bg: #18181b;
        --sidebar-border: #27272a;
        --sidebar-item: transparent;
        --sidebar-item-hover: #27272a;
        --sidebar-item-active: #2a2a2a;
        --secondary: #393028;
        --secondary-fg: #ffe0c2;
        --radius: 14px;
      }

      html, body, .stApp {
        background: var(--bg) !important;
        color: var(--fg) !important;
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont,
                     "Segoe UI", Roboto, Inter, "Helvetica Neue", Arial, sans-serif;
      }

      /* Hide menu & footer, but keep the header (sidebar toggle lives there) */
      #MainMenu, footer { visibility: hidden; height: 0; }
      header[data-testid="stHeader"] {
        background: transparent !important;
        height: auto !important;
      }
      /* Make sure the sidebar collapse/expand button is always visible */
      [data-testid="stSidebarCollapsedControl"],
      [data-testid="stSidebarCollapseButton"],
      [data-testid="stBaseButton-headerNoPadding"] {
        display: flex !important;
        visibility: visible !important;
        color: var(--fg) !important;
      }

      .block-container {
        max-width: 760px;
        padding-top: 2rem;
        padding-bottom: 8rem;
      }

      /* ============================================================
         SIDEBAR
         ============================================================ */
      [data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        border-right: 1px solid var(--sidebar-border) !important;
      }
      [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
      }
      [data-testid="stSidebar"] * {
        color: var(--fg);
      }
      [data-testid="stSidebar"] hr {
        border-color: var(--sidebar-border) !important;
        margin: 0.75rem 0 !important;
      }
      .side-brand {
        display: flex;
        align-items: baseline;
        gap: 0.5rem;
        padding: 0 0.5rem 0.75rem 0.5rem;
      }
      .side-brand-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--fg);
      }
      .side-brand-sub {
        font-size: 0.72rem;
        color: var(--fg-muted);
      }
      .side-section {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--fg-muted);
        padding: 0.75rem 0.5rem 0.25rem 0.5rem;
      }
      .side-empty {
        font-size: 0.82rem;
        color: var(--fg-muted);
        padding: 0.5rem 0.5rem;
        font-style: italic;
      }

      /* Sidebar primary "New chat" button */
      [data-testid="stSidebar"] .stButton > button {
        background: var(--card);
        color: var(--fg);
        border: 1px solid var(--sidebar-border);
        border-radius: 10px;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 0.5rem 0.75rem;
        text-align: left;
        justify-content: flex-start;
        transition: background 0.12s ease, border-color 0.12s ease;
      }
      [data-testid="stSidebar"] .stButton > button:hover {
        background: var(--sidebar-item-hover);
        border-color: var(--input-border);
        color: var(--fg);
      }
      [data-testid="stSidebar"] .stButton > button:focus {
        box-shadow: 0 0 0 2px color-mix(in srgb, var(--ring) 18%, transparent);
      }

      /* Active conversation row — uses st.button(type="primary") */
      [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: var(--sidebar-item-active) !important;
        color: var(--fg) !important;
        border: 1px solid var(--input-border) !important;
        border-left: 2px solid var(--primary) !important;
      }
      [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: var(--accent) !important;
        color: var(--fg) !important;
      }

      /* ============================================================
         TOP BAR
         ============================================================ */
      .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 0 1.25rem 0;
        margin-bottom: 1.25rem;
        border-bottom: 1px solid var(--border);
      }
      .topbar-brand {
        display: flex;
        align-items: baseline;
        gap: 0.6rem;
      }
      .topbar-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--fg);
      }
      .topbar-sub {
        font-size: 0.78rem;
        color: var(--fg-muted);
      }

      /* ============================================================
         EMPTY STATE — centered hero
         ============================================================ */
      .hero {
        text-align: center;
        padding: 4rem 1rem 2rem 1rem;
      }
      .hero-eyebrow {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--fg-muted);
        margin-bottom: 1rem;
      }
      .hero-title {
        font-size: 2rem;
        font-weight: 600;
        color: var(--fg);
        letter-spacing: -0.02em;
        margin: 0 0 0.75rem 0;
      }
      .hero-sub {
        font-size: 0.95rem;
        color: var(--fg-muted);
        max-width: 460px;
        margin: 0 auto 2.5rem auto;
        line-height: 1.5;
      }
      .chip-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--fg-muted);
        margin-bottom: 0.75rem;
        text-align: center;
      }

      /* ============================================================
         BUTTONS (main area) — chip style
         ============================================================ */
      .block-container .stButton > button {
        background: var(--card);
        color: var(--fg);
        border: 1px solid var(--border);
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 400;
        padding: 0.5rem 1rem;
        transition: background 0.15s ease, border-color 0.15s ease;
        box-shadow: none;
      }
      .block-container .stButton > button:hover {
        background: var(--accent);
        border-color: var(--input-border);
        color: var(--fg);
      }
      .block-container .stButton > button:focus {
        box-shadow: 0 0 0 3px color-mix(in srgb,
                    var(--ring) 18%, transparent);
      }

      /* ============================================================
         CHAT MESSAGES
         ============================================================ */
      [data-testid="stChatMessage"] {
        background: var(--card);
        color: var(--fg);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem 1.15rem;
        margin-bottom: 0.75rem;
        box-shadow: none;
      }
      [data-testid="stChatMessage"]:has(
        [data-testid="stChatMessageAvatarUser"]
      ) {
        background: var(--muted);
      }
      [data-testid="stChatMessage"] p,
      [data-testid="stChatMessage"] li {
        color: var(--fg);
        font-size: 0.95rem;
        line-height: 1.6;
      }
      [data-testid="stChatMessage"] [data-testid="stChatMessageAvatar"] {
        background: var(--muted) !important;
        border: 1px solid var(--border) !important;
      }

      /* ============================================================
         PINNED CHAT INPUT
         ============================================================ */
      [data-testid="stBottom"] > div,
      [data-testid="stBottomBlockContainer"] {
        background: var(--bg) !important;
        border-top: 1px solid transparent !important;
      }
      [data-testid="stChatInput"] {
        background: var(--card) !important;
        border: 1px solid var(--input-border) !important;
        border-radius: var(--radius) !important;
        box-shadow: none !important;
      }
      [data-testid="stChatInput"]:focus-within {
        border-color: var(--ring) !important;
        box-shadow: 0 0 0 3px color-mix(in srgb,
                    var(--ring) 15%, transparent) !important;
      }
      [data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: var(--fg) !important;
        font-size: 0.95rem !important;
      }
      [data-testid="stChatInput"] textarea::placeholder {
        color: var(--fg-muted) !important;
      }
      [data-testid="stChatInput"] button {
        background: var(--primary) !important;
        color: var(--primary-fg) !important;
        border-radius: 10px !important;
      }
      [data-testid="stChatInput"] button:hover {
        background: color-mix(in srgb, var(--primary) 88%, white) !important;
      }
      [data-testid="stChatInput"] button:disabled {
        background: var(--accent) !important;
        color: var(--fg-muted) !important;
      }

      /* ============================================================
         SOURCES
         ============================================================ */
      [data-testid="stExpander"] {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        background: var(--card);
        margin-top: 0.5rem;
      }
      [data-testid="stExpander"] summary {
        font-size: 0.8rem;
        color: var(--fg-muted);
        font-weight: 500;
        padding: 0.5rem 0.75rem;
      }
      [data-testid="stExpander"] summary:hover { color: var(--fg); }
      .source-card {
        background: var(--muted);
        border: 1px solid var(--border);
        border-left: 2px solid var(--primary);
        border-radius: 10px;
        padding: 0.7rem 0.9rem;
        margin: 0.5rem 0;
      }
      .source-card .src-title {
        font-weight: 600;
        color: var(--primary);
        font-size: 0.85rem;
      }
      .source-card .src-meta {
        color: var(--fg-muted);
        font-size: 0.75rem;
        margin-left: 0.5rem;
      }
      .source-card .src-snippet {
        color: var(--fg);
        opacity: 0.8;
        margin-top: 0.4rem;
        font-size: 0.85rem;
        line-height: 1.55;
      }

      hr { border-color: var(--border) !important; opacity: 1; }
      [data-testid="stSpinner"] > div { border-top-color: var(--primary) !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# State model
#   conversations: dict[id -> {title, created_at, messages: [...]}]
#   current_id:    id of the active conversation (None = empty/hero)
#   pending:       prompt to process on next run (from chip or new chat)
# ---------------------------------------------------------------------------
if "conversations" not in st.session_state:
    st.session_state.conversations = load_chats()
if "current_id" not in st.session_state:
    st.session_state.current_id = None
if "pending" not in st.session_state:
    st.session_state.pending = None


def new_conversation(first_prompt: str) -> str:
    cid = uuid.uuid4().hex[:8]
    title = first_prompt.strip().split("\n")[0][:48]
    if len(first_prompt.strip()) > 48:
        title += "…"
    st.session_state.conversations[cid] = {
        "title": title or "New chat",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "messages": [],
    }
    return cid


def current_messages():
    cid = st.session_state.current_id
    if cid and cid in st.session_state.conversations:
        return st.session_state.conversations[cid]["messages"]
    return []


def render_sources(hits):
    if not hits:
        return
    label = f"{len(hits)} source{'s' if len(hits) != 1 else ''} used"
    with st.expander(label):
        for h in hits:
            snippet = h["text"][:400].replace("\n", " ").strip()
            st.markdown(
                f"""
                <div class="source-card">
                  <span class="src-title">{h['source']}</span>
                  <span class="src-meta">similarity {h['similarity']}</span>
                  <div class="src-snippet">"{snippet}…"</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def run_turn(prompt: str):
    """Append user turn, run RAG, append assistant turn into current conv."""
    # If no active conversation, create one
    if st.session_state.current_id is None:
        st.session_state.current_id = new_conversation(prompt)

    msgs = current_messages()
    msgs.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Searching the notes..."):
            clean = [
                {"role": m["role"], "content": m["content"]} for m in msgs
            ]
            reply, hits = answer(prompt, clean)
        st.markdown(reply)
        render_sources(hits)
    msgs.append({"role": "assistant", "content": reply, "sources": hits})
    save_chats(st.session_state.conversations)


# ---------------------------------------------------------------------------
# SIDEBAR — chat history
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="side-brand">'
        '  <span class="side-brand-title">Study Buddy</span>'
        '  <span class="side-brand-sub">RAG</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.button("＋  New chat", key="new_chat", use_container_width=True):
        st.session_state.current_id = None
        st.session_state.pending = None
        st.rerun()

    st.markdown('<div class="side-section">Recent</div>', unsafe_allow_html=True)

    convs = st.session_state.conversations
    if not convs:
        st.markdown(
            '<div class="side-empty">No chats yet</div>',
            unsafe_allow_html=True,
        )
    else:
        # Most recent first
        items = sorted(
            convs.items(), key=lambda kv: kv[1]["created_at"], reverse=True
        )
        for cid, conv in items:
            is_active = cid == st.session_state.current_id
            if st.button(
                conv["title"],
                key=f"conv_{cid}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.current_id = cid
                st.session_state.pending = None
                st.rerun()

    if convs:
        st.divider()
        if st.button(
            "Clear all chats", key="clear_all", use_container_width=True
        ):
            st.session_state.conversations = {}
            st.session_state.current_id = None
            st.session_state.pending = None
            save_chats({})
            st.rerun()


# ---------------------------------------------------------------------------
# TOP BAR
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="topbar">'
    '  <div class="topbar-brand">'
    '    <span class="topbar-title">Study Buddy</span>'
    '    <span class="topbar-sub">RAG over your notes</span>'
    '  </div>'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# BODY — hero when no active conversation, chat otherwise
# ---------------------------------------------------------------------------
if st.session_state.current_id is None and st.session_state.pending is None:
    st.markdown(
        """
        <div class="hero">
          <div class="hero-eyebrow">Study Buddy</div>
          <h1 class="hero-title">What can I help you study?</h1>
          <p class="hero-sub">
            Ask anything from your notes. Answers come only from your
            documents, with sources attached.
          </p>
        </div>
        <div class="chip-label">Try one of these</div>
        """,
        unsafe_allow_html=True,
    )

    chips = [
        "What is RAG?",
        "Explain cosine similarity",
        "How do embeddings work?",
        "What is a transformer?",
    ]
    cols = st.columns(len(chips))
    for col, chip in zip(cols, chips):
        with col:
            if st.button(chip, key=f"chip_{chip}", use_container_width=True):
                st.session_state.pending = chip
                st.rerun()
else:
    # Replay existing messages
    for msg in current_messages():
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                render_sources(msg["sources"])

    # Process a chip-triggered prompt
    if st.session_state.pending:
        prompt = st.session_state.pending
        st.session_state.pending = None
        run_turn(prompt)

# ---------------------------------------------------------------------------
# PINNED CHAT INPUT
# ---------------------------------------------------------------------------
if prompt := st.chat_input("Ask Study Buddy a question..."):
    run_turn(prompt)
    st.rerun()
