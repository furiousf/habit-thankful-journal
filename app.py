import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# --- Page setup ---
st.set_page_config(
    page_title="Habit Thankful Journal",
    page_icon="🪶",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Mobile-friendly CSS ---
st.markdown("""
<style>
main, .block-container {max-width: 650px; margin:auto; padding:1rem 1.2rem;}
html, body, [class*="css"] {font-size:18px; line-height:1.5;}
button, .stButton>button, .stSelectbox, .stTextInput>div>input, textarea {
    font-size:18px!important; padding:0.6rem!important;
}
@media (max-width:600px){
 .stPlotlyChart,.stAltairChart,.stVegaLiteChart,.stMarkdown,.stImage{width:95%!important;margin:auto;}
 .stButton>button{width:100%;}
 h1,h2,h3{font-size:22px!important;}
}
#MainMenu, footer, header {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# --- Google Sheet setup ---
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPE)
client = gspread.authorize(CREDS)
SHEET_URL = "https://docs.google.com/spreadsheets/d/15hNZ96Lh5GGo0bQNl_XadE7B3Ii84XFBs7KH4Q03jLs/edit?usp=sharing"

journal_sheet = client.open_by_url(SHEET_URL).sheet1
thought_sheet = client.open_by_url(SHEET_URL).worksheet("JournalThoughts")

# --- Session setup ---
if "page" not in st.session_state:
    st.session_state.page = "home"

def goto(page):
    st.session_state.page = page
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()

# --- Load data ---
entries = journal_sheet.get_all_records()
df_entries = pd.DataFrame(entries) if entries else pd.DataFrame(
    columns=["timestamp","mood","thank1_who","thank1_for",
             "thank2_who","thank2_for","thank3_who","thank3_for"]
)

thoughts = thought_sheet.get_all_records()
df_thoughts = pd.DataFrame(thoughts) if thoughts else pd.DataFrame(
    columns=["date","thought","created_at"]
)

def get_thank_suggestions():
    try:
        names = pd.concat([
            df_entries["thank1_who"], df_entries["thank2_who"], df_entries["thank3_who"]
        ], ignore_index=True)
        names = names.dropna().astype(str).str.strip()
        names = names[names != ""]
        return sorted(names.unique().tolist())
    except Exception:
        return []

# --- Sidebar navigation ---
st.sidebar.title("🪶 Habit Thankful Journal")
menu = st.sidebar.radio("Navigate", ["🏠 Home","✍️ Journal","📊 Stats","📜 History"])
if menu == "🏠 Home": st.session_state.page = "home"
elif menu == "✍️ Journal": st.session_state.page = "journal"
elif menu == "📊 Stats": st.session_state.page = "stats"
elif menu == "📜 History": st.session_state.page = "history"

# ============================================================
#  HOME PAGE
# ============================================================
if st.session_state.page == "home":
    st.title("🪶 Habit Thankful Journal")
    st.write("Welcome to your gratitude and reflection space 🌿")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✍️ Write / Edit Journal", use_container_width=True): goto("journal")
    with col2:
        if st.button("📊 View Stats", use_container_width=True): goto("stats")
    st.markdown("---")
    st.write("Reflect daily. Be thankful. Grow mindfully 🌞")

# ============================================================
#  JOURNAL PAGE (entry + multiple thoughts)
# ============================================================
elif st.session_state.page == "journal":
    st.title("✍️ Create or Edit Journal Entry")

    today = date.today()
    min_date = today - timedelta(days=7)
    entry_date = st.date_input("📅 Choose date (past 7 days only):",
                               value=today, min_value=min_date, max_value=today)

    mood_list = ["😊 Happy","😐 Neutral","😞 Sad","🤩 Excited","😔 Tired"]

    # Load existing entry if exists
    df_entries["date_only"] = df_entries["timestamp"].apply(lambda x:str(x).split(" ")[0] if x else "")
    existing = df_entries.loc[df_entries["date_only"] == str(entry_date)]
    existing = existing.iloc[0].to_dict() if not existing.empty else {}

    thank_suggestions = get_thank_suggestions()
    mood = st.selectbox("Mood", mood_list,
                        index=mood_list.index(existing.get("mood","😊 Happy")) if existing else 0)

    thank1_who = st.selectbox("I thank (1):", [""]+thank_suggestions,
                              index=([""]+thank_suggestions).index(existing.get("thank1_who",""))
                              if existing.get("thank1_who","") in thank_suggestions else 0)
    thank1_for = st.text_input("for (1):", value=existing.get("thank1_for",""))

    thank2_who = st.selectbox("I thank (2):", [""]+thank_suggestions,
                              index=([""]+thank_suggestions).index(existing.get("thank2_who",""))
                              if existing.get("thank2_who","") in thank_suggestions else 0)
    thank2_for = st.text_input("for (2):", value=existing.get("thank2_for",""))

    thank3_who = st.selectbox("I thank (3):", [""]+thank_suggestions,
                              index=([""]+thank_suggestions).index(existing.get("thank3_who",""))
                              if existing.get("thank3_who","") in thank_suggestions else 0)
    thank3_for = st.text_input("for (3):", value=existing.get("thank3_for",""))

    # --- Thoughts section ---
    st.markdown("### 💭 Thoughts for this day")
    day_thoughts = df_thoughts[df_thoughts["date"] == str(entry_date)]
    for idx, row in day_thoughts.iterrows():
        st.text_area(f"Thought {idx+1}", value=row["thought"], height=100, disabled=True)

    if "thought_fields" not in st.session_state:
        st.session_state.thought_fields = [""]

    new_thoughts = []
    for i, val in enumerate(st.session_state.thought_fields):
        new_val = st.text_area(f"Add new thought {i+1}", value=val, height=100, key=f"new_thought_{i}")
        new_thoughts.append(new_val)

    if st.button("➕ Add another thought"):
        st.session_state.thought_fields.append("")
        try:
            st.rerun()
        except Exception:
            st.experimental_rerun()

    # --- Save button ---
    if st.button("💾 Save to Google Sheet"):
        timestamp = f"{entry_date} {datetime.now().strftime('%H:%M')}"
        row = [timestamp,mood,thank1_who,thank1_for,
               thank2_who,thank2_for,thank3_who,thank3_for]
        if not existing:
            journal_sheet.append_row(row)
        else:
            row_index = df_entries.index[df_entries["date_only"]==str(entry_date)][0]+2
            journal_sheet.update(f"A{row_index}:H{row_index}", [row])

        for t in new_thoughts:
            if t.strip():
                thought_sheet.append_row([str(entry_date), t.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")])
        st.success(f"✅ Entry and new thoughts saved for {entry_date}!")

    if st.button("🏠 Back to Home"): goto("home")

# ============================================================
#  STATS PAGE
# ============================================================
elif st.session_state.page == "stats":
    st.title("📊 Mood & Gratitude Insights")

    if df_entries.empty:
        st.info("No data yet 🌱 Please write some journal entries first.")
    else:
        df_entries["timestamp_dt"] = pd.to_datetime(df_entries["timestamp"], errors="coerce")
        today = date.today()

        col1, col2, _ = st.columns([1,1,2])
        with col1:
            if st.button("Last 7 Days"): st.session_state.selected_filter="7"
        with col2:
            if st.button("Last 30 Days"): st.session_state.selected_filter="30"

        if st.session_state.get("selected_filter")=="7":
            start_date=today-timedelta(days=7); end_date=today
            st.info(f"📅 Showing data from **{start_date}** to **{end_date}** (Last 7 days)")
        elif st.session_state.get("selected_filter")=="30":
            start_date=today-timedelta(days=30); end_date=today
            st.info(f"📅 Showing data from **{start_date}** to **{end_date}** (Last 30 days)")
        else:
            default_start=today-timedelta(days=30)
            date_range=st.date_input("📅 Select date range:", value=(default_start,today))
            start_date,end_date=date_range
            st.info(f"📅 Showing data from **{start_date}** to **{end_date}**")

        mask=(df_entries["timestamp_dt"].dt.date>=start_date)&(df_entries["timestamp_dt"].dt.date<=end_date)
        filtered=df_entries.loc[mask]
        chart_type=st.radio("Chart type:",["Bar","Pie"],horizontal=True)

        st.subheader("😊 Mood distribution")
        if not filtered.empty:
            mood_count=filtered.groupby("mood").size().reset_index(name="count")
            if chart_type=="Bar":
                st.bar_chart(mood_count.set_index("mood"),height=200)
            else:
                fig,ax=plt.subplots(figsize=(3,3))
                ax.pie(mood_count["count"],labels=mood_count["mood"],
                       autopct="%1.0f%%",startangle=90); ax.axis("equal")
                st.pyplot(fig)
        else:
            st.write("No mood data for this period.")

        st.subheader("🙌 Most thanked people")
        people=pd.concat([filtered["thank1_who"],filtered["thank2_who"],filtered["thank3_who"]]).dropna()
        if not people.empty:
            top_people=people.value_counts().head(10)
            if chart_type=="Bar":
                st.bar_chart(top_people,height=200)
            else:
                fig,ax=plt.subplots(figsize=(3,3))
                ax.pie(top_people.values,labels=top_people.index,
                       autopct="%1.0f%%",startangle=90); ax.axis("equal")
                st.pyplot(fig)
        else:
            st.write("No people data for this period.")

        st.subheader("💭 Total thoughts added")
        st.write(f"🧠 You have written {len(df_thoughts)} thoughts in total!")

    if st.button("🏠 Back to Home"): goto("home")

# ============================================================
#  HISTORY PAGE
# ============================================================
elif st.session_state.page == "history":
    st.title("📜 Journal History")

    if df_entries.empty:
        st.info("No data yet 🌱 Write your first gratitude entry.")
    else:
        df_display = df_entries.copy()
        df_display["Date"] = pd.to_datetime(df_display["timestamp"], errors="coerce").dt.date

        # Merge with number of thoughts
        thought_counts = df_thoughts.groupby("date").size().reset_index(name="ThoughtsCount")
        df_display = pd.merge(df_display, thought_counts, how="left",
                              left_on="Date", right_on="date").fillna({"ThoughtsCount":0})

        df_display = df_display[[
            "Date","mood","ThoughtsCount",
            "thank1_who","thank1_for",
            "thank2_who","thank2_for",
            "thank3_who","thank3_for"
        ]].sort_values("Date", ascending=False)

        st.dataframe(df_display, use_container_width=True, height=500)
        st.caption("🕒 Showing all journal records (latest first).")

    if st.button("🏠 Back to Home"): goto("home")