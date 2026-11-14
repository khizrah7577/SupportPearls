"""Animated login / signup / password recovery."""

from __future__ import annotations

import streamlit as st

from src.auth.service import AuthService


def _set_user(user) -> None:
    st.session_state.authenticated = True
    st.session_state.user = user.to_dict()
    st.session_state.page = "dashboard"
    st.session_state.llm_model = user.preferred_model
    st.session_state.auth_error = ""
    st.session_state.auth_info = ""


def render_auth() -> None:
    auth = AuthService()
    mode = st.session_state.get("auth_mode", "login")

    st.markdown(
        """
        <div class="auth-shell">
          <div class="auth-grid">
            <div class="auth-hero">
              <div class="brand-mark">Support<span>Pearlz</span></div>
              <p class="hero-copy">
                Premium AI support for Pearlz Home Systems — grounded answers from
                product manuals, warranty, shipping, and policy documents, with
                citations you can trust.
              </p>
              <div class="hero-pills">
                <span class="hero-pill">Grounded RAG</span>
                <span class="hero-pill">Source citations</span>
                <span class="hero-pill">Honest refusals</span>
                <span class="hero-pill">Secure accounts</span>
              </div>
            </div>
            <div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Place the form in the right column visually via a second grid-like layout
    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.markdown("<div style='height:0.1rem'></div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        if mode == "login":
            st.markdown("<h2>Welcome back</h2>", unsafe_allow_html=True)
            st.markdown(
                '<p class="sub">Sign in to continue to your SupportPearlz workspace.</p>',
                unsafe_allow_html=True,
            )
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("Email", placeholder="you@company.com")
                password = st.text_input(
                    "Password", type="password", placeholder="••••••••"
                )
                remember = st.checkbox("Remember this browser session", value=True)
                submitted = st.form_submit_button(
                    "Sign in", type="primary", use_container_width=True
                )
            if submitted:
                user, err = auth.login(email, password)
                if err:
                    st.session_state.auth_error = err
                else:
                    st.session_state.remember_session = remember
                    _set_user(user)
                    st.rerun()
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Create account", use_container_width=True):
                    st.session_state.auth_mode = "signup"
                    st.session_state.auth_error = ""
                    st.rerun()
            with c2:
                if st.button("Forgot password", use_container_width=True):
                    st.session_state.auth_mode = "reset"
                    st.session_state.auth_error = ""
                    st.rerun()

        elif mode == "signup":
            st.markdown("<h2>Create your account</h2>", unsafe_allow_html=True)
            st.markdown(
                '<p class="sub">Passwords are hashed with bcrypt — never stored in plain text.</p>',
                unsafe_allow_html=True,
            )
            with st.form("signup_form"):
                full_name = st.text_input("Full name", placeholder="Khizrah Javed")
                email = st.text_input("Email", placeholder="you@company.com")
                password = st.text_input(
                    "Password", type="password", placeholder="Min 8 chars, letters + numbers"
                )
                confirm = st.text_input("Confirm password", type="password")
                recovery_hint = st.text_input(
                    "Recovery hint",
                    placeholder="e.g. Favourite Pearlz product",
                )
                recovery_answer = st.text_input(
                    "Recovery answer",
                    type="password",
                    placeholder="Used only for password reset",
                )
                submitted = st.form_submit_button(
                    "Create account", type="primary", use_container_width=True
                )
            if submitted:
                if password != confirm:
                    st.session_state.auth_error = "Passwords do not match."
                else:
                    user, err = auth.register(
                        email=email,
                        full_name=full_name,
                        password=password,
                        recovery_hint=recovery_hint,
                        recovery_answer=recovery_answer,
                    )
                    if err:
                        st.session_state.auth_error = err
                    else:
                        _set_user(user)
                        st.rerun()
            if st.button("Back to sign in", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.session_state.auth_error = ""
                st.rerun()

        else:  # reset
            st.markdown("<h2>Reset password</h2>", unsafe_allow_html=True)
            st.markdown(
                '<p class="sub">Verify your recovery answer to set a new password.</p>',
                unsafe_allow_html=True,
            )
            email = st.text_input("Account email", key="reset_email")
            if st.button("Show recovery hint", use_container_width=True):
                hint = auth.get_recovery_hint(email)
                if hint:
                    st.session_state.auth_info = f"Hint: {hint}"
                    st.session_state.auth_error = ""
                else:
                    st.session_state.auth_error = "No account found for that email."
                    st.session_state.auth_info = ""
            with st.form("reset_form"):
                recovery_answer = st.text_input("Recovery answer", type="password")
                new_password = st.text_input("New password", type="password")
                confirm = st.text_input("Confirm new password", type="password")
                submitted = st.form_submit_button(
                    "Update password", type="primary", use_container_width=True
                )
            if submitted:
                if new_password != confirm:
                    st.session_state.auth_error = "Passwords do not match."
                else:
                    err = auth.reset_password(
                        email=email,
                        recovery_answer=recovery_answer,
                        new_password=new_password,
                    )
                    if err:
                        st.session_state.auth_error = err
                    else:
                        st.session_state.auth_mode = "login"
                        st.session_state.auth_error = ""
                        st.session_state.auth_info = (
                            "Password updated. Please sign in with your new password."
                        )
                        st.rerun()
            if st.button("Back to sign in", use_container_width=True):
                st.session_state.auth_mode = "login"
                st.session_state.auth_error = ""
                st.rerun()

        if st.session_state.get("auth_error"):
            st.error(st.session_state.auth_error)
        if st.session_state.get("auth_info"):
            st.info(st.session_state.auth_info)
        st.markdown("</div>", unsafe_allow_html=True)
