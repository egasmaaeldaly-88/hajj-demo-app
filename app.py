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
        tn=dict(dash="📊 لوحة التحكم", house="⚡ التسكين الذكي", buses="🚌 الحافلات", fleet="🚨 غرفة العمليات", energy="🔋 الطاقة والأسطول",
                driver="🧑‍✈️ السائق والمشرف", qr="📱 حضور QR", wa="📣 الإشعارات", hk="🛏️ الإشراف الداخلي", eco="🌿 وضع توفير الطاقة"),
        hk=dict(
            title="الإشراف الداخلي: حالة الغرف",
            note="حالات الغرف وعمليات النقل بيانات تجريبية (محاكاة) وغير مربوطة بأي نظام فندقي حقيقي.",
            st=("🟢 جاهزة ومعقمة", "🟡 تنظيف ومغادرة", "🔴 عطل (صيانة أو تكييف)"), refresh="تحديث", room="الغرفة", new="الحالة الجديدة", apply="تطبيق الحالة",
            occ="الساكنين", sp="حالة خاصة", nr="غرف غير جاهزة", lg2=("تنظيف", "عطل"),
            w_clean="🟡 غرف قيد التنظيف وفيها ساكنين (لم يتم نقلهم تلقائيًا):",
            man_t="تسكين يدوي مطلوب", man_warn="⚠️ مفيش غرفة 🟢 مناسبة حسب القواعد للوحدات دي. اختار غرفة يدويًا.",
            why=dict(low="لا توجد غرفة جاهزة في الدورين 1-2", none="لا توجد غرفة جاهزة بسعة أو شروط مناسبة"),
            pick="اختر الغرفة", seat="تسكين", viol="مخالفة لقاعدة الدورين 1-2", no_cand="مفيش غرفة جاهزة تناسب الوحدة دي حتى بعد تخفيف قاعدة الدور.",
            log_t="سجل النقل", no_log="لا توجد نقلات", none="بانتظار تسكين", fam="عيلة",
            lk=dict(auto="نقل تلقائي", manual="تسكين يدوي", viol="يدوي ⚠️ مخالفة الدور", pending="بانتظار تسكين يدوي", rej="مرفوض (الغرفة لم تعد مناسبة)")),
        eco=dict(
            title="وضع توفير الطاقة (Eco-Mode): معاينة فقط",
            sim_note="⚠️ محاكاة فقط: مفيش ربط فعلي بأي نظام تحكم في التكييف أو الإضاءة، ولا بيتغيّر التسكين الفعلي. كل القيم الافتراضية للتوضيح.",
            s_pct="الإشغال: سيناريو محاكاة % (للتوضيح)", s_thr="حد الإشغال المنخفض % (للتوضيح)",
            actual="الإشغال الفعلي الحالي", used="الإشغال المستخدم في المحاكاة", sug="الأدوار المقترح قفلها",
            auto="عدد الأدوار المقفولة: تلقائي (المقترح)", s_k="عدد الأدوار المقفولة (يدوي)",
            s_cons="استهلاك الدور (كيلوواط ساعة/يوم) · للتوضيح", s_red="نسبة التخفيض عند الإغلاق % · للتوضيح",
            s_days="عدد الأيام · للتوضيح", s_price="سعر الكيلوواط ساعة (ر.س) · للتوضيح",
            ok_sug="المقترح: قفل {k} أدوار (الأدوار: {fl}).", k0="مفيش دور ينفع يتفضّى بدون كسر قواعد التسكين.",
            not_low="الإشغال مش منخفض (أعلى من الحد)، فمفيش اقتراح.",
            fl_t="الأدوار قبل وبعد (محاكاة)", before="قبل", after="بعد", st=("مفتوح", "مقفول (اقتراح)"), units="وحدة هتتنقل",
            moved="{u} وحدة ({p} معتمر) هتتنقل لغرف تانية.",
            unplaced="🔴 {u} وحدة ({p} معتمر) مش لاقية مكان يحترم القواعد في الاختيار ده.",
            e_title="تقدير الطاقة (افتراضات قابلة للتعديل، للتوضيح)", e_kwh="تقدير الطاقة المخفّضة (كيلوواط ساعة)", e_cost="تقدير التكلفة المقابلة (ر.س)",
            e_formula="المعادلة: الأدوار المقفولة × استهلاك الدور × نسبة التخفيض × الأيام (وبالسعر للتكلفة). الأرقام تقدير مبني على افتراضات، مش بيانات حقيقية.",
            approx="الاقتراح تقريبي (خوارزمية بسيطة وممكن تفوّت ترتيب أفضل).",
            review="قفل الأدوار فعليًا يحتاج مراجعة السلامة وراحة النزلاء ومواعيد وصول الأفواج.",
            rules="القواعد المطبّقة: العيلة مع بعض، كبار السن والحالات الخاصة في الدورين 1-2 (ومابيتقفلوش)، فصل الرجال عن النساء، السعة، واستبعاد الغرف 🟡 و🔴. القفل من فوق لتحت."),
        rl=("ادخل بصفتك", dict(hotel=("🏨 فندق", "التسكين وإشغال الغرف"), bus=("🚌 شركة حافلات", "الأسطول والحافلات والحضور"),
                              mgr=("🧭 مدير المنصة", "كل الموديولات"))), sw="تبديل الدور", rst="إعادة ضبط الديمو",
        fs=("جاهزة", "تحت الفحص", "عطلانة"), fl_set="حالة الحافلة", fl_btn="تحديث الحالة", fl_alert="🚨 فيه حافلة عطلانة: تم إرسال فريق صيانة متنقل (محاكاة)",
        tr=("لوحة عامل الامتلاء وتجميع الرحلات (محاكاة)", "الفرق الزمني أقل من (دقيقة)", "امتلاء كل رحلة أقل من (%)", "رحلة", "الموعد", "الركاب",
            "نسبة الامتلاء", "تنبيه دمج: رحلتان متقاربتان وغير ممتلئتين", "{n} راكب في حافلة واحدة · الفارق {gap} دقيقة", "تأكيد الدمج",
            "ملغاة (مدمجة)", "كيلومترات موفّرة بالدمج", "لا توجد رحلات مناسبة للدمج بالعتبات الحالية",
            "جدول الرحلات وأعداد الركاب بيانات محاكاة وغير مربوطة بقائمة المعتمرين. العتبات قابلة للضبط وقيمها الافتراضية تجريبية. الكيلومترات الموفّرة معلومة تشغيلية وليست مبلغًا ماليًا.",
            "رحلات نشطة", "متوسط الامتلاء"),
        eg=("كفاءة الأسطول", "مقاعد الحافلة", "نسبة الركوب الفعلي", "حافلات لازمة بهذه السعة", "السعة المطلوبة لو قلّلنا حافلة",
            "نسبة الركوب محسوبة من عمليات الحضور الحالية (محاكاة).",
            "حاسبة الطاقة (قيم افتراضية للتوضيح)", "سعر لتر الوقود (ر.س)", "استهلاك الديزل (لتر/100 كم)", "استهلاك الكهرباء (kWh/100 كم)",
            "سعر الكيلوواط ساعة (ر.س)", "رحلات الحافلة في الموسم", "مسافة الرحلة (كم)", "نسبة الكيلومترات الكهربائية في الهجين (%)",
            ("ديزل", "كهرباء", "هجين"), "تكلفة الطاقة للأسطول (ر.س)", "إضافة تقدير الانبعاثات", "كجم CO₂ لكل لتر ديزل", "كجم CO₂ لكل kWh",
            "الانبعاثات التقديرية (طن CO₂)", "فحص المدى", "سعة البطارية (kWh)", "احتياطي أمان (%)", "مسافة الرحلة (كم)", "المدى المتاح (كم)",
            "المدى كافٍ للرحلة", "المدى غير كافٍ للرحلة",
            "كل القيم افتراضية للتوضيح وليست بيانات حقيقية. في الهجين، الكيلومترات غير الكهربائية بنفس استهلاك الديزل (تبسيط). معاملات الانبعاثات تقديرية وقابلة للتعديل.",
            "فحص مبسّط: لا يشمل التكييف ولا التضاريس ولا الحمولة. القيم افتراضية والبيانات وهمية (محاكاة).",
            "الحافلات الحالية"),
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
        tn=dict(dash="📊 Dashboard", house="⚡ Smart housing", buses="🚌 Buses", fleet="🚨 Operations room", energy="🔋 Energy & fleet",
                driver="🧑‍✈️ Driver & supervisor", qr="📱 QR check-in", wa="📣 Announcements", hk="🛏️ Internal supervision", eco="🌿 Eco-Mode"),
        hk=dict(
            title="Internal supervision: room status",
            note="Room statuses and moves are demo data (simulation) and not connected to any real hotel system.",
            st=("🟢 Ready & sanitized", "🟡 Cleaning / checkout", "🔴 Fault (maintenance or A/C)"), refresh="Refresh", room="Room", new="New status", apply="Apply status",
            occ="Occupants", sp="Special case", nr="Rooms not ready", lg2=("Cleaning", "Fault"),
            w_clean="🟡 Rooms under cleaning that still have guests (not moved automatically):",
            man_t="Manual seating required", man_warn="⚠️ No suitable 🟢 room under the rules for these units. Pick a room manually.",
            why=dict(low="No ready room on floors 1-2", none="No ready room with suitable capacity or rules"),
            pick="Choose room", seat="Seat", viol="breaks the floors 1-2 rule", no_cand="No ready room fits this unit, even with the floor rule relaxed.",
            log_t="Move log", no_log="No moves", none="Awaiting room", fam="family",
            lk=dict(auto="Automatic move", manual="Manual seating", viol="Manual ⚠️ floor rule broken", pending="Awaiting manual seating", rej="Rejected (room no longer suitable)")),
        eco=dict(
            title="Eco-Mode: preview only",
            sim_note="⚠️ Simulation only: no real connection to any A/C or lighting control system, and the actual housing is not changed. All default values are illustrative.",
            s_pct="Occupancy: simulation scenario % (illustrative)", s_thr="Low-occupancy threshold % (illustrative)",
            actual="Current actual occupancy", used="Occupancy used in the simulation", sug="Floors suggested to close",
            auto="Floors to close: automatic (suggested)", s_k="Floors to close (manual)",
            s_cons="Consumption per floor (kWh/day) · illustrative", s_red="Reduction when closed % · illustrative",
            s_days="Number of days · illustrative", s_price="Price per kWh (SAR) · illustrative",
            ok_sug="Suggested: close {k} floor(s) (floors: {fl}).", k0="No floor can be emptied without breaking the housing rules.",
            not_low="Occupancy is not low (above the threshold), so there is no suggestion.",
            fl_t="Floors before and after (simulation)", before="Before", after="After", st=("Open", "Closed (suggested)"), units="unit(s) to move",
            moved="{u} unit(s) ({p} pilgrims) would move to other rooms.",
            unplaced="🔴 {u} unit(s) ({p} pilgrims) have no room that respects the rules in this choice.",
            e_title="Energy estimate (editable assumptions, illustrative)", e_kwh="Estimated reduced energy (kWh)", e_cost="Estimated matching cost (SAR)",
            e_formula="Formula: closed floors × consumption per floor × reduction % × days (× price for the cost). Figures are an estimate based on assumptions, not real data.",
            approx="The suggestion is approximate (a simple algorithm that can miss a better arrangement).",
            review="Actually closing floors needs a review of safety, guest comfort and group arrival times.",
            rules="Rules applied: family together, elderly and special cases on floors 1-2 (never closed), men/women separation, capacity, and 🟡/🔴 rooms excluded. Closing goes from the top down."),
        rl=("Sign in as", dict(hotel=("🏨 Hotel", "Housing and room occupancy"), bus=("🚌 Bus company", "Fleet, buses and check-in"),
                              mgr=("🧭 Platform manager", "All modules"))), sw="Switch role", rst="Reset demo",
        fs=("Ready", "Inspection", "Broken down"), fl_set="Bus status", fl_btn="Update status", fl_alert="🚨 A bus is down: mobile maintenance team dispatched (simulated)",
        tr=("Load factor & trip consolidation (simulated)", "Time gap under (min)", "Each trip fill under (%)", "Trip", "Time", "Pax",
            "Fill rate", "Merge alert: two close, under-filled trips", "{n} pax in one bus · gap {gap} min", "Confirm merge",
            "Cancelled (merged)", "Km saved by merging", "No trips qualify for merging at the current thresholds",
            "Trip schedule and passenger counts are simulated and not linked to the pilgrim list. Thresholds are adjustable with illustrative defaults. Km saved is an operational figure, not a money amount.",
            "Active trips", "Average fill"),
        eg=("Fleet efficiency", "Seats per bus", "Actual boarding rate", "Buses needed at this capacity", "Seats needed with one fewer bus",
            "Boarding rate is computed from current check-in operations (simulated).",
            "Energy calculator (illustrative defaults)", "Fuel price per liter (SAR)", "Diesel consumption (L/100 km)", "Electric consumption (kWh/100 km)",
            "Electricity price per kWh (SAR)", "Trips per bus per season", "Trip distance (km)", "Electric share of km in hybrid (%)",
            ("Diesel", "Electric", "Hybrid"), "Fleet energy cost (SAR)", "Add emissions estimate", "kg CO₂ per liter of diesel", "kg CO₂ per kWh",
            "Estimated emissions (tonnes CO₂)", "Range check", "Battery capacity (kWh)", "Safety reserve (%)", "Trip distance (km)", "Available range (km)",
            "Range is sufficient for the trip", "Range is not sufficient for the trip",
            "All values are illustrative defaults, not real data. In hybrid, the non-electric km use the diesel consumption (simplification). Emission factors are estimates and editable.",
            "Simplified check: excludes A/C, terrain and load. Values are illustrative and data is simulated.",
            "Current buses"),
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
def demo(seed, n=280):
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


