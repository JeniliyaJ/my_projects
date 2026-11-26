import random
import time
from datetime import date
from pathlib import Path

import joblib
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Popcorn Oracle | Hit or Flop?", page_icon="🍿", layout="wide")

INK = "#111111"
YELLOW, PINK, CYAN = "#ffd23f", "#ff5fa2", "#2ec4ff"
HIT, FLOP = "#1fcf6a", "#ff3b3b"

LANGS = {
    "ar": "Arabic", "de": "German", "en": "English", "es": "Spanish", "fa": "Persian",
    "fr": "French", "hi": "Hindi", "id": "Indonesian", "it": "Italian", "ja": "Japanese",
    "ko": "Korean", "ml": "Malayalam", "nl": "Dutch", "pt": "Portuguese", "ru": "Russian",
    "ta": "Tamil", "te": "Telugu", "tr": "Turkish", "vi": "Vietnamese", "zh": "Chinese",
    "others": "Other language",
}
GROUPS = {
    "genres": "Genres",
    "production_companies": "Production companies",
    "production_countries": "Production countries",
    "spoken_languages": "Spoken languages",
    "keywords": "Keywords",
}

ss = st.session_state
ss.setdefault("page", "landing")      # landing -> form -> result
ss.setdefault("inputs", {})
ss.setdefault("hit_p", None)
ss.setdefault("revealed", False)


def goto(page):
    ss.page = page


# ------------------------------------------------------------------ styling
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&family=DM+Sans:wght@400;500;700&display=swap');

