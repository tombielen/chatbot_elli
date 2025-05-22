import streamlit as st
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import csv
import os
from utils.chatbot import summarize_results, safety_check, respond_to_feelings, extract_age, extract_gender

@st.cache_resource
def get_gsheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]  # or "gspread" if that's your key
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def append_to_google_sheet(data_dict, sheet_name="Chatbot_Study_Data"):
    try:
        client = get_gsheet_client()
        sheet = client.open(sheet_name).sheet1
        row = [str(datetime.datetime.now())] + list(data_dict.values())
        sheet.append_row(row, value_input_option="RAW")
    except Exception as e:
        st.error(f"Error saving to Google Sheet: {e}")


def mid_session_log(key, value, sheet_name="Chatbot_Study_Log"):
    try:
        client = get_gsheet_client()
        sheet = client.open(sheet_name).sheet1
        row = [str(datetime.datetime.now()), key, value]
        sheet.append_row(row, value_input_option="RAW")
    except Exception as e:
        print(f"Mid-session logging failed: {e}")

st.set_page_config(page_title="Elli - Mental Health Assistant", page_icon="🌱")

st.title("🌱 Elli – Your Mental Health Companion")

# --- Init session state ---
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "bot",
        "content": "Hi, I’m Elli. 🌱 What’s your name or nickname?"
    }]
    st.session_state.step = "intro"  # Start with the intro step
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

