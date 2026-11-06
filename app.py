import html
import io
import random
import time
from datetime import time as dtime

import numpy as np
import pandas as pd
import plotly.express as px
import qrcode
import streamlit as st

st.set_page_config(page_title="Smart Housing & Logistics", page_icon="🕋", layout="wide")
s = st.session_state
s.setdefault("lang", "ar")
s.setdefault("dark", False)

# ---------- THEME: edit colors here only ----------
THEME = {
    "light": dict(bg="#F6F1E7", card="#FFFFFF", ink="#10343A", mute="#5E7478",
                  pri="#0E7C86", pri2="#0A5A62", sand="#E8D9B5", line="#E3D8BF"),
    "dark": dict(bg="#0B1B1E", card="#12292D", ink="#EAF3F2", mute="#9DB5B8",
                 pri="#18A4B0", pri2="#0E7C86", sand="#E8D9B5", line="#21424A"),
}
GOLD = "#C9A227"
C = THEME["dark" if s.dark else "light"]

# ---------- TEXT ----------
L = {
    "ar": dict(
        title="منصة التسكين والتفويج الذكي", sub="نموذج أولي تفاعلي · بيانات تجريبية فقط", hotel="الفندق",
        hotels=["فندق أنوار المدينة", "فندق أبراج الساعة", "فندق دار الضيافة"],
        tabs=["📊 لوحة المدير", "⚡ التسكين الذكي", "🚌 الحافلات", "📱 حضور QR", "💬 واتساب"],
        k=["إجمالي المعتمرين", "الغرف المشغولة", "حالات خاصة بالأدوار الأرضية", "نسبة الحضور"],
        heat="خريطة حرارية لإشغال الغرف", fl="الدور", rm="الغرفة",
        up="ارفع كشف المعتمرين (Excel/CSV) ببيانات تجريبية فقط", smp="تحميل نموذج Excel",
        run="تشغيل التسكين الذكي", spin="جاري تطبيق قواعد التسكين...", res="نتيجة التسكين",
        dl="تحميل كشف الغرف (Excel)", hint="اضغط تشغيل التسكين لعرض النتيجة.",
        bad="الملف ناقص الأعمدة المطلوبة (name, family, gender, age, health)، تم استخدام البيانات التجريبية.",
        cols=dict(name="الاسم", family="العائلة", gender="النوع", age="العمر", floor="الدور",
                  room="الغرفة", bus="الحافلة", note="ملاحظة"),
        notes=("أولوية: دور أرضي", "العائلة معًا", "فرادى منظم", "بدون غرفة"),
        bus="حافلة", boarded="ركبوا", st=("انتظار", "جاري الركوب", "مكتملة"), map="مواقع الحافلات (محاكاة)",
        pick="اختر المعتمر", scan="محاكاة مسح الكارت", scan10="مسح 10 معتمرين", att="تم تسجيل الحضور",
        log="آخر عمليات المسح", wa_bus="الحافلة المتأثرة", wa_time="الموعد الجديد", wa_tpl="نص الرسالة",
        wa_btn="إرسال الإشعار", wa_msg="مرحبًا {name}، تم تغيير موعد {bus} إلى الساعة {time}. نرجو التواجد في نقطة التجمع قبلها بربع ساعة.",
        wa_q="رسالة في الطابور (محاكاة، بدون ربط فعلي بواتساب)",
        foot="نموذج أولي تجريبي: كل البيانات والخرائط والإشعارات محاكاة. يسعدنا سماع تحدياتكم التشغيلية.",
        gm=dict(M="ذكر", F="أنثى")),
    "en": dict(
        title="Smart Housing & Logistics Platform", sub="Interactive prototype · demo data only", hotel="Hotel",
        hotels=["Anwar Al-Madinah Hotel", "Abraj Clock Hotel", "Dar Al-Diyafa Hotel"],
        tabs=["📊 Manager", "⚡ Smart housing", "🚌 Buses", "📱 QR check-in", "💬 WhatsApp"],
        k=["Total pilgrims", "Rooms in use", "Special cases on lower floors", "Check-in rate"],
        heat="Room occupancy heatmap", fl="Floor", rm="Room",
        up="Upload pilgrim list (Excel/CSV), demo data only", smp="Download sample Excel",
        run="Run smart housing", spin="Applying housing rules...", res="Housing result",
        dl="Download room list (Excel)", hint="Press Run to see the result.",
        bad="The file is missing required columns (name, family, gender, age, health). Demo data is used.",
        cols=dict(name="Name", family="Family", gender="Gender", age="Age", floor="Floor",
                  room="Room", bus="Bus", note="Note"),
        notes=("Priority: ground floor", "Family together", "Single, grouped", "No room"),
        bus="Bus", boarded="boarded", st=("Waiting", "Boarding", "Complete"), map="Bus locations (simulated)",
        pick="Select pilgrim", scan="Simulate card scan", scan10="Scan 10 pilgrims", att="Checked in",
        log="Latest scans", wa_bus="Affected bus", wa_time="New time", wa_tpl="Message text",
        wa_btn="Send notification", wa_msg="Hello {name}, {bus} now departs at {time}. Please be at the meeting point 15 minutes earlier.",
        wa_q="messages queued (simulation, no real WhatsApp connection)",
        foot="Demo prototype: all data, maps and notifications are simulated. We would love to hear your operational challenges.",
        gm=dict(M="Male", F="Female")),
}
T = L[s.lang]
AR = s.lang == "ar"
NM = "name_ar" if AR else "name_en"

