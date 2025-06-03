import streamlit as st
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread
import uuid

st.set_page_config(page_title="Mental Health Screening (Static Form)", page_icon="📝", layout="centered")

st.title("📝 Mental Health Screening (Neutral Interface)")
st.markdown("""
Welcome to this mental health screening form. Please answer the following questions as honestly as possible.

**Note:** 
- Your responses are confidential, anonymous, and will not be reviewed by medical professionals.
- This tool cannot provide crisis support. If you are in emotional distress or thinking about hurting yourself, please contact a local mental health service or suicide hotline in your area.
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
]

feedback_questions = [
    {"label": "How much did you trust the questionnaire process?", "type": "radio", "options": [1, 2, 3, 4, 5], "key": "trust"},
    {"label": "How comfortable did you feel while answering?", "type": "radio", "options": [1, 2, 3, 4, 5], "key": "comfort"},
    {"label": "How empathic did you find the questionnaire?", "type": "radio", "options": [1, 2, 3, 4, 5], "key": "empathy"},
    {"label": "Do you have any feedback about your experience?", "type": "text", "key": "feedback"}
]

# --- State ---
for key, default in {
    "session_id": str(uuid.uuid4()),
    "step": 0,
    "answers": [],
    "start_time": datetime.now().timestamp(),
    "main_done": False,
    "feedback_done": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- Helper: Build row for Google Sheets ---
def build_row_with_progress(step_label, phq9_score=None, phq9_interp=None, gad7_score=None, gad7_interp=None):
    row = []
    row.append(st.session_state["session_id"])
    for dq in demographic_questions:
        row.append(str(st.session_state.get(dq["key"], "")))
    for q in phq9_items:
        ans = next((a["answer"] for a in st.session_state.answers if a["question"] == q), "")
        row.append(str(ans))
    for q in gad7_items:
        ans = next((a["answer"] for a in st.session_state.answers if a["question"] == q), "")
        row.append(str(ans))
    for fq in feedback_questions:
        row.append(str(st.session_state.get(fq["key"], "")))
    row.append(str(step_label))
    row.append(datetime.now().isoformat())
    if phq9_score is not None:
        row += [str(phq9_score), str(phq9_interp), str(gad7_score), str(gad7_interp)]
    return row

def log_row(row_data_dict):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["google_sheets"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(st.secrets["google_sheets"]["sheet_id"]).sheet1

        existing_rows = sheet.get_all_values()
        row_index = 2
        while row_index <= len(existing_rows):
            row = existing_rows[row_index - 1]
            if all(cell.strip() == "" for cell in row[:26]):
                break
            row_index += 1

        if row_index > len(existing_rows):
            sheet.append_row([""] * 26)  # ensure row exists

        # Get existing values to avoid overwriting
        existing_row = sheet.row_values(row_index)
        existing_row += [""] * (26 - len(existing_row))  # pad

        # Map the input data dict (like {"A": "static", "B": "25"}) to row index
        col_map = {chr(65 + i): i for i in range(26)}  # A-Z to 0-25
        new_row = existing_row.copy()
        for col_letter, value in row_data_dict.items():
            col_index = col_map[col_letter]
            if new_row[col_index].strip() == "":
                new_row[col_index] = str(value)

        sheet.update(f"A{row_index}:Z{row_index}", [new_row])
        print(f"✅ Logged progress at row {row_index}")
    except Exception as e:
        st.error(f"❌ Intermediate data write failed: {e}")


def log_row_static_final():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["google_sheets"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(st.secrets["google_sheets"]["sheet_id"]).sheet1

        # Find the next empty row in columns A–Z (row 2+)
        existing_rows = sheet.get_all_values()
        row_index = 2
        while row_index <= len(existing_rows):
            if all(cell.strip() == "" for cell in existing_rows[row_index - 1][:26]):
                break
            row_index += 1

        # Build the row based on the A-Z column spec
        row_data = [""] * 26  # A-Z

        row_data[0] = "static"  # A: Version
        row_data[1] = str(st.session_state.get("age", ""))  # B: Age
        row_data[2] = str(st.session_state.get("gender", ""))  # C: Gender
        # D is skipped for static version (mood)

        # E–M: PHQ-9
        phq_answers = [a["answer"] for a in st.session_state.answers if a["type"] == "phq9"]
        for i in range(min(9, len(phq_answers))):
            row_data[4 + i] = str(scale.index(phq_answers[i]))

        # N–T: GAD-7
        gad_answers = [a["answer"] for a in st.session_state.answers if a["type"] == "gad7"]
        for i in range(min(7, len(gad_answers))):
            row_data[13 + i] = str(scale.index(gad_answers[i]))

        # U: Total PHQ, V: Total GAD
        row_data[20] = str(sum(scale.index(ans) for ans in phq_answers))  # U
        row_data[21] = str(sum(scale.index(ans) for ans in gad_answers))  # V

        # W–Y: Trust, Comfort, Empathy
        row_data[22] = str(st.session_state.get("trust", ""))
        row_data[23] = str(st.session_state.get("comfort", ""))
        row_data[24] = str(st.session_state.get("empathy", ""))

        # Z: Feedback
        row_data[25] = str(st.session_state.get("feedback", ""))

        # Write the row
        sheet.update(f"A{row_index}:Z{row_index}", [row_data])
        print(f"✅ Wrote static data to row {row_index}")
    except Exception as e:
        st.error(f"❌ Final data write failed: {e}")


# --- Form Logic ---
if not st.session_state.main_done:
    current = st.session_state.step
    if current < len(phq9_items):
        q = phq9_items[current]
        st.markdown(f"<span style='font-size:1.5em'><b>{q}</b></span>", unsafe_allow_html=True)
        answer = st.radio("", scale, key=f"phq9_{current}")
        if st.button("Next", key=f"next_{current}"):
            elapsed = datetime.now().timestamp() - st.session_state.start_time
            st.session_state.answers.append({"type": "phq9", "question": q, "answer": answer, "elapsed": elapsed})
            row = {
                "A": "static",
                f"{chr(69 + current)}": str(scale.index(answer))  # E=69 in ASCII, for PHQ1–PHQ9 (E–M)
            }
            log_row(row)
            row = build_row_with_progress(f"phq9_{current+1}")
            st.session_state.step += 1
            st.session_state.start_time = datetime.now().timestamp()
            st.rerun()
    elif current < len(phq9_items) + len(gad7_items):
        idx = current - len(phq9_items)
        q = gad7_items[idx]
        st.markdown(f"<span style='font-size:1.5em'><b>{q}</b></span>", unsafe_allow_html=True)
        answer = st.radio("", scale, key=f"gad7_{idx}")
        if st.button("Next", key=f"next_{current}"):
            elapsed = datetime.now().timestamp() - st.session_state.start_time
            st.session_state.answers.append({"type": "gad7", "question": q, "answer": answer, "elapsed": elapsed})
            row = {
                "A": "static",
                f"{chr(78 + idx)}": str(scale.index(answer))  # N=78 for GAD1–GAD7 (N–T)
            }
            log_row(row)
            row = build_row_with_progress(f"gad7_{idx+1}")
            st.session_state.step += 1
            st.session_state.start_time = datetime.now().timestamp()
            st.rerun()
    elif current < len(phq9_items) + len(gad7_items) + len(demographic_questions):
        idx = current - len(phq9_items) - len(gad7_items)
        dq = demographic_questions[idx]
        st.markdown(f"<span style='font-size:1.5em'><b>{dq['label']}</b></span>", unsafe_allow_html=True)
        if dq["type"] == "number":
            answer = st.number_input("", min_value=dq["min_value"], max_value=dq["max_value"], value=dq["value"], step=dq["step"], key=dq["key"])
        else:
            answer = st.selectbox("", dq["options"], key=dq["key"])
        if st.button("Next", key=f"next_{current}"):
            elapsed = datetime.now().timestamp() - st.session_state.start_time
            st.session_state.answers.append({"type": "demographic", "question": dq["label"], "answer": answer, "elapsed": elapsed})
            row = {
                "A": "static",
                "B": str(answer)
            }
            log_row(row)
            row = build_row_with_progress(f"demographic_{idx+1}")
            st.session_state.start_time = datetime.now().timestamp()
            st.session_state.step += 1
            st.rerun()
    else:
        st.session_state.main_done = True
        st.session_state.start_time = datetime.now().timestamp()
        st.session_state.step += 1
        st.rerun()

# --- Results + Feedback ---
if st.session_state.main_done and not st.session_state.feedback_done:
    st.success("✅ You have completed the questionnaire.")
    phq9_scores = [scale.index(ans["answer"]) for ans in st.session_state.answers if ans["type"] == "phq9"]
    gad7_scores = [scale.index(ans["answer"]) for ans in st.session_state.answers if ans["type"] == "gad7"]
    total_phq9 = sum(phq9_scores)
    total_gad7 = sum(gad7_scores)
    phq_interp = interpret_phq(total_phq9)
    gad_interp = interpret_gad(total_gad7)

    st.markdown(
        f"**PHQ-9 Total Score:** {total_phq9}  \n"
        f"Your answers on the PHQ-9 suggest that your symptoms could be a sign of: **{phq_interp}**"
    )
    st.markdown(
        f"**GAD-7 Total Score:** {total_gad7}  \n"
        f"Your answers on the GAD-7 suggest that your symptoms could be a sign of: **{gad_interp}**"
    )
    st.markdown("Please note that this feedback is automatic and does not constitute a diagnosis.")

    feedback_answers = [a for a in st.session_state.answers if a["type"] == "feedback"]
    feedback_step = len(feedback_answers)

    if feedback_step < len(feedback_questions):
        fq = feedback_questions[feedback_step]
        st.markdown(f"<span style='font-size:1.3em'><b>{fq['label']}</b></span>", unsafe_allow_html=True)
        if fq["type"] == "radio":
            answer = st.radio("", fq["options"], key=fq["key"])
        else:
            answer = st.text_area("", key=fq["key"])
        if st.button("Next", key=f"feedback_next_{feedback_step}"):
            elapsed = datetime.now().timestamp() - st.session_state.start_time
            st.session_state.answers.append({"type": "feedback", "question": fq["label"], "answer": answer, "elapsed": elapsed})
            column_map = {
                "trust": "W",
                "comfort": "X",
                "empathy": "Y",
                "feedback": "Z"
            }
            row = {
                "A": "static",
                column_map[fq["key"]]: str(answer)
            }
            log_row(row)

            row = build_row_with_progress(f"feedback_{feedback_step+1}")
            st.session_state.start_time = datetime.now().timestamp()
            st.session_state.step += 1
            st.rerun()
    else:
        try:
            log_row_static_final()
            st.success("✅ Your responses and feedback have been logged. Thank you for participating!")
            st.session_state.feedback_done = True
        except Exception as e:
            st.error(f"❌ Data submission failed: {e}")


if st.session_state.feedback_done:
    st.info("You have already submitted your feedback. Thank you!")