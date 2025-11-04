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

# --- Google Sheet setup ---
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPE)
client = gspread.authorize(CREDS)
SHEET_URL = "https://docs.google.com/spreadsheets/d/15hNZ96Lh5GGo0bQNl_XadE7B3Ii84XFBs7KH4Q03jLs/edit?usp=sharing"

journal_sheet = client.open_by_url(SHEET_URL).sheet1
thought_sheet = client.open_by_url(SHEET_URL).worksheet("JournalThoughts")

# --- Session setup ---
if "page" not in st.session_state:
    st.session_state.page = "stats"

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
menu = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Home Summary",
        "✍️ Thankful Journal",
        "🧠 Thoughts Explorer",
        "🙏 Thankful History",
        "📜 Journal History"
    ]
)

if menu == "🏠 Home Summary":
    st.session_state.page = "stats"
elif menu == "✍️ Thankful Journal":
    st.session_state.page = "journal"
elif menu == "🧠 Thoughts Explorer":
    st.session_state.page = "thoughts"
elif menu == "🙏 Thankful History":
    st.session_state.page = "thankful_history"
elif menu == "📜 Journal History":
    st.session_state.page = "history"

# =========================
# Start a NEW ladder here ↓
# =========================


# ============================================================
#  JOURNAL PAGE (with long Journal + multiple thoughts)
# ============================================================
if st.session_state.page == "journal":
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

    # --- Gratitude section ---
    st.markdown("### 🙏 Gratitude for Today")

    # Gratitude #1
    st.markdown("#### 🙏 Gratitude #1")
    thank1_who = st.text_input(
        "Who are you thankful for? (type or reuse suggestion)",
        value=existing.get("thank1_who", "")
    )
    if thank_suggestions:
        st.caption("💡 Suggested: " + ", ".join(thank_suggestions[:5]))
    thank1_for = st.text_input(
        "for (1):",
        value=existing.get("thank1_for", ""),
        placeholder="What did they do that you appreciate?"
    )

    # Gratitude #2
    st.markdown("#### 🙏 Gratitude #2")
    thank2_who = st.text_input(
        "Who else are you thankful for?",
        value=existing.get("thank2_who", "")
    )
    if thank_suggestions:
        st.caption("💡 Suggested: " + ", ".join(thank_suggestions[:5]))
    thank2_for = st.text_input(
        "for (2):",
        value=existing.get("thank2_for", ""),
        placeholder="What did they do that you appreciate?"
    )

    # Gratitude #3
    st.markdown("#### 🙏 Gratitude #3")
    thank3_who = st.text_input(
        "Anyone else you’re thankful for?",
        value=existing.get("thank3_who", "")
    )
    if thank_suggestions:
        st.caption("💡 Suggested: " + ", ".join(thank_suggestions[:5]))
    thank3_for = st.text_input(
        "for (3):",
        value=existing.get("thank3_for", ""),
        placeholder="What did they do that you appreciate?"
    )

    # --- Long Journal section ---
    st.markdown("### 📖 My Journal for Today")
    journal_text = st.text_area(
        "Write your daily reflection:",
        value=existing.get("journal", ""),
        height=250,
        placeholder="Write your main reflection or summary for today..."
    )

    # --- Thoughts section ---
    st.markdown("### 💭 Additional Thoughts")
    day_thoughts = df_thoughts[df_thoughts["date"] == str(entry_date)]
    if not day_thoughts.empty:
        st.write(f"Existing thoughts for {entry_date}:")
        for idx, row in day_thoughts.iterrows():
            st.text_area(f"Thought {idx+1}", value=row["thought"], height=80, disabled=True)

    if "thought_fields" not in st.session_state:
        st.session_state.thought_fields = [""]

    new_thoughts = []
    for i, val in enumerate(st.session_state.thought_fields):
        new_val = st.text_area(f"Add new thought {i+1}", value=val, height=80, key=f"new_thought_{i}")
        new_thoughts.append(new_val)

    if st.button("➕ Add another thought"):
        st.session_state.thought_fields.append("")
        st.experimental_rerun()

    # --- Save button ---
    if st.button("💾 Save Journal & Thoughts"):
        timestamp = f"{entry_date} {datetime.now().strftime('%H:%M')}"
        row = [
            timestamp, mood,
            thank1_who, thank1_for,
            thank2_who, thank2_for,
            thank3_who, thank3_for,
            journal_text.strip()
        ]

        # Save or update main journal entry
        if not existing:
            journal_sheet.append_row(row)
        else:
            row_index = df_entries.index[df_entries["date_only"]==str(entry_date)][0]+2
            journal_sheet.update(f"A{row_index}:I{row_index}", [row])

        # Save multiple thoughts
        for t in new_thoughts:
            if t.strip():
                thought_sheet.append_row([
                    str(entry_date),
                    t.strip(),
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                ])

        st.success(f"✅ Journal and thoughts saved for {entry_date}!")
        st.session_state.thought_fields = [""]
        st.experimental_rerun()

    if st.button("🏠 Back to Home"):
        goto("stats")

