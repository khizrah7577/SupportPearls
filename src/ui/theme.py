"""SupportPearlz premium design system (CSS)."""

from __future__ import annotations

PEARL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Sora:wght@600;700;800&display=swap');

:root {
  --pearl-ink: #071726;
  --pearl-ink-soft: #1f3a4a;
  --pearl-muted: #4a6674;
  --pearl-white: #ffffff;
  --pearl-fog: #f3f8fa;
  --pearl-mist: #e7f3f4;
  --pearl-teal: #0e8f97;
  --pearl-teal-deep: #0a6b72;
  --pearl-navy: #0b2740;
  --pearl-gold: #c9a227;
  --pearl-line: rgba(7, 23, 38, 0.12);
  --pearl-shadow: 0 20px 60px rgba(7, 23, 38, 0.12);
  --pearl-radius: 18px;
}

html, body, [class*="css"], .stApp, .stMarkdown, p, label, span, li, h1, h2, h3, h4 {
  font-family: 'Outfit', sans-serif !important;
}

.stApp {
  background:
    radial-gradient(900px 500px at 8% -5%, rgba(14,143,151,0.18), transparent 55%),
    radial-gradient(800px 480px at 100% 0%, rgba(201,162,39,0.12), transparent 50%),
    radial-gradient(700px 420px at 50% 110%, rgba(11,39,64,0.08), transparent 55%),
    linear-gradient(165deg, #f7fbfc 0%, #eef6f7 45%, #f8f5ef 100%);
  background-attachment: fixed;
  color: var(--pearl-ink);
}

#MainMenu, footer, header { visibility: hidden; }
div[data-testid="stToolbar"], div[data-testid="stDecoration"] { display: none; }
div[role="tooltip"], [data-baseweb="tooltip"] { display: none !important; }

section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0b2740 0%, #0a3d4a 55%, #0e8f97 140%);
  border-right: none;
}
section[data-testid="stSidebar"] * {
  color: #f5fbfc !important;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
  color: #e8f4f5 !important;
}
section[data-testid="stSidebar"] div.stButton > button {
  background: rgba(255,255,255,0.08) !important;
  border: 1px solid rgba(255,255,255,0.18) !important;
  color: #ffffff !important;
}
section[data-testid="stSidebar"] div.stButton > button * {
  color: #ffffff !important;
}
section[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #0e8f97, #12a8b0) !important;
  border: none !important;
}

/* ---- Auth shell ---- */
.auth-shell {
  max-width: 1080px;
  margin: 1.2rem auto 0;
  animation: pearlRise 0.7s ease-out both;
}
.auth-grid {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 1.4rem;
  align-items: stretch;
}
@media (max-width: 900px) {
  .auth-grid { grid-template-columns: 1fr; }
}
.auth-hero {
  position: relative;
  overflow: hidden;
  border-radius: 28px;
  padding: 2.2rem 2rem;
  min-height: 520px;
  background:
    linear-gradient(145deg, rgba(11,39,64,0.92), rgba(10,107,114,0.88)),
    radial-gradient(circle at 20% 20%, rgba(201,162,39,0.25), transparent 40%);
  color: #ffffff !important;
  box-shadow: var(--pearl-shadow);
}
.auth-hero * { color: #ffffff !important; }
.auth-hero::before,
.auth-hero::after {
  content: "";
  position: absolute;
  border-radius: 50%;
  filter: blur(2px);
  animation: floatOrb 8s ease-in-out infinite;
}
.auth-hero::before {
  width: 180px; height: 180px;
  right: -30px; top: -20px;
  background: rgba(255,255,255,0.12);
}
.auth-hero::after {
  width: 120px; height: 120px;
  left: 18%; bottom: 12%;
  background: rgba(201,162,39,0.22);
  animation-delay: -3s;
}
.brand-mark {
  font-family: 'Sora', sans-serif !important;
  font-weight: 800;
  font-size: clamp(2.4rem, 5vw, 3.4rem);
  letter-spacing: -0.04em;
  line-height: 1;
  margin: 0 0 0.8rem 0;
  position: relative;
  z-index: 1;
}
.brand-mark span { color: #7fd6db !important; }
.hero-copy {
  position: relative;
  z-index: 1;
  font-size: 1.05rem;
  line-height: 1.6;
  max-width: 28rem;
  opacity: 0.92;
}
.hero-pills {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-top: 1.4rem;
}
.hero-pill {
  font-size: 0.78rem;
  font-weight: 600;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.18);
}
.glass-card {
  background: rgba(255,255,255,0.82);
  backdrop-filter: blur(16px);
  border: 1px solid var(--pearl-line);
  border-radius: 28px;
  padding: 1.6rem 1.45rem 1.3rem;
  box-shadow: var(--pearl-shadow);
  animation: pearlRise 0.7s ease-out 0.08s both;
}
.glass-card h2 {
  font-family: 'Sora', sans-serif !important;
  font-size: 1.45rem;
  margin: 0 0 0.35rem 0;
  color: var(--pearl-ink) !important;
}
.glass-card .sub {
  color: var(--pearl-muted) !important;
  margin-bottom: 1rem;
  font-size: 0.95rem;
}

/* ---- Dashboard ---- */
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}
.topbar-brand {
  font-family: 'Sora', sans-serif !important;
  font-weight: 800;
  font-size: 1.45rem;
  color: var(--pearl-ink) !important;
}
.topbar-brand span { color: var(--pearl-teal) !important; }
.welcome-banner {
  background:
    linear-gradient(120deg, rgba(11,39,64,0.95), rgba(14,143,151,0.9));
  color: #fff !important;
  border-radius: 24px;
  padding: 1.4rem 1.5rem;
  margin-bottom: 1rem;
  box-shadow: var(--pearl-shadow);
  animation: pearlRise 0.5s ease-out both;
}
.welcome-banner * { color: #fff !important; }
.welcome-banner h2 {
  font-family: 'Sora', sans-serif !important;
  margin: 0 0 0.35rem 0;
  font-size: 1.55rem;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.8rem;
  margin: 0.8rem 0 1.1rem;
}
@media (max-width: 800px) {
  .stat-grid { grid-template-columns: 1fr; }
}
.stat-card {
  background: #ffffff;
  border: 1px solid var(--pearl-line);
  border-radius: 18px;
  padding: 1rem 1.05rem;
  box-shadow: 0 10px 28px rgba(7,23,38,0.05);
}
.stat-card .label {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--pearl-muted) !important;
}
.stat-card .value {
  font-family: 'Sora', sans-serif !important;
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--pearl-ink) !important;
  margin-top: 0.2rem;
}
.feature-card, .history-card, .chat-shell, .settings-card {
  background: #ffffff;
  border: 1px solid var(--pearl-line);
  border-radius: 20px;
  padding: 1.1rem 1.15rem;
  box-shadow: 0 12px 30px rgba(7,23,38,0.05);
  margin-bottom: 0.85rem;
}
.feature-card h3, .history-card h3, .settings-card h3 {
  font-family: 'Sora', sans-serif !important;
  margin: 0 0 0.35rem 0;
  color: var(--pearl-ink) !important;
  font-size: 1.05rem;
}
.feature-card p, .history-card p { color: var(--pearl-muted) !important; margin: 0; }

