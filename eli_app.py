import streamlit as st
import time
from google.oauth2.service_account import Credentials
import gspread
import datetime
from utils.chatbot import summarize_results, safety_check, respond_to_feelings, extract_age, extract_gender

@st.cache_resource
def get_gsheet_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(st.secrets["google_sheets"], scopes=scope)
    client = gspread.authorize(creds)
    return client

def log_message_to_sheet(role, content):
    try:
        client = get_gsheet_client()
        sheet = client.open_by_key(st.secrets["google_sheets"]["sheet_id"]).sheet1
        row = [
            "",  # Do not store name
            st.session_state.get("gender", ""),
            st.session_state.get("age", ""),
            role,
            content,
            str(datetime.datetime.now())
        ]
        sheet.append_row(row, value_input_option="USER_ENTERED")
    except Exception as e:
        print("❌ Google Sheets message log failed:", e)

def append_to_google_sheet(data):
    try:
        client = get_gsheet_client()
        sheet = client.open_by_key(st.secrets["google_sheets"]["sheet_id"]).sheet1
        row = [
            "", 
            data.get("gender", ""),
            data.get("age", ""),
            data.get("initial_feeling", ""),
            data.get("phq_total", ""),
            data.get("gad_total", ""),
            data.get("elli_interp", ""),
            data.get("trust", ""),
            data.get("comfort", ""),
            data.get("initial_mood", ""),
            data.get("user_reflection", ""),
            "chatbot"
        ]
        sheet.append_row(row, value_input_option="USER_ENTERED")
        print("✅ Successfully appended summary row to Google Sheet.")
    except Exception as e:
        print("❌ Google Sheets append failed:", e)
        raise e

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

# Feedback phase flags
if "feedback_trust_asked" not in st.session_state:
    st.session_state.feedback_trust_asked = False
if "feedback_comfort_asked" not in st.session_state:
    st.session_state.feedback_comfort_asked = False
