"""Phase-1 temporary UI (Streamlit) — test the agent before the React frontend.

Run: streamlit run streamlit_app.py
"""
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="CanPath AI (dev)", page_icon="🍁", layout="wide")
st.title("🍁 CanPath AI — dev console")

with st.sidebar:
    st.header("Profil / Profile")
    lang = st.radio("Langue / Language", ["fr", "en"], horizontal=True)
    occupation = st.text_input("Profession / Occupation", "Software developer")
    noc = st.text_input("Code CNP / NOC code", "21232")
    province = st.selectbox("Province", [
        "Ontario", "Quebec", "British Columbia", "Alberta", "Manitoba",
        "Saskatchewan", "Nova Scotia", "New Brunswick",
    ])
    status = st.selectbox("Statut / Status", ["PGWP", "PR applicant", "Study permit", "Worker"])

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        for viz in msg.get("visualizations", []):
            st.plotly_chart(go.Figure(viz["figure"]), use_container_width=True)

prompt = st.chat_input("Posez votre question / Ask your question")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"), st.spinner("..."):
        from app.agent.agent import run_agent

        result = run_agent(
            prompt,
            session_id=st.session_state.session_id,
            language=lang,
            profile={"occupation": occupation, "noc_code": noc,
                     "province": province, "status": status, "language": lang},
        )
        st.session_state.session_id = result["session_id"]
        st.markdown(result["answer"])
        for viz in result["visualizations"]:
            st.plotly_chart(go.Figure(viz["figure"]), use_container_width=True)
        st.session_state.messages.append({
            "role": "assistant", "content": result["answer"],
            "visualizations": result["visualizations"],
        })