def save_to_csv(data, filename="data/user_responses.csv"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="", encoding="utf-8") as csvfile:
        fieldnames = list(data.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

def render_chat_message(msg):
    if msg["role"] == "bot":
        with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
            st.markdown(msg["content"], unsafe_allow_html=True)
    else:
        first_letter = st.session_state.name[0].upper() if st.session_state.get("name") else "U"
        avatar_html = f"""
        <div style='
            font-size: 16px;
            background: #d3f3e6;
            color: #1a1a1a;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        '>{first_letter}</div>
        """
        with st.chat_message("user", avatar="assets/user_avatar.png"):
            st.markdown(msg["content"], unsafe_allow_html=True)

# --- Render message history ---
for msg in st.session_state.messages:
    render_chat_message(msg)


# --- Chat Input ---
user_input = st.chat_input("Your message...")

if user_input:
    user_input = user_input.strip()
    user_msg = {"role": "user", "content": user_input}
    st.session_state.messages.append(user_msg)
    render_chat_message(user_msg)

    mid_session_log("UserInput", user_input)
    # SAFETY CHECK
    if st.session_state.step not in ["phq", "gad"]:
        if safety_check(user_input):
            bot_reply = "⚠️ It sounds like you're going through something really difficult. You're not alone.\n\n"
            "Elli isn't a crisis service, but there are people who care and can help. Please consider reaching out to a professional or one of these mental health support lines:\n\n"
            "- **US**: Call or text 988 (Suicide & Crisis Lifeline)\n"
            "- **UK**: Call Samaritans at 116 123\n"
            "- **Canada**: Call 1-833-456-4566 (Talk Suicide Canada)\n"
            "- **India**: Call 9152987821 (iCall)\n"
            "- **International**: [Find a helpline near you](https://findahelpline.com)\n\n"
            "You matter. 💛"
            st.session_state.messages.append({"role": "bot", "content": bot_reply})
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
            st.session_state.step = "mood"  # Move to the mood step
        else:
            elli_intro = "Thanks for sharing. Could you please give me just your name or nickname so I can know how to address you?"

        st.session_state.messages.append({"role": "bot", "content": elli_intro})
        st.rerun()

    elif step == "mood":
        with st.spinner("Elli is thinking..."):
            response = respond_to_feelings(user_input, st.session_state.name)
            st.session_state.initial_mood = user_input
            time.sleep(1.5)
        st.session_state.messages.append({"role": "bot", "content": response})
    
        # Move to demographic questions instead of skipping them
        st.session_state.step = "demographics"
        st.session_state.demographic_stage = "ask_age"
    
        # Ask the first demographic question
        first_demo_q = "Before we continue, could you share your age?"
        st.session_state.messages.append({"role": "bot", "content": first_demo_q})
        st.rerun()
    
    elif step == "demographics":
        stage = st.session_state.demographic_stage

        if stage == "ask_age":
            from utils.chatbot import extract_age
            extracted_age = extract_age(user_input)
            if isinstance(extracted_age, int) and extracted_age > 0:  # Ensure the age is a positive integer
                st.session_state.age = extracted_age
                st.session_state.demographic_stage = "ask_gender"
                question = "Thank you. What gender do you identify with?"
                st.session_state.messages.append({"role": "bot", "content": question})
            else:
                error_msg = "I couldn't understand your age. Could you please clarify?"
                st.session_state.messages.append({"role": "bot", "content": error_msg})
            st.rerun()

        elif stage == "ask_gender":
            try:
                extracted_gender = extract_gender(user_input)
                if extracted_gender:
                    st.session_state.gender = extracted_gender
                    st.session_state.step = "phq"  # Move directly to PHQ-9 step
                    st.session_state.phq_index = 0

                    next_question = (
                        "Thanks for sharing. Let’s reflect on some feelings together.\n\n"
                        "Please respond with a number: 0 (Not at all), 1 (Several days), 2 (More than half the days), or 3 (Nearly every day).\n\n"
                        "Over the last 2 weeks: " + PHQ_9_QUESTIONS[0]
                    )
                    st.session_state.messages.append({"role": "bot", "content": next_question})
                else:
                    error_msg = "I couldn't understand your gender. Could you please clarify?"
                    st.session_state.messages.append({"role": "bot", "content": error_msg})
            except Exception as e:
                error_msg = "An error occurred while processing your response. Please try again."
                st.session_state.messages.append({"role": "bot", "content": error_msg})
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
            with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
                st.markdown(error_msg)
        else:
            st.session_state.phq_answers.append(score)
            st.session_state.phq_index += 1
            if st.session_state.phq_index < len(PHQ_9_QUESTIONS):
                next_q = f"{st.session_state.phq_index + 1}. {PHQ_9_QUESTIONS[st.session_state.phq_index]}"
                if not any(msg["content"] == next_q for msg in st.session_state.messages):  # Avoid duplicate questions
                    st.session_state.messages.append({"role": "bot", "content": next_q})
                with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
                    st.markdown(next_q)
            else:
                st.session_state.step = "gad"
                st.session_state.gad_index = 0
                gad_intro = "Thank you. Now let’s look at anxiety. Over the last 2 weeks: " + GAD_7_QUESTIONS[0]
                if not any(msg["content"] == gad_intro for msg in st.session_state.messages):  # Avoid duplicate intro
                    st.session_state.messages.append({"role": "bot", "content": gad_intro})
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
            with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
                st.markdown(error_msg)
        else:
            st.session_state.gad_answers.append(score)
            st.session_state.gad_index += 1
            if st.session_state.gad_index < len(GAD_7_QUESTIONS):
                next_q = f"{st.session_state.gad_index + 1}. {GAD_7_QUESTIONS[st.session_state.gad_index]}"
                if not any(msg["content"] == next_q for msg in st.session_state.messages):  # Avoid duplicate questions
                    st.session_state.messages.append({"role": "bot", "content": next_q})
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
                follow_up = [
                    "Here’s a gentle summary of what you’ve shared:",
                    summary,
                    "To finish, how much did you feel you could trust Elli? (1–5)"
                ]
                for msg in follow_up:
                    if not any(existing_msg["content"] == msg for existing_msg in st.session_state.messages):  # Avoid duplicates
                        st.session_state.messages.append({"role": "bot", "content": msg})
                    with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
                        st.markdown(msg)

    elif step == "feedback":
        if st.session_state.trust == 0:
            try:
                trust_score = int(user_input)
                if trust_score not in [1, 2, 3, 4, 5]:
                    raise ValueError
                st.session_state.trust = trust_score
                bot_msg = "Thank you. How comfortable did you feel interacting with Elli? (1–5)"
            except ValueError:
                bot_msg = "Please enter a number from 1 to 5."
            st.session_state.messages.append({"role": "bot", "content": bot_msg})
            import time
            time.sleep(0.1)
            for msg in st.session_state.messages:
                render_chat_message(msg)

            # Allow Streamlit to update
            import time
            time.sleep(0.1)

            # Re-render the entire message history
            for msg in st.session_state.messages:
                render_chat_message(msg)

        elif st.session_state.comfort == 0:
            try:
                comfort_score = int(user_input)
                if comfort_score not in [1, 2, 3, 4, 5]:
                    raise ValueError
                st.session_state.comfort = comfort_score
                bot_msg = "Thanks. Finally, do you have any thoughts or feedback about this experience?"
            except ValueError:
                bot_msg = "Please enter a number from 1 to 5."
            st.session_state.messages.append({"role": "bot", "content": bot_msg})
            import time
            time.sleep(0.1)
            for msg in st.session_state.messages:
                render_chat_message(msg)
            with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
                st.markdown(bot_msg)

        elif st.session_state.feedback == "":
            try:
                st.session_state.feedback = user_input
                data = {
                    "name": st.session_state.get("name", ""),
                    "phq_answers": st.session_state.get("phq_answers", []),
                    "phq_total": sum(st.session_state.get("phq_answers", [])),
                    "phq_interp": interpret(sum(st.session_state.get("phq_answers", [])), "phq"),
                    "gad_answers": st.session_state.get("gad_answers", []),
                    "gad_total": sum(st.session_state.get("gad_answers", [])),
                    "gad_interp": interpret(sum(st.session_state.get("gad_answers", [])), "gad"),
                    "trust": st.session_state.get("trust", ""),
                    "comfort": st.session_state.get("comfort", ""),
                    "user_reflection": st.session_state.get("feedback", ""),
                    "initial_mood": st.session_state.messages[2]["content"] if len(st.session_state.messages) > 2 else "",
                    "full_chat": " | ".join([f"{m['role']}: {m['content']}" for m in st.session_state.get("messages", [])]),
                }

                append_to_google_sheet(data)

                closing = f"Thanks so much for checking in today, {st.session_state.name}. Wishing you care and calm. 🌻"
                st.session_state.messages.append({"role": "bot", "content": closing})
                import time
                time.sleep(0.1)
                for msg in st.session_state.messages:
                    render_chat_message(msg)
                with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
                    st.markdown(closing)
            except Exception as e:
                bot_msg = "An error occurred while processing your feedback. Please try again later."
                st.session_state.messages.append({"role": "bot", "content": bot_msg})
                with st.chat_message("assistant", avatar="assets/elli_avatar.png"):
                    st.markdown(bot_msg)
                st.error(f"Error: {e}")
