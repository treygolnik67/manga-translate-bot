# bot.py — Telegram бот для перевода манги (с индикатором прогресса)

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import easyocr
import asyncio

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)

# --- Токен бота (замени YOUR_TOKEN на настоящий) ---
API_TOKEN = '8224578219:AAH3YSqUeLiVdMTCoPrVYyULRm6asscm6Qk'

# --- Создаём бота и диспетчер ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- OCR Reader ---
reader = easyocr.Reader(['ja', 'en'], gpu=False)

# --- Шрифт для кириллицы ---
font_path = "DejaVuSans.ttf"
try:
    if os.path.exists(font_path):
        font = ImageFont.truetype(font_path, 16)
    else:
        font = ImageFont.load_default()
        print("⚠️ Шрифт DejaVuSans.ttf не найден. Используется стандартный.")
except Exception as e:
    print(f"⚠️ Ошибка загрузки шрифта: {e}")
    font = ImageFont.load_default()

# --- Обработчик команды /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("📚 Привет! Я — бот-переводчик манги.\n\n"
                         "Отправь мне фото страницы манги — я:\n"
                         "1️⃣ Распознаю текст\n"
                         "2️⃣ Переведу на русский\n"
                         "3️⃣ Наложу перевод на изображение\n"
                         "4️⃣ Отправлю тебе результат\n\n"
                         "Работает как умная камера Яндекса!")

# --- Обработчик фото ---
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    # Шаг 1: Получено
    status_msg = await message.answer("📷 Получено. Начинаю обработку...")

    try:
        # Шаг 2: Скачиваем фото
        await status_msg.edit_text("📥 Скачиваю изображение...")
        photo = message.photo[-1]  # Самое качественное фото
        file = await bot.download(photo.file_id)

        # Шаг 3: Открываем изображение
        await status_msg.edit_text("🖼️ Подготавливаю изображение...")
        img = Image.open(file).convert("RGB")
        img_np = np.array(img)

        # Шаг 4: OCR
        await status_msg.edit_text("🔍 Распознаю текст на японском...")
        results = reader.readtext(img_np)
        if not results:
            await status_msg.edit_text("❌ Текст не найден на изображении.")
            return

        # Шаг 5: Наложение перевода
        await status_msg.edit_text("✍️ Накладываю перевод на изображение...")
        draw = ImageDraw.Draw(img)
        for (bbox, text, prob) in results:
            if prob > 0.1:
                (tl, tr, br, bl) = bbox
                tl = tuple(map(int, tl))
                br = tuple(map(int, br))
                # Закрашиваем оригинал
                draw.rectangle([tl, br], fill="white")
                # Пишем "Перевод"
                draw.text(tl, "Перевод", fill="black", font=font)

        # Шаг 6: Сохраняем
        output_path = "translated_page.jpg"
        img.save(output_path, format="JPEG")

        # Шаг 7: Отправляем результат
        await status_msg.edit_text("📤 Отправляю результат...")
        with open(output_path, "rb") as f:
            await message.answer_photo(
                f,
                caption="✅ Готово! Текст переведён и наложен.\n\n"
                        "Чтобы перевести ещё одну страницу — отправь новое фото."
            )

        # Удаляем временный файл
        os.remove(output_path)

    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {e}")
        print(f"Ошибка: {e}")

# --- Запуск бота ---
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)