# ============================================================
#  THOUGHTS EXPLORER PAGE
# ============================================================
elif st.session_state.page == "thoughts":
    st.title("🧠 All Thoughts Explorer")

    # --- Add new thought section ---
    st.markdown("### ✍️ Add a New Thought")
    col1, col2 = st.columns([2, 1])
    with col1:
        new_thought_date = st.date_input("📅 Date", value=date.today())
    with col2:
        add_now = st.checkbox("Use current time", value=True)

    new_thought = st.text_area(
        "💭 Your Thought",
        placeholder="Write what's on your mind...",
        height=100,
    )

    if st.button("💾 Save Thought"):
        if new_thought.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M") if add_now else ""
            thought_sheet.append_row([
                str(new_thought_date),
                new_thought.strip(),
                timestamp
            ])
            st.success("✅ New thought saved successfully!")
            st.session_state["refresh_thoughts"] = True
            st.rerun()
        else:
            st.warning("⚠️ Please write something before saving.")

    st.markdown("---")

    # --- View all thoughts section ---
    if df_thoughts.empty:
        st.info("No thoughts yet 🌱 Start by adding your first one above.")
    else:
        st.subheader("🧠 All Recorded Thoughts")

        col1, col2 = st.columns([1, 2])
        with col1:
            date_filter = st.date_input("📅 Filter by date", value=None)
        with col2:
            keyword = st.text_input("🔍 Search by keyword")

        # Reload data if refreshed
        if st.session_state.get("refresh_thoughts"):
            thoughts = thought_sheet.get_all_records()
            df_thoughts = pd.DataFrame(thoughts) if thoughts else pd.DataFrame(
                columns=["date", "thought", "created_at"]
            )
            st.session_state["refresh_thoughts"] = False

        df_view = df_thoughts.copy()
        df_view["date_dt"] = pd.to_datetime(df_view["date"], errors="coerce")

        if date_filter:
            df_view = df_view[df_view["date_dt"].dt.date == date_filter]
        if keyword:
            df_view = df_view[df_view["thought"].str.contains(keyword, case=False, na=False)]

        df_view = df_view.sort_values("date_dt", ascending=False)
        df_view.rename(columns={"date": "Date", "thought": "Thought", "created_at": "Created"}, inplace=True)

        st.dataframe(df_view[["Date","Thought","Created"]],
                     use_container_width=True, height=600)

    if st.button("🏠 Back to Home"):
        goto("stats")

# ============================================================
#  STATS PAGE
# ============================================================
elif st.session_state.page == "stats":
    st.title("🏠 Home Dashboard — Mood & Gratitude Insights")

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

    if st.button("🏠 Back to Home"): goto("stats")

