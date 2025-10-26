import streamlit as st
import sqlite3
from datetime import datetime

# --- database setup ---
conn = sqlite3.connect("journal.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    type TEXT,
    mood TEXT,
    content TEXT
)
""")
conn.commit()

# --- page config ---
st.set_page_config(page_title="Habit Thankful Journal", page_icon="🪶", layout="centered")
st.title("🪶 Habit Thankful Journal")

menu = ["Add Entry", "View Entries"]
choice = st.sidebar.radio("Menu", menu)

if choice == "Add Entry":
    st.subheader("✍️ Write a New Entry")
    entry_type = st.selectbox("Entry Type", ["Gratitude", "Journal"])
    mood = st.selectbox("Mood", ["😊 Happy", "😐 Neutral", "😞 Sad", "🤩 Excited", "😔 Tired"])
    content = st.text_area("Write your thoughts here...")

    if st.button("Save Entry"):
        c.execute("INSERT INTO entries (date, type, mood, content) VALUES (?, ?, ?, ?)",
                  (datetime.now().strftime("%Y-%m-%d %H:%M"), entry_type, mood, content))
        conn.commit()
        st.success("✅ Saved successfully!")

elif choice == "View Entries":
    st.subheader("📖 Past Entries")
    filter_type = st.radio("Filter by", ["All", "Gratitude", "Journal"])
    if filter_type == "All":
        rows = c.execute("SELECT * FROM entries ORDER BY date DESC").fetchall()
    else:
        rows = c.execute("SELECT * FROM entries WHERE type=? ORDER BY date DESC", (filter_type,)).fetchall()

    for r in rows:
        st.markdown(f"""
        **📅 {r[1]}**  
        🧠 *{r[2]}* | {r[3]}  
        > {r[4]}
        ---
        """)

conn.close()