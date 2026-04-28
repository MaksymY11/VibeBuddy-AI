"""
VibeBuddy AI — Streamlit frontend
Run with: streamlit run streamlit_app.py
"""

import streamlit as st
from pipeline.guardrails import validate_input
from pipeline.conversation import ConversationManager
from pipeline.agent import Agent
from pipeline.rate_limiter import RateLimiter

# ── Page config (must be first Streamlit call) ────────────────────────────
st.set_page_config(
    page_title="VibeBuddy AI",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Matrix CSS ────────────────────────────────────────────────────────────
MATRIX_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

/* ── Global ── */
html, body, .stApp {
    background-color: #020802 !important;
    color: #b8f0b8 !important;
    font-family: 'Share Tech Mono', monospace !important;
}

/* scanlines */
.stApp::after {
    content: '';
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 9999;
    background: repeating-linear-gradient(
        0deg, transparent, transparent 2px,
        rgba(0,0,0,0.06) 2px, rgba(0,0,0,0.06) 4px
    );
}

/* ── Sidebar ── */
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}
[data-testid="stSidebar"] {
    background-color: #010601 !important;
    border-right: 1px solid #163016 !important;
}
[data-testid="stSidebar"] * {
    font-family: 'Share Tech Mono', monospace !important;
    color: #b8f0b8 !important;
}
[data-testid="stSidebarContent"] {
    padding: 0.5rem 1rem 1.2rem !important;
}
[data-testid="stSidebarHeader"] {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
}

/* ── Main content area ── */
.main .block-container {
    background-color: #020802;
    padding-top: 1.5rem;
    max-width: 860px;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background-color: #061006 !important;
    border: 1px solid #163016 !important;
    border-radius: 4px !important;
    font-family: 'Share Tech Mono', monospace !important;
    color: #b8f0b8 !important;
    padding: 0.75rem 1rem !important;
}
[data-testid="stChatMessage"] p {
    color: #b8f0b8 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.95rem !important;
    line-height: 1.65 !important;
}
/* Avatar */
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"] {
    background-color: #0b1e0b !important;
    border: 1px solid #2a5a2a !important;
    border-radius: 3px !important;
    font-size: 0.75rem !important;
    color: #39ff14 !important;
}

/* ── Chat input ── */
[data-testid="stChatInput"] {
    background-color: #061006 !important;
    border: 1px solid #2a5a2a !important;
    border-radius: 4px !important;
}
[data-testid="stChatInput"] textarea {
    background-color: transparent !important;
    color: #b8f0b8 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.95rem !important;
    caret-color: #39ff14 !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #5aaa5a !important;
    font-family: 'Share Tech Mono', monospace !important;
}
[data-testid="stChatInputSubmitButton"] button {
    background-color: #0b1e0b !important;
    border: 1px solid #2a5a2a !important;
    color: #39ff14 !important;
}
[data-testid="stChatInputSubmitButton"] button:hover {
    background-color: #39ff1422 !important;
    border-color: #39ff14 !important;
    box-shadow: 0 0 8px #39ff1444 !important;
}

/* ── Buttons ── */
.stButton > button {
    background-color: transparent !important;
    border: 1px solid #2a5a2a !important;
    border-radius: 4px !important;
    color: #7acc7a !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.08em !important;
    transition: all 0.15s !important;
    width: 100% !important;
}
.stButton > button:hover {
    border-color: #39ff1466 !important;
    color: #39ff14 !important;
    text-shadow: 0 0 6px #39ff1466 !important;
    background-color: #39ff1411 !important;
}

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div {
    background-color: #163016 !important;
    border-radius: 2px !important;
    height: 4px !important;
}
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #39ff14, #00cc33) !important;
    box-shadow: 0 0 6px #39ff1466 !important;
    border-radius: 2px !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background-color: #061006 !important;
    border: 1px solid #163016 !important;
    border-radius: 4px !important;
    padding: 0.5rem 0.75rem !important;
}
[data-testid="stMetricLabel"] p,
[data-testid="stMetricValue"] {
    color: #7acc7a !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.8rem !important;
}
[data-testid="stMetricValue"] {
    color: #39ff14 !important;
    font-size: 1.1rem !important;
    text-shadow: 0 0 6px #39ff1466 !important;
}

/* ── Dividers ── */
hr {
    border-color: #163016 !important;
    margin: 0.75rem 0 !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] * {
    color: #39ff14 !important;
    font-family: 'Share Tech Mono', monospace !important;
}

