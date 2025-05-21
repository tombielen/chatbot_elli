import streamlit as st
import time
import csv
import os
from utils.chatbot import summarize_results, safety_check, respond_to_feelings

st.set_page_config(page_title="Elli - Mental Health Assistant", page_icon="🌱")
st.markdown("""
    <style>
        .message-bubble {
            background-color: #f1f1f1;
            padding: 12px;
            border-radius: 12px;
            margin-bottom: 10px;
            max-width: 80%;
        }
        .user-message {
            background-color: #dcf8c6;
            align-self: flex-end;
        }
        .chat-container {
            display: flex;
            flex-direction: column;
        }
        .message-row {
            display: flex;
            margin-bottom: 8px;
        }
        .message-row.user {
            justify-content: flex-end;
        }
        .message-row.bot {
            justify-content: flex-start;
        }
        .bottom-bar input {
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🌱 Elli – Your Mental Health Companion")

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
        writer = csv.DictWriter(csvfile, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

for msg in st.session_state.messages:
    role_class = "user" if msg["role"] == "user" else "bot"
    st.markdown(f'<div class="message-row {role_class}"><div class="message-bubble {"user-message" if role_class=="user" else ""}">{msg["content"]}</div></div>', unsafe_allow_html=True)

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Your message:", key="input")
    submitted = st.form_submit_button("Send")

    if submitted and user_input:
        user_input = user_input.strip()
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Save user input in a temporary variable to avoid double processing
        step = st.session_state.step

        if step == "intro":
            st.session_state.name = user_input
            elli_intro = f"Hi {st.session_state.name}, I’m Elli. 🌱 I’m here to gently check in with you. How have things been for you lately?"
            st.session_state.messages.append({"role": "bot", "content": elli_intro})
            st.session_state.step = "mood"
            st.rerun()

        elif step == "mood":
            if safety_check(user_input):
                st.session_state.messages.append({"role": "bot", "content": "It sounds like you're going through something really tough. Please consider reaching out to a professional or crisis service. You're not alone. 💛"})
                st.stop()
            with st.spinner("Elli is thinking..."):
                response = respond_to_feelings(user_input, st.session_state.name)
                time.sleep(1.5)
            st.session_state.messages.append({"role": "bot", "content": response})
            st.session_state.step = "phq"
            st.session_state.phq_index = 0
            st.session_state.messages.append({"role": "bot", "content": "Let’s reflect on some feelings together. Over the last 2 weeks: " + PHQ_9_QUESTIONS[0]})
            st.rerun()

        elif step == "phq":
            try:
                score = int(user_input)
                if score not in [0,1,2,3]: raise ValueError
            except ValueError:
                st.session_state.messages.append({"role": "bot", "content": "Please respond with a number: 0 (Not at all), 1 (Several days), 2 (More than half the days), or 3 (Nearly every day)."})
            else:
                st.session_state.phq_answers.append(score)
                st.session_state.phq_index += 1
                if st.session_state.phq_index < len(PHQ_9_QUESTIONS):
                    st.session_state.messages.append({"role": "bot", "content": f"{st.session_state.phq_index + 1}. {PHQ_9_QUESTIONS[st.session_state.phq_index]}"})
                else:
                    st.session_state.step = "gad"
                    st.session_state.gad_index = 0
                    st.session_state.messages.append({"role": "bot", "content": "Thank you. Now let’s look at anxiety. Over the last 2 weeks: " + GAD_7_QUESTIONS[0]})
            st.rerun()

        elif step == "gad":
            try:
                score = int(user_input)
                if score not in [0,1,2,3]: raise ValueError
            except ValueError:
                st.session_state.messages.append({"role": "bot", "content": "Please respond with a number: 0 (Not at all), 1 (Several days), 2 (More than half the days), or 3 (Nearly every day)."})
            else:
                st.session_state.gad_answers.append(score)
                st.session_state.gad_index += 1
                if st.session_state.gad_index < len(GAD_7_QUESTIONS):
                    st.session_state.messages.append({"role": "bot", "content": f"{st.session_state.gad_index + 1}. {GAD_7_QUESTIONS[st.session_state.gad_index]}"})
                else:
                    phq_total = sum(st.session_state.phq_answers)
                    gad_total = sum(st.session_state.gad_answers)
                    phq_interp = interpret(phq_total, "phq")
                    gad_interp = interpret(gad_total, "gad")
                    summary = summarize_results(phq_total, phq_interp, gad_total, gad_interp)
                    st.session_state.messages.append({"role": "bot", "content": "Here’s a gentle summary of what you’ve shared:"})
                    st.session_state.messages.append({"role": "bot", "content": summary})
                    st.session_state.step = "feedback"
                    st.session_state.messages.append({"role": "bot", "content": "To finish, how much did you feel you could trust Elli? (1–5)"})
            st.rerun()

        elif step == "feedback":
            if st.session_state.trust == 0:
                try:
                    trust_score = int(user_input)
                    if trust_score not in [1,2,3,4,5]: raise ValueError
                    st.session_state.trust = trust_score
                    st.session_state.messages.append({"role": "bot", "content": "Thank you. How comfortable did you feel interacting with Elli? (1–5)"})
                except ValueError:
                    st.session_state.messages.append({"role": "bot", "content": "Please enter a number from 1 to 5."})
                st.rerun()

            elif st.session_state.comfort == 0:
                try:
                    comfort_score = int(user_input)
                    if comfort_score not in [1,2,3,4,5]: raise ValueError
                    st.session_state.comfort = comfort_score
                    st.session_state.messages.append({"role": "bot", "content": "Thanks. Finally, do you have any thoughts or feedback about this experience?"})
                except ValueError:
                    st.session_state.messages.append({"role": "bot", "content": "Please enter a number from 1 to 5."})
                st.rerun()

            elif st.session_state.feedback == "":
                st.session_state.feedback = user_input
                data = {
                    "name": st.session_state.name,
                    "initial_mood": st.session_state.messages[2]["content"],
                    "phq_total": sum(st.session_state.phq_answers),
                    "phq_interp": interpret(sum(st.session_state.phq_answers), "phq"),
                    "gad_total": sum(st.session_state.gad_answers),
                    "gad_interp": interpret(sum(st.session_state.gad_answers), "gad"),
                    "trust": st.session_state.trust,
                    "comfort": st.session_state.comfort,
                    "user_reflection": st.session_state.feedback
                }
                save_to_csv(data)
                st.session_state.messages.append({"role": "bot", "content": f"Thanks so much for checking in today, {st.session_state.name}. Wishing you care and calm. 🌻"})
                st.rerun()