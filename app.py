import streamlit as st
import json
import google.generativeai as genai
import time

# ---------------------------------------------------------
# 1. تنظیمات صفحه و تزریق CSS حرفه‌ای
# ---------------------------------------------------------
st.set_page_config(page_title="دستیار هوشمند طاهاگشت", layout="centered", page_icon="✈️")

# تعریف استایل‌های سفارشی (CSS)
CUSTOM_CSS = """
<style>
    /* ایمپورت فونت وزیرمتن */
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');

    /* تنظیمات کلی بدنه */
    html, body, [class*="css"] {
        font-family: 'Vazirmatn', sans-serif !important;
        direction: rtl;
    }
    
    /* مخفی کردن هدر و فوتر پیش‌فرض استریم‌لیت */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* رنگ پس‌زمینه کل صفحه */
    .stApp {
        background-color: #f8fafc;
    }

    /* استایل کارت‌ها (باکس‌های سفید) */
    .custom-card {
        background-color: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
    }
    
    /* هدر سفارشی بالای صفحه */
    .main-header {
        background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
        color: white;
        padding: 2rem;
        border-radius: 0 0 20px 20px;
        margin-top: -6rem; /* کشیدن به بالاترین حد */
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.2);
    }
    
    .main-header h1 {
        font-weight: 800;
        font-size: 2.5rem;
        margin: 0;
        color: #f59e0b; /* رنگ طلایی */
    }
    
    .main-header p {
        font-weight: 300;
        opacity: 0.9;
        font-size: 1.1rem;
    }

    /* استایل دکمه‌ها */
    .stButton > button {
        width: 100%;
        background-color: #0f172a;
        color: white;
        border-radius: 10px;
        height: 50px;
        font-weight: bold;
        border: none;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #f59e0b; /* تغییر رنگ به نارنجی در هاور */
        color: black;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(245, 158, 11, 0.3);
    }

    /* استایل اینپوت‌ها و تکست‌اریا */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 10px;
        direction: rtl;
        text-align: right;
    }

    /* استایل تب‌ها */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 10px 10px 0 0;
        border: 1px solid #e2e8f0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0f172a !important;
        color: white !important;
    }

    /* استایل اکسپندرها */
    div[data-testid="stExpander"] {
        background-color: white;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. منطق برنامه (Back-End Logic)
# ---------------------------------------------------------

# --- تابع اتصال به Gemini ---
def analyze_pdf_directly(file_bytes, year, api_key):
    genai.configure(api_key=api_key)
    
    system_instruction = f"""
    You are an AI assistant for "TahaGasht" travel agency.
    Target Year: {year}
    
    Task: Look at the provided PDF document. Extract the following sections clearly:
    1. Tour Title (Persian)
    2. Flight departure date (Convert extracted Persian date to Gregorian YYYY-MM-DD).
    3. Services Section (خدمات): Extract the full text.
    4. Flight Details Section (اطلاعات پرواز): Extract the full text.
    5. Daily Itinerary (Map each day to a Gregorian date).
    6. Full Clean Text: Extract all text content.
    
    Output Format: ONLY valid JSON.
    Structure:
    {{
      "tour_title": "string",
      "flight_info": {{ "shamsi": "string", "gregorian": "YYYY-MM-DD" }},
      "services_text": "string",
      "flight_details_text": "string",
      "full_pdf_text": "string",
      "itinerary": [
        {{ "day_number": 1, "date_gregorian": "YYYY-MM-DD", "day_title": "string", "content_summary": "string" }}
      ]
    }}
    """

    candidate_models = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash-exp", "gemini-1.5-pro-latest"]
    
    pdf_part = {"mime_type": "application/pdf", "data": file_bytes}
    
    last_error = None
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction,
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content(["Extract tour details.", pdf_part])
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str: time.sleep(2); continue
            if "404" in error_str: continue
            last_error = e; continue

    return f"ERROR: {str(last_error)}"

# ---------------------------------------------------------
# 3. رابط کاربری (Front-End Layout)
# ---------------------------------------------------------

# --- هدر سفارشی ---
st.markdown("""
<div class="main-header">
    <h1>دستیار هوشمند طاهاگشت</h1>
    <p>تبدیل پکیج‌های PDF به محتوای وب‌سایت در چند ثانیه</p>
