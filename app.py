import streamlit as st
import sqlite3
from datetime import datetime

# --- Database setup ---
conn = sqlite3.connect("journal.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    mood TEXT,
    thank1_who TEXT,
    thank1_for TEXT,
    thank2_who TEXT,
    thank2_for TEXT,
    thank3_who TEXT,
    thank3_for TEXT,
    thoughts TEXT
)
""")
conn.commit()

# --- Page layout ---
st.set_page_config(page_title="Habit Thankful Journal", page_icon="🪶", layout="centered")
st.title("🪶 Habit Thankful Journal")

st.write("Take a moment to slow down and reflect ✨")

# --- Form layout ---
mood = st.selectbox("Mood", ["😊 Happy", "😐 Neutral", "😞 Sad", "🤩 Excited", "😔 Tired"])

thank1_who = st.text_input("I thank (1):", placeholder="Who are you thankful for?")
thank1_for = st.text_input("for (1):", placeholder="What did they do?")

thank2_who = st.text_input("I thank (2):", placeholder="Who else?")
thank2_for = st.text_input("for (2):", placeholder="What did they do?")

thank3_who = st.text_input("I thank (3):", placeholder="Another person or thing?")
thank3_for = st.text_input("for (3):", placeholder="What did they do?")

thoughts = st.text_area("My thoughts and journey today...", height=200)

# --- Save button ---
if st.button("💾 Save Today's Entry"):
    c.execute("""
        INSERT INTO entries (
            date, mood,
            thank1_who, thank1_for,
            thank2_who, thank2_for,
            thank3_who, thank3_for,
            thoughts
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        mood,
        thank1_who, thank1_for,
        thank2_who, thank2_for,
        thank3_who, thank3_for,
        thoughts
    ))
    conn.commit()
    st.success("✅ Entry saved successfully!")

# --- View past entries section ---
st.markdown("---")
st.subheader("📖 Past Entries")

rows = c.execute("SELECT * FROM entries ORDER BY date DESC").fetchall()
for r in rows:
    st.markdown(f"""
    **📅 {r[1]}** | {r[2]}  
    🪶 **1.** I thank *{r[3]}* for *{r[4]}*  
    🪶 **2.** I thank *{r[5]}* for *{r[6]}*  
    🪶 **3.** I thank *{r[7]}* for *{r[8]}*  
    > {r[9]}
    ---
    """)

conn.close()