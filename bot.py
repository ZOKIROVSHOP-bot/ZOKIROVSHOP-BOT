
import os
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@zokirovyt"
CHANNEL_LINK = "https://t.me/zokirovyt"

PRODUCTS = [
    ("110 Almaz", 11000),
    ("341 Almaz", 32000),
    ("572 Almaz", 52000),
    ("1166 Almaz", 104000),
    ("2398 Almaz", 208000),
    ("6160 Almaz", 525000),
    ("Weekly Lite", 5000),
    ("Weekly Membership", 21000),
    ("Monthly Membership", 78000),
    ("Evo Access 3d", 6000),
    ("Evo Access 7d", 10000),
    ("Evo Access 30d", 28000),
    ("Newbie Bundle", 3000),
    ("Level Up 6", 4000),
    ("Level Up 10", 7000),
    ("Level Up 15", 7000),
    ("Level Up 20", 7000),
    ("Level Up 25", 7000),
    ("Level Up 30", 10000),
]

async def subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(
            CHANNEL, user_id
        )
        return member.status in [
            "member", "administrator", "creator"
        ]
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not await subscribed(user.id, context):
        keyboard = [
            [InlineKeyboardButton(
                "📢 Kanalga obuna bo‘lish",
                url=CHANNEL_LINK
            )],
            [InlineKeyboardButton(
                "✅ Tekshirish", callback_data="check"
            )]
        ]
        await update.message.reply_text(
            "ZOKIROV SHOP ga xush kelibsiz!\n\n"
            "Davom etish uchun kanalimizga obuna bo‘ling.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await show_menu(update.message, context)

async def show_menu(message, context):
    keyboard = [
        [InlineKeyboardButton(
            "💎 Almaz narxlari", callback_data="prices"
        )],
        [InlineKeyboardButton(
            "🎮 PUBG Mobile", callback_data="pubg"
        )],
        [InlineKeyboardButton(
            "ℹ️ Yordam", callback_data="help"
        )]
    ]
    await message.reply_text(
        "🏪 ZOKIROV SHOP\n\nKerakli bo‘limni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "check":
        if await subscribed(user_id, context):
            await query.message.reply_text(
                "✅ Obuna tasdiqlandi!"
            )
            await show_menu(query.message, context)
        else:
            await query.message.reply_text(
                "❌ Avval kanalga obuna bo‘ling."
            )
        return

    if not await subscribed(user_id, context):
        await query.message.reply_text(
            "Avval @zokirovyt kanaliga obuna bo‘ling. /start"
        )
        return

    if query.data == "prices":
        keyboard = []
        for i, (name, price) in enumerate(PRODUCTS):
            keyboard.append([
                InlineKeyboardButton(
                    f"{name} — {price:,} so‘m",
                    callback_data=f"item_{i}"
                )
            ])

        await query.message.reply_text(
            "💎 FREE FIRE NARXLARI\n\nMahsulotni tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("item_"):
        index = int(query.data.split("_")[1])
        name, price = PRODUCTS[index]
        context.user_data["product"] = name
        context.user_data["price"] = price
        context.user_data["waiting_id"] = True

        await query.message.reply_text(
            f"Tanlangan mahsulot: {name}\n"
            f"Narxi: {price:,} so‘m\n\n"
            "Endi Free Fire ID raqamingizni yuboring."
        )

    elif query.data == "pubg":
        await query.message.reply_text(
            "🎮 PUBG Mobile mahsulotlari tez orada qo‘shiladi."
        )

    elif query.data == "help":
        await query.message.reply_text(
            "Yordam: @zokirovyt"
        )

async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_id"):
        return

    player_id = update.message.text.strip()

    if not player_id.isdigit():
        await update.message.reply_text(
            "ID faqat raqamlardan iborat bo‘lishi kerak."
        )
        return

    name = context.user_data.get("product")
    price = context.user_data.get("price")

    context.user_data["waiting_id"] = False

    await update.message.reply_text(
        "✅ Sinov buyurtmangiz tayyor!\n\n"
        f"Mahsulot: {name}\n"
        f"O‘yin ID: {player_id}\n"
        f"Narxi: {price:,} so‘m\n\n"
        "Bu sinov rejimi. Hozircha to‘lov va almaz yetkazish ishlamaydi."
    )

async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN sozlanmagan")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id)
    )

    print("ZOKIROV SHOP bot ishga tushdi")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    import asyncio
    import logging
    logging.basicConfig(level=logging.INFO)
    import asyncio
    asyncio.run(main())
