import os
import sys
import io
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes
import docx
import pytesseract
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# استدعاء الدالة قبل تشغيل البوت
keep_alive()

# جلب التوكن من متغيرات البيئة
TOKEN = os.getenv("8049849829:AAEtmxs7GQyArz5U0ttk10jFIBKvKWw7NYs")

if not TOKEN:
    print("خطأ: لم يتم ضبط BOT_TOKEN في متغيرات البيئة!")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)
user_states = {}

def get_main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("🖼️ ⬅️ 📄 تحويل الصور إلى PDF", callback_data="img2pdf"),
        InlineKeyboardButton("🖼️ ⬅️ 📝 تحويل الصور إلى Word", callback_data="img2word"),
        InlineKeyboardButton("📄 ⬅️ 🖼️ تحويل الملفات (PDF) إلى صور", callback_data="pdf2img"),
        InlineKeyboardButton("🖼️ ⬅️ ✍️ استخراج النص من الصورة (OCR)", callback_data="img2text"),
        InlineKeyboardButton("✍️ ⬅️ 🖼️ تحويل الكتابة إلى صورة", callback_data="text2img")
    )
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_states[message.chat.id] = None
    bot.reply_to(message, "أهلاً بك! اختر الخدمة التي تريدها من القائمة أدناه:", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    user_states[chat_id] = call.data
    messages = {
        "img2pdf": "أرسل لي الصورة لتحويلها إلى ملف PDF.",
        "img2word": "أرسل لي الصورة لتحويلها وإدراجها في ملف Word.",
        "pdf2img": "أرسل لي ملف PDF لتحويل صفحاته إلى صور.",
        "img2text": "أرسل لي صورة تحتوي على نص لاستخراج الكتابة منها.",
        "text2img": "أرسل لي النص الذي تريد تحويله إلى صورة."
    }
    bot.answer_callback_query(call.id)
    bot.send_message(chat_id, messages.get(call.data, "اختر من القائمة."))

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    if not state or state not in ["img2pdf", "img2word", "img2text"]:
        bot.reply_to(message, "يرجى اختيار خدمة أولاً عبر /start")
        return
    bot.send_message(chat_id, "جاري المعالجة...")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    image = Image.open(io.BytesIO(downloaded_file)).convert("RGB")
    
    if state == "img2pdf":
        pdf_bytes = io.BytesIO()
        image.save(pdf_bytes, format="PDF")
        pdf_bytes.seek(0)
        bot.send_document(chat_id, pdf_bytes, visible_file_name="converted.pdf")
    elif state == "img2word":
        doc = docx.Document()
        img_path = "temp.jpg"
        image.save(img_path)
        doc.add_picture(img_path)
        doc_bytes = io.BytesIO()
        doc.save(doc_bytes)
        doc_bytes.seek(0)
        os.remove(img_path)
        bot.send_document(chat_id, doc_bytes, visible_file_name="converted.docx")
    elif state == "img2text":
        try:
            text = pytesseract.image_to_string(image, lang='ara+eng')
            bot.reply_to(message, f"النص المستخرج:\n\n{text if text.strip() else 'لم يتم العثور على نص واضح.'}")
        except:
            bot.reply_to(message, "حدث خطأ في قراءة النص.")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    if state == "pdf2img" and message.document.mime_type == "application/pdf":
        bot.send_message(chat_id, "جاري تحويل صفحات الـ PDF إلى صور...")
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        try:
            images = convert_from_bytes(downloaded_file)
            for i, img in enumerate(images):
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="JPEG")
                img_bytes.seek(0)
                bot.send_photo(chat_id, img_bytes)
        except:
            bot.reply_to(message, "حدث خطأ أثناء تحويل PDF.")
    else:
        bot.reply_to(message, "يرجى اختيار الخدمة المناسبة أولاً.")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    if state == "text2img":
        img = Image.new('RGB', (800, 400), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((20, 20), message.text, fill=(0, 0, 0))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        bot.send_photo(chat_id, img_bytes)
    else:
        bot.reply_to(message, "اختر خدمة من القائمة عبر /start", reply_markup=get_main_keyboard())

if __name__ == "__main__":
    print("البوت يعمل...")
    bot.infinity_polling()