# ---------- ENERGY LOGIC: pure functions, no Streamlit calls (to be moved to energy.py after the expo) ----------
def ceil_div(a, b):
    return -(-int(a) // int(b)) if b and b > 0 else 0


def buses_needed(total, seats):
    return ceil_div(total, seats)


def seats_for_n_buses(total, n):
    return ceil_div(total, n)


def fill_rate(boarded_n, seats):
    return boarded_n / seats if seats > 0 else 0.0


def season_energy(n_buses, trips, km, l100, kwh100, fuel_price, kwh_price, ev_share, co2_l, co2_kwh):
    km_all = n_buses * trips * km
    d_l = km_all * l100 / 100
    e_k = km_all * kwh100 / 100
    h_l, h_k = km_all * (1 - ev_share) * l100 / 100, km_all * ev_share * kwh100 / 100
    return dict(diesel=dict(cost=d_l * fuel_price, co2=d_l * co2_l),
                electric=dict(cost=e_k * kwh_price, co2=e_k * co2_kwh),
                hybrid=dict(cost=h_l * fuel_price + h_k * kwh_price, co2=h_l * co2_l + h_k * co2_kwh))


def range_check(battery_kwh, kwh100, reserve_pct, trip_km):
    rng = battery_kwh * (1 - reserve_pct / 100) / kwh100 * 100 if kwh100 > 0 else 0.0
    return rng, rng >= trip_km


def fill_pct(pax, seats):
    return pax / seats * 100 if seats > 0 else 0.0


def to_min(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def base_trips(nb, seats=45, km=25):
    plan = [("08:00", 18), ("08:20", 15), ("09:30", 44), ("10:15", 40), ("11:00", 20), ("11:25", 12), ("13:00", 38), ("14:30", 45)]
    return [dict(id=i + 1, bus=i % max(nb, 1) + 1, time=tm, pax=px_, seats=seats, km=km) for i, (tm, px_) in enumerate(plan)]


def apply_merges(trips, merged):
    out = [dict(x, cancelled=False) for x in trips]
    by = {x["id"]: x for x in out}
    for drop, keep in merged.items():
        if drop in by and keep in by and not by[keep]["cancelled"] and not by[drop]["cancelled"]:
            by[keep]["pax"] += by[drop]["pax"]
            by[drop]["pax"], by[drop]["cancelled"] = 0, True
    return out


def merge_candidates(trips, max_gap_min, max_fill_pct):
    live = sorted([x for x in trips if not x["cancelled"]], key=lambda x: to_min(x["time"]))
    out = []
    for a, b in zip(live, live[1:]):
        gap = to_min(b["time"]) - to_min(a["time"])
        if (gap < max_gap_min and fill_pct(a["pax"], a["seats"]) < max_fill_pct and fill_pct(b["pax"], b["seats"]) < max_fill_pct
                and a["pax"] + b["pax"] <= a["seats"]):
            out.append((a, b, gap))
    return out


# ---------- ROOM STATUS & MOVES: pure functions, no Streamlit calls (to be moved to housing.py after the expo) ----------
RS = ("ready", "clean", "fault")
ALL_ROOMS = [f"{f}{i + 1:02d}" for f in range(1, 11) for i in range(10)]


def room_floor(rid):
    return int(rid[:-2])


def room_cap(rid):
    return CAPS[int(rid[-2:]) - 1]


def room_status(rooms, rid):
    return rooms.get(rid, "ready")


def merged_housing(d_base, b):
    """The single place that combines the base allocation with the moves stored in box(). Bus is never touched."""
    mv = b.get("moves") or {}
    d = d_base.copy()
    if not mv:
        return d
    m = d.pid.map(mv)
    hit = m.notna()
    if hit.any():
        d.loc[hit, "room"] = m[hit]
        d.loc[hit, "floor"] = [room_floor(r) if r else 0 for r in m[hit]]
    return d


def _occupancy(d):
    occ = {}
    for p, rid, fam, g in zip(d.pid, d.room, d.family, d.gender):
        if rid:
            occ.setdefault(rid, []).append((p, fam, g))
    return occ


def _units(d, rid):
    o = d[d.room == rid]
    units = [dict(pids=list(g.pid), fam=fam, g=None, n=len(g), sp=bool(g.special.any()))
             for fam, g in o[o.family != ""].groupby("family")]
    units += [dict(pids=[r.pid], fam="", g=r.gender, n=1, sp=bool(r.special)) for _, r in o[o.family == ""].iterrows()]
    units.sort(key=lambda u: (not u["sp"], -u["n"], u["pids"][0]))
    return units


def _fits(unit, members):
    if not members:
        return True
    if unit["fam"]:
        return all(f == unit["fam"] for _, f, _ in members)
    return all(f == "" and g == unit["g"] for _, f, g in members)


def _candidates(d, rooms, occ, unit, origin, relax_floor=False):
    """Ready rooms that can take the unit, best first: [(room_id, breaks_floor_rule)]."""
    if unit["fam"]:
        rest = d[(d.family == unit["fam"]) & ~d.pid.isin(unit["pids"]) & (d.room != "")]
        rest_rooms, anchors = set(rest.room), set(int(x) for x in rest.floor)
    else:
        rest_rooms, anchors = set(), set()
    anchors = anchors or {room_floor(origin)}
    out = []
    for rid in ALL_ROOMS:
        if rid == origin or room_status(rooms, rid) != "ready":
            continue
        members = occ.get(rid, [])
        free = room_cap(rid) - len(members)
        if free < unit["n"] or not _fits(unit, members):
            continue
        viol = bool(unit["sp"]) and room_floor(rid) > 2
        if viol and not relax_floor:
            continue
        dist = min(abs(room_floor(rid) - a) for a in anchors)
        if unit["fam"]:
            key = (viol, rid not in rest_rooms, dist, free - unit["n"], rid)
        else:
            key = (viol, not members, dist, free - 1, rid)
        out.append((key, rid, viol))
    out.sort()
    return [(rid, viol) for _, rid, viol in out]


def plan_move(d, rooms, rid):
    """Moves the occupants of room rid to other ready rooms. Returns (moves {pid: room or ''}, manual units, log rows)."""
    work, moves, manual, log = d.copy(), {}, [], []
    occ = _occupancy(work)
    for u in _units(work, rid):
        c = _candidates(work, rooms, occ, u, rid)
        to = c[0][0] if c else ""
        if not c:
            why = "low" if u["sp"] and _candidates(work, rooms, occ, u, rid, True) else "none"
            manual.append(dict(u, frm=rid, why=why))
        occ[rid] = [x for x in occ.get(rid, []) if x[0] not in u["pids"]]
        if to:
            occ.setdefault(to, []).extend((p, u["fam"], u["g"] or work.loc[work.pid == p, "gender"].iloc[0]) for p in u["pids"])
        mask = work.pid.isin(u["pids"])
        work.loc[mask, "room"], work.loc[mask, "floor"] = to, (room_floor(to) if to else 0)
        for p in u["pids"]:
            moves[p] = to
        log.append(dict(frm=rid, to=to, pids=u["pids"], fam=u["fam"]))
    return moves, manual, log


# ---------- ECO-MODE (dry run only): pure functions, never write to box() ----------
TOTAL_BEDS = sum(CAPS) * 10
MAX_CLOSE = 8  # floors 1-2 are never closed (special cases live there)


def simulate_departures(d, target_pct, seed=11):
    """Dry run: removes whole families / single guests (stable random order) until occupied beds <= target_pct of all beds."""
    placed = d[d.room != ""]
    target = int(round(target_pct / 100 * TOTAL_BEDS))
    if len(placed) <= target:
        return d.copy()
    units = [list(placed[placed.family == f].pid) for f in sorted(set(placed.family) - {""})]
    units += [[p] for p in sorted(placed[placed.family == ""].pid)]
    random.Random(seed).shuffle(units)
    left, gone = len(placed), set()
    for u in units:
        if left <= target:
            break
        gone.update(u)
        left -= len(u)
    return d[~d.pid.isin(gone)].copy()


def top_floors(k):
    return list(range(10, 10 - k, -1))


def plan_consolidation(d, rooms, close_floors):
    """Dry run: tries to empty close_floors by moving their guests to other ready rooms under the housing rules. Never mutates d."""
    closed = set(close_floors)
    r2 = dict(rooms)
    for f in closed:
        for i in range(10):
            r2[f"{f}{i + 1:02d}"] = "fault"  # virtual: closed rooms cannot receive guests
    work = d.copy()
    occ, gd = _occupancy(work), dict(zip(work.pid, work.gender))
    moved_u = moved_p = un_u = un_p = 0
    from_f = {f: 0 for f in range(1, 11)}
    for f in sorted(closed, reverse=True):
        for i in range(10):
            rid = f"{f}{i + 1:02d}"
            for u in _units(work, rid):
                c = _candidates(work, r2, occ, u, rid)
                to = c[0][0] if c else ""
                occ[rid] = [x for x in occ.get(rid, []) if x[0] not in u["pids"]]
                if to:
                    occ.setdefault(to, []).extend((p, u["fam"], gd[p]) for p in u["pids"])
                    moved_u, moved_p, from_f[f] = moved_u + 1, moved_p + u["n"], from_f[f] + 1
                else:
                    un_u, un_p = un_u + 1, un_p + u["n"]
                mask = work.pid.isin(u["pids"])
                work.loc[mask, "room"], work.loc[mask, "floor"] = to, (room_floor(to) if to else 0)
    floors = [dict(floor=f, before=int((d.floor == f).sum()), after=int((work.floor == f).sum()), closed=f in closed, moves=from_f[f])
              for f in range(10, 0, -1)]
    return dict(ok=un_u == 0, closed=len(closed), moved_units=moved_u, moved_pilgrims=moved_p,
                unplaced_units=un_u, unplaced_pilgrims=un_p, floors=floors, after=work)


def suggest_close(d, rooms):
    best = 0
    for k in range(1, MAX_CLOSE + 1):
        if not plan_consolidation(d, rooms, top_floors(k))["ok"]:
            break
        best = k
    return best


def eco_estimate(k_closed, kwh_floor_day, reduction_pct, days, price):
    kwh = k_closed * kwh_floor_day * reduction_pct / 100 * days
    return kwh, kwh * price


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
    b.setdefault("merged", {})
    b.setdefault("rooms", {})
    b.setdefault("moves", {})
    b.setdefault("move_log", [])
    b.setdefault("manual", [])
    return b


def fstat(b, n):
    return b["fleet"].get(n, "check" if n % 4 == 0 else "ok")


qp = st.query_params
if "pid" in qp:  # opened by scanning a pilgrim QR code
    hq = int(qp["h"]) if str(qp.get("h", "0")).isdigit() and int(qp["h"]) < 3 else 0
    bq = box(hq)
    dq = merged_housing(alloc(demo(hq + 7)), bq)
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
        det = [(T["hotel"], T["hotels"][hq]), (T["rm"], r0.room or T["hk"]["none"]), (T["fl"], r0.floor or "-"),
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
d_base = alloc(raw)
bx = box(hi if up is None else ("up", up.name))
d = merged_housing(d_base, bx)
if s.role == "mgr":
    st.button(T["rst"], key="rst", on_click=lambda: (bx.update(checked=set(), log=[], msgs=None, fleet={}, inc=[], down_at={}, sla_min=60, rooms={}, moves={}, move_log=[], manual=[], merged={}), s.update(queue=[])))


NMAP, BMAP = d.set_index("pid")[NM], d.set_index("pid").bus


def commit(item):
    if item[0] == "scan":
        p = item[1]
        if p not in bx["checked"]:
            bx["checked"].add(p)
            bx["log"].insert(0, f"{p} · {NMAP[p]} · {T['bus']} {BMAP[p]}")
    elif item[0] == "merge":
        bx["merged"][item[2]] = item[1]
    elif item[0] == "fleet":
        _, b_, st_, kind, ts = item
        bx["fleet"][b_] = st_
        if st_ == "down":
            bx["down_at"].setdefault(b_, time.time())
        else:
            bx["down_at"].pop(b_, None)
        bx["inc"].insert(0, (ts, b_, kind, st_))
    elif item[0] == "room":
        _, rid, new, ts = item
        if new == bx["rooms"].get(rid, "ready"):
            return
        if new == "ready":
            bx["rooms"].pop(rid, None)
        else:
            bx["rooms"][rid] = new
        if new == "fault":
            mv, man, lg = plan_move(merged_housing(d_base, bx), bx["rooms"], rid)
            bx["moves"].update(mv)
            bx["manual"].extend(man)
            for row in reversed(lg):
                bx["move_log"].insert(0, (ts, "auto" if row["to"] else "pending", row["frm"], row["to"], tuple(row["pids"]), row["fam"]))
    elif item[0] == "seat":
        _, pids, rid, ts = item
        u = next((x for x in bx["manual"] if tuple(x["pids"]) == tuple(pids)), None)
        if u is None:
            return
        cur = merged_housing(d_base, bx)
        ok = dict(_candidates(cur, bx["rooms"], _occupancy(cur), u, u["frm"], True))
        if rid not in ok:
            bx["move_log"].insert(0, (ts, "rej", u["frm"], rid, tuple(pids), u["fam"]))
            return
        for p in pids:
            bx["moves"][p] = rid
        bx["manual"].remove(u)
        bx["move_log"].insert(0, (ts, "viol" if ok[rid] else "manual", u["frm"], rid, tuple(pids), u["fam"]))


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


def merge_trip(keep, drop):
    item = ("merge", keep, drop)
    if s.offline:
        if item not in s.queue:
            s.queue.append(item)
        s.flash = T["queued"].format(n=1)
    else:
        commit(item)
        s.flash = T["done_t"].format(n=1)


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
ROLE = dict(hotel=["dash", "house", "hk", "eco"], bus=["fleet", "energy", "buses", "driver", "qr", "wa"],
            mgr=["dash", "house", "hk", "eco", "buses", "fleet", "energy", "driver", "qr", "wa"])
keys = ROLE[s.role]
tb = st.tabs([T["tn"][k] for k in keys])
HID = st.container(key="hid_pages")
TB = {k: (tb[keys.index(k)] if k in keys else HID) for k in ("dash", "house", "hk", "eco", "buses", "fleet", "energy", "driver", "qr", "wa")}

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
        rs_ = room_status(bx["rooms"], rid)
        ol = "outline:2px solid #E0B400;outline-offset:1px;" if rs_ == "clean" else ""
        if rs_ == "fault":
            bg = "#B42A27"
        mk = T["hk"]["st"][RS.index(rs_)][0] if rs_ != "ready" else ""
        return f"<div class='rm' title='{rid}: {n_}/{cp} {mk}' style='background:{bg};border:{bd};{ol}'></div>"

    bld = "".join(f"<div class='fl'><span>{f}</span>" + "".join(cell(f, i) for i in range(10)) + "</div>"
                  for f in range(10, 0, -1))
    lg = "".join(f"<span class='lg'><i style='background:{c_}'></i>{t_}</span>"
                 for c_, t_ in zip(tone + ["#1B1B1B", "#E0B400", "#B42A27"], tuple(T["lg"]) + tuple(T["hk"]["lg2"])))
    st.markdown(f"### {T['heat']}")
    st.markdown(f"<div class='card'>{bld}<div style='margin-top:12px'>{lg}</div></div>", unsafe_allow_html=True)
    n_cl_, n_ft_ = list(bx["rooms"].values()).count("clean"), list(bx["rooms"].values()).count("fault")
    if n_cl_ or n_ft_:
        st.caption(f"{T['hk']['nr']}: 🟡 {n_cl_} · 🔴 {n_ft_}")

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
                 f"{T['rm']} {rw_.room or T['hk']['none']} · {T['bus']} {rw_.bus or '-'}</div></div>")
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

# ---------- ENERGY & FLEET ----------
with TB["energy"]:
    if "energy" in keys:
        G = T["eg"]
        TR = T["tr"]
        st.markdown(f"### {TR[0]}")
        mc1, mc2 = st.columns(2)
        mg_gap = mc1.slider(TR[1], 5, 90, 30, 5, key="e_mgap")
        mg_fill = mc2.slider(TR[2], 10, 100, 50, 5, key="e_mfill")
        trips = apply_merges(base_trips(nb), bx["merged"])
        live_ = [x for x in trips if not x["cancelled"]]
        km_saved = sum(x["km"] for x in trips if x["cancelled"])
        avg_fill = sum(fill_pct(x["pax"], x["seats"]) for x in live_) / len(live_) if live_ else 0
        for col, lab, v in zip(st.columns(3), (TR[14], TR[15], TR[11]), (len(live_), f"{avg_fill:.0f}%", f"{km_saved} km")):
            col.markdown(card(lab, v), unsafe_allow_html=True)
        trows = ""
        for x in trips:
            pc = fill_pct(x["pax"], x["seats"])
            low = (not x["cancelled"]) and pc < mg_fill
            colr = "#B42A27" if low else GOLD
            txt = f"{x['time']} · {T['bus']} {x['bus']} · " + (TR[10] if x["cancelled"] else f"{pc:.0f}%")
            trows += (f"<div class='row' style='grid-template-columns:90px 1fr 190px 60px;{'opacity:.45;' if x['cancelled'] else ''}'>"
                      f"<b>{TR[3]} {x['id']}</b>"
                      f"<div style='background:rgba(127,127,127,.22);border-radius:6px;height:12px'>"
                      f"<div style='width:{pc:.0f}%;height:12px;border-radius:6px;background:{colr};transition:width .6s ease'></div></div>"
                      f"<span>{txt}</span><span>{x['pax']}/{x['seats']}</span></div>")
        st.markdown(f"<div class='card' style='margin-top:12px'>{trows}</div>", unsafe_allow_html=True)
        cands = merge_candidates(trips, mg_gap, mg_fill)
        if cands:
            for ca, cb, gp in cands:
                cc1, cc2 = st.columns([4, 1])
                cc1.markdown(card(TR[7], f"{TR[3]} {ca['id']} ⟵ {TR[3]} {cb['id']}",
                                  TR[8].format(n=ca["pax"] + cb["pax"], gap=gp)), unsafe_allow_html=True)
                cc2.button(TR[9], key=f"mg_{cb['id']}", on_click=lambda k=ca["id"], d_=cb["id"]: merge_trip(k, d_))
        else:
            st.info(TR[12])
        st.caption(TR[13])

        st.markdown(f"### {G[6]}")
        g1, g2, g3, g4 = st.columns(4)
        ep = g1.slider(G[7], 1.0, 4.0, 2.0, 0.1, key="e_fp")
        el = g2.slider(G[8], 20, 60, 35, key="e_l")
        ek = g3.slider(G[9], 60, 200, 120, 5, key="e_k")
        ekp = g4.slider(G[10], 0.05, 1.0, 0.30, 0.05, key="e_kp")
        h1, h2, h3 = st.columns(3)
        et = h1.slider(G[11], 10, 200, 60, key="e_t")
        ed = h2.slider(G[12], 5, 100, 25, key="e_d")
        esh = h3.slider(G[13], 0, 100, 50, 5, key="e_sh")
        em_on = st.toggle(G[16], key="e_em")
        cl, ck = 2.7, 0.5
        if em_on:
            m1, m2 = st.columns(2)
            cl = m1.slider(G[17], 1.0, 4.0, 2.7, 0.1, key="e_cl")
            ck = m2.slider(G[18], 0.0, 1.0, 0.5, 0.05, key="e_ck")
        res = season_energy(nb, et, ed, el, ek, ep, ekp, esh / 100, cl, ck)
        modes = ("diesel", "electric", "hybrid")
        z1, z2 = st.columns(2)
        with z1:
            fe = px.bar(x=list(G[14]), y=[res[m]["cost"] for m in modes], color_discrete_sequence=[GOLD], title=G[15],
                        text=[f"{res[m]['cost']:,.0f}" for m in modes])
            fe.update_traces(textposition="outside", marker_cornerradius=6)
            fe.update_xaxes(title=None)
            fe.update_yaxes(title=None)
            show(fe)
        if em_on:
            with z2:
                fc2 = px.bar(x=list(G[14]), y=[res[m]["co2"] / 1000 for m in modes], color_discrete_sequence=[GOLD], title=G[19],
                             text=[f"{res[m]['co2'] / 1000:,.1f}" for m in modes])
                fc2.update_traces(textposition="outside", marker_cornerradius=6)
                fc2.update_xaxes(title=None)
                fc2.update_yaxes(title=None)
                show(fc2)
        st.caption(G[27])

        st.markdown(f"### {G[20]}")
        r1_, r2_, r3_ = st.columns(3)
        bk = r1_.slider(G[21], 100, 600, 300, 10, key="e_bk")
        rs = r2_.slider(G[22], 0, 50, 20, key="e_rs")
        td = r3_.slider(G[23], 5, 300, ed, key="e_td")
        rg, okr = range_check(bk, ek, rs, td)
        st.markdown(card(G[24], f"{rg:,.0f}", f"{td} km"), unsafe_allow_html=True)
        (st.success if okr else st.error)(G[25] if okr else G[26])
        st.caption(G[28])

# ---------- INTERNAL SUPERVISION (ROOM STATUS) ----------
RCOL = dict(ready=("#E7CF8A", "#10343A"), clean=("#E0B400", "#10343A"), fault=("#B42A27", "#FFFFFF"))


def room_set(rid, new):
    item = ("room", rid, new, time.strftime("%H:%M:%S"))
    if s.offline:
        s.queue.append(item)
        s.flash = T["queued"].format(n=1)
    else:
        commit(item)
        s.flash = T["done_t"].format(n=1)


def seat_unit(u, rid):
    item = ("seat", tuple(u["pids"]), rid, time.strftime("%H:%M:%S"))
    if s.offline:
        s.queue.append(item)
        s.flash = T["queued"].format(n=1)
    else:
        commit(item)
        s.flash = T["done_t"].format(n=1)


def names_of(pids):
    return ", ".join(str(NMAP.get(p, p)) for p in pids[:3]) + ("…" if len(pids) > 3 else "")


with TB["hk"]:
    if "hk" in keys:
        HK = T["hk"]
        st.markdown(f"### {HK['title']}")
        st.caption(HK["note"])
        st.button(HK["refresh"], key="hk_refresh")
        n_c_, n_f_ = list(bx["rooms"].values()).count("clean"), list(bx["rooms"].values()).count("fault")
        for col, lab, v in zip(st.columns(3), HK["st"], (len(ALL_ROOMS) - n_c_ - n_f_, n_c_, n_f_)):
            col.markdown(card(lab, v), unsafe_allow_html=True)
        h1, h2, h3 = st.columns(3)
        hf = h1.selectbox(T["fl"], range(1, 11), key="hk_fl")
        hr = h2.selectbox(HK["room"], [f"{hf}{i + 1:02d}" for i in range(10)], key=f"hk_rm_{hf}",
                          format_func=lambda r: f"{r} · {HK['st'][RS.index(room_status(bx['rooms'], r))]}")
        hn = h3.selectbox(HK["new"], RS, format_func=lambda c: HK["st"][RS.index(c)], key="hk_new")
        st.button(HK["apply"], key="hk_apply", on_click=lambda: room_set(hr, hn))
        occ_ = d[d.room != ""].groupby("room").size()
        spr_ = set(d[(d.room != "") & d.special].room)
        rws = ""
        for i in range(10):
            rid_ = f"{hf}{i + 1:02d}"
            rs_ = room_status(bx["rooms"], rid_)
            rws += (f"<div class='row'><b>{rid_}</b><span class='chip' style='background:{RCOL[rs_][0]};color:{RCOL[rs_][1]}'>{HK['st'][RS.index(rs_)]}</span>"
                    f"<span>{HK['occ']} {int(occ_.get(rid_, 0))}/{CAPS[i]}</span><span>{HK['sp'] if rid_ in spr_ else ''}</span></div>")
        st.markdown(f"<div class='card' style='margin-top:12px'>{rws}</div>", unsafe_allow_html=True)
        cl_occ_ = sorted(r for r, v in bx["rooms"].items() if v == "clean" and int(occ_.get(r, 0)) > 0)
        if cl_occ_:
            st.warning(f"{HK['w_clean']} {', '.join(cl_occ_)}")
        if bx["manual"]:
            st.markdown(f"### {HK['man_t']}")
            st.warning(HK["man_warn"])
            for u_ in list(bx["manual"]):
                opts_ = _candidates(d, bx["rooms"], _occupancy(d), u_, u_["frm"], True)
                fam_ = f" · {HK['fam']} {html.escape(u_['fam'])}" if u_["fam"] else ""
                st.markdown(card(f"{u_['frm']}{fam_} · {len(u_['pids'])}", html.escape(names_of(u_["pids"])), HK["why"][u_["why"]]), unsafe_allow_html=True)
                if opts_:
                    pa_, pb_ = st.columns([3, 1])
                    pk_ = pa_.selectbox(HK["pick"], [r for r, _ in opts_], key=f"hk_pick_{u_['pids'][0]}",
                                        format_func=lambda r, o=dict(opts_): f"{r} · {T['fl']} {room_floor(r)}" + (f" ⚠️ {HK['viol']}" if o[r] else ""))
                    pb_.button(HK["seat"], key=f"hk_seat_{u_['pids'][0]}", on_click=lambda u=u_, r=pk_: seat_unit(u, r))
                else:
                    st.info(HK["no_cand"])
        st.markdown(f"### {HK['log_t']}")
        lrows = ""
        for ts_, kind_, frm_, to_, pids_, fam_k in bx["move_log"][:10]:
            sty_ = "background:rgba(180,42,39,.14);color:#B42A27;font-weight:700;" if kind_ in ("pending", "rej") else ""
            lrows += (f"<div class='row' style='grid-template-columns:80px 120px 1fr 170px;border-radius:8px;padding:4px 8px;{sty_}'>"
                      f"<span>{ts_}</span><span dir='ltr'>{frm_} → {to_ or '—'}</span><span>{html.escape(names_of(pids_))}</span><span>{HK['lk'][kind_]}</span></div>")
        st.markdown(f"<div class='card'>{lrows or '<small>' + HK['no_log'] + '</small>'}</div>", unsafe_allow_html=True)

# ---------- ECO-MODE TAB (preview only) ----------
@st.cache_data
def eco_compute(dd, rooms_items, sim_pct, eligible, auto, manual_k):
    rooms_ = dict(rooms_items)
    sim = simulate_departures(dd, sim_pct)
    sug = suggest_close(sim, rooms_) if eligible else 0
    k = sug if auto else manual_k
    plan = {a: b for a, b in plan_consolidation(sim, rooms_, top_floors(k)).items() if a != "after"}
    return dict(sim_n=int((sim.room != "").sum()), sug=sug, k=k, plan=plan)


with TB["eco"]:
    if "eco" in keys:
        EC = T["eco"]
        st.markdown(f"### {EC['title']}")
        st.warning(EC["sim_note"])
        act_pct = int(round(int((d.room != "").sum()) / TOTAL_BEDS * 100))
        ea, eb = st.columns(2)
        pct_in = ea.slider(EC["s_pct"], 10, 100, 50, 5, key="eco_pct")
        thr = eb.slider(EC["s_thr"], 10, 100, 60, 5, key="eco_thr")
        use_actual = pct_in >= act_pct
        used_pct = act_pct if use_actual else pct_in
        eco_auto = st.toggle(EC["auto"], value=True, key="eco_auto")
        eco_mk = st.slider(EC["s_k"], 0, MAX_CLOSE, 2, key="eco_k", disabled=eco_auto)
        er = eco_compute(d, tuple(sorted(bx["rooms"].items())), 100 if use_actual else pct_in, used_pct < thr, eco_auto, eco_mk)
        pl = er["plan"]
        for col, lab, v, ex in zip(st.columns(3), (EC["actual"], EC["used"], EC["sug"]), (f"{act_pct}%", f"{used_pct}%", er["sug"]), ("", f"{er['sim_n']}", "")):
            col.markdown(card(lab, v, ex), unsafe_allow_html=True)
        if used_pct >= thr:
            st.info(EC["not_low"])
        elif er["sug"] > 0:
            st.success(EC["ok_sug"].format(k=er["sug"], fl=", ".join(str(x) for x in top_floors(er["sug"]))))
        else:
            st.info(EC["k0"])
        if er["k"] > 0:
            st.markdown(f"### {EC['fl_t']}")
            frs_ = ""
            for r_ in pl["floors"]:
                sty_ = "background:#F3EAD3;color:#10343A;border-radius:8px;padding:4px 8px;" if r_["closed"] else ""
                mv_ = f"{r_['moves']} {EC['units']}" if r_["moves"] else ""
                frs_ += (f"<div class='row' style='{sty_}'><b>{T['fl']} {r_['floor']}</b><span>{EC['before']} {r_['before']} · {EC['after']} {r_['after']}</span>"
                         f"<span>{EC['st'][1 if r_['closed'] else 0]}</span><span>{mv_}</span></div>")
            st.markdown(f"<div class='card'>{frs_}</div>", unsafe_allow_html=True)
            st.markdown(EC["moved"].format(u=pl["moved_units"], p=pl["moved_pilgrims"]))
            if pl["unplaced_units"]:
                st.error(EC["unplaced"].format(u=pl["unplaced_units"], p=pl["unplaced_pilgrims"]))
        st.markdown(f"### {EC['e_title']}")
        g1, g2, g3, g4 = st.columns(4)
        e_cons = g1.slider(EC["s_cons"], 100, 1500, 300, 50, key="eco_cons")
        e_red = g2.slider(EC["s_red"], 10, 100, 60, 5, key="eco_red")
        e_days = g3.slider(EC["s_days"], 1, 30, 7, key="eco_days")
        e_price = g4.slider(EC["s_price"], 0.05, 1.0, 0.30, 0.05, key="eco_price")
        e_kwh, e_cost = eco_estimate(er["k"], e_cons, e_red, e_days, e_price)
        for col, lab, v, unit in zip(st.columns(2), (EC["e_kwh"], EC["e_cost"]), (f"{e_kwh:,.0f}", f"{e_cost:,.0f}"), ("kWh", "SAR")):
            col.markdown(card(lab, v, unit), unsafe_allow_html=True)
        st.caption(EC["e_formula"])
        st.caption(EC["approx"])
        st.caption(EC["review"])
        st.caption(EC["rules"])

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