.stApp { background-color:#fff6e0; background-image:radial-gradient(rgba(17,17,17,.13) 1.6px, transparent 1.6px); background-size:22px 22px; font-family:'DM Sans',sans-serif; }
header[data-testid="stHeader"] { background:transparent; }
#MainMenu, footer { visibility:hidden; }
.block-container { padding-top:2.2rem; max-width:1180px; }
h1,h2,h3,.bangers { font-family:'Bangers',cursive !important; letter-spacing:2px; color:#111 !important; font-weight:400 !important; }
.stApp label p, .stApp [data-testid="stWidgetLabel"] p { color:#111 !important; font-weight:700; }

.hero-title { font-family:'Bangers',cursive; font-size:clamp(54px,9vw,104px); line-height:.95; text-align:center; color:#ffd23f; -webkit-text-stroke:3px #111; text-shadow:6px 6px 0 #111; letter-spacing:3px; margin:0; }
.hero-title span { color:#ff5fa2; }
.hero-sub { text-align:center; font-size:20px; font-weight:500; margin:16px auto 8px; max-width:640px; color:#111; }
.chips { display:flex; gap:12px; flex-wrap:wrap; justify-content:center; margin:26px 0 8px; }
.chip { background:#fff; border:3px solid #111; border-radius:999px; padding:6px 16px; font-weight:700; box-shadow:3px 3px 0 #111; color:#111; }
.chip:nth-child(odd) { transform:rotate(-2deg); }
.chip:nth-child(even) { transform:rotate(2deg); }

.stepper { display:flex; gap:10px; justify-content:center; margin-bottom:6px; font-family:'Bangers',cursive; letter-spacing:2px; font-size:20px; }
.step { padding:2px 16px; border:3px solid #111; border-radius:999px; background:#fff; color:#111; }
.step.on { background:#ffd23f; box-shadow:3px 3px 0 #111; }
.step.done { background:#c8f7dc; }

.bubble { position:relative; background:#fff; border:3px solid #111; border-radius:18px; padding:12px 18px; font-weight:700; text-align:center; box-shadow:5px 5px 0 #111; margin:0 auto 22px; max-width:330px; color:#111; animation:pop .5s ease-out both; }
.bubble:after { content:""; position:absolute; left:50%; bottom:-14px; width:20px; height:20px; background:#fff; border-right:3px solid #111; border-bottom:3px solid #111; transform:translateX(-50%) rotate(45deg); }

div[data-testid="stForm"] { background:#fff; border:3px solid #111; border-radius:18px; box-shadow:6px 6px 0 #111; padding:20px; }
div[data-testid="stPlotlyChart"] { background:#fff; border:3px solid #111; border-radius:18px; box-shadow:6px 6px 0 #111; padding:8px; }
div[data-testid="stExpander"] { background:#fff; border:3px solid #111 !important; border-radius:14px; box-shadow:4px 4px 0 #111; }

.stButton > button, div[data-testid="stFormSubmitButton"] > button { width:100%; background:#ffd23f; color:#111; border:3px solid #111; border-radius:14px; box-shadow:5px 5px 0 #111; padding:6px 10px; transition:transform .08s, box-shadow .08s; }
.stButton > button p, div[data-testid="stFormSubmitButton"] > button p { font-family:'Bangers',cursive; font-size:26px; letter-spacing:2px; color:#111; }
.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover { transform:translate(2px,2px); box-shadow:3px 3px 0 #111; background:#ffe27a; border-color:#111; color:#111; }
.stButton > button:active, div[data-testid="stFormSubmitButton"] > button:active { transform:translate(5px,5px); box-shadow:0 0 0 #111; }
button[kind="primary"], button[kind="primaryFormSubmit"], button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] { background:#ff5fa2 !important; color:#111 !important; }
button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover, button[data-testid="stBaseButton-primary"]:hover, button[data-testid="stBaseButton-primaryFormSubmit"]:hover { background:#ff86b9 !important; }

.ticket { border:4px solid #111; border-radius:22px; padding:22px 26px; box-shadow:8px 8px 0 #111; text-align:center; color:#111; }
.ticket.hit { background:#c8f7dc; animation:pop .7s cubic-bezier(.2,1.4,.4,1) both; }
.ticket.flop { background:#ffd6d6; animation:shake .7s ease-in-out both; }
.ticket .tag { font-weight:700; letter-spacing:4px; font-size:13px; }
.ticket .verdict { font-family:'Bangers',cursive; font-size:clamp(50px,7vw,90px); line-height:1; margin:6px 0; -webkit-text-stroke:2px #111; text-shadow:4px 4px 0 #111; letter-spacing:2px; }
.ticket.hit .verdict { color:#1fcf6a; }
.ticket.flop .verdict { color:#ff3b3b; }
.ticket .sub { font-weight:500; }
.nums { display:flex; gap:16px; margin-top:16px; }
.num { flex:1; background:#fff; border:3px solid #111; border-radius:14px; padding:8px 10px; box-shadow:4px 4px 0 #111; }
.num small { font-weight:700; letter-spacing:3px; }
.num b { display:block; font-family:'Bangers',cursive; font-size:42px; letter-spacing:1px; line-height:1.05; -webkit-text-stroke:1px #111; }
.num.h b { color:#1fcf6a; }
.num.f b { color:#ff3b3b; }

.drum { text-align:center; padding:6px 0 0; color:#111; }
.drum h2 { font-size:clamp(34px,6vw,64px); margin:0; }
.dots:after { content:""; animation:dots 1.2s steps(4,end) infinite; }
.prog { height:22px; border:3px solid #111; border-radius:999px; background:#fff; max-width:420px; margin:14px auto 0; overflow:hidden; }
.prog i { display:block; height:100%; background:repeating-linear-gradient(45deg,#ff5fa2,#ff5fa2 12px,#ffd23f 12px,#ffd23f 24px); animation:fillbar 2s linear both; }

.mascot svg { width:100%; max-width:320px; height:auto; overflow:visible; display:block; margin:0 auto; }
.mascot .buddy { transform-box:fill-box; transform-origin:50% 100%; }
.mascot .shadow, .mascot .spark, .mascot .eyes { transform-box:fill-box; transform-origin:center; }
.m-idle .buddy { animation:bob 2.6s ease-in-out infinite; }
.m-idle .eyes { animation:blink 4s infinite; }
.m-drum .buddy { animation:tremble .18s linear infinite !important; }
.m-hit .buddy { animation:jump .9s ease-in-out infinite; }
.m-hit .shadow { animation:shadowjump .9s ease-in-out infinite; }
.m-hit .armL { transform-box:view-box; transform-origin:64px 176px; animation:wave-l .45s ease-in-out infinite; }
.m-hit .armR { transform-box:view-box; transform-origin:176px 176px; animation:wave-r .45s ease-in-out infinite; }
.m-hit .spark { animation:twinkle 1s ease-in-out infinite; }
.m-flop .buddy { animation:slump .8s ease-out forwards, sway 3.2s ease-in-out .8s infinite; }
.m-flop .tear { animation:tear 1.3s ease-in infinite; }
.m-flop .drop { animation:drop .9s linear infinite; }

.confetti { position:fixed; inset:0; pointer-events:none; z-index:9999; overflow:hidden; }
.confetti i { position:absolute; top:-6vh; border:2px solid #111; animation-name:fall; animation-timing-function:linear; animation-fill-mode:both; animation-iteration-count:1; }
.rainfx { position:fixed; inset:0; pointer-events:none; z-index:9998; overflow:hidden; animation:fadeout 1.5s 9s forwards; }
.rainfx .tint { position:absolute; inset:0; background:rgba(40,60,110,.22); animation:tintin 1.2s ease-out both; }
.rainfx .flash { position:absolute; inset:0; background:#fff; opacity:0; animation:flash 1.6s ease-out .3s 1 both; }
.rainfx i { position:absolute; top:-8vh; width:2px; background:linear-gradient(transparent,#2ec4ff); animation-name:rain; animation-timing-function:linear; animation-iteration-count:infinite; }

@keyframes bob { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }
@keyframes tremble { 0%{transform:translate(-2px,0) rotate(-1deg)} 50%{transform:translate(2px,-2px) rotate(1deg)} 100%{transform:translate(-2px,0) rotate(-1deg)} }
@keyframes jump { 0%,100%{transform:translateY(0) scale(1.04,.94)} 45%{transform:translateY(-42px) scale(.96,1.05)} 70%{transform:translateY(0) scale(1,1)} }
@keyframes shadowjump { 0%,100%{transform:scale(1)} 45%{transform:scale(.6)} }
@keyframes slump { 0%{transform:translateY(0) rotate(0)} 100%{transform:translateY(14px) rotate(-5deg)} }
@keyframes sway { 0%,100%{transform:translateY(14px) rotate(-5deg)} 50%{transform:translateY(14px) rotate(-2deg)} }
@keyframes blink { 0%,92%,100%{transform:scaleY(1)} 96%{transform:scaleY(.1)} }
@keyframes wave-l { 0%,100%{transform:rotate(8deg)} 50%{transform:rotate(-22deg)} }
@keyframes wave-r { 0%,100%{transform:rotate(-8deg)} 50%{transform:rotate(22deg)} }
@keyframes tear { 0%{transform:translateY(0);opacity:0} 15%{opacity:1} 100%{transform:translateY(46px);opacity:0} }
@keyframes drop { 0%{transform:translateY(0);opacity:0} 10%{opacity:.9} 100%{transform:translateY(250px);opacity:0} }
@keyframes twinkle { 0%,100%{transform:scale(.35);opacity:.25} 50%{transform:scale(1.15);opacity:1} }
@keyframes fall { 0%{transform:translateY(0) rotate(0);opacity:1} 100%{transform:translateY(118vh) rotate(720deg);opacity:1} }
@keyframes rain { 0%{transform:translateY(0)} 100%{transform:translateY(112vh)} }
@keyframes fadeout { to{opacity:0} }
@keyframes tintin { from{opacity:0} to{opacity:1} }
@keyframes flash { 0%,100%{opacity:0} 6%,14%{opacity:.75} 10%{opacity:.1} 20%{opacity:0} }
@keyframes pop { 0%{transform:scale(.2) rotate(-8deg);opacity:0} 60%{transform:scale(1.1) rotate(3deg);opacity:1} 100%{transform:scale(1) rotate(0);opacity:1} }
@keyframes shake { 0%{transform:translateX(0)} 15%{transform:translateX(-14px) rotate(-1.5deg)} 30%{transform:translateX(12px) rotate(1.2deg)} 45%{transform:translateX(-9px)} 60%{transform:translateX(7px)} 75%{transform:translateX(-4px)} 100%{transform:translateX(0)} }
@keyframes dots { 0%{content:""} 25%{content:"."} 50%{content:".."} 75%,100%{content:"..."} }
@keyframes fillbar { from{width:0} to{width:100%} }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ html helpers
def bubble(text):
    return f'<div class="bubble">{text}</div>'


def stepper(active):
    order = ["form", "result"]
    labels = {"form": "1 · DETAILS", "result": "2 · VERDICT"}
    parts = []
    for p in order:
        cls = "on" if p == active else ("done" if order.index(p) < order.index(active) else "")
        parts.append(f'<div class="step {cls}">{labels[p]}</div>')
    st.markdown('<div class="stepper">' + "".join(parts) + "</div>", unsafe_allow_html=True)


def mascot(mood="idle", extra=""):
    """Popi the popcorn bucket. mood: idle | hit | flop"""
    y_top, y_bot = 112, 272

    def edge(y):
        t = (y - y_top) / (y_bot - y_top)
        return 52 + 18 * t, 188 - 18 * t

    lt, rt = edge(y_top)
    lb, rb = edge(y_bot)
    bucket_pts = f"{lt:.1f},{y_top} {rt:.1f},{y_top} {rb:.1f},{y_bot} {lb:.1f},{y_bot}"
    stripes = ""
    for k in (0, 2, 4):
        x1t, x2t = lt + (rt - lt) * k / 5, lt + (rt - lt) * (k + 1) / 5
        x1b, x2b = lb + (rb - lb) * k / 5, lb + (rb - lb) * (k + 1) / 5
        stripes += f'<polygon points="{x1t:.1f},{y_top} {x2t:.1f},{y_top} {x2b:.1f},{y_bot} {x1b:.1f},{y_bot}" fill="#ff3b3b"/>'

    clumps = [(62, 86, 26), (100, 64, 32), (146, 70, 30), (180, 96, 24), (46, 104, 20), (122, 96, 28)]
    popcorn = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#111" stroke="#111" stroke-width="7"/>' for x, y, r in clumps)
    popcorn += "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff3c4"/>' for x, y, r in clumps)
    popcorn += ('<circle cx="92" cy="56" r="5" fill="#ffd23f"/><circle cx="150" cy="58" r="4" fill="#ffd23f"/>'
                '<circle cx="64" cy="92" r="4" fill="#ffd23f"/><circle cx="182" cy="100" r="4" fill="#ffd23f"/>'
                '<circle cx="122" cy="84" r="5" fill="#ffd23f"/>')

    bucket = (f'<polygon points="{bucket_pts}" fill="#fff"/>' + stripes
              + f'<polygon points="{bucket_pts}" fill="none" stroke="#111" stroke-width="5" stroke-linejoin="round"/>'
              + '<rect x="44" y="104" width="152" height="16" rx="8" fill="#fff" stroke="#111" stroke-width="5"/>'
              + '<ellipse cx="120" cy="198" rx="46" ry="38" fill="#fff" stroke="#111" stroke-width="4"/>')

    feet = ('<ellipse cx="95" cy="278" rx="19" ry="9" fill="#111"/><ellipse cx="145" cy="278" rx="19" ry="9" fill="#111"/>')

    def arm(d, hx, hy, cls):
        return (f'<g class="{cls}"><path d="{d}" fill="none" stroke="#111" stroke-width="7" stroke-linecap="round"/>'
                f'<circle cx="{hx}" cy="{hy}" r="10" fill="#fff" stroke="#111" stroke-width="4"/></g>')

    back_fx = ""
    if mood == "hit":
        arms = (arm("M64 176 Q30 150 38 108", 38, 102, "armL") + arm("M176 176 Q210 150 202 108", 202, 102, "armR"))
        eyes = ('<path d="M95 194 Q105 177 115 194" fill="none" stroke="#111" stroke-width="5" stroke-linecap="round"/>'
                '<path d="M125 194 Q135 177 145 194" fill="none" stroke="#111" stroke-width="5" stroke-linecap="round"/>')
        mouth = ('<path d="M102 205 Q120 238 138 205 Z" fill="#7a1f1f" stroke="#111" stroke-width="4" stroke-linejoin="round"/>'
                 '<ellipse cx="120" cy="215" rx="8" ry="4" fill="#ff5fa2"/>')
        cheeks = '<circle cx="90" cy="208" r="8" fill="#ff9ec7"/><circle cx="150" cy="208" r="8" fill="#ff9ec7"/>'
        face = eyes + mouth + cheeks
        star = "0,-11 3,-3 11,0 3,3 0,11 -3,3 -11,0 -3,-3"
        for (sx, sy, col, dl) in [(26, 96, YELLOW, 0), (214, 90, PINK, .3), (16, 200, CYAN, .6), (226, 196, YELLOW, .15), (120, 24, PINK, .45), (58, 40, CYAN, .75), (186, 44, YELLOW, .9)]:
            back_fx += f'<g transform="translate({sx},{sy})"><polygon class="spark" points="{star}" fill="{col}" stroke="#111" stroke-width="2.5" style="animation-delay:{dl}s"/></g>'
    elif mood == "flop":
        arms = (arm("M64 176 Q40 214 56 252", 56, 256, "armL") + arm("M176 176 Q200 214 184 252", 184, 256, "armR"))
        brows = ('<path d="M94 180 L113 171" stroke="#111" stroke-width="4.5" stroke-linecap="round"/>'
                 '<path d="M146 180 L127 171" stroke="#111" stroke-width="4.5" stroke-linecap="round"/>')
        eyes = '<circle cx="105" cy="193" r="5.5" fill="#111"/><circle cx="135" cy="193" r="5.5" fill="#111"/>'
        mouth = '<path d="M105 219 Q120 203 135 219" fill="none" stroke="#111" stroke-width="4.5" stroke-linecap="round"/>'
        tear_path = "M0 0 C-4 7 -5 11 0 12 C5 11 4 7 0 0Z"
        tears = (f'<g transform="translate(101,200)"><path class="tear" d="{tear_path}" fill="#2ec4ff" stroke="#111" stroke-width="1.5"/></g>'
                 f'<g transform="translate(139,200)"><path class="tear" d="{tear_path}" fill="#2ec4ff" stroke="#111" stroke-width="1.5" style="animation-delay:.6s"/></g>')
        face = brows + eyes + mouth + tears
        cloud = [(80, 44, 20), (108, 32, 25), (140, 36, 24), (166, 46, 17), (120, 50, 22)]
        back_fx = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#111" stroke="#111" stroke-width="7"/>' for x, y, r in cloud)
        back_fx += "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#8d99ae"/>' for x, y, r in cloud)
        for i, x in enumerate([84, 100, 116, 132, 148, 164]):
            back_fx += (f'<line class="drop" x1="{x}" y1="74" x2="{x}" y2="88" stroke="#2ec4ff" stroke-width="3" '
                        f'stroke-linecap="round" style="animation-delay:{(i * 0.17) % 0.9:.2f}s"/>')
    else:
        arms = (arm("M64 176 Q34 190 30 222", 30, 226, "armL") + arm("M176 176 Q206 190 210 222", 210, 226, "armR"))
        eyes = '<g class="eyes"><circle cx="105" cy="190" r="5.5" fill="#111"/><circle cx="135" cy="190" r="5.5" fill="#111"/></g>'
        mouth = '<path d="M106 207 Q120 219 134 207" fill="none" stroke="#111" stroke-width="4.5" stroke-linecap="round"/>'
        cheeks = '<circle cx="92" cy="205" r="7" fill="#ff9ec7" opacity=".8"/><circle cx="148" cy="205" r="7" fill="#ff9ec7" opacity=".8"/>'
        face = eyes + mouth + cheeks

    svg = ('<svg viewBox="0 0 240 360" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Popi the popcorn mascot">'
           + back_fx
           + '<g transform="translate(0,48)">'
           + '<ellipse class="shadow" cx="120" cy="296" rx="64" ry="8" fill="rgba(17,17,17,.22)"/>'
           + '<g class="buddy">' + arms + feet + popcorn + bucket + face + '</g>'
           + '</g></svg>')
    return f'<div class="mascot m-{mood} {extra}">{svg}</div>'


def confetti_html(n=80, seed=7):
    rnd = random.Random(seed)
    colors = [YELLOW, PINK, CYAN, HIT, "#ff9f1c", "#ffffff"]
    bits = []
    for _ in range(n):
        w = rnd.randint(8, 14)
        bits.append(
            f'<i style="left:{rnd.uniform(0, 100):.1f}vw;width:{w}px;height:{int(w * 1.6)}px;background:{rnd.choice(colors)};'
            f'animation-delay:{rnd.uniform(0, 2.5):.2f}s;animation-duration:{rnd.uniform(3, 6):.2f}s;'
            f'border-radius:{rnd.choice(["2px", "50%"])}"></i>')
    return '<div class="confetti">' + "".join(bits) + "</div>"


def rain_html(n=90, seed=3):
    rnd = random.Random(seed)
    bits = ['<div class="tint"></div><div class="flash"></div>']
    for _ in range(n):
        bits.append(
            f'<i style="left:{rnd.uniform(0, 100):.1f}vw;height:{rnd.randint(14, 30)}px;'
            f'animation-delay:{rnd.uniform(0, 1.2):.2f}s;animation-duration:{rnd.uniform(.55, 1.0):.2f}s"></i>')
    return '<div class="rainfx">' + "".join(bits) + "</div>"


# ------------------------------------------------------------------ model
@st.cache_resource
def load_artifact():
    return joblib.load(Path(__file__).parent / "movie_success_sys.pkl")


try:
    art = load_artifact()
except FileNotFoundError:
    st.error("`movie_success_sys.pkl` not found. Put the .pkl files saved by your notebook in the same folder as app.py.")
    st.stop()

model, scaler = art["model"], art["scaler"]
importance = art["feature_important"]            # ordered exactly like the columns the scaler/model were trained on
FEATURES = list(importance.keys())
HIT_IDX = list(art["label_classes"]).index("hit")


def options_for(group):
    pre = group + "_"
    return sorted(f[len(pre):] for f in FEATURES if f.startswith(pre) and not f.endswith("_unkown"))


def make_vals(i):
    rel = i["release"]
    return dict(vote_average=i["vote_average"], release_year=rel.year, release_month=rel.month,
                release_day=rel.day, language=i["language"], **{g: i.get(g, []) for g in GROUPS})


def build_row(vals):
    row = dict.fromkeys(FEATURES, 0.0)
    for k in ("vote_average", "release_year", "release_month", "release_day"):
        if k in row:
            row[k] = float(vals[k])
    if "status_Released" in row:
        row["status_Released"] = 1.0
    lang_key = f"original_language_{vals['language']}"
    if lang_key in row:
        row[lang_key] = 1.0
    for g in GROUPS:
        picked = vals[g]
        for v in picked:
            if f"{g}_{v}" in row:
                row[f"{g}_{v}"] = 1.0
        if not picked and f"{g}_unkown" in row:
            row[f"{g}_unkown"] = 1.0
    return row


def hit_probability(row):
    X = pd.DataFrame([row])[FEATURES]
    return float(model.predict_proba(scaler.transform(X))[0][HIT_IDX])


def style(fig, title, h=320):
    fig.update_layout(
        title=dict(text=title, font=dict(family="Bangers", size=24, color=INK)),
        height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color=INK), margin=dict(l=14, r=14, t=56, b=14))
    return fig


# ------------------------------------------------------------------ pages
def page_landing():
    st.markdown('<h1 class="hero-title">POPCORN <span>ORACLE</span></h1>', unsafe_allow_html=True)
    st.markdown('<p class="hero-sub">Will your movie be a <b>HIT</b> or a <b>FLOP</b>? Tell Popi about it and he will '
                'predict its fate at the box office.</p>', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown(bubble("Hi, I'm Popi! Ready to predict your movie's fate? 🍿") + mascot("idle"), unsafe_allow_html=True)
        st.button("▶ START", type="primary", on_click=goto, args=("form",))
    st.markdown('<div class="chips"><div class="chip">🎞️ Trained on 18,792 TMDB movies</div>'
                '<div class="chip">🤖 XGBoost classifier</div><div class="chip">📊 Hit &amp; flop probabilities</div></div>',
                unsafe_allow_html=True)


def page_form():
    stepper("form")
    st.markdown('<h2 style="text-align:center;margin:0 0 14px;font-size:44px">TELL POPI ABOUT YOUR MOVIE</h2>', unsafe_allow_html=True)
    left, right = st.columns([1, 1.7], gap="large")
    with left:
        st.markdown(bubble("The more you tell me, the better I can guess! 🍿") + mascot("idle"), unsafe_allow_html=True)
        st.button("← BACK", on_click=goto, args=("landing",))
    with right:
        inp = ss.inputs
        with st.form("movie_form"):
            vote_average = st.slider("Audience rating (vote average)", 0.0, 10.0, float(inp.get("vote_average", 6.5)), 0.1,
                                     help="Use 0 if the movie is not released yet and has no ratings. This is the model's most important input.")
            release = st.date_input("Release date", value=inp.get("release", date(2024, 6, 14)),
                                    min_value=date(1900, 1, 1), max_value=date(2035, 12, 31))
            lang_codes = list(LANGS)
            language = st.selectbox("Original language", lang_codes,
                                    index=lang_codes.index(inp.get("language", "en")), format_func=lambda c: LANGS[c])
            picks = {}
            for g, label in GROUPS.items():
                opts = options_for(g)
                if opts:
                    picks[g] = st.multiselect(label, opts, default=[v for v in inp.get(g, []) if v in opts])
                else:
                    picks[g] = []
            submitted = st.form_submit_button("🎬 PREDICT!", type="primary")
        if submitted:
            ss.inputs = dict(vote_average=vote_average, release=release, language=language, **picks)
            ss.hit_p = hit_probability(build_row(make_vals(ss.inputs)))
            ss.revealed = False
            ss.page = "result"
            st.rerun()


def page_result():
    if ss.hit_p is None:
        ss.page = "form"
        st.rerun()
    stepper("result")

    if not ss.revealed:
        st.markdown('<div class="drum"><h2>AND THE VERDICT IS<span class="dots"></span></h2>'
                    '<div class="prog"><i></i></div></div>', unsafe_allow_html=True)
        _, mid, _ = st.columns([1, 1, 1])
        with mid:
            st.markdown(mascot("idle", "m-drum"), unsafe_allow_html=True)
        time.sleep(2.1)
        ss.revealed = True
        st.rerun()

    hit_p = ss.hit_p
    flop_p = 1 - hit_p
    is_hit = hit_p >= 0.5
    inp = ss.inputs

    if is_hit:
        st.markdown(confetti_html(), unsafe_allow_html=True)
        st.balloons()
        title, sub = ("BLOCKBUSTER!", "Studios are going to fight over this one.") if hit_p >= 0.75 else ("HIT!", "Looks like it will make its money back.")
        speech = "YAAAS! Popcorn's on me! 🎉"
    else:
        st.markdown(rain_html(), unsafe_allow_html=True)
        title, sub = ("TOTAL FLOP", "Rough day at the box office.") if hit_p < 0.25 else ("FLOP", "Probably won't recover its budget.")
        speech = "Oh noooo... the box office is crying 😭"

    left, right = st.columns([1, 1.4], gap="large")
    with left:
        st.markdown(bubble(speech) + mascot("hit" if is_hit else "flop"), unsafe_allow_html=True)
    with right:
        st.markdown(
            f'<div class="ticket {"hit" if is_hit else "flop"}"><div class="tag">🎟️ ADMIT ONE · THE VERDICT</div>'
            f'<div class="verdict">{title}</div><div class="sub">{sub}</div>'
            f'<div class="nums"><div class="num h"><small>HIT</small><b>{hit_p:.1%}</b></div>'
            f'<div class="num f"><small>FLOP</small><b>{flop_p:.1%}</b></div></div></div>', unsafe_allow_html=True)

    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        donut = go.Figure(go.Pie(labels=["Hit", "Flop"], values=[hit_p, flop_p], hole=0.6, sort=False, textinfo="none",
                                 marker=dict(colors=[HIT, FLOP], line=dict(color=INK, width=3))))
        donut.add_annotation(text=f"<b>{hit_p:.0%}</b>", showarrow=False, font=dict(family="Bangers", size=34, color=INK))
        st.plotly_chart(style(donut, "PROBABILITY SPLIT"))
    with c2:
        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=hit_p * 100, number=dict(suffix="%", font=dict(family="Bangers", color=INK)),
            gauge=dict(axis=dict(range=[0, 100], tickcolor=INK), bar=dict(color=PINK, thickness=0.4), bordercolor=INK, borderwidth=3,
                       steps=[dict(range=[0, 50], color="#ffd6d6"), dict(range=[50, 100], color="#c8f7dc")],
                       threshold=dict(line=dict(color=INK, width=4), value=50))))
        st.plotly_chart(style(gauge, "HIT METER"))
    with c3:
        bars = go.Figure(go.Bar(x=["HIT", "FLOP"], y=[hit_p * 100, flop_p * 100],
                                marker=dict(color=[HIT, FLOP], line=dict(color=INK, width=3)),
                                text=[f"{hit_p:.1%}", f"{flop_p:.1%}"], textposition="outside",
                                textfont=dict(family="Bangers", size=20, color=INK)))
        bars.update_layout(yaxis=dict(range=[0, 120], gridcolor="rgba(17,17,17,.12)", ticksuffix="%"))
        st.plotly_chart(style(bars, "HIT VS FLOP"))

    row = build_row(make_vals(inp))
    xs = [i / 2 for i in range(0, 21)]
    ys = [hit_probability({**row, "vote_average": r}) * 100 for r in xs]
    sweep = go.Figure(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=INK, width=4),
                                 marker=dict(color=YELLOW, size=9, line=dict(color=INK, width=2)),
                                 fill="tozeroy", fillcolor="rgba(255,210,63,.35)", name="Hit %"))
    if inp.get("vote_average", 0) > 0:
        sweep.add_trace(go.Scatter(x=[inp["vote_average"]], y=[ss.hit_p * 100], mode="markers", name="Your movie",
                                   marker=dict(color=PINK, size=18, line=dict(color=INK, width=3))))
    sweep.add_hline(y=50, line_dash="dash", line_color=INK)
    sweep.update_layout(xaxis_title="Audience rating", yaxis=dict(title="Hit probability %", range=[0, 100], gridcolor="rgba(17,17,17,.12)"),
                        showlegend=False)
    st.plotly_chart(style(sweep, "WHAT IF THE AUDIENCE RATING CHANGES?", 340))

    with st.expander("🔍 What does the model care about most?"):
        top = pd.Series(importance).nlargest(15).sort_values()
        fi = go.Figure(go.Bar(x=top.values, y=[n.replace("_", " ") for n in top.index], orientation="h",
                              marker=dict(color=PINK, line=dict(color=INK, width=2))))
        st.plotly_chart(style(fi, "TOP 15 FEATURES", 480))

    b1, b2 = st.columns(2, gap="large")
    with b1:
        st.button("↩ TRY ANOTHER MOVIE", type="primary", on_click=goto, args=("form",))
    with b2:
        st.button("🏠 HOME", on_click=goto, args=("landing",))
    st.caption("“Hit” = revenue > budget in the TMDB dataset. This is a statistical estimate, not a guarantee.")


{"landing": page_landing, "form": page_form, "result": page_result}[ss.page]()
