import streamlit as st
import pdfplumber
import json
import google.generativeai as genai
from google.api_core import retry

# --- تنظیمات صفحه ---
st.set_page_config(page_title="ابزار پکیج طاهاگشت (نسخه جمینای)", layout="wide", page_icon="💎")

# استایل برای راست‌چین کردن متن‌ها
st.markdown("""
<style>
    .stTextArea textarea { direction: rtl; }
    div[data-testid="stExpander"] div[role="button"] p { direction: rtl; }
</style>
""", unsafe_allow_html=True)

st.title("💎 تبدیل هوشمند پکیج (با موتور Gemini)")

# --- سایدبار ---
with st.sidebar:
    st.header("تنظیمات ورودی")
    target_year = st.number_input("سال برگزاری تور (شمسی)", min_value=1403, max_value=1410, value=1404)
    
    # دریافت API Key گوگل
    # اگر در secrets ذخیره کرده باشید خودش می‌خواند، وگرنه از کاربر می‌گیرد
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        api_key = st.text_input("کلید API گوگل (Gemini) را وارد کنید", type="password")

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
    # تنظیمات مدل
    genai.configure(api_key=api_key)
    
    # پرامپت سیستمی (دستورالعمل اصلی)
    system_instruction = f"""
    تو یک دستیار متخصص برای آژانس مسافرتی «طاهاگشت» هستی.
    ورودی: متن خام یک فایل PDF تور.
    سال تور: {year}
    
    وظایف تو:
    1. بخش "پرواز رفت" را پیدا کن و تاریخ شمسی آن را استخراج کن.
    2. آن تاریخ را دقیق به میلادی تبدیل کن (این می‌شود تاریخ مرجع).
    3. برنامه سفر (Itinerary) را بخوان. برای هر روز، تاریخ میلادی آن را محاسبه کن (روز اول معمولاً همان تاریخ پرواز است، مگر اینکه پرواز شبانه باشد و رسیدن به مقصد روز بعد باشد).
    4. عنوان تور را استخراج کن.
    
    خروجی تو باید فقط و فقط یک JSON معتبر باشد با این فیلدها:
    {{
      "tour_title": "عنوان تور",
      "flight_info": {{ "shamsi": "DD Month", "gregorian": "YYYY-MM-DD" }},
      "itinerary": [
        {{ "day_number": 1, "date_gregorian": "YYYY-MM-DD", "day_title": "...", "content_summary": "..." }},
        ...
      ]
    }}
    """

    # انتخاب مدل (Flash برای سرعت و قیمت عالی است)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest",
        system_instruction=system_instruction,
        generation_config={"response_mime_type": "application/json"} # تضمین خروجی JSON
    )

    # ارسال درخواست
    response = model.generate_content(f"این متن کامل PDF است، لطفاً تحلیل کن:\n\n{text}")
    
    return json.loads(response.text)

# --- بدنه اصلی رابط کاربری ---
uploaded_file = st.file_uploader("فایل PDF را اینجا بارگذاری کنید", type="pdf")

if uploaded_file and st.button("شروع پردازش با Gemini"):
    if not api_key:
        st.error("لطفا ابتدا API Key را وارد کنید.")
    else:
        with st.spinner('جمینای در حال مطالعه فایل و محاسبه تاریخ‌ها...'):
            try:
                # 1. خواندن PDF
                raw_text = extract_text_from_pdf(uploaded_file)
                
                # 2. فراخوانی Gemini
                data = analyze_with_gemini(raw_text, target_year, api_key)
                
                # 3. نمایش نتایج
                st.success("انجام شد!")
                
                # هدر گزارش
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"🏷️ {data.get('tour_title', 'بدون عنوان')}")
                with col2:
                    fl = data.get('flight_info', {})
                    st.info(f"پرواز: {fl.get('shamsi', '-')} \n({fl.get('gregorian', '-')})")
                
                # تب‌بندی
                tab_preview, tab_copy = st.tabs(["بازبینی دقیق (جدول)", "متن نهایی (سایت)"])
                
                with tab_preview:
                    for day in data.get('itinerary', []):
                        with st.expander(f"روز {day['day_number']}: {day['day_title']} ({day['date_gregorian']})"):
                            st.write(day['content_summary'])
                
                with tab_copy:
                    final_text = ""
                    for day in data.get('itinerary', []):
                        final_text += f"📅 {day['date_gregorian']} | {day['day_title']}\n{day['content_summary']}\n\n"
                    
                    st.text_area("متن آماده کپی برای ادمین:", value=final_text, height=600)
            
            except Exception as e:

                st.error(f"خطا در ارتباط با گوگل: {e}")
