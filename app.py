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
    
    # دستورالعمل سیستم
    system_instruction = f"""
    You are an AI assistant for "TahaGasht" travel agency.
    Target Year: {year}
    
    Task: Look at the provided PDF document. Extract:
    1. Tour Title
    2. Flight departure date (Convert extracted Persian date to Gregorian YYYY-MM-DD).
    3. Daily Itinerary (Map each day to a Gregorian date).
    
    Output Format: ONLY valid JSON.
    Structure:
    {{
      "tour_title": "string",
      "flight_info": {{ "shamsi": "string", "gregorian": "YYYY-MM-DD" }},
      "itinerary": [
        {{ "day_number": 1, "date_gregorian": "YYYY-MM-DD", "day_title": "string", "content_summary": "string" }}
      ]
    }}
    """

    # لیست اولویت‌بندی شده مدل‌ها (بر اساس لیست مجاز شما)
    # مدل 2.5 فلش اولویت دارد چون پایدارتر است
    candidate_models = [
        "gemini-2.5-flash",          # بهترین گزینه فعلی
        "gemini-flash-latest",       # فال‌بک مطمئن
        "gemini-2.0-flash-exp",      # آزمایشی (ممکن است محدود باشد)
        "gemini-1.5-pro-latest"      # آخرین سنگر
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
            
            # اگر خطای محدودیت (429) بود، کمی صبر کن و برو بعدی
            if "429" in error_str or "Quota" in error_str:
                time.sleep(2) # 2 ثانیه استراحت
                continue
            
            # اگر خطای پیدا نشدن مدل (404) بود، سریع برو بعدی
            if "404" in error_str or "not found" in error_str:
                continue
                
            # سایر خطاها
            print(f"Model {model_name} failed: {e}")
            continue

    # اگر هیچکدام کار نکرد
    return f"ERROR: All models failed. Last error: {str(last_error)}"

# --- بدنه اصلی ---
uploaded_file = st.file_uploader("فایل PDF (حتی اسکن شده) را آپلود کنید", type="pdf")

if uploaded_file and st.button("شروع پردازش"):
    if not api_key:
        st.error("کلید API وارد نشده است.")
    else:
        with st.spinner('در حال مشاهده و آنالیز فایل (ممکن است کمی بیشتر طول بکشد)...'):
            try:
                # خواندن بایت‌های فایل
                file_bytes = uploaded_file.getvalue()
                
                # ارسال مستقیم به هوش مصنوعی
                raw_response = analyze_pdf_directly(file_bytes, target_year, api_key)
                
                # تلاش برای پارس کردن JSON
                try:
                    data = json.loads(raw_response)
                    st.success("✅ پردازش موفق با تکنولوژی ویژن!")
                    
                    # نمایش خروجی
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(f"🏷️ {data.get('tour_title', 'عنوان یافت نشد')}")
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
                    st.error("❌ خطا در فرمت خروجی")
                    if "ERROR:" in raw_response:
                        st.error(raw_response)
                        st.info("نکته: خطای Quota یعنی درخواست‌های زیادی ارسال شده. چند لحظه صبر کنید و دوباره امتحان کنید.")
                    else:
                        st.code(raw_response)
                        
            except Exception as e:
                st.error(f"خطای کلی: {e}")
