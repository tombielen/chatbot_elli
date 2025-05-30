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

def interpret_phq(score):
    if score <= 4:
        return "Minimal depression"
    elif score <= 9:
        return "Mild depression"
    elif score <= 14:
        return "Moderate depression"
    elif score <= 19:
        return "Moderately severe depression"
    else:
        return "Severe depression"

def interpret_gad(score):
    if score <= 4:
        return "Minimal anxiety"
    elif score <= 9:
        return "Mild anxiety"
    elif score <= 14:
        return "Moderate anxiety"
    else:
        return "Severe anxiety"

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
mental_health_history = st.selectbox("Have you received mental health care in the past?", ["Prefer not to say", "Yes", "No"])

if st.button("Submit Questionnaire"):
    total_phq9 = sum(phq9_scores)
    total_gad7 = sum(gad7_scores)
    phq_interp = interpret_phq(total_phq9)
    gad_interp = interpret_gad(total_gad7)

    st.success("✅ Your responses have been recorded.")
    st.markdown(f"**PHQ-9 Total Score:** {total_phq9} ({phq_interp})")
    st.markdown(f"**GAD-7 Total Score:** {total_gad7} ({gad_interp})")
    st.markdown("Please note that this feedback is automatic and does not constitute a diagnosis.")

    st.header("Your Experience")
    trust = st.radio("How much did you trust the questionnaire process?", [1, 2, 3, 4, 5], index=2)
    comfort = st.radio("How comfortable did you feel while answering?", [1, 2, 3, 4, 5], index=2)
    feedback = st.text_area("Do you have any feedback about your experience?", "")

    if st.button("Submit Experience Feedback"):
        row = [
            "",  
            gender,
            age,
            "", 
            total_phq9,
            total_gad7,
            f"{phq_interp}; {gad_interp}",
            trust,
            comfort,
            "",  
            feedback,
            "static"
        ]

        try:
            scope = ["https://www.googleapis.com/auth/spreadsheets"]
            creds = Credentials.from_service_account_info(
                st.secrets["google_sheets"],
                scopes=scope,
            )
            client = gspread.authorize(creds)
            sheet = client.open_by_key(st.secrets["google_sheets"]["sheet_id"])
            worksheet = sheet.sheet1
            worksheet.append_row(row, value_input_option="USER_ENTERED")
            st.success("✅ Your responses and feedback have been logged. Thank you for participating!")
        except Exception as e:
            st.error(f"❌ Data submission failed: {e}")
