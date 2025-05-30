import streamlit as st
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread

st.set_page_config(page_title="Mental Health Screening (Static Form)", page_icon="📝", layout="centered")

st.title("📝 Mental Health Screening (Neutral Interface)")
st.markdown("""
Welcome to this mental health screening form. Please answer the following questions as honestly as possible.

**Note:** Your responses are confidential, anonymous, and will not be reviewed by medical professionals.
""")

scale = ["Not at all (0)", "Several days (1)", "More than half the days (2)", "Nearly every day (3)"]

st.header("PHQ-9 Depression Screening")
phq9_items = [
    "Little interest or pleasure in doing things",
    "Feeling down, depressed, or hopeless",
    "Trouble falling or staying asleep, or sleeping too much",
    "Feeling tired or having little energy",
    "Poor appetite or overeating",
    "Feeling bad about yourself — or that you are a failure",
    "Trouble concentrating on things",
    "Moving or speaking slowly or being fidgety/restless",
    "Thoughts that you would be better off dead or hurting yourself"
]

phq9_scores = []
for idx, question in enumerate(phq9_items):
    response = st.radio(f"{idx+1}. {question}", scale, key=f"phq9_{idx}")
    phq9_scores.append(scale.index(response))

st.header("GAD-7 Anxiety Screening")
gad7_items = [
    "Feeling nervous, anxious or on edge",
    "Not being able to stop or control worrying",
    "Worrying too much about different things",
    "Trouble relaxing",
    "Being so restless that it's hard to sit still",
    "Becoming easily annoyed or irritable",
    "Feeling afraid as if something awful might happen"
]

gad7_scores = []
for idx, question in enumerate(gad7_items):
    response = st.radio(f"{idx+1}. {question}", scale, key=f"gad7_{idx}")
    gad7_scores.append(scale.index(response))

st.header("Demographic Information")
age = st.number_input("Your age:", min_value=18, max_value=100, value=25, step=1)
gender = st.selectbox("Your gender:", ["Prefer not to say", "Male", "Female", "Other"])
# mental_health_history = st.selectbox("Have you received mental health care in the past?", ["Prefer not to say", "Yes", "No"])

if st.button("Submit"):
    timestamp = datetime.utcnow().isoformat()
    total_phq9 = sum(phq9_scores)
    total_gad7 = sum(gad7_scores)

    st.success("Form submitted successfully!")
    st.markdown(f"**PHQ-9 Total Score:** {total_phq9}")
    st.markdown(f"**GAD-7 Total Score:** {total_gad7}")
    st.markdown("Please note that this feedback is automatic and does not constitute a diagnosis.")

    row = [
        "",  
        gender,
        age,
        "", 
        total_phq9,
        total_gad7,
        "",  
        "",  
        "",  
        "",  
        "",  
        "static"  
    ]

    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(
        st.secrets["google_sheets"],  # ✅ this matches your Elli config
        scopes=scope,
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(st.secrets["google_sheets"]["sheet_id"])
        worksheet = sheet.sheet1  

        worksheet.append_row(row, value_input_option="USER_ENTERED")
        st.success("✅ Your responses have been recorded.")
    except Exception as e:
        st.error(f"❌ Data submission failed: {e}")