</div>
""", unsafe_allow_html=True)

# --- کانتینر اصلی ---
main_container = st.container()

with main_container:
    # استفاده از ستون‌بندی برای ایجاد فضای سفید (Margin)
    col_l, col_center, col_r = st.columns([1, 8, 1])
    
    with col_center:
        # کارت تنظیمات
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        st.markdown("### ⚙️ قدم اول: تنظیمات فایل")
        
        c1, c2 = st.columns(2)
        with c1:
            target_year = st.number_input("سال برگزاری تور", min_value=1403, max_value=1410, value=1404)
        with c2:
            # مدیریت کلید API
            try:
                api_key = st.secrets["GOOGLE_API_KEY"]
                st.success("✅ کلید فعال است")
            except:
                api_key = st.text_input("کلید API گوگل", type="password", placeholder="کلید را وارد کنید")
        
        st.markdown("<br>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("فایل پکیج (PDF) را اینجا رها کنید", type="pdf")
        
        if uploaded_file:
            process_btn = st.button("✨ شروع پردازش هوشمند")
        else:
            st.info("لطفاً فایل PDF را بارگذاری کنید.")
            process_btn = False
            
        st.markdown('</div>', unsafe_allow_html=True)

        # --- بخش نمایش نتایج ---
        if process_btn and uploaded_file:
            if not api_key:
                st.error("کلید API وارد نشده است.")
            else:
                with st.spinner('⏳ هوش مصنوعی در حال مطالعه فایل شماست...'):
                    try:
                        file_bytes = uploaded_file.getvalue()
                        raw_response = analyze_pdf_directly(file_bytes, target_year, api_key)
                        data = json.loads(raw_response)
                        
                        # کارت نتیجه
                        st.markdown('<div class="custom-card" style="border-top: 5px solid #f59e0b;">', unsafe_allow_html=True)
                        
                        # عنوان و پرواز
                        st.markdown(f"<h2 style='text-align:center; color:#0f172a;'>{data.get('tour_title', 'عنوان پیدا نشد')}</h2>", unsafe_allow_html=True)
                        fl = data.get('flight_info', {})
                        st.markdown(f"<p style='text-align:center; color:#64748b; font-size:1.1rem;'>🛫 تاریخ پرواز: <b>{fl.get('shamsi', '-')}</b> (میلادی: {fl.get('gregorian', '-')})</p>", unsafe_allow_html=True)
                        st.divider()

                        # تب‌ها
                        tab1, tab2, tab3 = st.tabs(["📅 برنامه سفر", "📋 خدمات و پرواز", "📄 متن کامل"])

                        with tab1:
                            final_text = ""
                            for day in data.get('itinerary', []):
                                d_date = day.get('date_gregorian', '-')
                                d_title = day.get('day_title', '')
                                d_content = day.get('content_summary', '')
                                
                                with st.expander(f"روز {day.get('day_number')}: {d_title}", expanded=False):
                                    st.write(d_content)
                                    st.caption(f"تاریخ: {d_date}")
                                
                                final_text += f"📅 {d_date} | {d_title}\n{d_content}\n\n"
                            
                            st.markdown("### متن نهایی جهت کپی:")
                            st.text_area("copy_area_1", value=final_text, height=400, label_visibility="collapsed")

                        with tab2:
                            c_s, c_f = st.columns(2)
                            with c_s:
                                st.info("خدمات تور")
                                st.text_area("services", value=data.get('services_text', ''), height=300)
                            with c_f:
                                st.warning("اطلاعات پرواز")
                                st.text_area("flights", value=data.get('flight_details_text', ''), height=300)

                        with tab3:
                            st.text_area("full_text", value=data.get('full_pdf_text', ''), height=500)

                        st.markdown('</div>', unsafe_allow_html=True)
                        st.success("✅ عملیات با موفقیت انجام شد.")

                    except json.JSONDecodeError:
                        st.error("خطا در خواندن پاسخ هوش مصنوعی. لطفاً دوباره تلاش کنید.")
                    except Exception as e:
                        st.error(f"خطای سیستمی: {e}")
