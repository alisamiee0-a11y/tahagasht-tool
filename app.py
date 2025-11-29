import streamlit as st
import json
import google.generativeai as genai
import time

# ---------------------------------------------------------
# 1. تنظیمات صفحه و تزریق CSS حرفه‌ای (تم دشبورد تیره)
# ---------------------------------------------------------
st.set_page_config(page_title="دستیار هوشمند طاهاگشت", layout="wide", page_icon="💎")

# تعریف استایل‌های سفارشی (Dark Glassmorphism Theme)
CUSTOM_CSS = """
<style>
    /* ایمپورت فونت وزیرمتن */
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');

    /* 1. تنظیمات کلی بدنه (تم تیره) */
    html, body, [class*="css"] {
        font-family: 'Vazirmatn', sans-serif !important;
        direction: rtl;
    }
    
    /* حذف هدر و فوتر پیش‌فرض */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* پس‌زمینه گرادینت تیره (Deep Navy) */
    .stApp {
        background: radial-gradient(circle at top left, #1e293b, #0f172a);
        background-attachment: fixed;
    }

    /* 2. استایل کارت‌ها (Glassmorphism) */
    .glass-card {
        background: rgba(30, 41, 59, 0.6); /* رنگ سرمه‌ای تیره و شفاف */
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
    }

    /* 3. تایپوگرافی */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    p, label, span, div {
        color: #e2e8f0 !important; /* رنگ متن خاکستری روشن */
    }
    
    /* تایتل‌های رنگی */
    .gradient-text {
        background: linear-gradient(45deg, #f59e0b, #fbbf24);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
    }

    /* 4. استایل اینپوت‌ها (فیلدها) */
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        background-color: rgba(15, 23, 42, 0.8) !important;
        color: white !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        height: 50px;
        font-size: 16px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #f59e0b !important;
        box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.2);
    }

    /* 5. استایل دکمه‌ها (مشابه دکمه آبی عکس) */
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%); /* آبی روشن مشابه عکس */
        color: white !important;
        border-radius: 12px;
        height: 55px;
        font-weight: bold;
        font-size: 18px;
        border: none;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #60a5fa 0%, #3b82f6 100%);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(37, 99, 235, 0.6);
    }

    /* 6. آپلودر فایل */
    .stFileUploader > div > div > button {
        display: none; /* مخفی کردن دکمه پیش‌فرض زشت */
    }
    .stFileUploader {
        background-color: rgba(15, 23, 42, 0.5);
        border: 2px dashed #475569;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
    }
    
    /* 7. استایل تب‌ها و نتایج */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        color: #94a3b8;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #f59e0b !important; /* تب فعال طلایی */
        color: black !important;
        font-weight: bold;
    }
    
    /* فیلدهای متنی بزرگ (Text Area) */
    .stTextArea > div > div > textarea {
        background-color: rgba(15, 23, 42, 0.9) !important;
        color: #e2e8f0 !important;
        border: 1px solid #334155 !important;
        border-radius: 12px;
        font-family: 'Courier New', monospace !important; /* فونت مناسب کد/متن خام */
    }
    
    /* Expander ها */
    div[data-testid="stExpander"] {
        background-color: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
        color: white;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. منطق برنامه (بدون تغییر)
# ---------------------------------------------------------
def analyze_pdf_directly(file_bytes, year, api_key):
    genai.configure(api_key=api_key)
    system_instruction = f"""
    You are an AI assistant for "TahaGasht" travel agency. Target Year: {year}
    Task: Look at the provided PDF document. Extract:
    1. Tour Title (Persian)
    2. Flight departure date (Convert extracted Persian date to Gregorian YYYY-MM-DD).
    3. Services Section (خدمات): Extract the full text.
    4. Flight Details Section (اطلاعات پرواز): Extract the full text.
    5. Daily Itinerary (Map each day to a Gregorian date).
    6. Full Clean Text: Extract all text content.
    
    Output Format: ONLY valid JSON.
    Structure: {{ "tour_title": "string", "flight_info": {{ "shamsi": "string", "gregorian": "YYYY-MM-DD" }}, "services_text": "string", "flight_details_text": "string", "full_pdf_text": "string", "itinerary": [ {{ "day_number": 1, "date_gregorian": "YYYY-MM-DD", "day_title": "string", "content_summary": "string" }} ] }}
    """
    candidate_models = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash-exp", "gemini-1.5-pro-latest"]
    pdf_part = {"mime_type": "application/pdf", "data": file_bytes}
    last_error = None
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction, generation_config={"response_mime_type": "application/json"})
            response = model.generate_content(["Extract tour details.", pdf_part])
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str: time.sleep(2); continue
            if "404" in error_str: continue
            last_error = e; continue
    return f"ERROR: {str(last_error)}"

# ---------------------------------------------------------
# 3. رابط کاربری (Layout مدرن و تیره)
# ---------------------------------------------------------

# --- هدر مینیمال و شیک ---
st.markdown("""
<div style="text-align: center; margin-bottom: 40px; padding-top: 20px;">
    <h1 style="font-size: 3rem; margin-bottom: 10px;">دستیار هوشمند <span class="gradient-text">طاهاگشت</span></h1>
    <p style="font-size: 1.2rem; color: #94a3b8 !important;">تبدیل حرفه‌ای پکیج‌های مسافرتی با قدرت هوش مصنوعی</p>