# ---------- STYLE ----------
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
:root{{--bg:{C['bg']};--card:{C['card']};--ink:{C['ink']};--mute:{C['mute']};--pri:{C['pri']};--pri2:{C['pri2']};--sand:{C['sand']};--line:{C['line']};--gold:{GOLD}}}
html,body,.stApp{{font-family:'Tajawal',sans-serif}}
.stApp{{background:var(--bg);color:var(--ink);direction:{'rtl' if AR else 'ltr'}}}
.stApp h1,.stApp h2,.stApp h3,.stApp p,.stApp label,.stApp li,.stApp span{{color:var(--ink)}}
#MainMenu,footer{{visibility:hidden}}
.stButton>button,.stDownloadButton>button{{background:linear-gradient(180deg,var(--pri),var(--pri2));border:0;border-radius:12px;
 padding:.6rem 1.2rem;font-weight:700;width:100%;box-shadow:0 6px 0 rgba(0,0,0,.28),0 12px 22px rgba(14,124,134,.30);transition:.12s}}
.stButton>button p,.stDownloadButton>button p{{color:#fff!important}}
.stButton>button:hover,.stDownloadButton>button:hover{{filter:brightness(1.1)}}
.stButton>button:active,.stDownloadButton>button:active{{transform:translateY(4px);box-shadow:0 2px 0 rgba(0,0,0,.28)}}
.card{{background:var(--card);border:1px solid var(--line);border-top:3px solid var(--gold);border-radius:16px;padding:16px 18px;
 box-shadow:0 10px 24px rgba(0,0,0,.10),inset 0 1px 0 rgba(255,255,255,.35)}}
.card small{{color:var(--mute);font-size:14px}} .card b{{display:block;font-size:32px;color:var(--pri);line-height:1.3}}
.bar{{height:12px;background:var(--line);border-radius:8px;overflow:hidden;box-shadow:inset 0 2px 3px rgba(0,0,0,.2)}}
.bar i{{display:block;height:100%;background:linear-gradient(90deg,var(--pri2),var(--pri),var(--sand))}}
.row{{display:grid;grid-template-columns:110px 1fr 120px 90px;gap:12px;align-items:center;margin:12px 0;color:var(--ink)}}
.phone{{max-width:360px;margin:auto;background:#0B141A;border-radius:28px;padding:16px;border:6px solid #222;box-shadow:0 18px 40px rgba(0,0,0,.35)}}
.bub{{background:#005C4B;color:#E9EDEF;border-radius:10px 10px 10px 2px;padding:8px 10px;margin:8px 0;font-size:14px}}
.stTabs [data-baseweb="tab"]{{font-weight:700}}
.stTabs [aria-selected="true"]{{color:var(--pri)}}
[data-baseweb="select"]>div,.stTextArea textarea,.stTimeInput input{{background:var(--card)!important;color:var(--ink)!important}}
.ttl{{border-bottom:3px solid var(--gold);display:inline-block;padding-bottom:4px;margin:0}}
</style>""", unsafe_allow_html=True)

# ---------- DATA ----------
MN = [("أحمد", "Ahmed"), ("محمد", "Mohamed"), ("عمر", "Omar"), ("خالد", "Khaled"), ("يوسف", "Youssef"), ("إبراهيم", "Ibrahim"), ("حسن", "Hassan"), ("سعيد", "Saeed")]
FN = [("فاطمة", "Fatima"), ("سارة", "Sara"), ("مريم", "Mariam"), ("عائشة", "Aisha"), ("نورة", "Noura"), ("هدى", "Huda"), ("ليلى", "Layla"), ("زينب", "Zainab")]
SN = [("المحمود", "Al-Mahmoud"), ("العبدالله", "Al-Abdullah"), ("الخالد", "Al-Khaled"), ("السيد", "El-Sayed"), ("الحسن", "Al-Hassan"), ("الشريف", "Al-Sharif"), ("الغامدي", "Al-Ghamdi"), ("القحطاني", "Al-Qahtani")]
CAPS = [2, 3, 4, 4, 4, 3, 2, 4, 4, 4]


@st.cache_data
def demo(seed, n=300):
    r, rows, f = random.Random(seed), [], 0

    def person(g, age, fam, sn):
        a, e = r.choice(MN if g == "M" else FN)
        hc = "wheelchair" if age >= 60 and r.random() < .12 else "ok"
        rows.append(dict(name_ar=f"{a} {sn[0]}", name_en=f"{e} {sn[1]}", family=fam, gender=g, age=age, health=hc))

    while len(rows) < n:
        sn = r.choice(SN)
        if r.random() < .55:
            f += 1
            for k in range(r.choice([2, 3, 4, 5, 6])):
                person("M" if k == 0 else r.choice("MF"), r.randint(40, 78) if k < 2 else r.randint(8, 38), f"F{f:02d}", sn)
        else:
            person(r.choice("MF"), r.randint(22, 76), "", sn)
    d = pd.DataFrame(rows[:n])
    d.insert(0, "pid", [f"P{i + 1:03d}" for i in range(len(d))])
    d["special"] = (d.age >= 70) | (d.health == "wheelchair")
    return d


def load(up, seed):
    if up is None:
        return demo(seed), False
    try:
        d = pd.read_csv(up) if up.name.endswith("csv") else pd.read_excel(up)
        d.columns = [c.strip().lower() for c in d.columns]
        d = d[["name", "family", "gender", "age", "health"]].copy()
    except Exception:
        return demo(seed), True
    d["family"] = d.family.fillna("").astype(str)
    g = d.gender.astype(str).str.upper().str[0]
    d["gender"] = g.where(g.isin(["M", "F"]), "M")
    d["health"] = d.health.fillna("ok").astype(str).str.lower()
    d["age"] = pd.to_numeric(d.age, errors="coerce").fillna(40).astype(int)
    d["name_ar"] = d["name_en"] = d.pop("name")
    d.insert(0, "pid", [f"P{i + 1:03d}" for i in range(len(d))])
    d["special"] = (d.age >= 70) | d.health.str.contains("wheel")
    return d, False


@st.cache_data
def alloc(d):
    d = d.reset_index(drop=True)
    rooms = [dict(id=f"{f}{i + 1:02d}", floor=f, cap=c, occ=[], g=None) for f in range(1, 11) for i, c in enumerate(CAPS)]
    free = lambda x: x["cap"] - len(x["occ"])
    fams = sorted(d[d.family != ""].groupby("family"), key=lambda x: (-x[1].special.any(), -len(x[1])))
    for _, g in fams:
        sp, ids = g.special.any(), list(g.index)
        while ids:
            n = min(len(ids), 4)
            chunk, ids = ids[:n], ids[n:]
            cand = [x for x in rooms if not x["occ"] and x["cap"] >= n]
            if not cand:
                continue
            k = (lambda x: (x["floor"], x["cap"] - n)) if sp else (lambda x: (x["floor"] < 3, x["cap"] - n, x["floor"]))
            x = min(cand, key=k)
            x["occ"] += chunk
            x["g"] = "FAM"
    for i, row in d[d.family == ""].sort_values("special", ascending=False).iterrows():
        sp, g = row.special, row.gender
        low = lambda x: (not sp) or x["floor"] <= 2
        pool = ([x for x in rooms if x["g"] == g and free(x) > 0 and low(x)]
                or [x for x in rooms if not x["occ"] and low(x)] or [x for x in rooms if not x["occ"]])
        if pool:
            x = min(pool, key=lambda x: x["floor"] if sp else (x["floor"] < 3, x["floor"]))
            x["occ"].append(i)
            x["g"] = g
    d["room"], d["floor"], d["bus"] = "", 0, 0
    for x in rooms:
        for i in x["occ"]:
            d.at[i, "room"], d.at[i, "floor"] = x["id"], x["floor"]
    a = d[d.room != ""].sort_values(["floor", "room"])
    d.loc[a.index, "bus"] = np.arange(len(a)) // 45 + 1
    return d


def to_xlsx(df):
    b = io.BytesIO()
    with pd.ExcelWriter(b, engine="openpyxl") as w:
        df.to_excel(w, index=False)
    return b.getvalue()


def card(label, value, extra=""):
    return f"<div class='card'><small>{label}</small><b>{value}</b><small>{extra}</small></div>"


# ---------- TOP BAR ----------
c1, c2, c3 = st.columns([8, 1, 1])
c1.markdown(f"<h1 class='ttl'>🕋 {T['title']}</h1><br><small style='color:var(--mute)'>{T['sub']}</small>", unsafe_allow_html=True)
c2.button("☀️" if s.dark else "🌙", key="tg_dark", on_click=lambda: s.update(dark=not s.dark))
c3.button("EN" if AR else "ع", key="tg_lang", on_click=lambda: s.update(lang="en" if AR else "ar"))

hi = st.selectbox(T["hotel"], range(3), format_func=lambda i: T["hotels"][i])
up = st.file_uploader(T["up"], type=["csv", "xlsx"])
raw, bad = load(up, hi + 7)
if bad:
    st.warning(T["bad"])
d = alloc(raw)
sig = (hi, len(d), d.pid.iloc[0], d.name_en.iloc[0])
if s.get("sig") != sig:
    s.update(sig=sig, checked=set(), log=[], msgs=None)

nb = int(d.bus.max())
tot = len(d)
placed = int((d.room != "").sum())
boarded = d[d.pid.isin(s.checked)].groupby("bus").size()
by_bus = d[d.bus > 0].groupby("bus").size()
tabs = st.tabs(T["tabs"])

# ---------- 1. DASHBOARD ----------
with tabs[0]:
    k = st.columns(4)
    used = d[d.room != ""].room.nunique()
    low = int(((d.special) & (d.floor.between(1, 2))).sum())
    vals = [(tot, f"{placed}/{tot}"), (f"{used}/100", ""), (low, f"/ {int(d.special.sum())}"),
            (f"{len(s.checked) / tot:.0%}", f"{len(s.checked)}/{tot}")]
    for col, lab, (v, ex) in zip(k, T["k"], vals):
        col.markdown(card(lab, v, ex), unsafe_allow_html=True)
    occ = d[d.room != ""].groupby("room").size()
    M = np.array([[occ.get(f"{f}{i + 1:02d}", 0) / CAPS[i] for i in range(10)] for f in range(10, 0, -1)])
    fig = px.imshow(M, x=[str(i + 1) for i in range(10)], y=[str(f) for f in range(10, 0, -1)],
                    color_continuous_scale=[C["sand"], C["pri"], C["pri2"]], zmin=0, zmax=1, text_auto=".0%",
                    aspect="auto", labels=dict(x=T["rm"], y=T["fl"], color=""))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color=C["ink"],
                      margin=dict(l=0, r=0, t=10, b=0), height=430)
    st.markdown(f"### {T['heat']}")
    st.plotly_chart(fig, use_container_width=True)

# ---------- 2. HOUSING ----------
with tabs[1]:
    a, b = st.columns([2, 1])
    smp = raw.head(25).rename(columns={"name_en": "name"})[["name", "family", "gender", "age", "health"]]
    b.download_button(T["smp"], to_xlsx(smp), "sample_pilgrims.xlsx", key="dl_smp")
    if a.button(T["run"], key="run"):
        with st.spinner(T["spin"]):
            time.sleep(1.0)
        s.ran = True
    if s.get("ran"):
        out = pd.DataFrame({
            T["cols"]["name"]: d[NM], T["cols"]["family"]: d.family,
            T["cols"]["gender"]: d.gender.map(T["gm"]), T["cols"]["age"]: d.age,
            T["cols"]["floor"]: d.floor, T["cols"]["room"]: d.room, T["cols"]["bus"]: d.bus,
            T["cols"]["note"]: [T["notes"][3] if r == "" else T["notes"][0] if (sp and fl <= 2) else T["notes"][1] if fm else T["notes"][2]
                                for r, sp, fl, fm in zip(d.room, d.special, d.floor, d.family != "")]})
        st.markdown(f"### {T['res']}")
        st.dataframe(out, use_container_width=True, height=380)
        st.download_button(T["dl"], to_xlsx(out), "room_allocation.xlsx", key="dl_out")
    else:
        st.info(T["hint"])

# ---------- 3. BUSES ----------
with tabs[2]:
    rows, ratios = "", []
    for n in range(1, nb + 1):
        t_, b_ = int(by_bus.get(n, 0)), int(boarded.get(n, 0))
        r_ = b_ / t_ if t_ else 0
        ratios.append(r_)
        stt = T["st"][2] if r_ >= .95 else T["st"][1] if r_ > 0 else T["st"][0]
        rows += (f"<div class='row'><b>{T['bus']} {n}</b><div class='bar'><i style='width:{r_ * 100:.0f}%'></i></div>"
                 f"<span>{b_}/{t_} {T['boarded']}</span><span>{stt}</span></div>")
    st.markdown(f"<div class='card'>{rows}</div>", unsafe_allow_html=True)
    hp, mn = (21.4225, 39.8262), (21.4133, 39.8933)
    pts = pd.DataFrame([dict(lat=hp[0] + (mn[0] - hp[0]) * r, lon=hp[1] + (mn[1] - hp[1]) * r) for r in ratios])
    st.markdown(f"### {T['map']}")
    st.map(pts, size=150, color=C["pri"])

# ---------- 4. QR CHECK-IN ----------
with tabs[3]:
    names = d.set_index("pid")[NM]
    a, b = st.columns([1, 1])
    with a:
        sel = st.selectbox(T["pick"], d.pid, format_func=lambda p: f"{p} · {names[p]}")
        buf = io.BytesIO()
        qrcode.make(sel).save(buf, "PNG")
        st.image(buf.getvalue(), width=200)
        busmap = d.set_index("pid").bus

        def mark(pids):
            for p in pids:
                if p not in s.checked:
                    s.checked.add(p)
                    s.log.insert(0, f"{p} · {names[p]} · {T['bus']} {busmap[p]}")

        if st.button(T["scan"], key="scan"):
            mark([sel])
        if st.button(T["scan10"], key="scan10"):
            mark([p for p in d[d.bus > 0].pid if p not in s.checked][:10])
    with b:
        rate = len(s.checked) / tot
        st.markdown(card(T["att"], f"{len(s.checked)}/{tot}", f"{rate:.0%}"), unsafe_allow_html=True)
        st.progress(rate)
        st.markdown(f"**{T['log']}**")
        for line in s.log[:6]:
            st.write("✅ " + line)

# ---------- 5. WHATSAPP ----------
with tabs[4]:
    a, b = st.columns([1, 1])
    with a:
        wb = st.selectbox(T["wa_bus"], range(1, nb + 1), format_func=lambda x: f"{T['bus']} {x}")
        wt = st.time_input(T["wa_time"], value=dtime(14, 0))
        tpl = st.text_area(T["wa_tpl"], T["wa_msg"], height=110)
        if st.button(T["wa_btn"], key="wa"):
            s.msgs = (wb, tpl, wt.strftime("%H:%M"))
    with b:
        if s.get("msgs"):
            mb, mt, mtime = s.msgs
            mem = d[d.bus == mb]
            bub = "".join(
                f"<div class='bub'>{html.escape(mt.replace('{name}', nm_).replace('{bus}', f'{T['bus']} {mb}').replace('{time}', mtime))}</div>"
                for nm_ in mem[NM].head(3))
            st.markdown(f"<div class='phone'>{bub}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card' style='margin-top:14px'><b>{len(mem)}</b><small>{T['wa_q']}</small></div>",
                        unsafe_allow_html=True)

st.markdown(f"<p style='text-align:center;color:var(--mute);margin-top:32px'>{T['foot']}</p>", unsafe_allow_html=True)
