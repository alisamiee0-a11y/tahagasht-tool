import streamlit as st
import json
import google.generativeai as genai
import time

# --- تنظیمات صفحه ---
st.set_page_config(page_title="ابزار پکیج طاهاگشت", layout="wide", page_icon="💎")

# استایل راست‌چین
st.markdown("""
<style>
    .stTextArea textarea { direction: rtl; }
    div[data-testid="stExpander"] div[role="button"] p { direction: rtl; }
    .stAlert { direction: rtl; }
</style>
""", unsafe_allow_html=True)

st.title("💎 تبدیل هوشمند پکیج (موتور ویژن پایدار)")
st.markdown("این نسخه از **چشم‌های هوش مصنوعی** استفاده می‌کند و می‌تواند فایل‌های اسکن‌شده و عکس‌دار را هم بخواند.")

# --- سایدبار ---
with st.sidebar:
    st.header("تنظیمات ورودی")
    target_year = st.number_input("سال برگزاری تور (شمسی)", min_value=1403, max_value=1410, value=1404)
    
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ کلید API شناسایی شد")
    except:
        api_key = st.text_input("کلید API گوگل را وارد کنید", type="password")

# --- تابع اتصال به Gemini (ارسال مستقیم فایل با تلاش مجدد) ---
def analyze_pdf_directly(file_bytes, year, api_key):
    genai.configure(api_key=api_key)
    
    # دستورالعمل سیستم (آپدیت شده برای استخراج خدمات و متن کامل)
    system_instruction = f"""
    You are an AI assistant for "TahaGasht" travel agency.
    Target Year: {year}
    
    Task: Look at the provided PDF document. Extract the following sections clearly:
    1. Tour Title
    2. Flight departure date (Convert extracted Persian date to Gregorian YYYY-MM-DD).
    3. Services Section (خدمات): Extract the full text of included services.
    4. Flight Details Section (اطلاعات پرواز): Extract the full text of flight details.
    5. Daily Itinerary (Map each day to a Gregorian date).
    6. Full Clean Text: Extract all text content from the PDF in a clean, structured format suitable for copying.
    
    Output Format: ONLY valid JSON.
    Structure:
    {{
      "tour_title": "string",
      "flight_info": {{ "shamsi": "string", "gregorian": "YYYY-MM-DD" }},
      "services_text": "string (full text of services)",
      "flight_details_text": "string (full text of flight info)",
      "full_pdf_text": "string (entire content of pdf cleaned)",
      "itinerary": [
        {{ "day_number": 1, "date_gregorian": "YYYY-MM-DD", "day_title": "string", "content_summary": "string" }}
      ]
    }}
    """

    # لیست اولویت‌بندی شده مدل‌ها
    candidate_models = [
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro-latest"
    ]
    
    # ساخت پکیج دیتا برای ارسال مستقیم PDF
    pdf_part = {
        "mime_type": "application/pdf",
        "data": file_bytes
    }
    
    last_error = None

    # حلقه تلاش برای مدل‌های مختلف
    for model_name in candidate_models:
        try:
            # ساخت مدل
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_instruction,
                generation_config={"response_mime_type": "application/json"}
            )
            
            # تلاش برای ارسال
            response = model.generate_content(["Extract tour details from this document.", pdf_part])
            return response.text
            
        except Exception as e:
            error_str = str(e)
            last_error = e
            
            # مدیریت خطای محدودیت (429)
            if "429" in error_str or "Quota" in error_str:
                time.sleep(2)
                continue
            
            # مدیریت خطای مدل (404)
            if "404" in error_str or "not found" in error_str:
                continue
                
            print(f"Model {model_name} failed: {e}")
            continue

    return f"ERROR: All models failed. Last error: {str(last_error)}"

# --- بدنه اصلی ---
uploaded_file = st.file_uploader("فایل PDF (حتی اسکن شده) را آپلود کنید", type="pdf")

if uploaded_file and st.button("شروع پردازش"):
    if not api_key:
        st.error("کلید API وارد نشده است.")
    else:
        with st.spinner('در حال آنالیز کامل PDF (خدمات، پرواز و برنامه سفر)...'):
            try:
                file_bytes = uploaded_file.getvalue()
                raw_response = analyze_pdf_directly(file_bytes, target_year, api_key)
                
                try:
                    data = json.loads(raw_response)
                    st.success("✅ پردازش کامل انجام شد!")
                    
                    # هدر
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(f"🏷️ {data.get('tour_title', 'عنوان یافت نشد')}")
                    with col2:
                        fl = data.get('flight_info', {})
                        st.info(f"پرواز: {fl.get('shamsi', '-')} \n({fl.get('gregorian', '-')})")
                    
                    # --- تب‌بندی بخش‌های مختلف ---
                    tab_itinerary, tab_services, tab_full_text = st.tabs(["📅 برنامه سفر (روزانه)", "✈️ خدمات و پرواز", "📄 متن کامل PDF"])
                    
                    # تب ۱: برنامه سفر
                    with tab_itinerary:
                        final_text = ""
                        for day in data.get('itinerary', []):
                            d_date = day.get('date_gregorian', '-')
                            d_title = day.get('day_title', '')
                            d_content = day.get('content_summary', '')
                            
                            with st.expander(f"روز {day.get('day_number')}: {d_title}"):
                                st.write(d_content)
                            
                            final_text += f"📅 {d_date} | {d_title}\n{d_content}\n\n"
                        
                        st.text_area("متن برنامه سفر (آماده کپی):", value=final_text, height=500)
                    
                    # تب ۲: خدمات و اطلاعات پرواز
                    with tab_services:
                        col_serv, col_flight = st.columns(2)
                        with col_serv:
                            st.subheader("لیست خدمات")
                            st.text_area("متن خدمات:", value=data.get('services_text', 'پیدا نشد'), height=300)
                        
                        with col_flight:
                            st.subheader("جزئیات پرواز")
                            st.text_area("متن پرواز:", value=data.get('flight_details_text', 'پیدا نشد'), height=300)

                    # تب ۳: متن کامل
                    with tab_full_text:
                        st.warning("در اینجا متن کل فایل PDF به صورت یکجا استخراج شده است:")
                        st.text_area("متن خام کل فایل:", value=data.get('full_pdf_text', ''), height=600)
                    
                except json.JSONDecodeError:
                    st.error("❌ خطا در فرمت خروجی")
                    if "ERROR:" in raw_response:
                        st.error(raw_response)
                    else:
                        st.code(raw_response)
                        
            except Exception as e:
                st.error(f"خطای کلی: {e}")
