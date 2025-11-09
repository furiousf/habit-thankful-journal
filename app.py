import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta
from supabase import create_client, Client
from urllib.parse import urlencode

# ------------------------------------------------------------
# Config
# ------------------------------------------------------------
st.set_page_config(
    page_title="Habit Thankful Journal",
    page_icon="🪶",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Supabase client
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["anon_key"]
REDIRECT_URL = st.secrets["supabase"]["redirect_url"]
PROVIDERS = st.secrets["supabase"].get("providers", ["google"])

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------------------------------------------
# Auth helpers
# ------------------------------------------------------------
def build_oauth_url(provider: str) -> str:
    # Construct OAuth URL (PKCE). Supabase-py returns an object in newer versions,
    # but building the URL manually is robust and explicit.
    params = {
        "provider": provider,
        "redirect_to": REDIRECT_URL,
    }
    return f"{SUPABASE_URL}/auth/v1/authorize?{urlencode(params)}"

def exchange_code_for_session():
    # Handle OAuth code after redirect back from provider
    code = st.query_params.get("code", None)
    if not code:
        return None
    try:
        res = supabase.auth.exchange_code_for_session({"auth_code": code})
        # Persist session user
        if res and res.user:
            st.session_state["sb_user"] = res.user
            # Clear code from URL (nicer UX)
            st.query_params.clear()
            return res.user
    except Exception:
        pass
    return None

def get_user():
    # 1) Already signed in this session?
    if "sb_user" in st.session_state and st.session_state["sb_user"]:
        return st.session_state["sb_user"]
    # 2) Did we just come back from OAuth provider?
    user = exchange_code_for_session()
    if user:
        return user
    # 3) Not logged in
    return None

def require_auth():
    user = get_user()
    if user:
        return user
    st.title("🪶 Habit Thankful Journal")
    st.subheader("Sign in to continue")
    cols = st.columns(len(PROVIDERS))
    for i, prov in enumerate(PROVIDERS):
        with cols[i]:
            if st.button(f"Sign in with {prov.title()}", use_container_width=True):
                st.link_button(
                    f"Click here if not redirected",
                    build_oauth_url(prov),
                    use_container_width=True,
                    type="primary",
                )
                st.stop()
    st.stop()

# ------------------------------------------------------------
# Data helpers
# ------------------------------------------------------------
def load_entries(user_id: str) -> pd.DataFrame:
    res = supabase.table("journal_entries").select("*").eq("user_id", user_id).execute()
    rows = res.data or []
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=[
            "id","user_id","date","mood","thank1_who","thank1_for",
            "thank2_who","thank2_for","thank3_who","thank3_for","journal",
            "inserted_at","updated_at"
        ])
    return df

def load_thoughts(user_id: str) -> pd.DataFrame:
    res = supabase.table("thoughts").select("*").eq("user_id", user_id).execute()
    rows = res.data or []
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["id","user_id","date","thought","created_at"])
    return df

def get_thank_suggestions(df_entries: pd.DataFrame):
    cols = ["thank1_who", "thank2_who", "thank3_who"]
    names = pd.Series(dtype=str)
    for c in cols:
        if c in df_entries.columns:
            names = pd.concat([names, df_entries[c].dropna().astype(str).str.strip()])
    names = names[names != ""].unique().tolist()
    return sorted(names)

def upsert_journal(user_id: str, entry_date: date, payload: dict):
    # upsert by (user_id, date)
    payload = dict(payload)
    payload["user_id"] = user_id
    payload["date"] = str(entry_date)
    supabase.table("journal_entries").upsert(payload, on_conflict="user_id,date").execute()

def add_thought(user_id: str, thought_date: date, text: str):
    supabase.table("thoughts").insert({
        "user_id": user_id,
        "date": str(thought_date),
        "thought": text.strip()
    }).execute()

# ------------------------------------------------------------
# UI: Sidebar Navigation
# ------------------------------------------------------------
user = require_auth()
user_id = user.id

st.sidebar.title("🪶 Habit Thankful Journal")
menu = st.sidebar.radio(
    "Navigate",
    [
        "🏠 Home (Stats)",
        "✍️ Journal",
        "🧠 Thoughts Explorer",
        "🙏 Thankful History",
        "📜 Journal History",
    ]
)

# Preload data for pages
df_entries = load_entries(user_id)
df_thoughts = load_thoughts(user_id)

