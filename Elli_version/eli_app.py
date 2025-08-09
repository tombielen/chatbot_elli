# eli_app.py
import os
import sys
import time
import datetime
import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root (one level up from Elli_version/)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Assets (robust paths regardless of working dir)
ASSETS_DIR = os.path.join(ROOT, "assets")
ELLI_AVATAR = os.path.join(ASSETS_DIR, "elli_avatar.png")
USER_AVATAR = os.path.join(ASSETS_DIR, "user_avatar.png")
if not os.path.exists(ELLI_AVATAR):
    ELLI_AVATAR = None  # Streamlit will fall back to default avatar
if not os.path.exists(USER_AVATAR):
    USER_AVATAR = None

# ---------- Project imports from utils/ ----------
try:
    from utils.chatbot import (
        summarize_results,
        safety_check,
        respond_to_feelings,
        extract_age,
        extract_gender,
        extract_name_from_input,
    )
except Exception as e:
    st.error(
        "Could not import from `utils/chatbot.py`. "
        "Ensure `utils/` exists at the repo root with an `__init__.py` file and a `chatbot.py` module. "
        f"\n\nImport error: {e}"
    )
    st.stop()

# ---------- Google Sheets helpers ----------
@st.cache_resource
def get_gsheet_client():
    # Expecting st.secrets["google_sheets"] to contain the full service account dict
    # plus a "sheet_id" field.
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/drive",
        ]
        gs_secrets = st.secrets["google_sheets"]
        creds = Credentials.from_service_account_info(gs_secrets, scopes=scope)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.warning(f"Google Sheets client init failed: {e}")
        return None

def _open_sheet():
    try:
        client = get_gsheet_client()
        if not client:
            return None
        sheet_id = st.secrets["google_sheets"]["sheet_id"]
        return client.open_by_key(sheet_id).sheet1
    except Exception as e:
        print("❌ Open sheet failed:", e)
        return None

def log_message_to_sheet(role, content):
    try:
        sheet = _open_sheet()
        if not sheet:
            return
        row = [
            "",  # placeholder for participant id or condition
            st.session_state.get("gender", ""),
            st.session_state.get("age", ""),
            role,
            content,
            str(datetime.datetime.now()),
        ]
        sheet.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        print("❌ Google Sheets message log failed:", e)

def append_to_google_sheet(data):
    try:
        sheet = _open_sheet()
        if not sheet:
            return
        row = [
            "",  # placeholder / condition
            data.get("gender", ""),
            data.get("age", ""),
            data.get("initial_feeling", ""),
            data.get("phq_total", ""),
            data.get("gad_total", ""),
            data.get("elli_interp", ""),
            data.get("trust", ""),
            data.get("comfort", ""),
            data.get("empathy", ""),
            data.get("initial_mood", ""),
            data.get("user_reflection", ""),
            "chatbot",
        ]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        print("✅ Successfully appended summary row to Google Sheet.")
    except Exception as e:
        print("❌ Google Sheets append failed:", e)

