import streamlit as st
import random

st.set_page_config(page_title="Study Consent", page_icon="🔗", layout="centered")

st.title("Take Part in Our Study")

st.markdown("""
### About This Study

Please consider participating in our research study exploring how digital interfaces influence user experiences in mental health screening.

In this study, you will be asked to complete two short self-assessment questionnaires related to mood and anxiety, followed by a brief feedback form. Participation should take approximately 5–7 minutes.

Your responses will be used anonymously for academic research. All data will be stored securely in accordance with GDPR regulations and used strictly for scientific purposes.

You may withdraw at any time before submitting your responses. If you later wish to delete your data, you can contact the lead researcher by email.

This study is conducted by **Tom Bielen** (tom.bielen@iu-study.org), BSc in Applied Psychology.
            
P.S: This survey contains Karma to get free survey responses at SurveySwap.io

---

### Privacy and Data Protection

- Your participation is **voluntary** and **anonymous**.
- No personally identifying data is collected.
- All responses are stored on **secure, encrypted servers**.
- Data will only be used for academic research and may be published in aggregated form.
- If you wish to have your data deleted after participation, contact **tom.bielen@iu-study.org**.

---

### Consent

By clicking "I Consent and Wish to Continue", you confirm that you have read and understood the information above, and agree to participate in this study.

If you do not wish to participate, you may close this page at any time.
""")

if "consented" not in st.session_state:
    st.session_state.consented = False

if not st.session_state.consented:
    if st.button("I Consent and Wish to Continue"):
        st.session_state.consented = True
        st.rerun()
        st.stop()
else:
    if "assigned_url" not in st.session_state:
        static_url = "https://ellistatic.streamlit.app"
        elli_url = "https://ellichat.streamlit.app"
        st.session_state.assigned_url = random.choice([static_url, elli_url])
    st.write("Thank you for consenting! You will now be redirected to the study.")
    st.markdown(f"[Click here if you are not redirected automatically.]({st.session_state.assigned_url})")
    st.markdown(
        f"""
        <script>
        window.top.location.href = "{st.session_state.assigned_url}";
        </script>
        """,
        unsafe_allow_html=True,
    )
