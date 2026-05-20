"""
Бот-консультант Mare Blanco для клиентов с Wildberries.
"""

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, MEASURE_PHOTOS
import sheets
from size_helper import recommend_size

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

MENU, SIZE_HEIGHT, SIZE_CHEST, SIZE_WAIST, CARE_ARTICLE = range(5)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Подобрать размер", callback_data="menu:size")],
            [InlineKeyboardButton("Уход за вещью", callback_data="menu:care")],
        ]
    )


async def send_step(message, text, photo_url=None, **kwargs):
    if photo_url:
        await message.reply_photo(photo=photo_url, caption=text, **kwargs)
    else:
        await message.reply_text(text, **kwargs)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    text = (
        f"Здравствуйте, {user.first_name}!\n\n"
        "Я помощник магазина *Mare Blanco*\n\n"
        "Помогу подобрать размер и расскажу, как ухаживать за вещью."
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            text, parse_mode="Markdown", reply_markup=main_menu_keyboard()
        )
    return MENU


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = "Главное меню - что дальше?"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, reply_markup=main_menu_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=main_menu_keyboard())
    return MENU


async def menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data.split(":", 1)[1]

    if choice == "size":
        text = "*Подбор размера*\n\nВведите ваш *рост* в см (например, 168):"
        photo = MEASURE_PHOTOS.get("height", "")
        if photo:
            await query.message.reply_photo(photo=photo, caption=text, parse_mode="Markdown")
        else:
            await query.edit_message_text(text, parse_mode="Markdown")
        return SIZE_HEIGHT

    if choice == "care":
        await query.edit_message_text(
            "*Рекомендации по уходу*\n\nВведите *артикул* товара (есть на странице WB):",
            parse_mode="Markdown",
        )
        return CARE_ARTICLE

    return MENU


def _parse_number(text: str, lo: int, hi: int):
    text = text.replace(",", ".").strip()
    try:
        value = float(text)
    except ValueError:
        return None
    if not (lo <= value <= hi):
        return None
    return value


async def size_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = _parse_number(update.message.text, 100, 220)
    if value is None:
        await update.message.reply_text("Введите рост числом в см (от 100 до 220):")
        return SIZE_HEIGHT
    context.user_data["height"] = value

    await send_step(
        update.message,
        "Хорошо! Теперь *обхват груди* в см (например, 92):",
        photo_url=MEASURE_PHOTOS.get("chest", ""),
        parse_mode="Markdown",
    )
    return SIZE_CHEST


async def size_chest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = _parse_number(update.message.text, 60, 150)
    if value is None:
        await update.message.reply_text("Введите обхват груди числом в см (от 60 до 150):")
        return SIZE_CHEST
    context.user_data["chest"] = value

    await send_step(
        update.message,
        "И последнее - *обхват талии* в см:",
        photo_url=MEASURE_PHOTOS.get("waist", ""),
        parse_mode="Markdown",
    )
    return SIZE_WAIST


async def size_waist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = _parse_number(update.message.text, 50, 140)
    if value is None:
        await update.message.reply_text("Введите обхват талии числом в см (от 50 до 140):")
        return SIZE_WAIST

    waist = value
    chest = context.user_data["chest"]
    height = context.user_data["height"]

    rec = recommend_size(chest, waist, height)
    await update.message.reply_text(
        f"Ваши параметры: рост {height:g} см, грудь {chest:g} см, талия {waist:g} см\n\n"
        f"Рекомендуемый размер: *{rec['size']}*\n"
        f"_{rec['comment']}_\n\n"
        "Если сомневаетесь - напишите нам, поможем подобрать.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    return MENU


async def care_receive_article(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    article = update.message.text.strip()
    if not article.isdigit() or not (5 <= len(article) <= 12):
        await update.message.reply_text(
            "Артикул должен быть числом из 7-10 цифр. Попробуйте ещё раз:"
        )
        return CARE_ARTICLE

    product = sheets.get_product(article)
    if not product:
        await update.message.reply_text(
            f"Не нашла товар с артикулом *{article}*.\n"
            "Проверьте артикул или напишите нам напрямую.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
        return MENU

    care = product.get("care") or "Инструкция по уходу скоро появится. Напишите нам - расскажем!"
    material = product.get("material") or "—"
    name = product.get("name") or article
    photo = product.get("photo") or ""

    caption = (
        f"*{name}*\n\n"
        f"Материал: {material}\n\n"
        f"_Рекомендации по уходу:_\n{care}"
    )

    if photo and len(caption) <= 1024:
        await update.message.reply_photo(
            photo=photo, caption=caption, parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
    elif photo:
        await update.message.reply_photo(photo=photo)
        await update.message.reply_text(
            caption, parse_mode="Markdown", reply_markup=main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            caption, parse_mode="Markdown", reply_markup=main_menu_keyboard()
        )

    return MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Действие отменено.", reply_markup=main_menu_keyboard()
    )
    return MENU


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Я - консультант магазина Mare Blanco.\n\n"
        "Что умею:\n"
        "- подобрать размер по вашим параметрам\n"
        "- рассказать, как ухаживать за вещью\n\n"
        "Команды:\n/start - начать\n/menu - меню\n/cancel - отменить"
    )


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Не указан BOT_TOKEN")

    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("menu", show_menu),
        ],
        states={
            MENU: [CallbackQueryHandler(menu_router, pattern=r"^menu:")],
            SIZE_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, size_height)],
            SIZE_CHEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, size_chest)],
            SIZE_WAIST: [MessageHandler(filters.TEXT & ~filters.COMMAND, size_waist)],
            CARE_ARTICLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, care_receive_article)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("menu", show_menu),
            CommandHandler("start", start),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("help", help_command))

    logger.info("Бот запущен. Жду сообщений...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
