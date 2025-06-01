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

# --- Scale & Interpretation ---
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

# --- Logging ---
def log_step_to_sheet(question, answer, step_type, elapsed=None):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["google_sheets"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(st.secrets["google_sheets"]["sheet_id"])
        worksheet = sheet.sheet1
        now = datetime.now().isoformat()
        row = [
            "",  # name
            st.session_state.get("gender", ""),
            st.session_state.get("age", ""),
            "",  # initial_feeling
            "",  # phq_total
            "",  # gad_total
            "",  # elli_interp
            "",  # trust
            "",  # comfort
            "",  # initial_mood
            "",  # user_reflection
            "static",
            step_type,
            question,
            answer,
            now,
            elapsed if elapsed is not None else ""
        ]
        worksheet.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        st.error(f"❌ Data submission failed: {e}")

# --- Content ---
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

gad7_items = [
    "Feeling nervous, anxious or on edge",
    "Not being able to stop or control worrying",
    "Worrying too much about different things",
    "Trouble relaxing",
    "Being so restless that it's hard to sit still",
    "Becoming easily annoyed or irritable",
    "Feeling afraid as if something awful might happen"
]

demographic_questions = [
    {"label": "Your age:", "type": "number", "min_value": 18, "max_value": 100, "value": 25, "step": 1, "key": "age"},
    {"label": "Your gender:", "type": "select", "options": ["Prefer not to say", "Male", "Female", "Other"], "key": "gender"},
    {"label": "Have you received mental health care in the past?", "type": "select", "options": ["Prefer not to say", "Yes", "No"], "key": "mental_health_history"},
]

feedback_questions = [
    {"label": "How much did you trust the questionnaire process?", "type": "radio", "options": [1, 2, 3, 4, 5], "key": "trust"},
    {"label": "How comfortable did you feel while answering?", "type": "radio", "options": [1, 2, 3, 4, 5], "key": "comfort"},
    {"label": "Do you have any feedback about your experience?", "type": "text", "key": "feedback"}
]

# --- State ---
for key, default in {
    "step": 0,
    "answers": [],
    "start_time": datetime.now().timestamp(),
    "main_done": False,
    "feedback_done": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- Form Logic ---
if not st.session_state.main_done:
    current = st.session_state.step
    if current < len(phq9_items):
        q = phq9_items[current]
        answer = st.radio(q, scale, key=f"phq9_{current}")
        if st.button("Next", key=f"next_{current}"):
            elapsed = datetime.now().timestamp() - st.session_state.start_time
            st.session_state.answers.append({"type": "phq9", "question": q, "answer": answer, "elapsed": elapsed})
            log_step_to_sheet(q, answer, "phq9", elapsed)
            st.session_state.step += 1
            st.session_state.start_time = datetime.now().timestamp()
            st.experimental_rerun()
    elif current < len(phq9_items) + len(gad7_items):
        idx = current - len(phq9_items)
        q = gad7_items[idx]
        answer = st.radio(q, scale, key=f"gad7_{idx}")
        if st.button("Next", key=f"next_{current}"):
            elapsed = datetime.now().timestamp() - st.session_state.start_time
            st.session_state.answers.append({"type": "gad7", "question": q, "answer": answer, "elapsed": elapsed})
            log_step_to_sheet(q, answer, "gad7", elapsed)
            st.session_state.step += 1
            st.session_state.start_time = datetime.now().timestamp()
            st.experimental_rerun()
    elif current < len(phq9_items) + len(gad7_items) + len(demographic_questions):
        idx = current - len(phq9_items) - len(gad7_items)
        dq = demographic_questions[idx]
        if dq["type"] == "number":
            answer = st.number_input(dq["label"], min_value=dq["min_value"], max_value=dq["max_value"], value=dq["value"], step=dq["step"], key=dq["key"])
        else:
            answer = st.selectbox(dq["label"], dq["options"], key=dq["key"])
        if st.button("Next", key=f"next_{current}"):
            elapsed = datetime.now().timestamp() - st.session_state.start_time
            st.session_state.answers.append({"type": "demographic", "question": dq["label"], "answer": answer, "elapsed": elapsed})
            log_step_to_sheet(dq["label"], answer, "demographic", elapsed)
            st.session_state.start_time = datetime.now().timestamp()
            st.session_state.step += 1
            st.experimental_rerun()
    else:
        st.session_state.main_done = True
        st.session_state.start_time = datetime.now().timestamp()
        st.experimental_rerun()

# --- Results + Feedback ---
if st.session_state.main_done and not st.session_state.feedback_done:
    st.success("✅ You have completed the questionnaire.")
    phq9_scores = [scale.index(ans["answer"]) for ans in st.session_state.answers if ans["type"] == "phq9"]
    gad7_scores = [scale.index(ans["answer"]) for ans in st.session_state.answers if ans["type"] == "gad7"]
    total_phq9 = sum(phq9_scores)
    total_gad7 = sum(gad7_scores)
    phq_interp = interpret_phq(total_phq9)
    gad_interp = interpret_gad(total_gad7)
    st.markdown(f"**PHQ-9 Total Score:** {total_phq9} ({phq_interp})")
    st.markdown(f"**GAD-7 Total Score:** {total_gad7} ({gad_interp})")
    st.markdown("Please note that this feedback is automatic and does not constitute a diagnosis.")

    feedback_answers = [a for a in st.session_state.answers if a["type"] == "feedback"]
    feedback_step = len(feedback_answers)

    if feedback_step < len(feedback_questions):
        fq = feedback_questions[feedback_step]
        if fq["type"] == "radio":
            answer = st.radio(fq["label"], fq["options"], key=fq["key"])
        else:
            answer = st.text_area(fq["label"], key=fq["key"])
        if st.button("Next", key=f"feedback_next_{feedback_step}"):
            elapsed = datetime.now().timestamp() - st.session_state.start_time
            st.session_state.answers.append({"type": "feedback", "question": fq["label"], "answer": answer, "elapsed": elapsed})
            log_step_to_sheet(fq["label"], answer, "feedback", elapsed)
            st.session_state[fq["key"]] = answer
            st.session_state.start_time = datetime.now().timestamp()
            st.session_state.step += 1
            st.experimental_rerun()
    else:
        try:
            scope = ["https://www.googleapis.com/auth/spreadsheets"]
            creds = Credentials.from_service_account_info(st.secrets["google_sheets"], scopes=scope)
            client = gspread.authorize(creds)
            sheet = client.open_by_key(st.secrets["google_sheets"]["sheet_id"])
            worksheet = sheet.sheet1
            row = [
                "",  # name
                st.session_state.get("gender", ""),
                st.session_state.get("age", ""),
                "",  # initial_feeling
                total_phq9,
                total_gad7,
                f"{phq_interp}; {gad_interp}",
                st.session_state.get("trust", ""),
                st.session_state.get("comfort", ""),
                "",  # initial_mood
                st.session_state.get("feedback", ""),
                "static"
            ]
            worksheet.append_row(row, value_input_option="USER_ENTERED")
            st.success("✅ Your responses and feedback have been logged. Thank you for participating!")
            st.session_state.feedback_done = True
        except Exception as e:
            st.error(f"❌ Data submission failed: {e}")

if st.session_state.feedback_done:
    st.info("You have already submitted your feedback. Thank you!")