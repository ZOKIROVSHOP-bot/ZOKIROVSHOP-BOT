
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
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

async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update.effective_user.id, context):
        keys = [
            [InlineKeyboardButton("📢 Kanalga obuna", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ Tekshirish", callback_data="check")]
        ]
        await update.message.reply_text(
            "ZOKIROV SHOP ga xush kelibsiz!\nAvval kanalga obuna bo‘ling.",
            reply_markup=InlineKeyboardMarkup(keys)
        )
        return
    await menu(update.message)

async def menu(message):
    keys = [
        [InlineKeyboardButton("💎 Almaz narxlari", callback_data="prices")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="help")]
    ]
    await message.reply_text(
        "🏪 ZOKIROV SHOP\nBo‘limni tanlang:",
        reply_markup=InlineKeyboardMarkup(keys)
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "check":
        if await is_subscribed(q.from_user.id, context):
            await q.message.reply_text("✅ Obuna tasdiqlandi!")
            await menu(q.message)
        else:
            await q.message.reply_text("Avval kanalga obuna bo‘ling.")
        return

    if q.data.startswith("item_"):
        i = int(q.data.split("_")[1])
        name, price = PRODUCTS[i]
        context.user_data["product"] = name
        context.user_data["price"] = price
        context.user_data["step"] = "player_id"
        await q.message.reply_text(
            f"{name}\nNarxi: {price:,} so‘m\n\nFree Fire ID raqamingizni yuboring."
        )
        return

    if q.data == "prices":
        keys = [
            [InlineKeyboardButton(
                f"{name} — {price:,} so‘m",
                callback_data=f"item_{i}"
            )]
            for i, (name, price) in enumerate(PRODUCTS)
        ]
        await q.message.reply_text(
            "💎 ALMAZ NARXLARI:",
            reply_markup=InlineKeyboardMarkup(keys)
        )
    elif q.data == "help":
        await q.message.reply_text("Yordam: @zokirovyt")
    elif q.data.startswith("approve_") or q.data.startswith("reject_"):
        if q.from_user.id != ADMIN_ID:
            await q.answer("Bu tugma faqat admin uchun.", show_alert=True)
            return

        order_id = q.data.split("_", 1)[1]
        order = context.application.bot_data.get("orders", {}).get(order_id)
        if not order or order["status"] != "pending":
            await q.message.reply_text("Buyurtma topilmadi yoki ko‘rib chiqilgan.")
            return

        approved = q.data.startswith("approve_")
        order["status"] = "approved" if approved else "rejected"
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=("✅ Buyurtmangiz admin tomonidan tasdiqlandi."
                  if approved else "❌ Buyurtmangiz rad etildi.")
        )
        await q.message.edit_reply_markup(reply_markup=None)
        await q.message.reply_text(
            f"Buyurtma #{order_id}: {'tasdiqlandi' if approved else 'rad etildi'}."
        )

async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")

    if step == "player_id":
        player_id = update.message.text.strip()
        if not player_id.isdigit():
            await update.message.reply_text("ID faqat raqamlardan iborat bo‘lsin.")
            return

        context.user_data["player_id"] = player_id
        context.user_data["step"] = "receipt"
        await update.message.reply_text(
            "Endi to‘lovni otangiz bergan rasmiy ko‘rsatma asosida amalga oshiring.\n"
            "So‘ng chek rasmini yuboring."
        )
        return

    if step == "receipt" and update.message.photo:
        if ADMIN_ID == 0:
            await update.message.reply_text("Admin ID hali sozlanmagan.")
            return

        name = context.user_data["product"]
        price = context.user_data["price"]
        player_id = context.user_data["player_id"]
        order_id = str(update.effective_user.id) + str(update.message.message_id)

        orders = context.application.bot_data.setdefault("orders", {})
        orders[order_id] = {
            "user_id": update.effective_user.id,
            "status": "pending"
        }

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{order_id}")],
            [InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{order_id}")]
        ])

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=update.message.photo[-1].file_id,
            caption=(
                f"Yangi buyurtma #{order_id}\n"
                f"Mahsulot: {name}\nNarx: {price:,} so‘m\n"
                f"O‘yin ID: {player_id}\n"
                f"Mijoz ID: {update.effective_user.id}\n\n"
                "Pul tushganini bankdan tekshiring."
            ),
            reply_markup=keyboard
        )
        context.user_data.clear()
        await update.message.reply_text(
            "✅ Chek adminga yuborildi. Pul tushishi tekshirilgach javob beriladi."
        )
        return

    if step == "receipt":
        await update.message.reply_text("Iltimos, chek rasmini yuboring.")

async def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN sozlanmagan")
    if not ADMIN_ID:
        raise RuntimeError("ADMIN_ID sozlanmagan")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, messages))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
