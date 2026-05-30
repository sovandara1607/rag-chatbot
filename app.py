"""
app.py  —  STEP 3 of RAG: the chat interface (Frontend Developer's file).

Run it with:
    streamlit run app.py

Features:
  - A chat box with full conversation history.
  - Each bot answer shows the source passages it used, inside an expander
    ("render citations visibly inside chat bubbles").
"""

import streamlit as st
from rag_core import answer

st.set_page_config(page_title="Study Buddy — RAG Chatbot", page_icon="📚")
st.title("Study Buddy")
st.caption("An open-book AI that answers from your documents using RAG.")

# --- conversation history lives in session_state so it survives reruns -------
if "history" not in st.session_state:
    st.session_state.history = []   # list of {role, content}

# Replay the conversation so far
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # If we saved citations for this assistant turn, show them.
        if msg.get("sources"):
            with st.expander("📎 Sources used"):
                for h in msg["sources"]:
                    st.markdown(
                        f"**{h['source']}** · similarity {h['similarity']}\n\n"
                        f"> {h['text'][:400]}…"
                    )

# --- handle a new question ---------------------------------------------------
if prompt := st.chat_input("Ask me something from the notes..."):
    # show + store the user turn
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # run the RAG pipeline
    with st.chat_message("assistant"):
        with st.spinner("Searching the notes..."):
            # pass only role/content pairs to the LLM, not our extra fields
            clean_history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.history
            ]
            reply, hits = answer(prompt, clean_history)
        st.markdown(reply)
        with st.expander("📎 Sources used"):
            for h in hits:
                st.markdown(
                    f"**{h['source']}** · similarity {h['similarity']}\n\n"
                    f"> {h['text'][:400]}…"
                )

    # store the assistant turn (with its citations)
    st.session_state.history.append(
        {"role": "assistant", "content": reply, "sources": hits}
    )

with st.sidebar:
    st.header("About")
    st.write(
        "This bot retrieves relevant chunks from a ChromaDB vector store "
        "and feeds them to an LLM. It only answers from your data."
    )
    if st.button("Clear chat"):
        st.session_state.history = []
        st.rerun()