if "feedback_final_asked" not in st.session_state:
    st.session_state.feedback_final_asked = False

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
        with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
            st.markdown(msg["content"], unsafe_allow_html=True)
    else:
        first_letter = st.session_state.name[0].upper() if st.session_state.get("name") else "U"
        with st.chat_message("user", avatar="assets/user_avatar.png"):
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

    if st.session_state.step not in ["phq", "gad"]:
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
            with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
                st.markdown(bot_reply)
            st.stop()

    step = st.session_state.step

    if step == "intro":
        from utils.chatbot import extract_name_from_input
        name = extract_name_from_input(user_input)
        if name:
            st.session_state.name = name
            elli_intro = f"Hi {name}, I’m Elli. 🌱 I’m here to gently check in with you. How are you feeling today? (2-3 sentences)"
            st.session_state.step = "mood"
        else:
            elli_intro = "Thanks for sharing. Could you please give me just your name or nickname so I can know how to address you?"
        st.session_state.messages.append({"role": "bot", "content": elli_intro})
        log_message_to_sheet("bot", elli_intro)
        st.rerun()

    elif step == "mood":
        with st.spinner("Elli is thinking..."):
            response = respond_to_feelings(user_input, st.session_state.name)
            st.session_state.initial_mood = user_input
            time.sleep(1.5)
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
            with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
                st.markdown(error_msg)
        else:
            st.session_state.phq_answers.append(score)
            st.session_state.phq_index += 1
            if st.session_state.phq_index < len(PHQ_9_QUESTIONS):
                next_q = f"{st.session_state.phq_index + 1}. {PHQ_9_QUESTIONS[st.session_state.phq_index]}"
                if not any(msg["content"] == next_q for msg in st.session_state.messages):
                    st.session_state.messages.append({"role": "bot", "content": next_q})
                    log_message_to_sheet("bot", next_q)
                with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
                    st.markdown(next_q)
            else:
                st.session_state.step = "gad"
                st.session_state.gad_index = 0
                gad_intro = "Thank you. Now let’s look at anxiety. Over the last 2 weeks: " + GAD_7_QUESTIONS[0]
                if not any(msg["content"] == gad_intro for msg in st.session_state.messages):
                    st.session_state.messages.append({"role": "bot", "content": gad_intro})
                    log_message_to_sheet("bot", gad_intro)
                with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
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
            with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
                st.markdown(error_msg)
        else:
            st.session_state.gad_answers.append(score)
            st.session_state.gad_index += 1
            if st.session_state.gad_index < len(GAD_7_QUESTIONS):
                next_q = f"{st.session_state.gad_index + 1}. {GAD_7_QUESTIONS[st.session_state.gad_index]}"
                if not any(msg["content"] == next_q for msg in st.session_state.messages):
                    st.session_state.messages.append({"role": "bot", "content": next_q})
                    log_message_to_sheet("bot", next_q)
                with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
                    st.markdown(next_q)
            else:
                phq_total = sum(st.session_state.phq_answers)
                gad_total = sum(st.session_state.gad_answers)
                phq_interp = interpret(phq_total, "phq")
                gad_interp = interpret(gad_total, "gad")
                summary = summarize_results(
                    phq_total,
                    phq_interp,
                    gad_total,
                    gad_interp,
                    mood_text=st.session_state.initial_mood
                )
                st.session_state.step = "feedback"
                summary_msgs = [
                    "Here’s a gentle summary of what you’ve shared:",
                    summary,
                    "To finish, how much did you feel you could trust Elli? (1–5)"
                ]
                for msg in summary_msgs:
                    if not any(existing_msg["content"] == msg for existing_msg in st.session_state.messages):
                        st.session_state.messages.append({"role": "bot", "content": msg})
                        log_message_to_sheet("bot", msg)
                    with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
                        st.markdown(msg)
                st.session_state.feedback_trust_asked = True
                st.session_state.feedback_comfort_asked = False
                st.session_state.feedback_final_asked = False
                st.stop()

    elif step == "feedback":
        # 1. Trust question
        if st.session_state.feedback_trust_asked and st.session_state.trust == 0:
            try:
                trust_score = int(user_input)
                if trust_score not in [1, 2, 3, 4, 5]:
                    raise ValueError
                st.session_state.trust = trust_score
                st.session_state.feedback_trust_asked = False
                st.session_state.feedback_comfort_asked = True
                bot_msg = "Thank you. How comfortable did you feel interacting with Elli? (1–5)"
                st.session_state.messages.append({"role": "bot", "content": bot_msg})
                log_message_to_sheet("bot", bot_msg)
                st.stop()
            except ValueError:
                bot_msg = "Please enter a number from 1 to 5."
                st.session_state.messages.append({"role": "bot", "content": bot_msg})
                log_message_to_sheet("bot", bot_msg)
                st.stop()
        # 2. Comfort question
        elif st.session_state.feedback_comfort_asked and st.session_state.comfort == 0:
            try:
                comfort_score = int(user_input)
                if comfort_score not in [1, 2, 3, 4, 5]:
                    raise ValueError
                st.session_state.comfort = comfort_score
                st.session_state.feedback_comfort_asked = False
                st.session_state.feedback_final_asked = True
                bot_msg = "Thanks. Finally, do you have any thoughts or feedback about this experience?"
                st.session_state.messages.append({"role": "bot", "content": bot_msg})
                log_message_to_sheet("bot", bot_msg)
                st.stop()
            except ValueError:
                bot_msg = "Please enter a number from 1 to 5."
                st.session_state.messages.append({"role": "bot", "content": bot_msg})
                log_message_to_sheet("bot", bot_msg)
                st.stop()
        # 3. Open feedback
        elif st.session_state.feedback_final_asked and st.session_state.feedback == "":
            st.session_state.feedback = user_input
            try:
                data = {
                    "name": st.session_state.get("name", ""),
                    "gender": st.session_state.get("gender", ""),
                    "age": st.session_state.get("age", ""),
                    "initial_feeling": st.session_state.get("initial_feeling", ""),
                    "phq_total": sum(st.session_state.get("phq_answers", [])),
                    "gad_total": sum(st.session_state.get("gad_answers", [])),
                    "elli_interp": st.session_state.get("elli_interp", ""),  
                    "trust": st.session_state.get("trust", ""),
                    "comfort": st.session_state.get("comfort", ""),
                    "initial_mood": st.session_state.messages[2]["content"] if len(st.session_state.messages) > 2 else "",
                    "user_reflection": st.session_state.get("feedback", ""),
                }
                append_to_google_sheet(data)
                closing = f"Thanks so much for checking in today, {st.session_state.name}. Wishing you care and calm. 🌻"
                st.session_state.messages.append({"role": "bot", "content": closing})
                log_message_to_sheet("bot", closing)
                st.session_state.feedback_final_asked = False
                st.session_state.step = "done"
                st.stop()
            except Exception as e:
                bot_msg = "An error occurred while processing your feedback. Please try again later."
                st.session_state.messages.append({"role": "bot", "content": bot_msg})
                log_message_to_sheet("bot", bot_msg)
                st.error(f"Error: {e}")
        # If no feedback flags are set, start with trust question
        elif not (st.session_state.feedback_trust_asked or st.session_state.feedback_comfort_asked or st.session_state.feedback_final_asked):
            bot_msg = "To finish, how much did you feel you could trust Elli? (1–5)"
            st.session_state.messages.append({"role": "bot", "content": bot_msg})
            log_message_to_sheet("bot", bot_msg)
            st.session_state.feedback_trust_asked = True
            st.stop()