def log_row_elli_final():
    try:
        sheet = _open_sheet()
        if not sheet:
            st.warning("Google Sheet not available; final row not written.")
            return

        if "row_index" not in st.session_state:
            existing_rows = sheet.get_all_values()
            row_index = 2
            while row_index <= len(existing_rows):
                if all(cell.strip() == "" for cell in existing_rows[row_index - 1][:26]):
                    break
                row_index += 1
            if row_index > len(existing_rows):
                sheet.append_row([""] * 26)
            st.session_state["row_index"] = row_index
        else:
            row_index = st.session_state["row_index"]

        row_data = [""] * 26  # A-Z

        # A: condition
        row_data[0] = "Elli"
        # B: age
        row_data[1] = str(st.session_state.get("age", ""))
        # C: gender
        row_data[2] = str(st.session_state.get("gender", ""))

        # D: initial mood exchange (user + elli first response)
        user_mood = st.session_state.get("initial_mood", "")
        elli_mood_response = ""
        for i, msg in enumerate(st.session_state.messages):
            if msg["role"] == "user" and msg["content"] == user_mood:
                for j in range(i + 1, len(st.session_state.messages)):
                    next_msg = st.session_state.messages[j]
                    if next_msg["role"] == "bot":
                        elli_mood_response = next_msg["content"]
                        break
                break
        if user_mood or elli_mood_response:
            row_data[3] = f"User: {user_mood}\nElli: {elli_mood_response}"

        # E-M: PHQ-9 items (9)
        phq_answers = st.session_state.get("phq_answers", [])
        for i in range(9):
            row_data[4 + i] = str(phq_answers[i]) if i < len(phq_answers) else ""

        # N-T: GAD-7 items (7)
        gad_answers = st.session_state.get("gad_answers", [])
        for i in range(7):
            row_data[13 + i] = str(gad_answers[i]) if i < len(gad_answers) else ""

        # U: PHQ total
        row_data[20] = str(sum(phq_answers)) if phq_answers else ""
        # V: GAD total
        row_data[21] = str(sum(gad_answers)) if gad_answers else ""
        # W: trust
        row_data[22] = str(st.session_state.get("trust", ""))
        # X: comfort
        row_data[23] = str(st.session_state.get("comfort", ""))
        # Y: empathy
        row_data[24] = str(st.session_state.get("empathy", ""))
        # Z: free feedback
        row_data[25] = str(st.session_state.get("feedback", ""))

        sheet.update(f"A{row_index}:Z{row_index}", [row_data])
        print(f"✅ Wrote Elli data to row {row_index}")
    except Exception as e:
        st.error(f"❌ Final data write failed: {e}")

# ---------- App UI ----------
st.set_page_config(page_title="Elli - Mental Health Assistant", page_icon="🌱")
st.title("🌱 Elli – Your Mental Health Companion")

# --- Init session state ---
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "bot",
        "content": "Hi, I’m Elli. 🌱 What’s your name or nickname?"
    }]
    st.session_state.step = "intro"
    st.session_state.name = ""
    st.session_state.phq_answers = []
    st.session_state.gad_answers = []
    st.session_state.phq_index = 0
    st.session_state.gad_index = 0
    st.session_state.trust = 0
    st.session_state.comfort = 0
    st.session_state.feedback = ""
    st.session_state.age = ""
    st.session_state.gender = ""
    st.session_state.psych_history = ""
    st.session_state.demographic_stage = "ask_age"

if "feedback_trust_asked" not in st.session_state:
    st.session_state.feedback_trust_asked = False
if "feedback_comfort_asked" not in st.session_state:
    st.session_state.feedback_comfort_asked = False
if "feedback_final_asked" not in st.session_state:
    st.session_state.feedback_final_asked = False
if "feedback_empathy_asked" not in st.session_state:
    st.session_state.feedback_empathy_asked = False
if "empathy" not in st.session_state:
    st.session_state.empathy = 0

PHQ_9_QUESTIONS = [
    "Little interest or pleasure in doing things?",
    "Feeling down, depressed, or hopeless?",
    "Trouble falling or staying asleep, or sleeping too much?",
    "Feeling tired or having little energy?",
    "Poor appetite or overeating?",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down?",
    "Trouble concentrating on things, such as reading or watching TV?",
    "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you’ve been moving around a lot more than usual?",
    "Thoughts that you would be better off dead, or thoughts of hurting yourself in some way?"
]

GAD_7_QUESTIONS = [
    "Feeling nervous, anxious, or on edge?",
    "Not being able to stop or control worrying?",
    "Worrying too much about different things?",
    "Trouble relaxing?",
    "Being so restless that it is hard to sit still?",
    "Becoming easily annoyed or irritable?",
    "Feeling afraid as if something awful might happen?"
]

def interpret(score, scale):
    if scale == "phq":
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
    elif scale == "gad":
        if score <= 4:
            return "Minimal anxiety"
        elif score <= 9:
            return "Mild anxiety"
        elif score <= 14:
            return "Moderate anxiety"
        else:
            return "Severe anxiety"

def render_chat_message(msg):
    if msg["role"] == "bot":
        with st.chat_message("assistant", avatar=ELLI_AVATAR):
            st.markdown(msg["content"], unsafe_allow_html=True)
    else:
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(msg["content"], unsafe_allow_html=True)

# --- Render message history ---
for msg in st.session_state.messages:
    render_chat_message(msg)

