# -*- coding: utf-8 -*-
# بوت تحويل الملفات - نسخة الهاتف

import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram import F
from PIL import Image
import img2pdf
import fitz  # PyMuPDF

# ============ الإعدادات ============
BOT_TOKEN = "8049849829:AAEtmxs7GQyArz5U0ttk10jFIBKvKWw7NYs"  # ⚠️ ضع توكن البوت هنا

# ============ التسجيل ============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ إنشاء البوت ============
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ============ تخزين مؤقت ============
user_languages = {}
user_images = {}
user_pdfs = {}

# ============ القوائم ============
def get_main_menu(lang='ar'):
    if lang == 'ar':
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🖼️ صور → PDF", callback_data="images_to_pdf")],
            [InlineKeyboardButton(text="📄 PDF → صور", callback_data="pdf_to_images")],
            [InlineKeyboardButton(text="📑 دمج PDF", callback_data="merge_pdf")],
            [InlineKeyboardButton(text="✂️ تقسيم PDF", callback_data="split_pdf")],
            [InlineKeyboardButton(text="🌐 تغيير اللغة", callback_data="change_lang")],
            [InlineKeyboardButton(text="ℹ️ المساعدة", callback_data="help")]
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🖼️ Wêne → PDF", callback_data="images_to_pdf")],
            [InlineKeyboardButton(text="📄 PDF → Wêne", callback_data="pdf_to_images")],
            [InlineKeyboardButton(text="📑 PDF tevlihev bike", callback_data="merge_pdf")],
            [InlineKeyboardButton(text="✂️ PDF dabeş bike", callback_data="split_pdf")],
            [InlineKeyboardButton(text="🌐 Ziman biguherîne", callback_data="change_lang")],
            [InlineKeyboardButton(text="ℹ️ Alîkarî", callback_data="help")]
        ])
    return keyboard

def get_lang_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇸🇦 العربية", callback_data="lang_ar"),
            InlineKeyboardButton(text="🌿 Kurmancî", callback_data="lang_ku")
        ]
    ])
    return keyboard

