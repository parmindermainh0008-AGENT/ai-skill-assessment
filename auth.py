"""
Google Login — uses Streamlit's native OIDC auth (st.login / st.user / st.logout).
This is built into Streamlit 1.42+ and based on Authlib — no third-party auth
library needed, which also avoids PKCE/session bugs.

Required: the [auth] section must be configured in .streamlit/secrets.toml.
See README.md for the full setup steps.
"""

import streamlit as st


def require_login():
    """
    Shows the login screen if the user isn't authenticated.
    Returns (email, name) once authenticated, otherwise None.
    """
    if not st.user.is_logged_in:
        st.title("🎯 AI Skill Assessment")
        st.write("Test your knowledge in any domain — with AI-generated questions.")
        st.divider()
        st.button("Log in with Google", on_click=st.login, use_container_width=True)
        return None

    email = st.user.email
    name = st.user.name or email
    return email, name


def logout_button():
    with st.sidebar:
        st.write(f"👤 **{st.user.name}**")
        st.button("Log out", on_click=st.logout)