</div>
""", unsafe_allow_html=True)

# --- چیدمان شبکه‌ای (Grid) ---
# ستون‌بندی اصلی برای وسط‌چین کردن محتوا
col_spacer1, col_main, col_spacer2 = st.columns([1, 6, 1])

with col_main:
    # --- کارت ورودی (Input Card) ---
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    # ردیف اول: عنوان کارت + آیکون
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <span style="font-size: 24px; margin-left: 10px;">📂</span>
        <h3 style="margin: 0; font-size: 20px;">بارگذاری و تنظیمات</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # فرم ورودی دو ستونه
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<p style="font-size: 14px; margin-bottom: 5px; color: #cbd5e1 !important;">📅 سال برگزاری تور</p>', unsafe_allow_html=True)
        target_year = st.number_input("year_input", min_value=1403, max_value=1410, value=1404, label_visibility="collapsed")
    with c2:
        st.markdown('<p style="font-size: 14px; margin-bottom: 5px; color: #cbd5e1 !important;">🔑 کلید دسترسی (API)</p>', unsafe_allow_html=True)
        try:
            api_key = st.secrets["GOOGLE_API_KEY"]
            st.success("✅ متصل به سرور")
        except:
            api_key = st.text_input("api_input", type="password", placeholder="کلید را وارد کنید...", label_visibility="collapsed")

    # آپلودر
    st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("فایل پکیج را انتخاب کنید", type="pdf")
    
    # دکمه اکشن (بزرگ و برجسته)
    st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
    if uploaded_file:
        process_btn = st.button("🚀 شروع پردازش هوشمند")
    else:
        st.info("لطفاً فایل PDF پکیج را آپلود کنید تا دکمه فعال شود.")
        process_btn = False
        
    st.markdown('</div>', unsafe_allow_html=True) # پایان کارت ورودی


    # --- بخش نمایش نتایج (فقط وقتی دکمه زده شد ظاهر می‌شود) ---
    if process_btn and uploaded_file:
        if not api_key:
            st.error("❌ کلید API یافت نشد.")
        else:
            with st.spinner('💎 در حال آنالیز سند و استخراج داده‌ها...'):
                try:
                    file_bytes = uploaded_file.getvalue()
                    raw_response = analyze_pdf_directly(file_bytes, target_year, api_key)
                    data = json.loads(raw_response)
                    
                    # --- کارت نتایج ---
                    st.markdown('<div class="glass-card" style="border-top: 4px solid #f59e0b;">', unsafe_allow_html=True)
                    
                    # هدر نتایج
                    tour_title = data.get('tour_title', 'عنوان یافت نشد')
                    flight_shamsi = data.get('flight_info', {}).get('shamsi', '-')
                    flight_greg = data.get('flight_info', {}).get('gregorian', '-')
                    
                    st.markdown(f"""
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h2 style="color: #f59e0b !important; font-size: 26px;">{tour_title}</h2>
                        <div style="background: rgba(255,255,255,0.1); display: inline-block; padding: 5px 15px; border-radius: 20px; margin-top: 10px;">
                            <span style="color: #94a3b8 !important; font-size: 14px;">تاریخ پرواز:</span>
                            <span style="color: white !important; font-weight: bold; margin-right: 5px;">{flight_shamsi}</span>
                            <span style="color: #64748b !important; font-size: 12px; margin-right: 5px;">({flight_greg})</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # تب‌ها با استایل تیره
                    tab1, tab2, tab3 = st.tabs(["📅 برنامه روزانه", "✈️ خدمات و پرواز", "📝 متن کامل"])

                    with tab1:
                        final_text = ""
                        for day in data.get('itinerary', []):
                            d_date = day.get('date_gregorian', '-')
                            d_title = day.get('day_title', '')
                            d_content = day.get('content_summary', '')
                            
                            with st.expander(f"روز {day.get('day_number')}: {d_title}", expanded=False):
                                st.write(d_content)
                                st.caption(f"تاریخ میلادی: {d_date}")
                            
                            final_text += f"📅 {d_date} | {d_title}\n{d_content}\n\n"
                        
                        st.markdown('<p style="color: #f59e0b !important; margin-top: 20px;">👇 متن آماده کپی:</p>', unsafe_allow_html=True)
                        st.text_area("copy_itinerary", value=final_text, height=400, label_visibility="collapsed")

                    with tab2:
                        col_srv, col_flt = st.columns(2)
                        with col_srv:
                            st.markdown('<h4 style="color:white;">لیست خدمات</h4>', unsafe_allow_html=True)
                            st.text_area("srv_txt", value=data.get('services_text', ''), height=300, label_visibility="collapsed")
                        with col_flt:
                            st.markdown('<h4 style="color:white;">جزئیات پرواز</h4>', unsafe_allow_html=True)
                            st.text_area("flt_txt", value=data.get('flight_details_text', ''), height=300, label_visibility="collapsed")

                    with tab3:
                        st.text_area("full_pdf", value=data.get('full_pdf_text', ''), height=500, label_visibility="collapsed")

                    st.markdown('</div>', unsafe_allow_html=True) # پایان کارت نتایج
                    st.balloons()

                except Exception as e:
                    st.error(f"خطا: {e}")
