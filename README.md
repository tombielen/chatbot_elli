# Elli: AI-Powered Chatbot for Mental Health Screening

**Author**: Tom Bielen  
**Affiliation**: IU International University of Applied Sciences  
**Preprint**: [PsyArXiv – The Illusion of Empathy (link pending)](https://psyarxiv.com/xxxxxx)  
**Preregistration**: [OSF Protocol](https://osf.io/6yrkw/)  
**License**: MIT

---

This repository contains **Elli**, a GPT-4-powered research chatbot developed for an independent, preregistered experimental study. Elli conducts conversational mental health screening using the PHQ-9 and GAD-7 with adaptive, empathic dialogue. The project compares this chatbot interface against a static web form to evaluate trust, emotional response, and user disclosure.

> ⚠️ **Disclaimer**:  
> Elli is a **research prototype only** and is not intended for diagnosis, therapy, or crisis support.  
> If you are in emotional distress, please seek help from a qualified mental health professional or hotline.

---

## 🧠 Study Overview

**Study Title**:  
_The Illusion of Empathy: Why Users Distrust GPT-4 Chatbots for Mental Health Screening_

**Objective**:  
Evaluate whether an AI chatbot offering simulated empathy enhances or hinders trust, comfort, and disclosure compared to a static mental health screening form.

---

## 🔬 Methodology

- **Design**: Randomized, cross-sectional, between-subjects, mixed-methods experiment
- **Participants**: 149 adults (age 18+), English-speaking, recruited online
- **Conditions**:
  - **Elli Chatbot**: Adaptive, GPT-4-powered, empathic
  - **Static Form**: No feedback, simple input form (control)
- **Measures**:
  - PHQ-9 and GAD-7 (validated tools)
  - Trust, comfort, and empathy (Likert ratings)
  - Completion time, dropout rate, and open-ended self-disclosure

---

## 📁 Repository Structure

```bash
elli-chatbot-study/
├── README.md                  ← This file
├── preprint.pdf               ← Final preprint manuscript (PsyArXiv)
├── LICENSE                    ← MIT license
├── requirements.txt           ← Python dependencies

# Main chatbot logic and Streamlit apps
├── Elli_version/
│   └── eli_app.py             ← Streamlit app for Elli (GPT-4 chatbot)
├── Static_version/
│   └── static_app.py          ← Streamlit app for static form (control)
├── Consent_script/
│   └── router_app.py          ← Pre-screening consent and eligibility logic

# Data and results
├── data/
│   ├── Chatbot_Study_Data_Cleaned.csv
│   ├── Chatbot_Study_Dataset_Summary.txt
│   └── data analysis/
│       ├── age_subgroup_analysis.py
│       ├── analyze_feedback.py
│       ├── analyze_outcomes_with_assumptions.py
│       ├── demographic_table.py
│       ├── dropout_analysis.py
│       ├── interaction_effects.py
│       ├── mediation_analysis.py
│       ├── Participant_flow_table.py
│       ├── plotting_visuals.py
│       └── save_thematic_table.py

# Final statistical output tables (partial due to .gitignore exclusions)
├── outputs/
│   ├── table1_demographic_table1.csv
│   └── table2_outcomes.csv

# Assets
├── gpt_prompts.py             ← Prompt engineering for chatbot empathy
├── chat_log.txt               ← Example output log (demo or testing)
├── utils/
│   └── chatbot.py             ← Utility functions for interaction logic
├── assets/
│   ├── elli_avatar.png
│   └── user_avatar.png
