"""User settings, API key (session-only), and account security."""

from __future__ import annotations

import streamlit as st

from src.auth.service import AuthService
from src.services.agent_service import clear_agent_cache, resolve_openai_api_key


MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"]


def render_settings() -> None:
    user = st.session_state.user
    auth = AuthService()
    user_id = int(user["id"])

    st.markdown(
        '<div class="topbar"><div class="topbar-brand">Settings &amp; <span>Profile</span></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("### Profile")
    name = st.text_input("Full name", value=user.get("full_name", ""))
    st.text_input("Email", value=user.get("email", ""), disabled=True)
    model = st.selectbox(
        "Preferred chat model",
        MODELS,
        index=MODELS.index(user.get("preferred_model", "gpt-4o-mini"))
        if user.get("preferred_model") in MODELS
        else 0,
    )
    if st.button("Save profile", type="primary"):
        updated = auth.update_profile(
            user_id, full_name=name, preferred_model=model
        )
        if updated:
            st.session_state.user = updated.to_dict()
            st.session_state.llm_model = updated.preferred_model
            clear_agent_cache()
            st.success("Profile updated.")
        else:
            st.error("Could not update profile.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("### OpenAI API key")
    st.caption(
        "Stored only in this browser session (and/or Streamlit secrets). "
        "Never written to the user database."
    )
    current = resolve_openai_api_key()
    if current:
        masked = f"{current[:7]}…{current[-4:]}" if len(current) > 12 else "••••••••"
        st.success(f"Active key: `{masked}`")
    else:
        st.warning("No API key configured yet.")
    key = st.text_input(
        "Set / replace session API key",
        type="password",
        placeholder="sk-… or sk-proj-…",
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Save key to session", use_container_width=True):
            if not key.strip().startswith("sk-") or len(key.strip()) < 20:
                st.error("That does not look like a valid OpenAI API key.")
            else:
                st.session_state.openai_api_key = key.strip()
                clear_agent_cache()
                st.success("API key saved for this session.")
                st.rerun()
    with c2:
        if st.button("Clear session key", use_container_width=True):
            st.session_state.pop("openai_api_key", None)
            clear_agent_cache()
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("### Change password")
    with st.form("change_password_form"):
        current_pw = st.text_input("Current password", type="password")
        new_pw = st.text_input("New password", type="password")
        confirm = st.text_input("Confirm new password", type="password")
        submitted = st.form_submit_button("Update password", type="primary")
    if submitted:
        if new_pw != confirm:
            st.error("New passwords do not match.")
        else:
            err = auth.change_password(user_id, current_pw, new_pw)
            if err:
                st.error(err)
            else:
                st.success("Password updated.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown("### Session")
    if st.button("Sign out", type="primary"):
        clear_agent_cache()
        for key_name in list(st.session_state.keys()):
            del st.session_state[key_name]
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