/* ── Headings ── */
h1, h2, h3, h4 {
    color: #39ff14 !important;
    font-family: 'Share Tech Mono', monospace !important;
    text-shadow: 0 0 8px #39ff1455 !important;
    letter-spacing: 0.08em !important;
}

/* ── Markdown text ── */
[data-testid="stMarkdown"] p,
[data-testid="stMarkdown"] li,
[data-testid="stMarkdown"] span {
    color: #b8f0b8 !important;
    font-family: 'Share Tech Mono', monospace !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a5a2a; border-radius: 2px; }
</style>
"""
st.markdown(MATRIX_CSS, unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────
def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hey! What kind of music are you in the mood for?"}
        ]
    if "pipeline_steps" not in st.session_state:
        st.session_state.pipeline_steps = []
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = []
    if "flow_count" not in st.session_state:
        st.session_state.flow_count = 0
    if "turn_count" not in st.session_state:
        st.session_state.turn_count = 0
    if "conv_manager" not in st.session_state:
        st.session_state.conv_manager = ConversationManager()
    if "rate_limiter" not in st.session_state:
        st.session_state.rate_limiter = RateLimiter()
    if "session_blocked" not in st.session_state:
        st.session_state.session_blocked = False
    if "last_profile" not in st.session_state:
        st.session_state.last_profile = None

init_session()

MAX_FLOWS = 3
MAX_TURNS = 4

# ── Helper: render a pipeline step row ───────────────────────────────────
def render_step(step_name, status, detail=""):
    """
    status: 'pending' | 'running' | 'done' | 'fail'
    """
    icons   = {"pending": "·", "running": "▶", "done": "✓", "fail": "✗"}
    colors  = {"pending": "#3a6a3a", "running": "#39ff14", "done": "#39ff14", "fail": "#ff4444"}
    glows   = {
        "pending": "",
        "running": "text-shadow:0 0 8px #39ff14; animation: pulse 1s infinite;",
        "done":    "text-shadow:0 0 6px #39ff1466;",
        "fail":    "text-shadow:0 0 8px #ff444488;",
    }
    icon  = icons[status]
    color = colors[status]
    glow  = glows[status]
    label_color = color if status in ("done","fail","running") else "#3a6a3a"
    detail_text = f' — <span style="color:#5aaa5a;font-size:0.72rem;">{detail}</span>' if detail and status in ("done", "fail") else ""
    return f'<p style="margin:2px 0;font-size:0.78rem;color:{label_color};letter-spacing:0.05em;{glow}">{icon}{step_name}{detail_text}</p>'

# ── Helper: render a song card ────────────────────────────────────────────
CARD_COLORS = ["#39ff14","#00e836","#00c82d","#00b025","#009a1e"]

def render_song_card(song, rank):
    color = CARD_COLORS[(rank - 1) % len(CARD_COLORS)]
    score = song.get("score", 0)
    score_pct = min(int((score/10.75)*100), 100)
    title = song.get("title", "Unknown")
    artist = song.get("artist", "Unknown")
    genre = song.get("genre", "")
    explanation = song.get("explanation", "").replace('"', '&quot;').replace('<', '&lt;').replace('>','&gt;')
    return f"""
    <div style="
        display:flex; border-radius:3px; overflow:hidden; margin-bottom:8px;
        background:#061006; border:1px solid #1a3a1a;
        font-family:'Share Tech Mono',monospace;
        transition:border-color 0.2s;
    ">
        <div style="width:3px;flex-shrink:0;background:{color};box-shadow:0 0 6px {color}88;"></div>
        <div style="flex:1;padding:14px 16px;min-width:0;">
            <div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:6px;">
                <span style="
                    font-size:0.75rem;color:{color};background:{color}18;
                    padding:1px 7px;border-radius:2px;flex-shrink:0;
                    text-shadow:0 0 6px {color}88;letter-spacing:0.1em;
                ">#{rank}</span>
                <span style="font-family:'Playfair Display',Georgia,serif;font-size:1.05rem;color:#c8f5c8;font-weight:500;">
                    {title}
                </span>
                <span style="font-size:0.85rem;color:#72c472;">— {artist}</span>
            </div>
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap;">
                <span style="
                    font-size:0.72rem;letter-spacing:0.06em;padding:2px 8px;border-radius:2px;
                    background:{color}14;color:{color};border:1px solid {color}33;
                ">{genre}</span>
                <div style="flex:1;min-width:80px;display:flex;align-items:center;gap:8px;">
                    <div style="flex:1;height:2px;background:#163016;border-radius:1px;overflow:hidden;">
                        <div style="height:100%;width:{score_pct}%;background:{color};box-shadow:0 0 4px {color}88;border-radius:1px;"></div>
                    </div>
                    <span style="font-size:0.75rem;color:#72c472;flex-shrink:0;">{score:.2f}</span>
                </div>
            </div>
            <p style="font-size:0.82rem;color:#72c472;line-height:1.7;font-style:italic;margin:0;">
                {explanation}
            </p>
        </div>
    </div>
    """

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding-bottom:16px;border-bottom:1px solid #163016;margin-bottom:16px;">
        <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
            <rect x="1" y="1" width="6" height="6" rx="1" fill="#39ff14" opacity="0.9"/>
            <rect x="9" y="1" width="6" height="6" rx="1" fill="#39ff14" opacity="0.4"/>
            <rect x="17" y="1" width="6" height="6" rx="1" fill="#39ff14" opacity="0.2"/>
            <rect x="1" y="9" width="6" height="6" rx="1" fill="#39ff14" opacity="0.3"/>
            <rect x="9" y="9" width="6" height="6" rx="1" fill="#39ff14" opacity="1.0"/>
            <rect x="17" y="9" width="6" height="6" rx="1" fill="#39ff14" opacity="0.5"/>
            <rect x="1" y="17" width="6" height="6" rx="1" fill="#39ff14" opacity="0.15"/>
            <rect x="9" y="17" width="6" height="6" rx="1" fill="#39ff14" opacity="0.6"/>
            <rect x="17" y="17" width="6" height="6" rx="1" fill="#39ff14" opacity="0.9"/>
        </svg>
        <div>
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.95rem;color:#39ff14;text-shadow:0 0 8px #39ff1455;letter-spacing:0.1em;">
                VIBEBUDDY<span style="opacity:0.6;font-size:0.8rem;">.AI</span>
            </div>
            <div style="font-size:0.65rem;color:#5aaa5a;letter-spacing:0.15em;">MOOD &gt; MUSIC</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Session meter
    fc = st.session_state.flow_count
    blocked = fc >= MAX_FLOWS
    flow_color = "#ff4444" if blocked else "#39ff14"
    st.markdown(f"""
    <div style="margin-bottom:16px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="font-size:0.75rem;letter-spacing:0.1em;color:#7acc7a;">SESSION</span>
            <span style="font-size:0.75rem;color:{flow_color};text-shadow:0 0 6px {flow_color}66;
                background:{flow_color}18;padding:1px 7px;border-radius:3px;letter-spacing:0.08em;">
                FLOW {fc}/{MAX_FLOWS}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(fc / MAX_FLOWS)

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    # Pipeline steps
    st.markdown('<div style="font-size:0.7rem;letter-spacing:0.14em;color:#5aaa5a;margin-bottom:8px;">AGENT PIPELINE</div>', unsafe_allow_html=True)

    steps_html = ""
    step_keys = ["ELICIT","VALIDATE","RETRIEVE","CHECK_CANDIDATES","SCORE","GUARDRAILS","EXPLAIN","REFLECT"]

    # Build a lookup from stored steps
    step_lookup = {}
    for s in st.session_state.pipeline_steps:
        step_lookup[s.step_name] = s

    for key in step_keys:
        if key in step_lookup:
            s = step_lookup[key]
            # Detect fail from output summary
            status = "fail" if "FAIL" in s.output_summary.upper() else "done"
            steps_html += render_step(key, status, s.output_summary)
        else:
            steps_html += render_step(key, "pending")

    st.markdown(steps_html, unsafe_allow_html=True)

    if st.session_state.last_profile:
        st.markdown('<div style="font-size:0.7rem;letter-spacing:0.14em;color:#5aaa5a;margin-top:12px;margin-bottom:8px;">EXTRACTED PROFILE</div>', unsafe_allow_html=True)
        p = st.session_state.last_profile
        profile_html = f'<p style="margin:2px 0;font-size:0.72rem;color:#5aaa5a;">mood: <span style="color:#39ff14;">{p["mood"]}</span></p>'
        profile_html += f'<p style="margin:2px 0;font-size:0.72rem;color:#5aaa5a;">genre_hint: <span style="color:#39ff14;">{p["genre_hint"]}</span></p>'
        for feat in ["energy","valence","danceability","acousticness","instrumentalness","liveness","speechiness","tempo_bpm"]:
            profile_html += f'<p style="margin:1px 0;font-size:0.72rem;color:#5aaa5a;">{feat}: <span style="color:#7acc7a;">{p[feat]:.2f}</span></p>'
        st.markdown(profile_html, unsafe_allow_html=True)

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    st.divider()

    # Start Fresh
    if st.button("[ START FRESH ]"):
        st.session_state.messages = []
        st.session_state.pipeline_steps = []
        st.session_state.recommendations = []
        st.session_state.turn_count = 0
        st.session_state.session_blocked = False
        st.session_state.conv_manager = ConversationManager()
        st.session_state.last_profile = None
        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────
