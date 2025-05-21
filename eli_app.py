import streamlit as st
import time
import csv
import os
from utils.chatbot import summarize_results, safety_check
from gpt_prompts import SYSTEM_INSTRUCTION  


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


st.set_page_config(page_title="Elli - Mental Health Assistant", page_icon="🌱")
st.title("🌱 Elli – Your Mental Health Companion")


if "intro_done" not in st.session_state:
    with st.form("intro_form"):
        st.markdown("This isn’t therapy, but it’s a warm, thoughtful space.")
        name = st.text_input("What’s your name or nickname you'd like me to use?", max_chars=30)
        age = st.text_input("Age")
        gender = st.text_input("Gender (optional)")
        therapy = st.selectbox("Have you done therapy before?", ["Yes", "No"])
        mood = st.text_area("How have things been for you lately? Just a sentence or two.")
        submitted = st.form_submit_button("Start check-in")
    
    if submitted:
        if not name:
            name = "friend"
        st.session_state.demographics = {
            "name": name,
            "age": age,
            "gender": gender,
            "therapy": therapy,
            "mood": mood
        }
        
        if safety_check(mood):
            st.error("It sounds like you're going through something really tough. Please consider reaching out to a professional or crisis service. You're not alone. 💛")
            st.stop()
        
        st.session_state.intro_done = True
        st.session_state.conversation = []
        st.session_state.conversation.append({
            "role": "assistant",
            "content": f"Nice to meet you, {name} 💬"
        })
        st.session_state.phase = "phq" 
        st.session_state.phq_index = 0
        st.session_state.phq_scores = []
        st.session_state.gad_index = 0
        st.session_state.gad_scores = []
        st.session_state.final_feedback = {}  
        
        st.session_state.conversation.append({
            "role": "assistant",
            "content": ("Let's start our check-in. For each question, please reply with a number from 0 to 3 "
                        "(0: Not at all, 1: Several days, 2: More than half the days, 3: Nearly every day).\n\n"
                        f"PHQ Question 1: {PHQ_9_QUESTIONS[0]}")
        })
        st.experimental_rerun()
    else:
        st.stop()


from streamlit_chat import message

for i, msg in enumerate(st.session_state.conversation):
    if msg["role"] == "assistant":
        message(msg["content"], key=f"assistant_{i}")
    else:
        message(msg["content"], is_user=True, key=f"user_{i}")

with st.form("chat_form", clear_on_submit=True):
    user_message = st.text_input("Your message:", key="user_message")
    chat_submit = st.form_submit_button("Send")

