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

with st.form("intro_form"):
    st.markdown("This isn’t therapy, but it’s a warm, thoughtful space.")
    name = st.text_input("What’s your name or nickname you'd like me to use?", max_chars=30)
    age = st.text_input("Age")
    gender = st.text_input("Gender (optional)")
    therapy = st.selectbox("Have you done therapy before?", ["Yes", "No"])
    mood = st.text_area("How have things been for you lately? Just a sentence or two.")
    submitted = st.form_submit_button("Begin Conversation")

if submitted:
    if not name:
        name = "friend"
    st.write(f"Nice to meet you, {name} 💬")

    if safety_check(mood):
        st.error("It sounds like you're going through something really tough. Please consider reaching out to a professional or crisis service. You're not alone. 💛")
        st.stop()

    with st.spinner("Elli is thinking about what you shared..."):
        feeling_response = respond_to_feelings(mood, name)
        time.sleep(2)
        st.write(feeling_response)

    st.markdown("---")
    st.write("### Let’s reflect on some feelings together...")

    phq_scores = []
    for i, q in enumerate(PHQ_9_QUESTIONS):
        score = st.radio(f"{i+1}. Over the last 2 weeks: {q}", [0, 1, 2, 3], format_func=lambda x: ["Not at all", "Several days", "More than half the days", "Nearly every day"][x], key=f"phq_{i}")
        phq_scores.append(score)

    gad_scores = []
    for i, q in enumerate(GAD_7_QUESTIONS):
        score = st.radio(f"{i+1}. Over the last 2 weeks: {q}", [0, 1, 2, 3], format_func=lambda x: ["Not at all", "Several days", "More than half the days", "Nearly every day"][x], key=f"gad_{i}")
        gad_scores.append(score)

    phq_total = sum(phq_scores)
    gad_total = sum(gad_scores)
    phq_interp = interpret(phq_total, "phq")
    gad_interp = interpret(gad_total, "gad")

    st.success("Thanks for sharing that. Elli is now preparing your personalized summary...")
    with st.spinner("Elli is writing your summary..."):
        summary = summarize_results(phq_total, phq_interp, gad_total, gad_interp)
        time.sleep(2)
        st.write("### 🌼 Your Personalized Summary")
        st.write(summary)

    st.markdown("---")
    st.write("#### Final Thoughts")
    trust = st.slider("I felt like I could trust Elli.", 1, 5)
    comfort = st.slider("I felt comfortable interacting with Elli.", 1, 5)
    reflection = st.text_area("Any feedback you'd like to share about this experience?")

    data = {
        "name": name,
        "age": age,
        "gender": gender,
        "therapy_history": therapy,
        "initial_mood": mood,
        "phq_total": phq_total,
        "phq_interp": phq_interp,
        "gad_total": gad_total,
        "gad_interp": gad_interp,
        "trust": trust,
        "comfort": comfort,
        "user_reflection": reflection
    }

    save_to_csv(data)
    st.balloons()
    st.success(f"Thanks so much for checking in today, {name}. Wishing you care and calm. 🌻")