tc = st.session_state.turn_count
status_label = "// SESSION_ENDED" if blocked else f"// TURN_{tc}/{MAX_TURNS}"
status_color = "#ff4444" if blocked else "#5aaa5a"
st.markdown(f"""
<div style="
    display:flex;justify-content:space-between;align-items:center;
    padding:10px 0 14px;border-bottom:1px solid #163016;margin-bottom:16px;
">
    <span style="font-size:0.8rem;letter-spacing:0.12em;color:#7acc7a;">CONVERSATION</span>
    <span style="font-size:0.8rem;color:{status_color};letter-spacing:0.08em;">{status_label}</span>
</div>
""", unsafe_allow_html=True)

# ── Render chat history ───────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ── Render recommendations (if any) ──────────────────────────────────────
if st.session_state.recommendations:
    flow_num = st.session_state.flow_count
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin:16px 0 12px;padding-bottom:10px;border-bottom:1px solid #163016;">
        <div style="width:20px;height:1px;background:linear-gradient(90deg,#39ff14,#00cc33);"></div>
        <span style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;color:#72c472;letter-spacing:0.1em;">
            RECOMMENDATIONS · FLOW_{flow_num}
        </span>
        <div style="flex:1;height:1px;background:#163016;"></div>
    </div>
    """, unsafe_allow_html=True)

    cards_html = ""
    for i, song in enumerate(st.session_state.recommendations):
        cards_html += render_song_card(song, i + 1)
    st.markdown(cards_html, unsafe_allow_html=True)

# ── Blocked state ─────────────────────────────────────────────────────────
if blocked:
    st.markdown("""
    <div style="
        padding:18px 20px;margin:12px 0;
        background:rgba(255,68,68,0.07);
        border:1px solid rgba(255,68,68,0.25);
        border-radius:3px;
        font-family:'Share Tech Mono',monospace;
    ">
        <div style="color:#ff4444;margin-bottom:4px;letter-spacing:0.08em;">// SESSION_LIMIT_REACHED</div>
        <div style="color:#72c472;font-size:0.85rem;">All 3 flows consumed. Refresh the webpage to reset.</div>
    </div>
    """, unsafe_allow_html=True)

# ── Chat input ────────────────────────────────────────────────────────────
if not blocked:
    prompt = st.chat_input("enter your vibe…")
else:
    prompt = None

if prompt:
    clean = validate_input(prompt)
    if clean is None:
        st.warning("// INPUT_REJECTED - message too short")
        st.stop()
    rl = st.session_state.rate_limiter
    cm = st.session_state.conv_manager

    # Gate on rate limiter
    if not rl.can_send_message():
        st.session_state.session_blocked = True
        st.rerun()

    # Show user message immediately
    st.session_state.messages.append({"role": "user", "content": clean})
    st.session_state.turn_count += 1
    rl.add_turn()

    with st.chat_message("user"):
        st.write(clean)

    # Get bot response
    cm.add_user_message(clean)
    with st.spinner("// PROCESSING_INPUT"):
        bot_reply = cm.get_response()

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.write(bot_reply)

    # Check if profile extracted → run agent pipeline
    profile_ready = (cm.is_complete())

    if profile_ready:
        st.session_state.pipeline_steps = []
        st.session_state.recommendations = []

        if not rl.can_start_flow():
            st.session_state.session_blocked = True
            st.rerun()

        rl.start_flow()

        with st.spinner("// PIPELINE_RUNNING — scanning catalog…"):
            agent = Agent()
            songs, steps = agent.run(cm.profile, cm.messages)

        st.session_state.pipeline_steps = steps
        st.session_state.recommendations = songs
        st.session_state.flow_count += 1
        st.session_state.last_profile = cm.profile

        # Reset conversation for next flow
        st.session_state.conv_manager = ConversationManager()

        if st.session_state.flow_count >= MAX_FLOWS:
            st.session_state.session_blocked = True

    st.rerun()
