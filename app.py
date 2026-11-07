import base64
import html
import io
import random
import time
from urllib.parse import quote
from datetime import time as dtime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import qrcode
import streamlit as st

st.set_page_config(page_title="Daly Track | Smart Housing & Logistics", page_icon="🕋", layout="wide")
s = st.session_state
s.setdefault("lang", "ar")
s.setdefault("dark", False)
s.setdefault("offline", False)
s.setdefault("queue", [])

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
        brand="Daly Track", by="بتقنية",
        net="الاتصال (محاكاة)", off_msg="🔴 وضع بدون إنترنت (محاكاة): العمليات بتتحفظ محليًا في طابور ومش بتوصل للسيرفر لحد المزامنة.",
        q_lbl="عمليات في انتظار المزامنة", sync="🔄 مزامنة الآن", syncing="جاري رفع العمليات للسيرفر...",
        synced="تمت مزامنة {n} عملية بنجاح", queued="تم الحفظ محليًا: {n} عملية في الطابور", done_t="تم تسجيل {n} عملية",
        inc="سجل البلاغات والتنبيهات", pg_rep="بلّغ عن مشكلة", ann_title="إعلان من الإدارة", ann_share="شارك على واتساب", ann_reach="يظهر لـ {n} معتمر في صفحة الكود وفي شاشة السائق والمشرف", ann_all="الأحبة المعتمرين", pg_sent="وصل بلاغك للإدارة", pg_badge="تحميل كارت الهوية للطباعة", ik=("بلاغ طوارئ SOS", "تحديث حالة", "بلاغ من معتمر"), no_inc="لا توجد بلاغات",
        fin=("الحاسبة المالية (قيم افتراضية للتوضيح)", "سعر لتر الوقود (ر.س)", "استهلاك الحافلة (لتر/100 كم)", "رحلات الحافلة في الموسم",
             "مسافة الرحلة (كم)", "تكلفة تشغيل الحافلة في الموسم (ر.س)", "سعر العقد للمعتمر (ر.س)", "تكاليف ثابتة (ر.س)",
             "الإيراد", "التكلفة", "صافي الربح", "هامش الربح", "الوقود", "التشغيل", "ثابتة", "الإيراد مقابل التكلفة",
             "الأرقام افتراضية وتتغير بالمدخلات، وليست بيانات حقيقية."),
        tn=dict(dash="📊 لوحة التحكم", house="⚡ التسكين الذكي", buses="🚌 الحافلات", fleet="🚨 غرفة العمليات",
                driver="🧑‍✈️ السائق والمشرف", qr="📱 حضور QR", wa="📣 الإشعارات"),
        rl=("ادخل بصفتك", dict(hotel=("🏨 فندق", "التسكين وإشغال الغرف"), bus=("🚌 شركة حافلات", "الأسطول والحافلات والحضور"),
                              mgr=("🧭 مدير المنصة", "كل الموديولات"))), sw="تبديل الدور", rst="إعادة ضبط الديمو",
        fs=("جاهزة", "تحت الفحص", "عطلانة"), fl_set="حالة الحافلة", fl_btn="تحديث الحالة", fl_alert="🚨 فيه حافلة عطلانة: تم إرسال فريق صيانة متنقل (محاكاة)",
        sla_t="مهلة توفير حافلة بديلة", sla_lbl="مهلة البديلة (دقيقة)", sla_left="المتبقي", sla_over="متأخرة بـ", sla_exp="انتهت المهلة",
        sla_note="المهلة قابلة للضبط، والقيمة الافتراضية (60 دقيقة) للتوضيح فقط وليست لائحة رسمية، والبيانات وهمية (محاكاة).",
        dr_route="المسار: الحرم ← منى (محاكاة)", dr_dep="موعد الانطلاق", dr_done="اكتمل الركوب", dr_sos="بلاغ طوارئ",
        dr_ok="تم تسجيل ركوب {n} معتمر", dr_sosm="تم إبلاغ الإدارة وتحويل الحافلة لحالة عطل (محاكاة)",
        qr_ok="تم تسجيل حضورك", qr_note="الكود بيفتح التطبيق ويسجل الحضور (ببيانات الديمو فقط)", title="منصة التسكين والتفويج الذكي", sub="نموذج أولي تفاعلي · بيانات تجريبية فقط", hotel="الفندق",
        hotels=["فندق أنوار المدينة", "فندق أبراج الساعة", "فندق دار الضيافة"],
        tabs=["📊 لوحة المدير", "⚡ التسكين الذكي", "🚌 الحافلات", "📱 حضور QR", "💬 واتساب"],
        k=["إجمالي المعتمرين", "الغرف المشغولة", "حالات خاصة بالأدوار الأرضية", "نسبة الحضور"],
        heat="مبنى الفندق: إشغال الغرف", all="الكل", ch=("حالة الغرف", "أنواع المعتمرين", "نسبة الحضور", "الإشغال حسب الدور", "ركوب الحافلات", "الفئات العمرية"), rs=("مليانة", "فيها أماكن", "فاضية"), ty=("عائلات", "رجال فرادى", "نساء فرادى", "حالات خاصة"), ag=("أقل من 18", "18–39", "40–59", "60–69", "70+"), ser=("الإجمالي", "ركبوا"), ok=("سجّلوا", "لم يسجّلوا"), lg=("فاضية", "فيها أماكن", "مليانة", "حالة خاصة"), fb="الإشغال حسب الدور", fl="الدور", rm="الغرفة",
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
        brand="Daly Track", by="Powered by",
        net="Connection (simulated)", off_msg="🔴 Offline mode (simulated): operations are saved locally in a queue and do not reach the server until sync.",
        q_lbl="Operations waiting to sync", sync="🔄 Sync now", syncing="Uploading operations to the server...",
        synced="{n} operations synced successfully", queued="Saved locally: {n} operation(s) queued", done_t="{n} operation(s) recorded",
        inc="Incident and alert log", pg_rep="Report a problem", ann_title="Management announcement", ann_share="Share on WhatsApp", ann_reach="Shown to {n} pilgrims on their code page and on the driver and supervisor screen", ann_all="dear pilgrims", pg_sent="Your report reached management", pg_badge="Download printable ID card", ik=("SOS emergency", "Status update", "Pilgrim report"), no_inc="No incidents",
        fin=("Financial calculator (illustrative defaults)", "Fuel price per liter (SAR)", "Bus consumption (L/100 km)", "Trips per bus per season",
             "Trip distance (km)", "Bus operating cost per season (SAR)", "Contract price per pilgrim (SAR)", "Fixed costs (SAR)",
             "Revenue", "Cost", "Net profit", "Profit margin", "Fuel", "Operations", "Fixed", "Revenue vs cost",
             "Figures are illustrative and change with the inputs; they are not real data."),
        tn=dict(dash="📊 Dashboard", house="⚡ Smart housing", buses="🚌 Buses", fleet="🚨 Operations room",
                driver="🧑‍✈️ Driver & supervisor", qr="📱 QR check-in", wa="📣 Announcements"),
        rl=("Sign in as", dict(hotel=("🏨 Hotel", "Housing and room occupancy"), bus=("🚌 Bus company", "Fleet, buses and check-in"),
                              mgr=("🧭 Platform manager", "All modules"))), sw="Switch role", rst="Reset demo",
        fs=("Ready", "Inspection", "Broken down"), fl_set="Bus status", fl_btn="Update status", fl_alert="🚨 A bus is down: mobile maintenance team dispatched (simulated)",
        sla_t="Replacement bus deadline", sla_lbl="Replacement deadline (min)", sla_left="Remaining", sla_over="Overdue by", sla_exp="Deadline passed",
        sla_note="The deadline is adjustable; the default (60 min) is illustrative only, not an official regulation. Data is simulated.",
        dr_route="Route: Haram → Mina (simulated)", dr_dep="Departure", dr_done="Boarding complete", dr_sos="Emergency report",
        dr_ok="{n} pilgrims marked as boarded", dr_sosm="Management notified and the bus marked as broken down (simulated)",
        qr_ok="You are checked in", qr_note="The code opens the app and records check-in (demo data only)", title="Smart Housing & Logistics Platform", sub="Interactive prototype · demo data only", hotel="Hotel",
        hotels=["Anwar Al-Madinah Hotel", "Abraj Clock Hotel", "Dar Al-Diyafa Hotel"],
        tabs=["📊 Manager", "⚡ Smart housing", "🚌 Buses", "📱 QR check-in", "💬 WhatsApp"],
        k=["Total pilgrims", "Rooms in use", "Special cases on lower floors", "Check-in rate"],
        heat="Hotel building: room occupancy", all="All", ch=("Room status", "Pilgrim types", "Check-in rate", "Occupancy by floor", "Bus boarding", "Age groups"), rs=("Full", "Has space", "Empty"), ty=("Families", "Single men", "Single women", "Special cases"), ag=("Under 18", "18–39", "40–59", "60–69", "70+"), ser=("Total", "Boarded"), ok=("Checked in", "Not yet"), lg=("Empty", "Has space", "Full", "Special case"), fb="Occupancy by floor", fl="Floor", rm="Room",
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
.bar i{{display:block;height:100%;background:linear-gradient(90deg,#E7CF8A,#C9A227)}}
.fl{{display:grid;grid-template-columns:28px repeat(10,1fr);gap:6px;align-items:center;margin:5px 0;color:var(--ink)}}
.rm{{height:28px;border-radius:6px;box-shadow:0 3px 0 rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.45)}}
.lg{{margin-inline-end:16px;font-size:13px;color:var(--mute)}}
.lg i{{display:inline-block;width:12px;height:12px;border-radius:3px;margin-inline-end:6px;vertical-align:middle;border:1px solid var(--gold)}}
.row{{display:grid;grid-template-columns:110px 1fr 120px 90px;gap:12px;align-items:center;margin:12px 0;color:var(--ink)}}
.phone{{max-width:360px;margin:auto;background:#0B141A;border-radius:28px;padding:16px;border:6px solid #222;box-shadow:0 18px 40px rgba(0,0,0,.35)}}
.bub{{background:#005C4B;color:#E9EDEF;border-radius:10px 10px 10px 2px;padding:8px 10px;margin:8px 0;font-size:14px}}
.stTabs [data-baseweb="tab"]{{font-weight:700}}
.stTabs [aria-selected="true"]{{color:var(--pri)}}
[data-baseweb="select"]>div,.stTextArea textarea,.stTimeInput input{{background:var(--card)!important;color:var(--ink)!important}}
.ttl{{border-bottom:3px solid var(--gold);display:inline-block;padding-bottom:4px;margin:0}}
.st-key-hid_pages{{display:none}}
.chip{{padding:3px 12px;border-radius:12px;font-size:13px;font-weight:700;display:inline-block}}
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
    fams = sorted(d[d.family != ""].groupby("family"), key=lambda x: (-int(x[1].special.any()), -len(x[1])))
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



PAL = [GOLD, "#E7CF8A", "#F3EAD3", "#1B1B1B"]


def show(fig, h=290, donut=None):
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", dragmode=False, height=h,
                      font=dict(color=C["ink"], family="Tajawal"), margin=dict(l=0, r=0, t=40, b=0), title_font_size=16,
                      legend=dict(orientation="h", y=-0.08, itemclick=False, itemdoubleclick=False))
    fig.update_xaxes(fixedrange=True, gridcolor=C["line"])
    fig.update_yaxes(fixedrange=True, gridcolor=C["line"])
    if donut:
        fig.add_annotation(text=f"<b>{donut}</b>", showarrow=False, font=dict(size=24, color=C["ink"]))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})


def donut(names, vals, title, centre):
    f = px.pie(names=names, values=vals, hole=.64, title=title, color_discrete_sequence=PAL)
    f.update_traces(textinfo="percent", textfont_color="#10343A", marker=dict(line=dict(color=C["card"], width=3)),
                    sort=False, pull=[0.02] * len(names))
    show(f, donut=centre)


def card(label, value, extra=""):
    return f"<div class='card'><small>{label}</small><b>{value}</b><small>{extra}</small></div>"


def ann_text(tpl, name, bus, tm):
    return tpl.replace("{name}", name).replace("{bus}", f"{T['bus']} {bus}").replace("{time}", tm)


APP_URL = "https://hajj-demo-app-7fkifuz3mr3zgtohpqnlqi.streamlit.app/"


@st.cache_resource
def _shared():
    return {}


def box(k):
    b = _shared().setdefault(k, dict(checked=set(), log=[], msgs=None, fleet={}))
    b.setdefault("inc", [])
    b.setdefault("down_at", {})
    b.setdefault("sla_min", 60)
    return b


def fstat(b, n):
    return b["fleet"].get(n, "check" if n % 4 == 0 else "ok")


qp = st.query_params
if "pid" in qp:  # opened by scanning a pilgrim QR code
    hq = int(qp["h"]) if str(qp.get("h", "0")).isdigit() and int(qp["h"]) < 3 else 0
    dq, bq = alloc(demo(hq + 7)), box(hq)
    rw = dq[dq.pid == qp["pid"]]
    if rw.empty:
        st.error("QR ?")
    else:
        r0 = rw.iloc[0]
        if r0.pid not in bq["checked"]:
            bq["checked"].add(r0.pid)
            bq["log"].insert(0, f"{r0.pid} · {r0[NM]} · {T['bus']} {r0.bus}")
        st.markdown(f"<h1 class='ttl'>🕋 {T['brand']}</h1>", unsafe_allow_html=True)
        dep_q = bq["msgs"][2] if bq["msgs"] and bq["msgs"][0] == r0.bus else "14:00"
        st.markdown(card(T["qr_ok"], f"✅ {r0[NM]}", f"{r0.pid}"), unsafe_allow_html=True)
        det = [(T["hotel"], T["hotels"][hq]), (T["rm"], r0.room or "-"), (T["fl"], r0.floor or "-"),
               (T["bus"], r0.bus or "-"), (T["dr_dep"], dep_q)]
        st.markdown("<div class='card' style='margin-top:12px'>" + "".join(
            f"<div class='row' style='grid-template-columns:110px 1fr'><b>{a_}</b><span>{b_}</span></div>" for a_, b_ in det)
            + "</div>", unsafe_allow_html=True)
        if bq["msgs"] and bq["msgs"][0] == r0.bus:
            st.markdown(card(T["ann_title"], "📣", html.escape(ann_text(bq["msgs"][1], str(r0[NM]), r0.bus, bq["msgs"][2]))),
                        unsafe_allow_html=True)
        st.button(T["pg_rep"], key="pg_rep", on_click=lambda: (
            bq["inc"].insert(0, (time.strftime("%H:%M:%S"), int(r0.bus), "pilgrim", fstat(bq, int(r0.bus)))),
            s.update(pg_sent=True)))
        if s.get("pg_sent"):
            st.success(T["pg_sent"])
    st.stop()

# ---------- TOP BAR ----------
c1, c2, c3, c4, c5 = st.columns([7, 1, 1, 1, 1])
c1.markdown(f"<h1 class='ttl'>🕋 {T['brand']}</h1><br><small style='color:var(--mute)'>{T['title']} · {T['sub']}</small>", unsafe_allow_html=True)
c2.button("☀️" if s.dark else "🌙", key="tg_dark", on_click=lambda: s.update(dark=not s.dark))
c3.button("EN" if AR else "ع", key="tg_lang", on_click=lambda: s.update(lang="en" if AR else "ar"))
c4.button("🔁", key="tg_role", on_click=lambda: s.update(role=None), help=T["sw"])
c5.button("🔴" if s.offline else "🟢", key="tg_net", on_click=lambda: s.update(offline=not s.offline), help=T["net"])
if not s.get("role"):
    st.markdown(f"### {T['rl'][0]}")
    for col, k_ in zip(st.columns(3), ("hotel", "bus", "mgr")):
        nm_, ds_ = T["rl"][1][k_]
        col.markdown(f"<div class='card'><b style='font-size:22px'>{nm_}</b><small>{ds_}</small></div>", unsafe_allow_html=True)
        col.button(nm_, key=f"role_{k_}", on_click=lambda k=k_: s.update(role=k))
    st.stop()

hi = st.selectbox(T["hotel"], range(3), format_func=lambda i: T["hotels"][i])
up = st.file_uploader(T["up"], type=["csv", "xlsx"])
raw, bad = load(up, hi + 7)
if bad:
    st.warning(T["bad"])
d = alloc(raw)
bx = box(hi if up is None else ("up", up.name))
if s.role == "mgr":
    st.button(T["rst"], key="rst", on_click=lambda: (bx.update(checked=set(), log=[], msgs=None, fleet={}, inc=[], down_at={}, sla_min=60), s.update(queue=[])))


NMAP, BMAP = d.set_index("pid")[NM], d.set_index("pid").bus


def commit(item):
    if item[0] == "scan":
        p = item[1]
        if p not in bx["checked"]:
            bx["checked"].add(p)
            bx["log"].insert(0, f"{p} · {NMAP[p]} · {T['bus']} {BMAP[p]}")
    else:
        _, b_, st_, kind, ts = item
        bx["fleet"][b_] = st_
        if st_ == "down":
            bx["down_at"].setdefault(b_, time.time())
        else:
            bx["down_at"].pop(b_, None)
        bx["inc"].insert(0, (ts, b_, kind, st_))


def mark(pids):
    queued = {q[1] for q in s.queue if q[0] == "scan"}
    new = [p for p in pids if p not in bx["checked"] and p not in queued]
    if s.offline:
        s.queue += [("scan", p) for p in new]
        s.flash = T["queued"].format(n=len(new))
    else:
        for p in new:
            commit(("scan", p))
        s.flash = T["done_t"].format(n=len(new))


def fleet_set(bus, status, kind):
    item = ("fleet", bus, status, kind, time.strftime("%H:%M:%S"))
    if s.offline:
        s.queue.append(item)
        s.flash = T["queued"].format(n=1)
    else:
        commit(item)
        s.flash = T["done_t"].format(n=1)


if s.get("flash"):
    st.toast(s.pop("flash"))
if s.offline:
    st.warning(T["off_msg"])
if s.queue:
    qa, qb = st.columns([3, 1])
    qa.markdown(card(T["q_lbl"], len(s.queue)), unsafe_allow_html=True)
    if qb.button(T["sync"], key="sync", disabled=s.offline):
        with st.spinner(T["syncing"]):
            time.sleep(1.4)
        n_sync = len(s.queue)
        for it in s.queue:
            commit(it)
        s.queue = []
        st.success(T["synced"].format(n=n_sync))


nb = int(d.bus.max())
tot = len(d)
placed = int((d.room != "").sum())
boarded = d[d.pid.isin(bx["checked"])].groupby("bus").size()
by_bus = d[d.bus > 0].groupby("bus").size()
ROLE = dict(hotel=["dash", "house"], bus=["fleet", "buses", "driver", "qr", "wa"],
            mgr=["dash", "house", "buses", "fleet", "driver", "qr", "wa"])
keys = ROLE[s.role]
tb = st.tabs([T["tn"][k] for k in keys])
HID = st.container(key="hid_pages")
TB = {k: (tb[keys.index(k)] if k in keys else HID) for k in ("dash", "house", "buses", "fleet", "driver", "qr", "wa")}

# ---------- 1. DASHBOARD ----------
with TB["dash"]:
    k = st.columns(4)
    used = d[d.room != ""].room.nunique()
    low = int(((d.special) & (d.floor.between(1, 2))).sum())
    vals = [(tot, f"{placed}/{tot}"), (f"{used}/100", ""), (low, f"/ {int(d.special.sum())}"),
            (f"{len(bx["checked"]) / tot:.0%}", f"{len(bx["checked"])}/{tot}")]
    for col, lab, (v, ex) in zip(k, T["k"], vals):
        col.markdown(card(lab, v, ex), unsafe_allow_html=True)
    occ = d[d.room != ""].groupby("room").size()
    f1, f2 = st.columns(2)
    rng = f1.slider(T["fl"], 1, 10, (1, 10), key="frng")
    bf = f2.selectbox(T["bus"], [0] + list(range(1, nb + 1)), format_func=lambda x: T["all"] if x == 0 else f"{T['bus']} {x}")
    dd = d[(d.room != "") & d.floor.between(*rng)]
    if bf:
        dd = dd[dd.bus == bf]
    fl_rng = range(rng[0], rng[1] + 1)
    cnt = [0, 0, 0]
    for f in fl_rng:
        for i in range(10):
            n_ = int(occ.get(f"{f}{i + 1:02d}", 0))
            cnt[0 if n_ >= CAPS[i] else 2 if n_ == 0 else 1] += 1
    g1, g2, g3 = st.columns(3)
    with g1:
        donut(T["rs"], cnt, T["ch"][0], f"{cnt[0] + cnt[1]}/{sum(cnt)}")
    with g2:
        kind = np.where(dd.special, 3, np.where(dd.family != "", 0, np.where(dd.gender == "M", 1, 2)))
        donut(T["ty"], [int((kind == k_).sum()) for k_ in range(4)], T["ch"][1], len(dd))
    with g3:
        rate = len(bx["checked"]) / tot
        donut(T["ok"], [len(bx["checked"]), tot - len(bx["checked"])], T["ch"][2], f"{rate:.0%}")
    h1, h2, h3 = st.columns(3)
    with h1:
        pf = [int((d.floor == f).sum()) / sum(CAPS) for f in fl_rng]
        f = px.bar(x=[str(x) for x in fl_rng], y=pf, title=T["ch"][3], color_discrete_sequence=[GOLD], text=[f"{v:.0%}" for v in pf])
        f.update_yaxes(tickformat=".0%", range=[0, 1.05], title=None)
        f.update_xaxes(title=T["fl"])
        f.update_traces(textposition="outside", hovertemplate="%{x}: %{y:.0%}<extra></extra>", marker_cornerradius=6)
        show(f)
    with h2:
        bs = [x for x in range(1, nb + 1) if not bf or x == bf]
        f = go.Figure([go.Bar(name=T["ser"][0], x=[f"{T['bus']} {x}" for x in bs], y=[int(by_bus.get(x, 0)) for x in bs], marker_color="#E7CF8A"),
                       go.Bar(name=T["ser"][1], x=[f"{T['bus']} {x}" for x in bs], y=[int(boarded.get(x, 0)) for x in bs], marker_color=GOLD)])
        f.update_layout(barmode="group", title=T["ch"][4])
        show(f)
    with h3:
        grp = pd.cut(dd.age, [-1, 17, 39, 59, 69, 200], labels=list(T["ag"])).value_counts().reindex(list(T["ag"]))
        f = px.bar(x=list(T["ag"]), y=grp.values, title=T["ch"][5], color_discrete_sequence=[GOLD], text=grp.values)
        f.update_xaxes(title=None)
        f.update_yaxes(title=None)
        f.update_traces(textposition="outside", marker_cornerradius=6)
        show(f)

    spr = set(d[(d.room != "") & d.special].room)
    tone = [C["line"] if s.dark else "#F3EAD3", "#E7CF8A", GOLD]

    def cell(f, i):
        rid, n_, cp = f"{f}{i + 1:02d}", int(occ.get(f"{f}{i + 1:02d}", 0)), CAPS[i]
        if rid in spr:
            bg, bd = "#1B1B1B", f"2px solid {GOLD}"
        else:
            bg, bd = tone[0 if n_ == 0 else 2 if n_ >= cp else 1], "0"
        return f"<div class='rm' title='{rid}: {n_}/{cp}' style='background:{bg};border:{bd}'></div>"

    bld = "".join(f"<div class='fl'><span>{f}</span>" + "".join(cell(f, i) for i in range(10)) + "</div>"
                  for f in range(10, 0, -1))
    lg = "".join(f"<span class='lg'><i style='background:{c_}'></i>{t_}</span>"
                 for c_, t_ in zip(tone + ["#1B1B1B"], T["lg"]))
    st.markdown(f"### {T['heat']}")
    st.markdown(f"<div class='card'>{bld}<div style='margin-top:12px'>{lg}</div></div>", unsafe_allow_html=True)

    if s.role == "mgr":
        F = T["fin"]
        st.markdown(f"### {F[0]}")
        q1, q2, q3, q4 = st.columns(4)
        fp = q1.slider(F[1], 1.0, 4.0, 2.0, 0.1, key="f_fp")
        fc = q2.slider(F[2], 20, 60, 35, key="f_fc")
        ft = q3.slider(F[3], 10, 200, 60, key="f_ft")
        fk = q4.slider(F[4], 5, 100, 25, key="f_fk")
        r1, r2, r3 = st.columns(3)
        fo = r1.slider(F[5], 0, 30000, 8000, 500, key="f_fo")
        fcn = r2.slider(F[6], 500, 5000, 1500, 100, key="f_fcn")
        fx = r3.slider(F[7], 0, 100000, 20000, 1000, key="f_fx")
        fuel, ops_c = nb * ft * fk * fc / 100 * fp, nb * fo
        cost = fuel + ops_c + fx
        rev = placed * fcn
        prof = rev - cost
        vals_ = (f"{rev:,.0f}", f"{cost:,.0f}", f"{prof:,.0f}", f"{prof / rev:.0%}" if rev else "-")
        for col, lab, v, unit in zip(st.columns(4), F[8:12], vals_, ("SAR", "SAR", "SAR", "")):
            col.markdown(card(lab, v, unit), unsafe_allow_html=True)
        z1, z2 = st.columns(2)
        with z1:
            donut(F[12:15], [fuel, ops_c, fx], F[9], f"{cost:,.0f}")
        with z2:
            fb_ = px.bar(x=list(F[8:11]), y=[rev, cost, prof], color_discrete_sequence=[GOLD], title=F[15],
                         text=[f"{v:,.0f}" for v in (rev, cost, prof)])
            fb_.update_traces(textposition="outside", marker_cornerradius=6)
            fb_.update_xaxes(title=None)
            fb_.update_yaxes(title=None)
            show(fb_)
        st.caption(F[16])

# ---------- 2. HOUSING ----------
with TB["house"]:
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
with TB["buses"]:
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
with TB["qr"]:
    names = d.set_index("pid")[NM]
    a, b = st.columns([1, 1])
    with a:
        sel = st.selectbox(T["pick"], d.pid, format_func=lambda p: f"{p} · {names[p]}")
        buf = io.BytesIO()
        qrcode.make(f"{APP_URL}?pid={sel}&h={hi}").save(buf, "PNG")
        st.image(buf.getvalue(), width=200)
        st.caption(T["qr_note"])
        rw_ = d[d.pid == sel].iloc[0]
        b64 = base64.b64encode(buf.getvalue()).decode()
        badge = (f"<div dir='{'rtl' if AR else 'ltr'}' style='width:320px;font-family:Tajawal,Arial,sans-serif;"
                 f"border:2px solid {GOLD};border-radius:16px;padding:16px;text-align:center;background:#fff;color:#10343A'>"
                 f"<div style='font-weight:700;color:#0E7C86'>🕋 {T['brand']}</div>"
                 f"<div style='font-size:22px;font-weight:700;margin:8px 0'>{html.escape(str(rw_[NM]))}</div>"
                 f"<img src='data:image/png;base64,{b64}' width='150'/>"
                 f"<div style='font-size:13px;margin-top:8px'>{sel} · {T['hotels'][hi]}<br>"
                 f"{T['rm']} {rw_.room or '-'} · {T['bus']} {rw_.bus or '-'}</div></div>")
        st.markdown(badge, unsafe_allow_html=True)
        st.download_button(T["pg_badge"], ("<meta charset='utf-8'>" + badge).encode("utf-8"), f"{sel}_badge.html", "text/html", key="dl_badge")
        st.button(T["scan"], key="scan", on_click=lambda: mark([sel]))
        st.button(T["scan10"], key="scan10", on_click=lambda: mark([p for p in d[d.bus > 0].pid if p not in bx["checked"]][:10]))
    with b:
        rate = len(bx["checked"]) / tot
        st.markdown(card(T["att"], f"{len(bx["checked"])}/{tot}", f"{rate:.0%}"), unsafe_allow_html=True)
        st.progress(rate)
        st.markdown(f"**{T['log']}**")
        for line in bx["log"][:6]:
            st.write("✅ " + line)

# ---------- 5. ANNOUNCEMENTS ----------
with TB["wa"]:
    a, b = st.columns([1, 1])
    with a:
        st.selectbox(T["wa_bus"], range(1, nb + 1), format_func=lambda x: f"{T['bus']} {x}", key="wa_b")
        st.time_input(T["wa_time"], value=dtime(14, 0), key="wa_t")
        st.text_area(T["wa_tpl"], T["wa_msg"], height=110, key="wa_x")
        st.button(T["wa_btn"], key="wa", on_click=lambda: bx.update(msgs=(s.wa_b, s.wa_x, s.wa_t.strftime("%H:%M"))))
    with b:
        if bx["msgs"]:
            mb, mt, mtime = bx["msgs"]
            n_m = int((d.bus == mb).sum())
            atxt = ann_text(mt, T["ann_all"], mb, mtime)
            st.markdown(f"<div class='phone'><div class='bub'>{html.escape(atxt)}</div></div>", unsafe_allow_html=True)
            st.markdown(card(T["ann_title"], n_m, T["ann_reach"].format(n=n_m)), unsafe_allow_html=True)
            st.link_button(T["ann_share"], "https://wa.me/?text=" + quote(atxt))

# ---------- OPERATIONS ROOM ----------
OKS = ("ok", "check", "down")


@st.fragment(run_every=5)
def ops_feed():
    fs_ = [fstat(bx, n) for n in range(1, nb + 1)]
    for col, code, lab in zip(st.columns(3), OKS, T["fs"]):
        col.markdown(card(lab, fs_.count(code)), unsafe_allow_html=True)
    if "down" in fs_:
        st.warning(T["fl_alert"])
    now_ = time.time()
    srows = ""
    for n_ in range(1, nb + 1):
        t0_ = bx["down_at"].get(n_)
        if fstat(bx, n_) != "down" or t0_ is None:
            continue
        left_ = int(bx["sla_min"] * 60 - (now_ - t0_))
        mm_, ss_ = divmod(abs(left_), 60)
        hh_, mm_ = divmod(mm_, 60)
        clk_ = f"{hh_:02d}:{mm_:02d}:{ss_:02d}"
        if left_ < 0:
            sc_, tx_ = "background:#7A1412;color:#FFFFFF;", f"{T['sla_exp']} · {T['sla_over']} {clk_}"
        elif left_ < 900:
            sc_, tx_ = "background:rgba(180,42,39,.14);color:#B42A27;font-weight:700;", f"{T['sla_left']} {clk_}"
        else:
            sc_, tx_ = "background:#F3EAD3;color:#10343A;", f"{T['sla_left']} {clk_}"
        srows += (f"<div class='row' style='border-radius:8px;padding:4px 8px;{sc_}'>"
                  f"<b>{T['bus']} {n_}</b><span>{tx_}</span><span></span><span></span></div>")
    if srows:
        st.markdown(f"### {T['sla_t']}")
        st.markdown(f"<div class='card'>{srows}</div>", unsafe_allow_html=True)
        st.caption(T["sla_note"])
    bgc, fgc = dict(ok="#E7CF8A", check="#F3EAD3", down="#1B1B1B"), dict(ok="#10343A", check="#10343A", down="#FFFFFF")
    frows = "".join(
        f"<div class='row'><b>{T['bus']} {n}</b><span class='chip' style='background:{bgc[c_]};color:{fgc[c_]}'>"
        f"{T['fs'][OKS.index(c_)]}</span><span>{int(by_bus.get(n, 0))}</span><span></span></div>"
        for n, c_ in zip(range(1, nb + 1), fs_))
    st.markdown(f"<div class='card' style='margin-top:12px'>{frows}</div>", unsafe_allow_html=True)
    st.markdown(f"### {T['inc']}")
    irows = ""
    for ts, n, kind, stt in bx["inc"][:8]:
        sty = "background:rgba(180,42,39,.14);color:#B42A27;font-weight:700;" if kind in ("sos", "pilgrim") else ""
        irows += (f"<div class='row' style='grid-template-columns:90px 1fr 120px;border-radius:8px;padding:4px 8px;{sty}'>"
                  f"<span>{ts}</span><span>{T['bus']} {n} · {T['ik'][{'sos': 0, 'pilgrim': 2}.get(kind, 1)]}</span>"
                  f"<span>{T['fs'][OKS.index(stt)]}</span></div>")
    st.markdown(f"<div class='card'>{irows or '<small>' + T['no_inc'] + '</small>'}</div>", unsafe_allow_html=True)


with TB["fleet"]:
    fa, fb2 = st.columns(2)
    fbus = fa.selectbox(T["bus"], range(1, nb + 1), format_func=lambda x: f"{T['bus']} {x}", key="fl_bus")
    fnew = fb2.selectbox(T["fl_set"], OKS, format_func=lambda c: T["fs"][OKS.index(c)], key="fl_new")
    st.button(T["fl_btn"], key="fl_go", on_click=lambda: fleet_set(fbus, fnew, "ops"))
    if s.role == "mgr":
        bx["sla_min"] = int(st.number_input(T["sla_lbl"], 5, 240, int(bx["sla_min"]), 5, key="sla_in"))
    ops_feed()

# ---------- DRIVER / SUPERVISOR ----------
with TB["driver"]:
    dbus = st.selectbox(T["bus"], range(1, nb + 1), format_func=lambda x: f"{T['bus']} {x}", key="drv_bus")
    mem_ = d[d.bus == dbus]
    da, db_ = st.columns(2)
    da.button(T["dr_done"], key="dr_done", on_click=lambda: mark(list(mem_.pid)))
    db_.button(T["dr_sos"], key="dr_sos", on_click=lambda: fleet_set(dbus, "down", "sos"))
    dep = bx["msgs"][2] if bx["msgs"] and bx["msgs"][0] == dbus else "14:00"
    nbd = int(d[d.pid.isin(bx["checked"]) & (d.bus == dbus)].shape[0])
    st.markdown(card(f"{T['bus']} {dbus}", f"{nbd}/{len(mem_)}", f"{T['dr_route']} · {T['dr_dep']} {dep}"), unsafe_allow_html=True)
    if bx["msgs"] and bx["msgs"][0] == dbus:
        atxt_d = ann_text(bx["msgs"][1], T["ann_all"], dbus, bx["msgs"][2])
        st.info("📣 " + atxt_d)
        st.link_button(T["ann_share"], "https://wa.me/?text=" + quote(atxt_d))

st.markdown(f"<p style='text-align:center;color:var(--mute);margin-top:32px'>{T['foot']}<br><b style='color:var(--pri)'>{T['by']} {T['brand']}</b></p>", unsafe_allow_html=True)