if chat_submit and user_message:

    if st.session_state.phase == "phq":
        try:
            score = int(user_message.strip())
            if score not in [0, 1, 2, 3]:
                raise ValueError
        except ValueError:
            st.session_state.conversation.append({
                "role": "assistant",
                "content": "Invalid input. Please reply with a number between 0 and 3."
            })
            st.experimental_rerun()
        
        st.session_state.conversation.append({"role": "user", "content": str(score)})
        st.session_state.phq_scores.append(score)
        st.session_state.phq_index += 1
        
        if st.session_state.phq_index < len(PHQ_9_QUESTIONS):
            next_q = PHQ_9_QUESTIONS[st.session_state.phq_index]
            st.session_state.conversation.append({
                "role": "assistant",
                "content": f"PHQ Question {st.session_state.phq_index+1}: {next_q}"
            })
        else:
            st.session_state.phase = "gad"
            next_q = GAD_7_QUESTIONS[0]
            st.session_state.conversation.append({
                "role": "assistant",
                "content": ("Great, let's move to the next set of questions.\n"
                            "For each question, please reply with a number between 0 and 3.\n\n"
                            f"GAD Question 1: {next_q}")
            })
        st.experimental_rerun()

    elif st.session_state.phase == "gad":
        try:
            score = int(user_message.strip())
            if score not in [0, 1, 2, 3]:
                raise ValueError
        except ValueError:
            st.session_state.conversation.append({
                "role": "assistant",
                "content": "Invalid input. Please reply with a number between 0 and 3."
            })
            st.experimental_rerun()
        
        st.session_state.conversation.append({"role": "user", "content": str(score)})
        st.session_state.gad_scores.append(score)
        st.session_state.gad_index += 1
        
        if st.session_state.gad_index < len(GAD_7_QUESTIONS):
            next_q = GAD_7_QUESTIONS[st.session_state.gad_index]
            st.session_state.conversation.append({
                "role": "assistant",
                "content": f"GAD Question {st.session_state.gad_index+1}: {next_q}"
            })
        else:
            phq_total = sum(st.session_state.phq_scores)
            gad_total = sum(st.session_state.gad_scores)
            phq_interp = interpret(phq_total, "phq")
            gad_interp = interpret(gad_total, "gad")
            st.session_state.conversation.append({
                "role": "assistant",
                "content": "Thanks for completing the questions! Generating your personalized summary..."
            })
            with st.spinner("Elli is thinking..."):
                time.sleep(2)
                summary = summarize_results(phq_total, phq_interp, gad_total, gad_interp)
            st.session_state.conversation.append({
                "role": "assistant",
                "content": f"### 🌼 Your Personalized Summary\n\n{summary}"
            })
            st.session_state.phase = "final"
            st.session_state.conversation.append({
                "role": "assistant",
                "content": ("Before we wrap up, please rate how much you trusted our conversation with Elli on a scale from 1 to 5 "
                            "(1 = very low, 5 = very high).")
            })
        st.experimental_rerun()

    elif st.session_state.phase == "final":
        if "trust" not in st.session_state.final_feedback:
            try:
                trust_val = int(user_message.strip())
                if trust_val < 1 or trust_val > 5:
                    raise ValueError
            except ValueError:
                st.session_state.conversation.append({
                    "role": "assistant",
                    "content": "Please enter a valid number between 1 and 5 for trust."
                })
                st.experimental_rerun()
            st.session_state.conversation.append({"role": "user", "content": str(trust_val)})
            st.session_state.final_feedback["trust"] = trust_val
            st.session_state.conversation.append({
                "role": "assistant",
                "content": "How comfortable did you feel interacting with Elli? (Enter a number between 1 and 5)"
            })
            st.experimental_rerun()
        elif "comfort" not in st.session_state.final_feedback:
            try:
                comfort_val = int(user_message.strip())
                if comfort_val < 1 or comfort_val > 5:
                    raise ValueError
            except ValueError:
                st.session_state.conversation.append({
                    "role": "assistant",
                    "content": "Please enter a valid number between 1 and 5 for comfort."
                })
                st.experimental_rerun()
            st.session_state.conversation.append({"role": "user", "content": str(comfort_val)})
            st.session_state.final_feedback["comfort"] = comfort_val
            st.session_state.conversation.append({
                "role": "assistant",
                "content": "Any additional feedback you'd like to share about this experience? Type your thoughts below."
            })
            st.experimental_rerun()
        else:
            st.session_state.conversation.append({"role": "user", "content": user_message})
            st.session_state.final_feedback["reflection"] = user_message

            demog = st.session_state.demographics
            data = {
                "name": demog.get("name", ""),
                "age": demog.get("age", ""),
                "gender": demog.get("gender", ""),
                "therapy_history": demog.get("therapy", ""),
                "initial_mood": demog.get("mood", ""),
                "phq_total": sum(st.session_state.phq_scores),
                "phq_interp": interpret(sum(st.session_state.phq_scores), "phq"),
                "gad_total": sum(st.session_state.gad_scores),
                "gad_interp": interpret(sum(st.session_state.gad_scores), "gad"),
                "trust": st.session_state.final_feedback.get("trust"),
                "comfort": st.session_state.final_feedback.get("comfort"),
                "user_reflection": st.session_state.final_feedback.get("reflection")
            }
            save_to_csv(data)
            st.session_state.conversation.append({
                "role": "assistant",
                "content": f"Thanks so much for checking in today, {demog.get('name', 'friend')}. Wishing you care and calm. 🌻"
            })
            st.session_state.phase = "end"
            st.experimental_rerun()
    