# ============ الأوامر ============
@dp.message(Command("start"))
async def start(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in user_languages:
        await message.answer(
            "🌐 اختر لغة البوت\n\nZimanê botê hilbijêre:",
            reply_markup=get_lang_menu()
        )
    else:
        lang = user_languages[user_id]
        if lang == 'ar':
            text = "🔧 اختر العملية المطلوبة:"
        else:
            text = "🔧 Operasyona xwestî hilbijêre:"
        await message.answer(text, reply_markup=get_main_menu(lang))

@dp.message(Command("menu"))
async def menu(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ar')
    
    if lang == 'ar':
        text = "🔧 اختر العملية المطلوبة:"
    else:
        text = "🔧 Operasyona xwestî hilbijêre:"
    
    await message.answer(text, reply_markup=get_main_menu(lang))

# ============ اختيار اللغة ============
@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user_languages[user_id] = lang
    
    if lang == 'ar':
        text = "✅ تم اختيار العربية\n\n🔧 اختر العملية:"
    else:
        text = "✅ Kurmancî hate hilbijartin\n\n🔧 Operasyonê hilbijêre:"
    
    await callback.message.answer(text, reply_markup=get_main_menu(lang))
    await callback.answer()

@dp.callback_query(F.data == "change_lang")
async def change_lang(callback: types.CallbackQuery):
    await callback.message.answer(
        "🌐 اختر اللغة / Ziman hilbijêre:",
        reply_markup=get_lang_menu()
    )
    await callback.answer()

# ============ تحويل صور → PDF ============
@dp.callback_query(F.data == "images_to_pdf")
async def images_to_pdf_start(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ar')
    user_images[user_id] = []
    
    if lang == 'ar':
        text = "📤 أرسل صورة أو عدة صور\nبعد الانتهاء اضغط زر (إنشاء PDF)"
        create_btn = "✅ إنشاء PDF"
        cancel_btn = "❌ إلغاء"
    else:
        text = "📤 Wêne yan çend wêneyan bişîne\nPiştî qedandinê (PDF çêke) bikirtîne"
        create_btn = "✅ PDF çêke"
        cancel_btn = "❌ Betal"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=create_btn, callback_data="create_pdf"),
            InlineKeyboardButton(text=cancel_btn, callback_data="cancel_op")
        ]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

@dp.message(F.photo)
async def receive_image(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ar')
    
    if user_id not in user_images:
        user_images[user_id] = []
    
    # تنزيل الصورة
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    
    # إنشاء مجلد للمستخدم
    user_dir = f"temp_{user_id}"
    os.makedirs(user_dir, exist_ok=True)
    
    file_path = os.path.join(user_dir, f"img_{len(user_images[user_id])}.jpg")
    await bot.download_file(file.file_path, file_path)
    
    user_images[user_id].append(file_path)
    
    if lang == 'ar':
        text = f"✅ تم استلام الصورة ({len(user_images[user_id])})\nأرسل المزيد أو اضغط (إنشاء PDF)"
    else:
        text = f"✅ Wêne hat wergirtin ({len(user_images[user_id])})\nZêdetir bişîne yan (PDF çêke) bikirtîne"
    
    await message.answer(text)

@dp.callback_query(F.data == "create_pdf")
async def create_pdf(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ar')
    
    images = user_images.get(user_id, [])
    
    if not images:
        if lang == 'ar':
            await callback.message.answer("❌ لم ترسل أي صور")
        else:
            await callback.message.answer("❌ Te tu wêne neşandiye")
        await callback.answer()
        return
    
    if lang == 'ar':
        await callback.message.answer("⏳ جاري إنشاء PDF...")
    else:
        await callback.message.answer("⏳ PDF tê çêkirin...")
    
    try:
        output_path = f"output_{user_id}.pdf"
        
        # تحويل الصور إلى PDF
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(images))
        
        # إرسال الملف
        await callback.message.answer_document(
            FSInputFile(output_path, filename="converted.pdf"),
            caption="✅ تم!" if lang == 'ar' else "✅ Qediya!"
        )
        
        # تنظيف
        os.remove(output_path)
        for img in images:
            os.remove(img)
        user_images[user_id] = []
        
    except Exception as e:
        if lang == 'ar':
            await callback.message.answer(f"❌ خطأ: {e}")
        else:
            await callback.message.answer(f"❌ Xeletî: {e}")
    
    await callback.answer()

# ============ تحويل PDF → صور ============
@dp.callback_query(F.data == "pdf_to_images")
async def pdf_to_images_start(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ar')
    
    if lang == 'ar':
        await callback.message.answer("📄 أرسل ملف PDF:")
    else:
        await callback.message.answer("📄 PDF bişîne:")
    
    await callback.answer()

@dp.message(F.document)
async def receive_document(message: types.Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, 'ar')
    
    document = message.document
    
    # تحقق من النوع
    if document.mime_type == "application/pdf":
        if lang == 'ar':
            await message.answer("⏳ جاري تحويل PDF...")
        else:
            await message.answer("⏳ PDF tê veguherandin...")
        
        try:
            # تنزيل الملف
            file = await bot.get_file(document.file_id)
            pdf_path = f"input_{user_id}.pdf"
            await bot.download_file(file.file_path, pdf_path)
            
            # فتح PDF
            pdf_doc = fitz.open(pdf_path)
            
            # إنشاء مجلد للصور
            output_dir = f"pdf_images_{user_id}"
            os.makedirs(output_dir, exist_ok=True)
            
            # تحويل كل صفحة
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_path = os.path.join(output_dir, f"page_{page_num+1}.jpg")
                pix.save(img_path)
                
                # إرسال الصورة
                await message.answer_photo(
                    FSInputFile(img_path),
                    caption=f"Page {page_num+1}" if lang == 'ar' else f"Rûpel {page_num+1}"
                )
                
                # حذف الصورة
                os.remove(img_path)
            
            pdf_doc.close()
            os.remove(pdf_path)
            os.rmdir(output_dir)
            
            if lang == 'ar':
                await message.answer("✅ تم التحويل!")
            else:
                await message.answer("✅ Veguherandin qediya!")
            
        except Exception as e:
            if lang == 'ar':
                await message.answer(f"❌ خطأ: {e}")
            else:
                await message.answer(f"❌ Xeletî: {e}")
    else:
        if lang == 'ar':
            await message.answer("❌ هذا ليس ملف PDF")
        else:
            await message.answer("❌ Ev ne pelê PDF ye")

# ============ دمج PDF ============
@dp.callback_query(F.data == "merge_pdf")
async def merge_pdf_start(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ar')
    user_pdfs[user_id] = []
    
    if lang == 'ar':
        text = "📑 أرسل ملفات PDF للدمج\nبعد الانتهاء اضغط (دمج)"
        merge_btn = "✅ دمج"
    else:
        text = "📑 PDF bişîne ji bo tevlihevkirinê\nPiştî qedandinê (Tevlihev bike) bikirtîne"
        merge_btn = "✅ Tevlihev bike"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=merge_btn, callback_data="do_merge"),
            InlineKeyboardButton(text="❌ إلغاء" if lang == 'ar' else "❌ Betal", callback_data="cancel_op")
        ]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "do_merge")
async def do_merge(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ar')
    
    pdfs = user_pdfs.get(user_id, [])
    
    if len(pdfs) < 2:
        if lang == 'ar':
            await callback.message.answer("❌ أرسل ملفين على الأقل")
        else:
            await callback.message.answer("❌ Herî kêm du pelan bişîne")
        await callback.answer()
        return
    
    try:
        merged = fitz.open()
        
        for pdf_path in pdfs:
            pdf = fitz.open(pdf_path)
            merged.insert_pdf(pdf)
            pdf.close()
        
        output_path = f"merged_{user_id}.pdf"
        merged.save(output_path)
        merged.close()
        
        await callback.message.answer_document(
            FSInputFile(output_path, filename="merged.pdf"),
            caption="✅ تم الدمج!" if lang == 'ar' else "✅ Tevlihev kirin qediya!"
        )
        
        # تنظيف
        os.remove(output_path)
        for pdf in pdfs:
            os.remove(pdf)
        user_pdfs[user_id] = []
        
    except Exception as e:
        await callback.message.answer(f"❌ خطأ: {e}")
    
    await callback.answer()

# ============ تقسيم PDF ============
@dp.callback_query(F.data == "split_pdf")
async def split_pdf_start(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ar')
    
    if lang == 'ar':
        await callback.message.answer("📄 أرسل ملف PDF للتقسيم:")
    else:
        await callback.message.answer("📄 PDF bişîne ji bo dabeşkirinê:")
    
    await callback.answer()

# ============ إلغاء ============
@dp.callback_query(F.data == "cancel_op")
async def cancel_op(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ar')
    
    # تنظيف
    if user_id in user_images:
        user_images[user_id] = []
    if user_id in user_pdfs:
        user_pdfs[user_id] = []
    
    if lang == 'ar':
        await callback.message.answer("❌ تم الإلغاء")
    else:
        await callback.message.answer("❌ Hate betalkirin")
    
    await callback.answer()

# ============ مساعدة ============
@dp.callback_query(F.data == "help")
async def help(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, 'ar')
    
    if lang == 'ar':
        text = """
ℹ️ المساعدة

- 🖼️ صور → PDF: أرسل صور واضغط إنشاء
- 📄 PDF → صور: أرسل PDF
- 📑 دمج PDF: أرسل ملفين أو أكثر
- ✂️ تقسيم PDF: أرسل PDF

/start - البداية
/menu - القائمة
        """
    else:
        text = """
ℹ️ Alîkarî

- 🖼️ Wêne → PDF: Wêneyan bişîne
- 📄 PDF → Wêne: PDF bişîne
- 📑 Tevlihevkirin: Du yan zêdetir PDF bişîne
- ✂️ Dabeşkirin: PDF bişîne

/start - Destpêk
/menu - Menû
        """
    
    await callback.message.answer(text)
    await callback.answer()

# ============ التشغيل ============
async def main():
    print("✅ البوت يعمل الآن!")
    print("⚠️ لا تغلق التطبيق")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())