import streamlit as st
import random

st.set_page_config(page_title="Study Consent", page_icon="🔗", layout="centered")

st.title("Consent for Participation")
st.markdown("""
Before you begin, please read the following consent information:

*Your participation is voluntary. Your responses are confidential and will be used for research purposes only. You may withdraw at any time.*

If you agree to participate, click the button below to continue.
""")

if "consented" not in st.session_state:
    st.session_state.consented = False

if not st.session_state.consented:
    if st.button("I Consent and Wish to Continue"):
        st.session_state.consented = True
        st.experimental_rerun()
        st.stop()
else:
    if "assigned_url" not in st.session_state:
        static_url = "https://ellistatic.streamlit.app"
        elli_url = "https://ellichatbot.streamlit.app"
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