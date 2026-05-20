"""
Генерирует QR-код, ведущий на вашего Telegram-бота.
Поменяйте BOT_USERNAME ниже на username вашего бота (без @).
Запуск: python generate_qr.py
"""

import qrcode

# 👇 Поменяйте на username вашего бота (без @)
BOT_USERNAME = "your_bot_username"

URL = f"https://t.me/{BOT_USERNAME}"

qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,  # высокая коррекция — лучше читается даже потёртый
    box_size=12,
    border=2,
)
qr.add_data(URL)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save("qr-code.png")

print(f"QR-код создан: qr-code.png")
print(f"Ссылка: {URL}")