/* Chat */
div[data-testid="stChatMessage"] {
  background: #ffffff;
  border: 1px solid var(--pearl-line);
  border-radius: 16px;
  margin-bottom: 0.55rem;
  box-shadow: 0 8px 22px rgba(7,23,38,0.04);
  animation: pearlRise 0.35s ease-out both;
}
div[data-testid="stChatMessage"] p,
div[data-testid="stChatMessage"] li,
div[data-testid="stChatMessage"] span {
  color: var(--pearl-ink) !important;
  line-height: 1.55;
}
.cite-box {
  margin-top: 0.65rem;
  padding: 0.7rem 0.85rem;
  border-radius: 12px;
  background: #f0f8f8;
  border: 1px solid rgba(14,143,151,0.15);
}
.cite-box .title {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--pearl-teal-deep) !important;
  margin-bottom: 0.3rem;
}
.cite-item { font-size: 0.85rem; color: var(--pearl-ink) !important; margin: 0.2rem 0; }
.cite-snip {
  display: block;
  color: var(--pearl-muted) !important;
  font-size: 0.78rem;
  font-style: italic;
}
.badge-row { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.5rem; }
.badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
}
.badge-high { background: var(--pearl-teal-deep); color: #fff !important; }
.badge-partial { background: #8a6418; color: #fff !important; }
.badge-none { background: #9a3d2a; color: #fff !important; }
.badge-rewrite { background: var(--pearl-navy); color: #fff !important; }

/* Controls */
div.stButton > button {
  border-radius: 12px !important;
  font-weight: 700 !important;
  border: 1px solid var(--pearl-line) !important;
  background: #ffffff !important;
  color: var(--pearl-ink) !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
div.stButton > button * { color: var(--pearl-ink) !important; }
div.stButton > button[kind="primary"],
button[kind="primary"] {
  background: linear-gradient(135deg, #0a6b72, #0e8f97) !important;
  color: #ffffff !important;
  border: none !important;
  box-shadow: 0 12px 28px rgba(14,143,151,0.28) !important;
}
div.stButton > button[kind="primary"] *,
button[kind="primary"] * { color: #ffffff !important; }
div.stButton > button:hover { transform: translateY(-1px); }

div[data-testid="stTextInput"] input,
div[data-baseweb="input"] input,
div[data-baseweb="select"] > div,
textarea,
div[data-testid="stChatInput"] textarea {
  background: #ffffff !important;
  color: var(--pearl-ink) !important;
  border: 1px solid rgba(7,23,38,0.16) !important;
  border-radius: 12px !important;
  -webkit-text-fill-color: var(--pearl-ink) !important;
}
div[data-testid="stSelectbox"] span,
div[data-baseweb="select"] span { color: var(--pearl-ink) !important; }
div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label,
div[data-testid="stCheckbox"] label,
div[data-testid="stCheckbox"] span,
div[data-testid="stRadio"] label {
  color: var(--pearl-ink) !important;
}
::placeholder { color: #5b7380 !important; opacity: 1 !important; }
div[data-testid="stAlert"] p, div[data-testid="stAlert"] span {
  color: var(--pearl-ink) !important;
}

@keyframes pearlRise {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes floatOrb {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(14px); }
}
</style>
"""


def inject_theme() -> None:
    import streamlit as st

    st.markdown(PEARL_CSS, unsafe_allow_html=True)
