import requests
from bs4 import BeautifulSoup
import time
import os
from telegram import Bot
from datetime import datetime

# إعدادات البوت من متغيرات البيئة
BOT_TOKEN = os.getenv("8030992926:AAGSx-RBzv4xYenHx1gZBTr0Mo3DntLvSeQ")
CHAT_ID = os.getenv("7580329356")
FMI_WEBSITE = "https://fmi.univ-tiaret.dz/"  # رابط الموقع

bot = Bot(token=BOT_TOKEN)
last_post_url = None  # لتتبع آخر منشور تم إرساله

def get_latest_post():
    """ يجلب أحدث منشور من الموقع باستخدام Web Scraping """
    response = requests.get(FMI_WEBSITE)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        # هنا نبحث عن المنشورات أو الأخبار
        posts = soup.find_all('a', {'class': 'post-link'})  # قم بتعديل هذه السطر حسب الموقع
        if posts:
            latest_post = posts[0]
            title = latest_post.get_text()
            link = latest_post.get('href')
            return title, link
    return None, None

def download_and_send_file(url, file_type="pdf"):
    """ تحميل ملف وإرساله إلى Telegram """
    response = requests.get(url)
    if response.status_code == 200:
        file_name = url.split("/")[-1]  # استخراج اسم الملف
        file_path = f"/tmp/{file_name}"  # حفظ الملف مؤقتًا
        
        with open(file_path, "wb") as file:
            file.write(response.content)

        # إرسال الملف إلى Telegram
        with open(file_path, "rb") as file:
            if file_type == "pdf":
                bot.send_document(chat_id=CHAT_ID, document=file, caption="📄 ملف PDF مرفق")
            elif file_type == "image":
                bot.send_photo(chat_id=CHAT_ID, photo=file, caption="🖼️ صورة مرفقة")
        
        os.remove(file_path)  # حذف الملف بعد الإرسال
    else:
        print(f"❌ فشل تحميل {file_type}")

def send_to_telegram(title, link):
    """ إرسال المنشور إلى Telegram مع الصور والملفات المرفقة """
    global last_post_url
    if link != last_post_url:
        post_date = datetime.now().strftime("%Y-%m-%d")  # استخراج التاريخ الحالي
        message = f"منشور جديد 🗞️\n📅 *التاريخ:* {post_date}\n\n"
        message += f"🔹 *العنوان:* {title}\n\n"
        message += f"🔗 [رابط المنشور]({link})\n"

        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        last_post_url = link

        # فحص وجود ملفات PDF وصور داخل المنشور
        response = requests.get(link)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.find_all("a", href=True)
            images = soup.find_all("img", src=True)

            pdf_links = [link["href"] for link in links if link["href"].endswith(".pdf")]
            image_links = [img["src"] for img in images if img["src"].startswith("http")]

            # إرسال ملفات PDF
            for pdf in pdf_links:
                download_and_send_file(pdf, file_type="pdf")

            # إرسال الصور
            for img in image_links:
                download_and_send_file(img, file_type="image")

# حلقة مستمرة لجلب المنشورات كل 10 دقائق
while True:
    title, link = get_latest_post()
    if title and link:
        send_to_telegram(title, link)
    
    time.sleep(600)  # تحديث كل 10 دقائق