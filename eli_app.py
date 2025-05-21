import streamlit as st
import time
import csv
import os
from utils.chatbot import summarize_results, safety_check
from streamlit_chat import message  # pip install streamlit-chat

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

st.set_page_config(page_title="Elli - Mental Health Companion", page_icon="🌱")
st.title("🌱 Elli – Your Mental Health Companion")


if "phase" not in st.session_state:
    st.session_state.phase = "intro"
    st.session_state.intro_step = 1  
    st.session_state.demographics = {}
    st.session_state.phq_index = 0
    st.session_state.phq_scores = []
    st.session_state.gad_index = 0
    st.session_state.gad_scores = []
    st.session_state.final_feedback = {}
    st.session_state.chat_history = []
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": "Hi, I'm Elli, your mental health companion. What's your name?"
    })

with st.form("chat_form", clear_on_submit=True):
    user_message = st.text_input("Your message:")
    submitted = st.form_submit_button("Send")

if submitted and user_message:
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_message
    })

    if st.session_state.phase == "intro":
        if st.session_state.intro_step == 1:
            st.session_state.demographics["name"] = user_message.strip()
            response = f"Nice to meet you, {st.session_state.demographics['name']}. How have you been feeling lately?"
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
            st.session_state.intro_step = 2

        elif st.session_state.intro_step == 2:
            st.session_state.demographics["mood"] = user_message.strip()
            if safety_check(user_message):
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "It sounds like you're going through something really tough. Please consider reaching out to a professional or crisis service. You're not alone. 💛"
                })
                st.session_state.phase = "end"
            else:
                response = "Thanks for sharing. Can you tell me your age?"
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response
                })
                st.session_state.intro_step = 3

        elif st.session_state.intro_step == 3:
            st.session_state.demographics["age"] = user_message.strip()
            response = "And what is your gender? (You can leave this blank if you prefer.)"
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
            st.session_state.intro_step = 4

        elif st.session_state.intro_step == 4:
            st.session_state.demographics["gender"] = user_message.strip()
            response = "Have you done therapy before? (Yes/No)"
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response
            })
            st.session_state.intro_step = 5

        elif st.session_state.intro_step == 5:
            st.session_state.demographics["therapy"] = user_message.strip()
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "Great, thanks for sharing your info. Let's now check in on how you've been feeling with a few structured questions."
            })
            st.session_state.phase = "phq"
            st.session_state.intro_step = None
            q = PHQ_9_QUESTIONS[0]
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"PHQ Question 1: {q} (Please reply with a number from 0 to 3)"
            })

    elif st.session_state.phase == "phq":
        try:
            answer = int(user_message.strip())
            if answer not in [0, 1, 2, 3]:
                raise ValueError
        except ValueError:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "Invalid input. Please reply with a number between 0 and 3."
            })
        else:
            st.session_state.phq_scores.append(answer)
            st.session_state.phq_index += 1
            if st.session_state.phq_index < len(PHQ_9_QUESTIONS):
                q = PHQ_9_QUESTIONS[st.session_state.phq_index]
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"PHQ Question {st.session_state.phq_index+1}: {q} (Please reply with a number from 0 to 3)"
                })
            else:
                st.session_state.phase = "gad"
                st.session_state.gad_index = 0
                q = GAD_7_QUESTIONS[st.session_state.gad_index]
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": ("Great, now let's move on to the next set of questions.\n" +
                                f"GAD Question 1: {q} (Please reply with a number from 0 to 3)")
                })

    elif st.session_state.phase == "gad":
        try:
            answer = int(user_message.strip())
            if answer not in [0, 1, 2, 3]:
                raise ValueError
        except ValueError:
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "Invalid input. Please reply with a number between 0 and 3."
            })
        else:
            st.session_state.gad_scores.append(answer)
            st.session_state.gad_index += 1
            if st.session_state.gad_index < len(GAD_7_QUESTIONS):
                q = GAD_7_QUESTIONS[st.session_state.gad_index]
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"GAD Question {st.session_state.gad_index+1}: {q} (Please reply with a number from 0 to 3)"
                })
            else:
                phq_total = sum(st.session_state.phq_scores)
                gad_total = sum(st.session_state.gad_scores)
                phq_interp = interpret(phq_total, "phq")
                gad_interp = interpret(gad_total, "gad")
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "Thanks for answering those questions! Let me generate your personalized summary..."
                })
                with st.spinner("Elli is thinking..."):
                    time.sleep(2)
                    summary = summarize_results(phq_total, phq_interp, gad_total, gad_interp)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"### 🌼 Your Personalized Summary\n\n{summary}"
                })
                st.session_state.phase = "final"
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "Before we wrap up, please rate how much you trusted our conversation with Elli on a scale from 1 (low) to 5 (high)."
                })
                
    elif st.session_state.phase == "final":
        if "trust" not in st.session_state.final_feedback:
            try:
                trust_val = int(user_message.strip())
                if trust_val < 1 or trust_val > 5:
                    raise ValueError
            except ValueError:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "Please enter a valid number between 1 and 5 for trust."
                })
            else:
                st.session_state.final_feedback["trust"] = trust_val
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "How comfortable did you feel interacting with Elli? (Please reply with a number between 1 and 5)"
                })
        elif "comfort" not in st.session_state.final_feedback:
            try:
                comfort_val = int(user_message.strip())
                if comfort_val < 1 or comfort_val > 5:
                    raise ValueError
            except ValueError:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "Please enter a valid number between 1 and 5 for comfort."
                })
            else:
                st.session_state.final_feedback["comfort"] = comfort_val
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "Any additional feedback you'd like to share about this experience?"
                })
        else:
            st.session_state.final_feedback["reflection"] = user_message.strip()
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
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Thanks so much for checking in today, {demog.get('name', 'friend')}. Wishing you care and calm. 🌻"
            })
            st.session_state.phase = "end"

for i, chat in enumerate(st.session_state.chat_history):
    if chat["role"] == "assistant":
        message(chat["content"], key=f"assistant_{i}")
    else:
        message(chat["content"], key=f"user_{i}", is_user=True)