# --- Chat Input ---
if st.session_state.get("step") != "done":
    user_input = st.chat_input("Your message...")
else:
    user_input = None

if user_input:
    user_input = user_input.strip()
    user_msg = {"role": "user", "content": user_input}
    st.session_state.messages.append(user_msg)
    render_chat_message(user_msg)
    log_message_to_sheet("user", user_input)

    # Crisis/safety check (not during questionnaires)
    if st.session_state.step not in ["phq", "gad"]:
        try:
            if safety_check(user_input):
                bot_reply = (
                    "⚠️ It sounds like you're going through something really difficult. You're not alone.\n\n"
                    "Elli isn't a crisis service, but there are people who care and can help. Please consider reaching out to a professional or one of these mental health support lines:\n\n"
                    "- **US**: Call or text 988 (Suicide & Crisis Lifeline)\n"
                    "- **UK**: Call Samaritans at 116 123\n"
                    "- **Canada**: Call 1-833-456-4566 (Talk Suicide Canada)\n"
                    "- **India**: Call 9152987821 (iCall)\n"
                    "- **International**: [Find a helpline near you](https://findahelpline.com)\n\n"
                    "You matter. 💛"
                )
                st.session_state.messages.append({"role": "bot", "content": bot_reply})
                log_message_to_sheet("bot", bot_reply)
                with st.chat_message("assistant", avatar=ELLI_AVATAR):
                    st.markdown(bot_reply)
                st.stop()
        except Exception as e:
            # Fail safe: never crash on safety check
            print("Safety check error:", e)

    step = st.session_state.step

    if step == "intro":
        name = extract_name_from_input(user_input)
        if name:
            st.session_state.name = name
            elli_intro = f"Hi {name}, I’m Elli. 🌱 I’m here to gently check in with you. How are you feeling today? (2-3 sentences)"
            st.session_state.step = "mood"
        else:
            elli_intro = (
                "Thanks for sharing. Could you please give me just your name or nickname so I can know how to address you? "
                "(Your name will not be stored or used for any other purpose.)"
            )
        st.session_state.messages.append({"role": "bot", "content": elli_intro})
        log_message_to_sheet("bot", elli_intro)
        st.rerun()

    elif step == "mood":
        with st.spinner("Elli is thinking..."):
            response = respond_to_feelings(user_input, st.session_state.name)
            st.session_state.initial_mood = user_input
            time.sleep(1.0)
        st.session_state.messages.append({"role": "bot", "content": response})
        log_message_to_sheet("bot", response)
        st.session_state.step = "demographics"
        st.session_state.demographic_stage = "ask_age"
        first_demo_q = "Before we continue, could you share your age?"
        st.session_state.messages.append({"role": "bot", "content": first_demo_q})
        log_message_to_sheet("bot", first_demo_q)
        st.rerun()

    elif step == "demographics":
        stage = st.session_state.demographic_stage
        if stage == "ask_age":
            extracted_age = extract_age(user_input)
            if isinstance(extracted_age, int) and extracted_age > 0:
                st.session_state.age = extracted_age
                st.session_state.demographic_stage = "ask_gender"
                question = "Thank you. What gender do you identify with?"
                st.session_state.messages.append({"role": "bot", "content": question})
                log_message_to_sheet("bot", question)
            else:
                error_msg = "I couldn't understand your age. Could you please clarify?"
                st.session_state.messages.append({"role": "bot", "content": error_msg})
                log_message_to_sheet("bot", error_msg)
            st.rerun()

        elif stage == "ask_gender":
            try:
                extracted_gender = extract_gender(user_input)
                if extracted_gender:
                    st.session_state.gender = extracted_gender
                    st.session_state.step = "phq"
                    st.session_state.phq_index = 0
                    next_question = (
                        "Thanks for sharing. Let’s reflect on some feelings together.\n\n"
                        "Please respond with a number: 0 (Not at all), 1 (Several days), 2 (More than half the days), or 3 (Nearly every day).\n\n"
                        "Over the last 2 weeks: " + PHQ_9_QUESTIONS[0]
                    )
                    st.session_state.messages.append({"role": "bot", "content": next_question})
                    log_message_to_sheet("bot", next_question)
                else:
                    error_msg = "I couldn't understand your gender. Could you please clarify?"
                    st.session_state.messages.append({"role": "bot", "content": error_msg})
                    log_message_to_sheet("bot", error_msg)
            except Exception as e:
                error_msg = "An error occurred while processing your response. Please try again."
                st.session_state.messages.append({"role": "bot", "content": error_msg})
                log_message_to_sheet("bot", error_msg)
                st.error(f"Error: {e}")
            st.rerun()

    elif step == "phq":
        try:
            score = int(user_input)
            if score not in [0, 1, 2, 3]:
                raise ValueError
        except ValueError:
            error_msg = "Please respond with a number: 0 (Not at all), 1 (Several days), 2 (More than half the days), or 3 (Nearly every day)."
            st.session_state.messages.append({"role": "bot", "content": error_msg})
            log_message_to_sheet("bot", error_msg)
            with st.chat_message("assistant", avatar=ELLI_AVATAR):
                st.markdown(error_msg)
        else:
            st.session_state.phq_answers.append(score)
            st.session_state.phq_index += 1
            if st.session_state.phq_index < len(PHQ_9_QUESTIONS):
                next_q = f"{st.session_state.phq_index + 1}. {PHQ_9_QUESTIONS[st.session_state.phq_index]}"
                st.session_state.messages.append({"role": "bot", "content": next_q})
                log_message_to_sheet("bot", next_q)
                with st.chat_message("assistant", avatar=ELLI_AVATAR):
                    st.markdown(next_q)
            else:
                st.session_state.step = "gad"
                st.session_state.gad_index = 0
                gad_intro = "Thank you. Now let’s look at anxiety. Over the last 2 weeks: " + GAD_7_QUESTIONS[0]
                st.session_state.messages.append({"role": "bot", "content": gad_intro})
                log_message_to_sheet("bot", gad_intro)
                with st.chat_message("assistant", avatar=ELLI_AVATAR):
                    st.markdown(gad_intro)

    elif step == "gad":
        try:
            score = int(user_input)
            if score not in [0, 1, 2, 3]:
                raise ValueError
        except ValueError:
            error_msg = "Please respond with a number: 0 (Not at all), 1 (Several days), 2 (More than half the days), or 3 (Nearly every day)."
            st.session_state.messages.append({"role": "bot", "content": error_msg})
            log_message_to_sheet("bot", error_msg)
            with st.chat_message("assistant", avatar=ELLI_AVATAR):
                st.markdown(error_msg)
        else:
            st.session_state.gad_answers.append(score)
            st.session_state.gad_index += 1
            if st.session_state.gad_index < len(GAD_7_QUESTIONS):
                next_q = f"{st.session_state.gad_index + 1}. {GAD_7_QUESTIONS[st.session_state.gad_index]}"
                st.session_state.messages.append({"role": "bot", "content": next_q})
                log_message_to_sheet("bot", next_q)
                with st.chat_message("assistant", avatar=ELLI_AVATAR):
                    st.markdown(next_q)
            else:
                phq_total = sum(st.session_state.phq_answers)
                gad_total = sum(st.session_state.gad_answers)
                phq_interp = interpret(phq_total, "phq")
                gad_interp = interpret(gad_total, "gad")
                user_name = st.session_state.get("name", "there")
                summary = summarize_results(
                    phq_total,
                    phq_interp,
                    gad_total,
                    gad_interp,
                    mood_text=st.session_state.initial_mood
                )
                st.session_state.step = "feedback"
                summary_msgs = [
                    f"Here’s a gentle summary of what you’ve shared, {user_name}:",
                    summary,
                    "How much did you feel you could trust Elli? (1–5)"
                ]
                for msg in summary_msgs:
                    st.session_state.messages.append({"role": "bot", "content": msg})
                    log_message_to_sheet("bot", msg)
                    with st.chat_message("assistant", avatar=ELLI_AVATAR):
                        st.markdown(msg)
                st.session_state.feedback_trust_asked = True
                st.session_state.feedback_comfort_asked = False
                st.session_state.feedback_final_asked = False
                st.stop()

    elif step == "feedback":
        if st.session_state.feedback_trust_asked and st.session_state.trust == 0:
            try:
                trust_score = int(user_input)
                if trust_score not in [1, 2, 3, 4, 5]:
                    raise ValueError
                st.session_state.trust = trust_score
                st.session_state.feedback_trust_asked = False
                st.session_state.comfort = 0
                st.session_state.feedback_comfort_asked = True
                bot_msg = "Thank you. How comfortable did you feel interacting with Elli? (1–5)"
                st.session_state.messages.append({"role": "bot", "content": bot_msg})
                log_message_to_sheet("bot", bot_msg)
                st.rerun()
            except ValueError:
                bot_msg = "Please enter a number from 1 to 5."
                st.session_state.messages.append({"role": "bot", "content": bot_msg})
                log_message_to_sheet("bot", bot_msg)
                st.rerun()

        elif st.session_state.feedback_comfort_asked and st.session_state.comfort == 0:
            try:
                comfort_score = int(user_input)
                if comfort_score not in [1, 2, 3, 4, 5]:
                    raise ValueError
                st.session_state.comfort = comfort_score
                st.session_state.feedback_comfort_asked = False
                st.session_state.empathy = 0
                st.session_state.feedback_empathy_asked = True
                bot_msg = "And how empathic did you find Elli? (1–5)"
                st.session_state.messages.append({"role": "bot", "content": bot_msg})
                log_message_to_sheet("bot", bot_msg)
                st.rerun()
            except ValueError:
                bot_msg = "Please enter a number from 1 to 5."
                st.session_state.messages.append({"role": "bot", "content": bot_msg})
                log_message_to_sheet("bot", bot_msg)
                st.rerun()

        elif st.session_state.feedback_empathy_asked and st.session_state.empathy == 0:
            try:
                empathy_score = int(user_input)
                if empathy_score not in [1, 2, 3, 4, 5]:
                    raise ValueError
                st.session_state.empathy = empathy_score
                st.session_state.feedback_empathy_asked = False
                st.session_state.feedback = ""
                st.session_state.feedback_final_asked = True
                bot_msg = "Thanks. Finally, do you have any thoughts or feedback about this experience?"
                st.session_state.messages.append({"role": "bot", "content": bot_msg})
                log_message_to_sheet("bot", bot_msg)
                st.rerun()
            except ValueError:
                bot_msg = "Please enter a number from 1 to 5."
                st.session_state.messages.append({"role": "bot", "content": bot_msg})
                log_message_to_sheet("bot", bot_msg)
                st.rerun()

        elif st.session_state.feedback_final_asked and st.session_state.feedback == "":
            st.session_state.feedback = user_input
            try:
                log_row_elli_final()
                closing = f"Thanks so much for checking in today, {st.session_state.name}. Wishing you care and calm. 🌻"
                st.session_state.messages.append({"role": "bot", "content": closing})
                log_message_to_sheet("bot", closing)
                st.session_state.feedback_final_asked = False
                st.session_state.step = "done"
                st.rerun()
            except Exception as e:
                bot_msg = "An error occurred while processing your feedback. Please try again later."
                st.session_state.messages.append({"role": "bot", "content": bot_msg})
                log_message_to_sheet("bot", bot_msg)
                st.error(f"Error: {e}")

        elif st.session_state.step == "feedback" and not any([
            st.session_state.feedback_trust_asked,
            st.session_state.feedback_comfort_asked,
            st.session_state.feedback_empathy_asked,
            st.session_state.feedback_final_asked
        ]):
            if st.session_state.trust == 0:
                bot_msg = "How much did you feel you could trust Elli? (1–5)"
                st.session_state.feedback_trust_asked = True
            elif st.session_state.comfort == 0:
                bot_msg = "How comfortable did you feel interacting with Elli? (1–5)"
                st.session_state.feedback_comfort_asked = True
            elif st.session_state.empathy == 0:
                bot_msg = "And how empathic did you find Elli? (1–5)"
                st.session_state.feedback_empathy_asked = True
            else:
                bot_msg = "Finally, do you have any thoughts or feedback about this experience?"
                st.session_state.feedback_final_asked = True

            st.session_state.messages.append({"role": "bot", "content": bot_msg})
            log_message_to_sheet("bot", bot_msg)
            st.rerun()
