import streamlit as st
import time
import csv
import os
from utils.chatbot import summarize_results, safety_check, respond_to_feelings

st.set_page_config(page_title="Elli - Mental Health Assistant", page_icon="🌱")
st.title("🌱 Elli – Your Mental Health Companion")

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

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("Write a message to Elli...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if "name" not in st.session_state:
        st.session_state.name = user_input.strip() or "friend"
        with st.chat_message("assistant"):
            with st.spinner("Elli is thinking..."):
                time.sleep(2)
                st.write(f"Nice to meet you, {st.session_state.name}. 🌱 Before we chat further, may I ask how you’ve been feeling lately?")
    elif "mood" not in st.session_state:
        st.session_state.mood = user_input
        if safety_check(user_input):
            with st.chat_message("assistant"):
                st.error("It sounds like you're going through something really tough. Please consider reaching out to a professional or crisis service. You're not alone. 💛")
            st.stop()

        with st.chat_message("assistant"):
            with st.spinner("Elli is thinking..."):
                response = respond_to_feelings(st.session_state.mood, st.session_state.name)
                time.sleep(2)
                st.write(response)
                st.write("I'd like to ask you a few short questions to better understand how you're feeling. These are quick and used by mental health professionals.")

    elif "phq_scores" not in st.session_state:
        st.session_state.phq_scores = []
        st.session_state.question_index = 0

    elif "question_index" in st.session_state and st.session_state.question_index < len(PHQ_9_QUESTIONS):
        q = PHQ_9_QUESTIONS[st.session_state.question_index]
        options = ["Not at all", "Several days", "More than half the days", "Nearly every day"]
        choice = st.radio(f"{q}", options, key=f"phq_{st.session_state.question_index}")
        if choice:
            st.session_state.phq_scores.append(options.index(choice))
            st.session_state.question_index += 1
            st.experimental_rerun()

    elif "gad_scores" not in st.session_state:
        st.session_state.gad_scores = []
        st.session_state.gad_index = 0

    elif "gad_index" in st.session_state and st.session_state.gad_index < len(GAD_7_QUESTIONS):
        q = GAD_7_QUESTIONS[st.session_state.gad_index]
        options = ["Not at all", "Several days", "More than half the days", "Nearly every day"]
        choice = st.radio(f"{q}", options, key=f"gad_{st.session_state.gad_index}")
        if choice:
            st.session_state.gad_scores.append(options.index(choice))
            st.session_state.gad_index += 1
            st.experimental_rerun()

    elif "summary_shown" not in st.session_state:
        phq_total = sum(st.session_state.phq_scores)
        gad_total = sum(st.session_state.gad_scores)
        phq_interp = interpret(phq_total, "phq")
        gad_interp = interpret(gad_total, "gad")

        with st.chat_message("assistant"):
            with st.spinner("Elli is thinking..."):
                summary = summarize_results(phq_total, phq_interp, gad_total, gad_interp)
                time.sleep(2)
                st.write("Here’s your personalized emotional summary:")
                st.write(summary)

        st.session_state.summary_shown = True

    elif "reflection_done" not in st.session_state:
        trust = st.slider("I felt like I could trust Elli.", 1, 5)
        comfort = st.slider("I felt comfortable interacting with Elli.", 1, 5)
        reflection = st.text_area("Any feedback you'd like to share about this experience?")

        data = {
            "name": st.session_state.name,
            "age": "",  
            "gender": "",
            "therapy_history": "",
            "initial_mood": st.session_state.mood,
            "phq_total": sum(st.session_state.phq_scores),
            "phq_interp": interpret(sum(st.session_state.phq_scores), "phq"),
            "gad_total": sum(st.session_state.gad_scores),
            "gad_interp": interpret(sum(st.session_state.gad_scores), "gad"),
            "trust": trust,
            "comfort": comfort,
            "user_reflection": reflection
        }

        save_to_csv(data)
        st.balloons()
        with st.chat_message("assistant"):
            st.success(f"Thanks for checking in today, {st.session_state.name}. 🌻 Take gentle care.")
        st.session_state.reflection_done = True

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
