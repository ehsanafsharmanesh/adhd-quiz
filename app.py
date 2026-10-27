from flask import Flask, render_template_string, request, redirect, url_for, session
from datetime import datetime
import os
import json
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-fallback-change-me-in-production')

QUESTIONS_PER_PAGE = 1
TOTAL_QUESTIONS = 27
MAX_POSSIBLE_SCORE = TOTAL_QUESTIONS * 3

GOOGLE_SHEET_NAME = 'ADHD_Quiz_Results'

adhd_questions = {
    1: {"text": "بی‌توجه است، حواسش به راحتی پرت می‌شود.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    2: {"text": "عصبانی و خشمگین است.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    3: {"text": "در انجام دادن یا تمام کردن تکالیف مشکل دارد.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    4: {"text": "همیشه در حال حرکت است یا طوری عمل می‌کند که انگار با یک موتور حرکت می‌کند.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    5: {"text": "مدت زمان توجه و تمرکز او کوتاه است.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    6: {"text": "با بزرگترها مشاجره می‌کند.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    7: {"text": "دست یا پاهایش را تکان می‌دهد یا در جای خود وول می‌خورد.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    8: {"text": "در تمام کردن تکالیفش ناموفق است.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    9: {"text": "کنترل کردن او در فروشگاه‌های بزرگ یا هنگام خرید از مغازه دشوار است.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    10: {"text": "در خانه یا مدرسه بی‌نظم و به هم ریخته است.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    11: {"text": "کنترل خود را از دست می‌دهد.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    12: {"text": "برای انجام تکالیف نیاز به نظارت از نزدیک دارد.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    13: {"text": "فقط وقتی به چیزی علاقمند باشد به آن توجه می‌کند.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    14: {"text": "در موقعیت‌های نامناسب به شدت می‌دود یا بالا و پایین می‌رود.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    15: {"text": "حواس‌پرت است یا مدت زمان توجه و تمرکز او مشکل دارد.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    16: {"text": "تحریک‌پذیر است.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    17: {"text": "از مشغول شدن به تکالیفی که نیازمند تلاش ذهنی مدام است اجتناب می‌کند یا اکراه نشان می‌دهد.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    18: {"text": "بی‌قرار است و وول می‌خورد.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    19: {"text": "وقتی برای انجام کاری دستور می‌گیرد حواسش پرت می‌شود.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    20: {"text": "به طور جدی با درخواست بزرگترها مخالفت می‌کند یا از انجام آن خودداری می‌نماید.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    21: {"text": "در تمرکز پیدا کردن در کلاس مشکل دارد.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    22: {"text": "در انتظار کشیدن در صف یا منتظر نوبت ماندن در بازی‌ها مشکل دارد.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    23: {"text": "جای خود را در کلاس یا سایر موقعیت‌هایی که انتظار می‌رود در جای خود باقی بماند ترک می‌کند.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    24: {"text": "عمداً کارهایی می‌کند که دیگران را آزار دهد.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    25: {"text": "دستورات را پیگیری نمی‌کند و در تمام کردن وظایف خود ناموفق است.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    26: {"text": "برای او مشکل است که به آرامی بازی کند یا به فعالیت‌های سرگرم‌کننده مشغول باشد.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
    27: {"text": "به راحتی در تلاش‌هایش مایوس می‌شود.", "options": {"هرگز": 0, "گاهی": 1, "اغلب": 2, "خیلی زیاد": 3}},
}

FONT_FAMILY_NAME = 'Vazirmatn'
FONT_FAMILY_CSS = f"'{FONT_FAMILY_NAME}', sans-serif"
FONT_FACE_RULES = f"""
@font-face {{font-family: '{FONT_FAMILY_NAME}'; src: url("/static/mycustomfonts/Vazirmatn-Regular.woff2") format('woff2'); font-weight: 400; font-style: normal;}}
@font-face {{font-family: '{FONT_FAMILY_NAME}'; src: url("/static/mycustomfonts/Vazirmatn-Bold.woff2") format('woff2'); font-weight: 700; font-style: normal;}}
"""

def save_to_google_sheets(data_row):
    """ذخیرهٔ یک ردیف در Google Sheets. برمی‌گرداند (موفقیت, پیام خطا)."""
    try:
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if not creds_json:
            return False, "متغیر محیطی GOOGLE_CREDENTIALS_JSON تنظیم نشده است."
        creds_dict = json.loads(creds_json)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        sheet.append_row(data_row, value_input_option="USER_ENTERED")
        return True, None
    except Exception as e:
        return False, str(e)

def get_recommendations(score):
    if 0 <= score <= 20:
        return {"title": "وضعیت: علائم خفیف یا احتمال پایین ADHD", "details": ["توصیه نمونه ۱ برای این گروه...", "توصیه نمونه ۲..."], "severity_class": "mild"}
    elif 21 <= score <= 50:
        return {"title": "وضعیت: علائم متوسط یا احتمال متوسط ADHD", "details": ["توصیه نمونه ۱ برای این گروه...", "توصیه نمونه ۲..."], "severity_class": "moderate"}
    elif 51 <= score <= MAX_POSSIBLE_SCORE:
        return {"title": "وضعیت: علائم شدید یا احتمال بالای ADHD", "details": ["توصیه نمونه ۱ برای این گروه...", "توصیه نمونه ۲..."], "severity_class": "severe"}
    else:
        return {"title": "امتیاز نامعتبر", "details": ["امتیاز محاسبه شده خارج از محدوده مورد انتظار است."], "severity_class": "unknown"}

@app.route('/')
def index():
    session.clear()
    return redirect(url_for('start'))

@app.route('/start', methods=['GET', 'POST'])
def start():
    if request.method == 'POST':
        session['name'] = request.form.get('name', '').strip()
        session['family'] = request.form.get('family', '').strip()
        session['phone'] = request.form.get('phone', '').strip()

        if not all(session.get(key) for key in ['name', 'family', 'phone']):
            error_message = "لطفاً تمام اطلاعات (نام، نام خانوادگی و شماره تلفن) را وارد کنید!"
            return render_template_string(f"""
            <html><head><title>خطا در ورود اطلاعات</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>{FONT_FACE_RULES} body{{font-family:{FONT_FAMILY_CSS};direction:rtl;text-align:center;margin:0;padding:20px;background-color:#f8f9fa;color:#333;display:flex;flex-direction:column;justify-content:center;align-items:center;min-height:100vh;}}
            .container{{background-color:#fff;padding:30px;border-radius:10px;box-shadow:0 4px 8px rgba(0,0,0,0.1);max-width:500px;width:100%;}} h1{{color:#dc3545;margin-bottom:20px;font-weight:700;}} p{{font-size:1.1em;margin-bottom:20px;}}
            a{{display:inline-block;margin-top:20px;color:#007bff;text-decoration:none;padding:10px 20px;border:1px solid #007bff;border-radius:5px;transition:background-color .3s,color .3s;}} a:hover{{background-color:#007bff;color:white;}}</style></head>
            <body><div class="container"><h1>⚠️ خطا</h1><p>{error_message}</p><a href="{{{{ url_for('start') }}}}">بازگشت و تلاش مجدد</a></div></body></html>""")

        session['answers'] = {}
        session['start_time'] = datetime.now().isoformat()
        return redirect(url_for('quiz', page=1))

    return render_template_string(f"""
    <html><head><title>شروع آزمون ADHD</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{FONT_FACE_RULES} body{{font-family:{FONT_FAMILY_CSS};direction:rtl;text-align:right;margin:0;padding:20px;background-color:#f0f4f8;color:#333;display:flex;justify-content:center;align-items:center;min-height:100vh;}}
    .container{{max-width:600px;width:100%;padding:35px;background-color:#fff;border-radius:12px;box-shadow:0 6px 12px rgba(0,0,0,0.15);}} h1{{text-align:center;color:#0056b3;margin-bottom:15px;font-weight:700;font-size:1.8em;}}
    h3{{text-align:center;font-size:1.1em;color:#555;margin-bottom:30px;font-weight:400;}} form{{display:flex;flex-direction:column;gap:18px;}} label{{display:block;margin-bottom:6px;font-weight:700;color:#444;font-size:0.95em;}}
    input[type="text"]{{width:100%;padding:12px;border:1px solid #ccc;border-radius:6px;box-sizing:border-box;font-size:1em;font-family:{FONT_FAMILY_CSS};}}
    input[type="text"]:focus{{border-color:#007bff;box-shadow:0 0 0 .2rem rgba(0,123,255,.25);outline:none;}}
    button[type="submit"]{{background-color:#28a745;color:white;padding:12px 20px;border:none;border-radius:6px;cursor:pointer;font-size:1.1em;font-weight:700;transition:background-color .3s ease;margin-top:15px;font-family:{FONT_FAMILY_CSS};}}
    button[type="submit"]:hover{{background-color:#218838;}} @media (max-width:576px){{.container{{padding:20px;}}h1{{font-size:1.6em;}}}}</style></head>
    <body><div class="container"><h1>🔶 پرسشنامه تشخیص ADHD (والدین)</h1><h3>طراح آزمون: احسان افشارمنش (مشاور تحصیلی و روانشناس بالینی)</h3>
    <form method="post">
        <div><label for="name">نام فرزند:</label><input type="text" id="name" name="name" value="{{{{ session.get('name', '') }}}}" required></div>
        <div><label for="family">نام خانوادگی:</label><input type="text" id="family" name="family" value="{{{{ session.get('family', '') }}}}" required></div>
        <div><label for="phone">شماره تلفن ولی:</label><input type="text" id="phone" name="phone" value="{{{{ session.get('phone', '') }}}}" pattern="[0-9\\s]{{10,13}}" title="شماره تلفن معتبر وارد کنید (مثال: 09123456789)" required></div>
        <button type="submit">شروع آزمون</button>
    </form></div></body></html>""")

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if not all(field in session for field in ['name', 'family', 'phone', 'answers']):
        return redirect(url_for('start'))

    if request.method == 'POST':
        try:
            current_page = int(request.form.get('current_page'))
            q_num_on_page = (current_page - 1) * QUESTIONS_PER_PAGE + 1
            answer_value_str = request.form.get(f'q_{q_num_on_page}')

            if answer_value_str is not None and answer_value_str.isdigit():
                session['answers'][str(q_num_on_page)] = int(answer_value_str)
                session.modified = True
        except (ValueError, TypeError, KeyError):
            return render_template_string(f"""
            <html><head><title>خطا</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>{FONT_FACE_RULES} body{{font-family:{FONT_FAMILY_CSS};direction:rtl;text-align:center;padding:20px;}}h1{{color:red;}}a{{color:blue;}}</style></head>
            <body><h1>⚠️ خطا: اطلاعات ارسالی نامعتبر است.</h1><p><a href="{{{{ url_for('quiz', page=session.get('current_quiz_page', 1)) }}}}">بازگشت به آزمون</a></p></body></html>""")

        next_page_num = current_page + 1
        if (current_page * QUESTIONS_PER_PAGE) >= TOTAL_QUESTIONS:
            return redirect(url_for('submit_quiz'))
        else:
            session['current_quiz_page'] = next_page_num
            return redirect(url_for('quiz', page=next_page_num))

    try:
        page = int(request.args.get('page', '1'))
        if not (1 <= page <= TOTAL_QUESTIONS):
            page = 1 if page < 1 else TOTAL_QUESTIONS
        session['current_quiz_page'] = page
    except ValueError:
        page = 1
        session['current_quiz_page'] = page

    current_question_number = page
    if current_question_number > TOTAL_QUESTIONS:
        return redirect(url_for('submit_quiz'))

    questions_to_display = {}
    if current_question_number in adhd_questions:
        questions_to_display = {current_question_number: adhd_questions[current_question_number]}
    else:
        if TOTAL_QUESTIONS > 0: return redirect(url_for('start'))
        else: return "خطا: هیچ سوالی تعریف نشده است."

    progress_percentage = (page / TOTAL_QUESTIONS) * 100
    user_answers = session.get('answers', {})

    questions_html_block = ""
    for q_num_loop, question_data_loop in questions_to_display.items():
        options_html_block = ""
        q_num_str_for_session = str(q_num_loop)
        for option_text_loop, score_val_loop in question_data_loop['options'].items():
            is_checked_attr = ""
            if user_answers.get(q_num_str_for_session) == score_val_loop:
                is_checked_attr = "checked"
            options_html_block += f"""
            <label><input type="radio" name="q_{q_num_loop}" value="{score_val_loop}" {is_checked_attr} required><span>{option_text_loop.replace("'", "'")}</span></label>
            """
        questions_html_block += f"""
        <div class="question"><p>{q_num_loop}. {question_data_loop['text'].replace("'", "'")}</p>
        <div class="options">
        {options_html_block}
        </div></div>
        """

    navigation_html_block = ""
    if page > 1:
        navigation_html_block += f"""<a href="{url_for('quiz', page=page-1)}" class="prev-btn">→ سوال قبل</a>"""
    else:
        navigation_html_block += """<span class="placeholder-btn"></span>"""
    navigation_html_block += """<span class="placeholder-btn"></span>"""

    quiz_template = f"""
    <html><head><title>آزمون آنلاین ADHD - سوال {{{{ page }}}}</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{FONT_FACE_RULES} body{{font-family:{FONT_FAMILY_CSS};direction:rtl;text-align:right;margin:0;padding:20px;background-color:#eef2f7;color:#333;display:flex;flex-direction:column;align-items:center;min-height:100vh;}}
    .progress-bar-container{{width:100%;max-width:700px;background-color:#ddd;border-radius:5px;margin-bottom:20px;overflow:hidden;}}
    .progress-bar{{width:{progress_percentage}%;background-color:#4CAF50;color:white;text-align:center;line-height:20px;height:20px;font-size:.8em;transition:width .3s ease-in-out;}}
    .container{{max-width:700px;width:100%;padding:30px;background-color:#fff;border-radius:10px;box-shadow:0 5px 15px rgba(0,0,0,0.1);}}
    h1.quiz-title{{text-align:center;color:#0056b3;margin-bottom:10px;font-weight:700;font-size:1.6em;}}
    .page-info{{text-align:center;color:#555;margin-bottom:25px;font-size:1em;font-weight:400;}} form{{display:flex;flex-direction:column;}}
    .question{{margin-bottom:25px;padding:20px;border:1px solid #e0e0e0;border-radius:8px;background-color:#fdfdfd;}}
    .question p{{margin:0 0 18px 0;font-weight:700;color:#333;font-size:1.2em;line-height:1.7;}} .options{{display:flex;flex-direction:column;gap:10px;}}
    .options label{{cursor:pointer;font-size:1.05em;color:#444;padding:12px 15px;border:1px solid #eee;border-radius:6px;transition:background-color .2s ease,border-color .2s ease,box-shadow .2s ease;font-weight:400;display:flex;align-items:center;background-color:#fff;}}
    .options label:hover{{background-color:#f0f8ff;border-color:#add8e6;box-shadow:0 2px 4px rgba(0,0,0,0.05);}}
    .options input[type="radio"]{{margin-left:12px;transform:scale(1.3);vertical-align:middle;accent-color:#007bff;}}
    .options label:has(input[type="radio"]:checked){{background-color:#d4edda;border-color:#28a745;box-shadow:0 2px 5px rgba(40,167,69,0.2);}}
    .options label:has(input[type="radio"]:checked) span{{font-weight:700;color:#155724;}} .options label span{{display:inline-block;vertical-align:middle;}}
    .navigation{{margin-top:25px;text-align:center;display:flex;justify-content:space-between;align-items:center;}}
    .navigation a.prev-btn {{padding:10px 20px;border:none;border-radius:6px;cursor:pointer;text-decoration:none;font-size:1em;font-weight:700;transition:background-color .3s ease;color:white;font-family:{FONT_FAMILY_CSS};background-color:#6c757d;}}
    .navigation a.prev-btn:hover{{background-color:#5a6268;}}
    .navigation span.placeholder-btn {{ width: 100px; display: inline-block; }}
    .form-submit-info{{font-size:.8em;color:#777;text-align:center;margin-top:10px;}}
    @media (max-width:576px){{.container{{padding:20px;}}body{{padding:10px;}}.question p{{font-size:1.1em;}}.options label{{font-size:1em;padding:10px;}}.progress-bar-container{{margin-left:10px;margin-right:10px;}}}}</style></head>
    <body><div class="progress-bar-container"><div class="progress-bar">سوال {{{{ page }}}} از {{{{ TOTAL_QUESTIONS }}}}</div></div>
    <div class="container"><h1 class="quiz-title">🔶 پرسشنامه تشخیص ADHD (والدین)</h1>
    <p class="page-info">لطفاً گزینه‌ای را انتخاب کنید که بهترین توصیف از رفتار فرزندتان در <b>شش ماه گذشته</b> است.</p>
    <form id="quizForm" method="post" action="{{{{ url_for('quiz') }}}}"> <input type="hidden" name="current_page" value="{{{{ page }}}}">
    {questions_html_block}
    <div class="navigation">
    {navigation_html_block}
    </div><p class="form-submit-info">با انتخاب گزینه، پاسخ شما ثبت و به سوال بعد منتقل می‌شود.</p></form></div>
    <script>
    const form=document.getElementById('quizForm');
    const radioButtons=form.querySelectorAll('.options input[type="radio"]');
    let autoSubmitEnabled=true;
    radioButtons.forEach(radio=>{{
        radio.addEventListener('change',function(){{
            if(autoSubmitEnabled && this.checked){{
                setTimeout(()=>{{form.submit()}}, 100);
            }}
        }});
    }});
    const prevButton=document.querySelector('.navigation a.prev-btn');
    if(prevButton){{
        prevButton.addEventListener('click',function(event){{
            autoSubmitEnabled=false;
        }});
    }}
    </script>
    </body></html>"""
    return render_template_string(quiz_template, page=page, TOTAL_QUESTIONS=TOTAL_QUESTIONS,
                                  progress_percentage=progress_percentage)

@app.route('/submit_quiz')
def submit_quiz():
    if not all(field in session for field in ['name', 'family', 'phone', 'answers']):
        return redirect(url_for('start'))

    user_name = session.get('name', 'N/A')
    user_family = session.get('family', 'N/A')
    user_phone = session.get('phone', 'N/A')
    user_answers = session.get('answers', {})
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    total_score = sum(user_answers.values())
    recommendations = get_recommendations(total_score)

    important_notice_message = "این آزمون یک ابزار غربالگری اولیه است و به هیچ عنوان جایگزین تشخیص قطعی توسط متخصص نمی‌باشد."
    important_notice_class = "info"
    important_notice_icon = "ℹ️"

    ok, err = save_to_google_sheets([timestamp, user_name, user_family, user_phone, total_score])
    if not ok:
        important_notice_message = f"خطا در ذخیره اطلاعات در Google Sheets: {err}. " + important_notice_message
        important_notice_class = "error"
        important_notice_icon = "❌"
        print(f"[GoogleSheets Error] {err}")

    student_full_name = f"{user_name} {user_family}"
    keys_to_pop = ['name', 'family', 'phone', 'answers', 'start_time', 'current_quiz_page']
    for key in keys_to_pop:
        session.pop(key, None)

    recommendations_details_html = ""
    for item_loop in recommendations['details']:
        safe_item_loop = item_loop.replace("'", "'")
        recommendations_details_html += f"<li>{safe_item_loop}</li>"

    results_template = f"""
    <html><head><title>پایان آزمون ADHD - نتایج</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{FONT_FACE_RULES} body{{font-family:{FONT_FAMILY_CSS};direction:rtl;text-align:right;margin:0;padding:20px;background-color:#f0f4f8;color:#333;}}
    .page-container{{max-width:800px;margin:20px auto;padding:25px;background-color:#fff;border-radius:12px;box-shadow:0 6px 12px rgba(0,0,0,0.1);}}
    .header-print{{display:none;text-align:center;margin-bottom:20px;border-bottom:1px solid #ccc;padding-bottom:15px;}} .header-print h1{{font-size:1.5em;color:#333;margin:0 0 5px 0;}} .header-print p{{font-size:.9em;color:#555;margin:2px 0;}}
    .important-notice {{ text-align:center; padding:12px; margin-top: 15px; margin-bottom:20px; border-radius:6px; font-weight:normal; border: 1px solid #ddd; }}
    .important-notice.info {{ background-color:#e7f3fe; color:#31708f; border-color:#bce8f1; }}
    .important-notice.error {{ background-color:#f8d7da; color:#721c24; border:1px solid #f5c6cb; }}
    .important-notice .icon {{ font-size:1.2em; margin-left:8px; vertical-align:middle; }}
    .score-section{{text-align:center;margin-bottom:25px;padding:15px;background-color:#e9ecef;border-radius:8px;}} .score-section p{{margin:5px 0;font-size:1.2em;}} .score-section .total-score{{font-weight:700;font-size:1.5em;color:#007bff;}}
    .recommendations-section{{margin-top:20px;padding:20px;border:1px solid #ddd;border-radius:8px;background-color:#fdfdfd;}}
    .recommendations-section h2{{font-size:1.4em;color:#333;border-bottom:2px solid #007bff;padding-bottom:8px;margin-bottom:15px;font-weight:700;display:flex;align-items:center;}}
    .recommendations-section .status-circle {{display:inline-block;width:0.8em;height:0.8em;border-radius:50%;margin-left:10px; vertical-align: middle;}}
    .recommendations-section ul{{list-style-type:disc;padding-right:20px;margin:0;}} .recommendations-section ul li{{margin-bottom:12px;line-height:1.7;font-size:1.05em;text-align:justify;}}
    .recommendations-section ul li.static-recom{{font-weight:bold; list-style-type:none; margin-top:15px; padding-right: 0;}}
    .recommendations-section ul hr {{ margin: 15px 0; border: 0; border-top: 1px solid #eee; }}
    .severity-mild .recommendations-section h2{{border-color:#28a745;}} .severity-moderate .recommendations-section h2{{border-color:#ffc107;}} .severity-severe .recommendations-section h2{{border-color:#dc3545;}}
    .actions{{text-align:center;margin-top:30px;padding-top:20px;border-top:1px solid #eee;}}
    .actions button,.actions a{{font-family:{FONT_FAMILY_CSS};color:white;text-decoration:none;font-size:1em;padding:10px 20px;border:none;border-radius:6px;cursor:pointer;transition:background-color .3s ease;margin:0 8px;}}
    .actions .print-btn{{background-color:#17a2b8;}}.actions .print-btn:hover{{background-color:#138496;}} .actions .restart-btn{{background-color:#6c757d;}}.actions .restart-btn:hover{{background-color:#5a6268;}}
    .footer-info{{text-align:center;margin-top:30px;font-size:.9em;color:#777;}} .footer-info a{{color:#007bff;text-decoration:none;}} .footer-info a:hover{{text-decoration:underline;}}
    @media print{{body{{background-color:#fff;padding:0;margin:1cm;font-size:12pt;}}.page-container{{box-shadow:none;border:none;margin:0;padding:0;max-width:100%;}}
    .actions,.important-notice,.footer-info .restart-link{{display:none!important;}}.header-print{{display:block!important;}}
    .footer-print-info{{display:block!important;text-align:center;font-size:.8em;color:#555;margin-top:30px;border-top:1px solid #ccc;padding-top:10px;}}
    .recommendations-section ul li{{page-break-inside:avoid;}}h1,h2,h3,p,li{{orphans:3;widows:3;}}}}
    .footer-print-info{{display:none;}}</style></head>
    <body class="page-container {{{{ recommendations.severity_class }}}}">
    <div class="header-print">
        <h1>نتایج آزمون تشخیص ADHD (والدین)</h1>
        <p><strong>{{{{ student_full_name_for_template }}}}</strong></p>
        <p>تاریخ آزمون: {{{{ timestamp.split(' ')[0] }}}}</p>
    </div>

    <div class="important-notice {{{{ important_notice_class_for_template }}}}">
        <span class="icon">{{{{ important_notice_icon_for_template }}}}</span> {{{{ important_notice_message_for_template }}}}
    </div>

    <div class="score-section">
        <p><strong>{{{{ student_full_name_for_template }}}}</strong></p>
        <p>امتیاز کل کسب شده: <strong class="total-score">{{{{ total_score }}}}</strong> از {{{{ MAX_POSSIBLE_SCORE }}}}</p>
    </div>

    <div class="recommendations-section">
        <h2>
            {{% if recommendations.severity_class == 'severe' %}}
                <span class="status-circle" style="background-color: red;"></span>
            {{% elif recommendations.severity_class == 'mild' %}}
                <span class="status-circle" style="background-color: green;"></span>
            {{% elif recommendations.severity_class == 'moderate' %}}
                <span class="status-circle" style="background-color: orange;"></span>
            {{% endif %}}
            {{{{ recommendations.title }}}}
        </h2>
        <ul>
            {recommendations_details_html}
            <hr>
            <li class="static-recom">تلفن اورژانس اجتماعی برای تماس ۲۴ ساعته: ۱۲۳</li>
            <li class="static-recom">تلفن اورژانس دانش آموزی (ساعت فعالیت از ۸ صبح تا ۸ شب): ۱۵۷۰</li>
        </ul>
    </div>

    <div class="footer-info">
        <p>طراح آزمون: احسان افشارمنش (مشاور تحصیلی و روانشناس بالینی) | ارتباط: <a href="https://zil.ink/ehsan.afshar" target="_blank">zil.ink/ehsan.afshar</a></p>
    </div>
    <div class="actions"><button onclick="window.print()" class="print-btn">🖨️ چاپ نتایج</button><a href="{{{{ url_for('start') }}}}" class="restart-btn restart-link">شروع مجدد آزمون</a></div>
    <div class="footer-print-info">
        <p>طراح آزمون: احسان افشارمنش (مشاور تحصیلی و روانشناس بالینی) | zil.ink/ehsan.afshar</p>
        <p>این نتایج بر اساس پرسشنامه تکمیل شده توسط والدین در تاریخ {{{{ timestamp.split(' ')[0] }}}} می‌باشد.</p>
    </div>
    </body></html>"""

    return render_template_string(results_template,
                                  student_full_name_for_template=student_full_name,
                                  total_score=total_score,
                                  MAX_POSSIBLE_SCORE=MAX_POSSIBLE_SCORE,
                                  recommendations=recommendations,
                                  important_notice_message_for_template=important_notice_message,
                                  important_notice_class_for_template=important_notice_class,
                                  important_notice_icon_for_template=important_notice_icon,
                                  timestamp=timestamp)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting Flask app on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)