# ------------------------------------------------------------
# 🏠 Home (Stats)
# ------------------------------------------------------------
if menu == "🏠 Home (Stats)":
    st.title("🏠 Home Dashboard — Mood & Gratitude Insights")

    if df_entries.empty:
        st.info("No data yet 🌱 Create your first entry on the Journal page.")
    else:
        df_entries["date_dt"] = pd.to_datetime(df_entries["date"], errors="coerce")

        # Quick filters
        col1, col2, _ = st.columns([1, 1, 2])
        quick = st.session_state.get("home_quick", None)
        with col1:
            if st.button("Last 7 Days"): st.session_state["home_quick"] = 7
        with col2:
            if st.button("Last 30 Days"): st.session_state["home_quick"] = 30

        today = date.today()
        if st.session_state.get("home_quick") == 7:
            start, end = today - timedelta(days=7), today
        elif st.session_state.get("home_quick") == 30:
            start, end = today - timedelta(days=30), today
        else:
            default_start = today - timedelta(days=30)
            start, end = st.date_input("Custom range", (default_start, today))

        mask = (df_entries["date_dt"].dt.date >= start) & (df_entries["date_dt"].dt.date <= end)
        filtered = df_entries.loc[mask]

        chart_type = st.radio("Chart type", ["Bar", "Pie"], horizontal=True)

        # Mood chart
        st.subheader("😊 Mood distribution")
        if not filtered.empty and "mood" in filtered.columns:
            mood_count = filtered["mood"].value_counts()
            if chart_type == "Bar":
                st.bar_chart(mood_count, height=200)
            else:
                fig, ax = plt.subplots(figsize=(3,3))
                ax.pie(mood_count.values, labels=mood_count.index, autopct="%1.0f%%", startangle=90)
                ax.axis("equal")
                st.pyplot(fig)
        else:
            st.write("No mood data for this period.")

        # People thanked
        st.subheader("🙌 Most thanked people")
        who = pd.Series(dtype=str)
        for col in ["thank1_who","thank2_who","thank3_who"]:
            if col in filtered.columns:
                who = pd.concat([who, filtered[col].dropna().astype(str).str.strip()])
        who = who[who != ""]
        if not who.empty:
            top_people = who.value_counts().head(10)
            if chart_type == "Bar":
                st.bar_chart(top_people, height=200)
            else:
                fig, ax = plt.subplots(figsize=(3,3))
                ax.pie(top_people.values, labels=top_people.index, autopct="%1.0f%%", startangle=90)
                ax.axis("equal")
                st.pyplot(fig)
        else:
            st.write("No people data for this period.")

        # Thoughts count
        st.subheader("💭 Thoughts written")
        st.write(f"🧠 Total thoughts: **{len(df_thoughts)}**")

# ------------------------------------------------------------
# ✍️ Journal page (long journal + 3 thanks + thoughts)
# ------------------------------------------------------------
elif menu == "✍️ Journal":
    st.title("✍️ Create or Edit Journal Entry")

    today = date.today()
    min_date = today - timedelta(days=7)
    entry_date = st.date_input("📅 Choose date (past 7 days only):",
                               value=today, min_value=min_date, max_value=today)

    mood_list = ["😊 Happy","😐 Neutral","😞 Sad","🤩 Excited","😔 Tired"]

    # Existing
    existing = df_entries[df_entries["date"] == str(entry_date)]
    existing_row = existing.iloc[0].to_dict() if not existing.empty else {}

    thank_suggestions = get_thank_suggestions(df_entries)

    mood = st.selectbox("Mood", mood_list,
                        index=mood_list.index(existing_row.get("mood","😊 Happy")) if existing_row else 0)

    st.markdown("### 🙏 Gratitude for Today")
    # Editable inputs (type freely) + show top suggestions as caption
    st.markdown("#### 🙏 Gratitude #1")
    thank1_who = st.text_input("Who are you thankful for? (type or reuse)", value=existing_row.get("thank1_who",""))
    if thank_suggestions: st.caption("💡 Suggested: " + ", ".join(thank_suggestions[:5]))
    thank1_for = st.text_input("for (1):", value=existing_row.get("thank1_for",""))

    st.markdown("#### 🙏 Gratitude #2")
    thank2_who = st.text_input("Who else are you thankful for?", value=existing_row.get("thank2_who",""))
    if thank_suggestions: st.caption("💡 Suggested: " + ", ".join(thank_suggestions[:5]))
    thank2_for = st.text_input("for (2):", value=existing_row.get("thank2_for",""))

    st.markdown("#### 🙏 Gratitude #3")
    thank3_who = st.text_input("Anyone else you’re thankful for?", value=existing_row.get("thank3_who",""))
    if thank_suggestions: st.caption("💡 Suggested: " + ", ".join(thank_suggestions[:5]))
    thank3_for = st.text_input("for (3):", value=existing_row.get("thank3_for",""))

    st.markdown("### 📖 My Journal for Today")
    journal_text = st.text_area("Write your daily reflection:",
                                value=existing_row.get("journal",""),
                                height=250,
                                placeholder="Write your main reflection or summary for today...")

    st.markdown("### 💭 Additional Thoughts")
    day_thoughts = df_thoughts[df_thoughts["date"] == str(entry_date)]
    if not day_thoughts.empty:
        st.write(f"Existing thoughts for {entry_date}:")
        for i, r in day_thoughts.iterrows():
            st.text_area(f"Thought {i+1}", value=r["thought"], height=80, disabled=True)

    if "thought_fields" not in st.session_state:
        st.session_state.thought_fields = [""]

    new_thoughts = []
    for i, val in enumerate(st.session_state.thought_fields):
        new_val = st.text_area(f"Add new thought {i+1}", value=val, height=80, key=f"new_thought_{i}")
        new_thoughts.append(new_val)

    if st.button("➕ Add another thought"):
        st.session_state.thought_fields.append("")
        st.rerun()

    if st.button("💾 Save Journal & Thoughts"):
        upsert_journal(user_id, entry_date, {
            "mood": mood,
            "thank1_who": thank1_who, "thank1_for": thank1_for,
            "thank2_who": thank2_who, "thank2_for": thank2_for,
            "thank3_who": thank3_who, "thank3_for": thank3_for,
            "journal": journal_text.strip()
        })
        for t in new_thoughts:
            if t and t.strip():
                add_thought(user_id, entry_date, t.strip())
        st.session_state.thought_fields = [""]
        st.success(f"✅ Saved entry for {entry_date}")
        st.rerun()

