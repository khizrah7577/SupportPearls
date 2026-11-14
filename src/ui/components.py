"""Reusable Streamlit UI helpers."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.chains.schemas import Confidence, DisplayResponse


SUGGESTED_PROMPTS = [
    "My AquaPearl 500 keeps beeping three times — what should I do?",
    "How long is the warranty on the AquaPearl 500 Pro?",
    "How much does a replacement sediment filter cost?",
    "Do you offer student discounts?",
    "What's the return window if I opened the box?",
    "Can I get next-day delivery to Skardu?",
]


def render_sidebar_nav(current: str) -> str:
    st.markdown("### SupportPearlz")
    st.caption("Pearlz knowledge assistant")
    pages = {
        "dashboard": "Dashboard",
        "chat": "Chat",
        "history": "History",
        "settings": "Settings",
    }
    choice = st.radio(
        "Navigate",
        options=list(pages.keys()),
        format_func=lambda k: pages[k],
        index=list(pages.keys()).index(current) if current in pages else 0,
        label_visibility="collapsed",
    )
    st.divider()
    return choice


def confidence_badges(resp: DisplayResponse) -> None:
    mapping = {
        Confidence.high: "badge-high",
        Confidence.partial: "badge-partial",
        Confidence.none: "badge-none",
    }
    badges = [
        f'<span class="badge {mapping[resp.confidence]}">Confidence · {resp.confidence.value}</span>'
    ]
    if resp.refusal or not resp.answered:
        badges.append('<span class="badge badge-none">Refusal / escalate</span>')
    if resp.rewritten_query and resp.rewritten_query != resp.original_query:
        safe = (
            resp.rewritten_query.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        badges.append(f'<span class="badge badge-rewrite">Rewritten · {safe}</span>')
    st.markdown(f'<div class="badge-row">{"".join(badges)}</div>', unsafe_allow_html=True)


def render_citations(resp: DisplayResponse) -> None:
    if resp.citations:
        items = []
        for i, cite in enumerate(resp.citations, start=1):
            snip = (
                f'<span class="cite-snip">“{cite.snippet[:140]}”</span>'
                if cite.snippet
                else ""
            )
            items.append(
                f'<div class="cite-item"><strong>[{i}]</strong> {cite.display()}{snip}</div>'
            )
        st.markdown(
            f'<div class="cite-box"><div class="title">Sources used</div>{"".join(items)}</div>',
            unsafe_allow_html=True,
        )
    elif resp.refusal or not resp.answered:
        st.markdown(
            '<div class="cite-box"><div class="title">Sources used</div>'
            '<div class="cite-item">None — no supporting documentation found</div></div>',
            unsafe_allow_html=True,
        )


def render_assistant_meta(meta: dict[str, Any] | None) -> None:
    if not meta:
        return
    try:
        resp = DisplayResponse.model_validate(meta)
    except Exception:  # noqa: BLE001
        return
    confidence_badges(resp)
    render_citations(resp)
