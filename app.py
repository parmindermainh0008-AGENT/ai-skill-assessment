"""
AI Skill Assessment App
Flow: Google Login -> Domain + Level select -> LLM Questions -> User Answers -> LLM Evaluation -> Results
"""

import streamlit as st

st.set_page_config(page_title="AI Skill Assessment", page_icon="🎯", layout="centered")

from config import LEVELS, NUM_QUESTIONS
from auth import require_login, logout_button
from llm_service import generate_questions, evaluate_answers
from db import init_db, upsert_user, create_quiz_session, save_evaluation, get_user_history

init_db()

# ---------- LOGIN ----------
login_result = require_login()
if not login_result:
    st.stop()

user_email, user_name = login_result
upsert_user(user_email, user_name)
logout_button()

# ---------- SESSION STATE DEFAULTS ----------
defaults = {
    "stage": "setup",       # setup -> quiz -> results
    "questions": [],
    "session_id": None,
    "domain": "",
    "level": "",
    "answers": {},
    "evaluation": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


def reset_quiz():
    st.session_state.stage = "setup"
    st.session_state.questions = []
    st.session_state.session_id = None
    st.session_state.answers = {}
    st.session_state.evaluation = None


# ---------- SIDEBAR: HISTORY ----------
with st.sidebar:
    st.divider()
    st.subheader("📊 Your History")
    history = get_user_history(user_email)
    if not history:
        st.caption("No quizzes attempted yet.")
    else:
        for h in history[:10]:
            pct = round((h["total_score"] / h["max_score"]) * 100) if h["max_score"] else 0
            st.caption(f"**{h['domain']}** ({h['level']}) — {pct}%")

# ---------- STAGE 1: SETUP ----------
if st.session_state.stage == "setup":
    st.title("🎯 AI Skill Assessment")
    st.write(f"Welcome, **{user_name}**! Choose a domain and difficulty level to start your quiz.")

    with st.form("setup_form"):
        domain = st.text_input(
            "Domain / Topic",
            placeholder="e.g. Python, Machine Learning, LangChain, DBMS, React",
        )
        level = st.selectbox("Difficulty Level", LEVELS)
        submitted = st.form_submit_button("Generate Questions →", use_container_width=True)

    if submitted:
        if not domain.strip():
            st.error("Please enter a domain first.")
        else:
            with st.spinner(f"Generating {NUM_QUESTIONS} questions for {domain} ({level})..."):
                questions = generate_questions(domain.strip(), level)
                session_id = create_quiz_session(user_email, domain.strip(), level, questions)

            st.session_state.questions = questions
            st.session_state.session_id = session_id
            st.session_state.domain = domain.strip()
            st.session_state.level = level
            st.session_state.stage = "quiz"
            st.rerun()

# ---------- STAGE 2: QUIZ ----------
elif st.session_state.stage == "quiz":
    st.title(f"📝 {st.session_state.domain} — {st.session_state.level}")
    st.caption(f"{len(st.session_state.questions)} questions. Give your best answer, then submit.")
    st.divider()

    with st.form("quiz_form"):
        for q in st.session_state.questions:
            st.markdown(f"**Q{q['id']}. {q['question']}**")
            answer = st.text_area(
                f"Your answer to Q{q['id']}",
                key=f"answer_{q['id']}",
                label_visibility="collapsed",
                height=100,
            )
            st.session_state.answers[q["id"]] = answer
            st.write("")

        submitted = st.form_submit_button("Submit for Evaluation →", use_container_width=True)

    if submitted:
        qa_pairs = [
            {"question": q["question"], "answer": st.session_state.answers.get(q["id"], "")}
            for q in st.session_state.questions
        ]
        with st.spinner("Evaluating your answers..."):
            evaluation = evaluate_answers(
                st.session_state.domain, st.session_state.level, qa_pairs
            )
            save_evaluation(
                st.session_state.session_id,
                qa_pairs,
                evaluation["evaluations"],
                evaluation["total_score"],
                evaluation["max_score"],
            )

        st.session_state.evaluation = evaluation
        st.session_state.stage = "results"
        st.rerun()

    if st.button("← Cancel and start over"):
        reset_quiz()
        st.rerun()

# ---------- STAGE 3: RESULTS ----------
elif st.session_state.stage == "results":
    ev = st.session_state.evaluation
    pct = round((ev["total_score"] / ev["max_score"]) * 100) if ev["max_score"] else 0

    st.title("📊 Results")
    st.subheader(f"{st.session_state.domain} — {st.session_state.level}")

    col1, col2 = st.columns(2)
    col1.metric("Score", f"{ev['total_score']} / {ev['max_score']}")
    col2.metric("Percentage", f"{pct}%")

    st.info(ev.get("overall_feedback", ""))
    st.divider()

    for i, e in enumerate(ev["evaluations"], 1):
        with st.expander(f"Q{i}: {e['question'][:80]}... — {e['score']}/{e['max_score']}"):
            st.write(f"**Feedback:** {e.get('feedback', '')}")
            if e.get("missing_points"):
                st.write(f"**Could improve:** {e.get('missing_points')}")

    st.divider()
    if st.button("🔁 Try Another Domain", use_container_width=True):
        reset_quiz()
        st.rerun()