# ------------------------------------------------------------
# 🧠 Thoughts Explorer
# ------------------------------------------------------------
elif menu == "🧠 Thoughts Explorer":
    st.title("🧠 All Thoughts Explorer")

    st.markdown("### ✍️ Add a New Thought")
    c1, c2 = st.columns([2,1])
    with c1:
        new_thought_date = st.date_input("📅 Date", value=date.today(), key="th_date")
    with c2:
        use_now = st.checkbox("Use current time", value=True, key="th_now")

    new_thought = st.text_area("💭 Your Thought", height=100, key="th_text")

    if st.button("💾 Save Thought"):
        if new_thought and new_thought.strip():
            add_thought(user_id, new_thought_date, new_thought.strip())
            st.success("✅ New thought saved!")
            st.rerun()
        else:
            st.warning("⚠️ Please write something before saving.")

    st.markdown("---")

    if df_thoughts.empty:
        st.info("No thoughts yet 🌱")
    else:
        st.subheader("🧠 All Recorded Thoughts")
        c1, c2 = st.columns([1,2])
        with c1:
            df_thoughts["date_dt"] = pd.to_datetime(df_thoughts["date"], errors="coerce")
            date_filter = st.date_input("📅 Filter by date", value=None, key="th_filter")
        with c2:
            keyword = st.text_input("🔍 Search by keyword", key="th_kw")

        df_view = df_thoughts.copy()
        if date_filter:
            df_view = df_view[df_view["date_dt"].dt.date == date_filter]
        if keyword:
            df_view = df_view[df_view["thought"].str.contains(keyword, case=False, na=False)]

        df_view = df_view.sort_values("date_dt", ascending=False)
        df_view.rename(columns={"date":"Date","thought":"Thought","created_at":"Created"}, inplace=True)

        st.dataframe(df_view[["Date","Thought","Created"]], use_container_width=True, height=600)

# ------------------------------------------------------------
# 🙏 Thankful History (table)
# ------------------------------------------------------------
elif menu == "🙏 Thankful History":
    st.title("🙏 Thankful History")

    if df_entries.empty:
        st.info("No thankful entries yet 🌱")
    else:
        df = df_entries.copy()
        df["Date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
        df = df[[
            "Date","mood",
            "thank1_who","thank1_for",
            "thank2_who","thank2_for",
            "thank3_who","thank3_for"
        ]].sort_values("Date", ascending=False)

        c1, c2 = st.columns([1,2])
        with c1:
            d = st.date_input("📅 Filter by date", value=None, key="thk_date")
        with c2:
            k = st.text_input("🔍 Search name or keyword", key="thk_kw")

        view = df.copy()
        if d: view = view[view["Date"] == d]
        if k:
            mask = pd.Series(False, index=view.index)
            for col in ["thank1_who","thank1_for","thank2_who","thank2_for","thank3_who","thank3_for"]:
                mask = mask | view[col].astype(str).str.contains(k, case=False, na=False)
            view = view[mask]

        st.dataframe(view, use_container_width=True, height=600)

        csv = view.to_csv(index=False).encode("utf-8")
        st.download_button("📤 Download Thankful CSV", data=csv, file_name="thankful_history.csv", mime="text/csv")

# ------------------------------------------------------------
# 📜 Journal History (table)
# ------------------------------------------------------------
elif menu == "📜 Journal History":
    st.title("📜 Journal History")

    if df_entries.empty:
        st.info("No journal entries yet 🌱")
    else:
        df = df_entries.copy()
        df["Date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
        if "journal" not in df.columns:
            df["journal"] = ""
        df = df[["Date","mood","journal"]].sort_values("Date", ascending=False)

        c1, c2 = st.columns([1,2])
        with c1:
            d = st.date_input("📅 Filter by date", value=None, key="jh_date")
        with c2:
            k = st.text_input("🔍 Search keyword in journal", key="jh_kw")

        view = df.copy()
        if d: view = view[view["Date"] == d]
        if k:
            view = view[view["journal"].str.contains(k, case=False, na=False)]

        st.dataframe(view, use_container_width=True, height=600)

        csv = view.to_csv(index=False).encode("utf-8")
        st.download_button("📤 Download Journal CSV", data=csv, file_name="journal_history.csv", mime="text/csv")