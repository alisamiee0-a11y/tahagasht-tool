import streamlit as st
import pdfplumber
import json
import google.generativeai as genai

# --- تنظیمات صفحه ---
st.set_page_config(page_title="ابزار پکیج طاهاگشت", layout="wide", page_icon="💎")

# استایل برای راست‌چین کردن
st.markdown("""
<style>
    .stTextArea textarea { direction: rtl; }
    div[data-testid="stExpander"] div[role="button"] p { direction: rtl; }
    .stAlert { direction: rtl; }
</style>
""", unsafe_allow_html=True)

st.title("💎 تبدیل هوشمند پکیج (عیب‌یابی پیشرفته)")

# --- سایدبار ---
with st.sidebar:
    st.header("تنظیمات ورودی")
    target_year = st.number_input("سال برگزاری تور (شمسی)", min_value=1403, max_value=1410, value=1404)
    
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ کلید API شناسایی شد")
    except:
        api_key = st.text_input("کلید API گوگل را وارد کنید", type="password")

# --- تابع استخراج متن ---
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text

# --- تابع اتصال به Gemini ---
def analyze_with_gemini(text, year, api_key):
    genai.configure(api_key=api_key)
    
    system_instruction = f"""
    You are a data extraction assistant for a travel agency called "TahaGasht".
    Tour Year: {year}
    
    Task: Extract flight date (convert to Gregorian), tour title, and daily itinerary.
    
    CRITICAL: Output MUST be valid JSON only. Do not add markdown like ```json ... ```.
    
    JSON Structure:
    {{
      "tour_title": "string",
      "flight_info": {{ "shamsi": "string", "gregorian": "YYYY-MM-DD" }},
      "itinerary": [
        {{ "day_number": 1, "date_gregorian": "YYYY-MM-DD", "day_title": "string", "content_summary": "string" }}
      ]
    }}
    """

    # استفاده از مدلی که در لیست شما وجود داشت و قوی است
    # مدل gemini-2.5-flash هم سریع است هم هوشمند
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction=system_instruction,
        generation_config={"response_mime_type": "application/json"}
    )
    
    try:
        response = model.generate_content(f"Extract info from this PDF content:\n\n{text}")
        return response.text # بازگرداندن متن خام برای بررسی
    except Exception as e:
        return f"ERROR: {str(e)}"

# --- بدنه اصلی ---
uploaded_file = st.file_uploader("فایل PDF را آپلود کنید", type="pdf")

if uploaded_file and st.button("شروع پردازش"):
    if not api_key:
        st.error("کلید API وارد نشده است.")
    else:
        with st.spinner('در حال خواندن فایل و پردازش...'):
            # 1. خواندن PDF
            raw_text = extract_text_from_pdf(uploaded_file)
            
            # --- چک کردن اینکه آیا PDF متن دارد؟ ---
            if not raw_text or len(raw_text.strip()) < 10:
                st.error("❌ خطا: هیچ متنی از این PDF استخراج نشد!")
                st.warning("به نظر می‌رسد این فایل «اسکن» یا «عکس» است. این برنامه فقط روی PDFهایی کار می‌کند که متن آنها قابل کپی کردن باشد.")
                st.stop() # توقف برنامه
            
            # نمایش بخشی از متن برای اطمینان کاربر
            with st.expander("متن استخراج شده از PDF (چک کنید درست باشد)"):
                st.text(raw_text[:1000])

            # 2. ارسال به AI
            raw_response = analyze_with_gemini(raw_text, target_year, api_key)
            
            # 3. تلاش برای تبدیل به JSON
            try:
                data = json.loads(raw_response)
                st.success("✅ پردازش موفق بود!")
                
                # نمایش خروجی نهایی
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"🏷️ {data.get('tour_title', 'بدون عنوان')}")
                with col2:
                    fl = data.get('flight_info', {})
                    st.info(f"پرواز: {fl.get('shamsi', '-')} \n({fl.get('gregorian', '-')})")
                
                final_text = ""
                for day in data.get('itinerary', []):
                    d_date = day.get('date_gregorian', '-')
                    d_title = day.get('day_title', '')
                    d_content = day.get('content_summary', '')
                    
                    with st.expander(f"روز {day.get('day_number')}: {d_title}"):
                        st.write(d_content)
                    
                    final_text += f"📅 {d_date} | {d_title}\n{d_content}\n\n"
                
                st.text_area("متن نهایی برای کپی:", value=final_text, height=600)
                
            except json.JSONDecodeError:
                st.error("❌ خطا در ساختار خروجی هوش مصنوعی")
                st.warning("هوش مصنوعی پاسخ داد، اما فرمت آن JSON استاندارد نبود. پاسخ خام را در زیر ببینید:")
                st.code(raw_response)
            except Exception as e:
                st.error(f"خطای غیرمنتظره: {e}")
