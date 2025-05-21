import streamlit as st
import time
import csv
import os
from utils.chatbot import summarize_results, safety_check, respond_to_feelings

st.set_page_config(page_title="Elli - Mental Health Assistant", page_icon="🌱")

st.markdown("""
    <style>
        .stChatMessage {
            border-radius: 20px;
            padding: 12px 18px;
            margin-bottom: 10px;
        }
        .stChatMessage.user {
            background-color: #f0f2f6;
            color: #000;
        }
        .stChatMessage.assistant {
            background-color: #e6f4ea;
            color: #000;
        }
        .stTextInput > div > div {
            border-radius: 15px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🌱 Elli – Your Mental Health Companion")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Hi there, I’m Elli. What’s your name or nickname you'd like me to use?"}
    ]
    st.session_state.step = "ask_name"
    st.session_state.user_data = {}

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

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Send a message")

if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    if st.session_state.step == "ask_name":
        st.session_state.user_data["name"] = user_input.strip()
        response = f"Nice to meet you, {user_input.strip()}! How have things been for you lately?"
        st.session_state.step = "ask_mood"

    elif st.session_state.step == "ask_mood":
        mood = user_input.strip()
        st.session_state.user_data["initial_mood"] = mood
        if safety_check(mood):
            st.session_state.chat_history.append({"role": "assistant", "content": "It sounds like you're going through something really tough. Please consider reaching out to a professional or crisis service. You're not alone. 💛"})
            st.stop()
        with st.spinner("Elli is thinking about what you shared..."):
            response = respond_to_feelings(mood, st.session_state.user_data["name"])
        st.session_state.step = "phq"

    elif st.session_state.step == "phq":
        st.write("### Let's reflect on some feelings together...")
        phq_scores = []
        for i, q in enumerate(PHQ_9_QUESTIONS):
            score = st.radio(
                f"{i+1}. Over the last 2 weeks: {q}",
                [0, 1, 2, 3],
                format_func=lambda x: ["Not at all", "Several days", "More than half the days", "Nearly every day"][x],
                key=f"phq_{i}"
            )
            phq_scores.append(score)
        st.session_state.user_data["phq_scores"] = phq_scores
        st.session_state.step = "gad"
        response = "Thanks for sharing those. Let’s move on to a few more."

    elif st.session_state.step == "gad":
        gad_scores = []
        for i, q in enumerate(GAD_7_QUESTIONS):
            score = st.radio(
                f"{i+1}. Over the last 2 weeks: {q}",
                [0, 1, 2, 3],
                format_func=lambda x: ["Not at all", "Several days", "More than half the days", "Nearly every day"][x],
                key=f"gad_{i}"
            )
            gad_scores.append(score)
        st.session_state.user_data["gad_scores"] = gad_scores

        phq_total = sum(st.session_state.user_data["phq_scores"])
        gad_total = sum(st.session_state.user_data["gad_scores"])
        phq_interp = interpret(phq_total, "phq")
        gad_interp = interpret(gad_total, "gad")

        with st.spinner("Elli is writing your summary..."):
            summary = summarize_results(phq_total, phq_interp, gad_total, gad_interp)
            st.session_state.chat_history.append({"role": "assistant", "content": f"### 🌼 Your Personalized Summary\n{summary}"})

        trust = st.slider("I felt like I could trust Elli.", 1, 5)
        comfort = st.slider("I felt comfortable interacting with Elli.", 1, 5)
        reflection = st.text_area("Any feedback you'd like to share about this experience?")

        data = {
            "name": st.session_state.user_data["name"],
            "initial_mood": st.session_state.user_data["initial_mood"],
            "phq_total": phq_total,
            "phq_interp": phq_interp,
            "gad_total": gad_total,
            "gad_interp": gad_interp,
            "trust": trust,
            "comfort": comfort,
            "user_reflection": reflection
        }

        save_to_csv(data)
        response = f"Thanks so much for checking in today, {st.session_state.user_data['name']}. Wishing you care and calm. 🌻"
        st.session_state.step = "done"

    elif st.session_state.step == "done":
        response = "You've already completed the check-in. Come back any time, friend 🌿"

    st.chat_message("assistant").markdown(response)
    st.session_state.chat_history.append({"role": "assistant", "content": response})
