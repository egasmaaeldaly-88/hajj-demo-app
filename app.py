import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time

# --- 1. إعدادات الصفحة والهوية البصرية ---
st.set_page_config(
    page_title="منصة التسكين والتفويج الذكي | Smart Pilgrim Systems",
    page_icon="🕋",
    layout="wide"
)

# Custom CSS للألوان الجذابة والتصميم المحترف
st.markdown("""
    <style>
    .main { background-color: #f4f6f8; }
    .stButton>button {
        background-color: #0d5c3a;
        color: white;
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 24px;
        width: 100%;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-right: 5px solid #d4af37;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. الشريط الجانبي (Sidebar) ---
st.sidebar.image("https://img.icons8.com/color/96/kaaba.png", width=70)
st.sidebar.title("منصة التسكين الذكي")
st.sidebar.subheader("إدارة الحملات والتفويج")
selected_hotel = st.sidebar.selectbox("اختر الفندق / المخيم:", ["فندق أنوار المدينة", "مخيمات منى (أ)", "فندق أبراج الساعة"])
st.sidebar.markdown("---")
st.sidebar.info("💡 **نصيحة للمشرف:** اضغط على زر التسكين التلقائي لإعادة توزيع العائلات وكبار السن في الأدوار المخصصة.")

# --- 3. الهيدر الرئيسي ---
col_logo, col_title = st.columns([1, 6])
with col_title:
    st.title("🕋 نظام إدارة التفويج والتسكين الآلي")
    st.caption("حلول برمجية مخصصة لشركات الحج والعمرة | Powered by Python & Django Architecture")

st.markdown("---")

# --- 4. مؤشرات الأداء الحية (Live KPIs) ---
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown("""
        <div class="metric-card">
            <h4 style="color: #666; margin:0;">إجمالي الحجاج</h4>
            <h2 style="color: #0d5c3a; margin:5px 0;">1,250</h2>
            <p style="color: green; font-size:12px; margin:0;">▲ 100% مكتمل البيانات</p>
        </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown("""
        <div class="metric-card">
            <h4 style="color: #666; margin:0;">الغرف المشغولة</h4>
            <h2 style="color: #0d5c3a; margin:5px 0;">312 / 330</h2>
            <p style="color: #d4af37; font-size:12px; margin:0;">نسبة الإشغال: 94.5%</p>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown("""
        <div class="metric-card">
            <h4 style="color: #666; margin:0;">كبار السن والحالات الخاصة</h4>
            <h2 style="color: #c0392b; margin:5px 0;">84</h2>
            <p style="color: #c0392b; font-size:12px; margin:0;">مخصص لهم أدوار سفلية</p>
        </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown("""
        <div class="metric-card">
            <h4 style="color: #666; margin:0;">حافلات التفويج</h4>
            <h2 style="color: #0d5c3a; margin:5px 0;">25 حافلة</h2>
            <p style="color: green; font-size:12px; margin:0;">مرفوقة بمشرف لكل حافلة</p>
        </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

# --- 5. منطقة التجربة التفاعلية (Interactive Demo Section) ---
tab1, tab2, tab3 = st.tabs(["⚡ التسكين الآلي الفوري", "📊 تحليل توزيع الغرف", "🚌 خريطة حركة الأتوبيسات"])

with tab1:
    st.subheader("تسكين الحجاج بناءً على العائلات والحالات الصحية")
    
    col_btn, col_upload = st.columns([1, 2])
    with col_upload:
        uploaded_file = st.file_uploader("رفع كشف الحجاج (Excel/CSV):", type=["csv", "xlsx"])
    
    with col_btn:
        st.write("أو جرب الخوارزمية الآن:")
        run_btn = st.button("🚀 تشغيل التسكين الذكي الآن")

    # بيانات افتراضية للعرض
    data = {
        "اسم الحاج": ["أحمد محمود والأسرة", "فاطمة السيد", "محمد علي (كرسي متحرك)", "عمر الخالد", "خالد عبدالله والأسرة", "سارة إبراهيم"],
        "النوع": ["عائلة (4)", "فرادى - نساء", "حالة خاصة", "فرادى - رجال", "عائلة (3)", "فرادى - نساء"],
        "الفندق": [selected_hotel] * 6,
        "رقم الغرفة المقترح": ["101 - 102", "305", "103 (دور أرضي)", "401", "104 - 105", "305"],
        "حالة التسكين": ["تم الجمع تلقائياً", "مؤكد", "أولوية قريبة من المصعد", "مؤكد", "تم الجمع تلقائياً", "مؤكد"]
    }
    df = pd.DataFrame(data)

    if run_btn:
        with st.spinner('جاري معالجة الشروط وتوزيع الغرف لتقليل الهدر...'):
            time.sleep(1.5)
        st.success("✅ تم تسكين 1,250 حاج في 4.2 ثانية فقط دون أي تعارضات!")
        st.dataframe(df, use_container_width=True)
        st.download_button("📥 تحميل كشف الغرف والباركود (Excel)", data=df.to_csv().encode('utf-8'), file_name="rooms_allocation.csv")
    else:
        st.dataframe(df, use_container_width=True)

with tab2:
    st.subheader("تحليلات استغلال الطاقة الاستيعابية للفنادق")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # رسم بياني لتوزيع الغرف
        room_types = pd.DataFrame({
            'نوع الغرفة': ['ثنائي', 'ثلاثي', 'رباعي', 'جناح عائلي'],
            'العدد': [50, 120, 100, 42]
        })
        fig1 = px.pie(room_types, values='العدد', names='نوع الغرفة', title="توزيع أنواع الغرف المتاحة", color_discrete_sequence=px.colors.sequential.Greens_r)
        st.plotly_chart(fig1, use_container_width=True)
        
    with col_chart2:
        # رسم بياني للجنسيات أو التوزيع
        dept_data = pd.DataFrame({
            'المرحلة': ['الوصول للجمارك', 'في الحافلات', 'تم التسكين بالفندق', 'في الحرم'],
            'عدد الحجاج': [50, 200, 850, 150]
        })
        fig2 = px.bar(dept_data, x='المرحلة', y='عدد الحجاج', title="متابعة التدفق الحي للحجاج (Real-Time Flow)", color_discrete_sequence=['#0d5c3a'])
        st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("متابعة حافلات التفويج بين مكة والمدينة والمشاعر")
    # خريطة افتراضية لمواقع الحافلات
    map_data = pd.DataFrame({
        'lat': [21.4225, 21.3549, 24.4672, 21.4133],
        'lon': [39.8262, 39.9841, 39.6112, 39.8933],
        'اسم الحافلة': ['حافلة 101 - مكة', 'حافلة 102 - منى', 'حافلة 103 - المدينة', 'حافلة 104 - عرفة']
    })
    st.map(map_data, zoom=7)

# --- 6. الفوتر التسويقي (Call to Action) ---
st.markdown("---")
st.markdown("""
    <div style="text-align: center; background-color: #0d5c3a; color: white; padding: 20px; border-radius: 10px;">
        <h3>هل تحتاج لوحة تحكم مخصصة لشركتك في موسم الحج والعمرة؟</h3>
        <p>نحن نوفر حلولاً برمجية متكاملة (Django / Custom Dashboards / APIs Integration) تناسب احتياجاتكم تماماً.</p>
        <h4 style="color: #d4af37;">تواصل معنا فوراً لتجربة النظام على أنظمتكم الحالية!</h4>
    </div>
""", unsafe_allow_html=True)