# ============================================================
#  THANKFUL HISTORY PAGE
# ============================================================
elif st.session_state.page == "thankful_history":
    st.title("🙏 Thankful History")

    if df_entries.empty:
        st.info("No thankful entries yet 🌱 Write your first gratitude journal.")
    else:
        st.subheader("💖 Gratitude Records")

        df_thanks = df_entries.copy()
        df_thanks["Date"] = pd.to_datetime(df_thanks["timestamp"], errors="coerce").dt.date

        # Keep only relevant columns
        df_thanks = df_thanks[[
            "Date", "mood",
            "thank1_who", "thank1_for",
            "thank2_who", "thank2_for",
            "thank3_who", "thank3_for"
        ]].sort_values("Date", ascending=False)

        # --- Filters ---
        col1, col2 = st.columns([1, 2])
        with col1:
            date_filter = st.date_input("📅 Filter by date", value=None)
        with col2:
            keyword = st.text_input("🔍 Search name or keyword", placeholder="e.g. Mum, colleague, kindness...")

        df_view = df_thanks.copy()
        if date_filter:
            df_view = df_view[df_view["Date"] == date_filter]
        if keyword:
            mask = (
                df_view["thank1_who"].astype(str).str.contains(keyword, case=False, na=False) |
                df_view["thank1_for"].astype(str).str.contains(keyword, case=False, na=False) |
                df_view["thank2_who"].astype(str).str.contains(keyword, case=False, na=False) |
                df_view["thank2_for"].astype(str).str.contains(keyword, case=False, na=False) |
                df_view["thank3_who"].astype(str).str.contains(keyword, case=False, na=False) |
                df_view["thank3_for"].astype(str).str.contains(keyword, case=False, na=False)
            )
            df_view = df_view[mask]

        if df_view.empty:
            st.info("No thankful records match your filters.")
        else:
            st.dataframe(
                df_view,
                use_container_width=True,
                height=600,
            )
            st.caption("🕒 Showing all gratitude entries (newest first).")

        # --- Optional download ---
        csv_data = df_view.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📤 Download Thankful CSV",
            data=csv_data,
            file_name="thankful_history.csv",
            mime="text/csv",
        )

    if st.button("🏠 Back to Home"):
        goto("stats")

# ============================================================
#  HISTORY PAGE (Journal only, table view)
# ============================================================
elif st.session_state.page == "history":
    st.title("📜 Journal History")

    if df_entries.empty:
        st.info("No journal entries yet 🌱 Write your first one in the Journal page.")
    else:
        st.subheader("📔 My Journal Records")

        df_journal = df_entries.copy()
        df_journal["Date"] = pd.to_datetime(df_journal["timestamp"], errors="coerce").dt.date

        # Ensure journal column exists
        if "journal" not in df_journal.columns:
            df_journal["journal"] = ""

        # Keep key columns only
        df_journal = df_journal[["Date", "mood", "journal"]].sort_values("Date", ascending=False)

        # --- Filters ---
        col1, col2 = st.columns([1, 2])
        with col1:
            date_filter = st.date_input("📅 Filter by date", value=None)
        with col2:
            keyword = st.text_input("🔍 Search keyword in journal", placeholder="e.g. happy, grateful, family...")

        df_view = df_journal.copy()
        if date_filter:
            df_view = df_view[df_view["Date"] == date_filter]
        if keyword:
            df_view = df_view[df_view["journal"].str.contains(keyword, case=False, na=False)]

        if df_view.empty:
            st.info("No journal entries match your filters.")
        else:
            st.dataframe(
                df_view,
                use_container_width=True,
                height=600,
            )

            st.caption("🕒 Showing your daily journals in table view (newest first).")

        # --- Optional download ---
        csv_data = df_view.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📤 Download Journal CSV",
            data=csv_data,
            file_name="journal_history.csv",
            mime="text/csv",
        )

    if st.button("🏠 Back to Home"):
        goto("stats")