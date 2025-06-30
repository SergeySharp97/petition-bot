from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = "6935472754:AAGe6GRLmhosWSYLbN6Dgh-qpMQpgQxxEuE"
ADMIN_CHAT_ID = 5185045869
CHANNEL_USERNAME = "@Save_Ukraine_UA"

user_states = {}

def clean_text(text: str) -> str:
    import re
    text = re.sub(r'[\*_`]', '', text)
    return text.strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("\U0001F4E8 Подати петицію", callback_data="submit_petition")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("\U0001F44B Привіт! Оберіть опцію:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text("\U0001F44B Привіт! Оберіть опцію:", reply_markup=reply_markup)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "submit_petition":
        caption = (
            "❗️ Щоб ми опублікували вашу петицію, виконайте одну з умов:\n"
            "1. Поширте посилання на групу серед 15–20 знайомих.\n"
            "2. Або підтримайте розвиток спільноти.\n\n"
            "Оберіть варіант нижче."
        )
        keyboard = [
            [InlineKeyboardButton("\U0001F501 Поширити групу", callback_data="share_group")],
            [InlineKeyboardButton("\U0001F4B8 Підтримати розвиток спільноти", callback_data="donate")]
        ]
        await query.message.reply_text(caption, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["share_group", "donate"]:
        method = "Поширення групи" if query.data == "share_group" else "Донат"
        user_states[user_id] = {"step": "awaiting_proof", "method": method, "proof_photos": []}

        if query.data == "donate":
            text = (
                "Ми вже два роки активно розвиваємо спільноти та канали, які наближають нашу країну до Перемоги.\n"
                "Частина прибутку з монетизації Каналу йде на підтримку людей, які щодня працюють задля допомоги нашим захисникам.\n"
                "Але щоб ці спільноти приносили ще більше користі, потрібно постійно інвестувати в рекламу.\n\n"
                "Саме для цього ми створили банку для розвитку Каналу.\n\n"
                "\U0001F517 Посилання банки: https://send.monobank.ua/jar/3fFzMioXwn\n"
                "\U0001F3E6 Номер банки: 5375 4112 1778 2270\n\n"
                "<b>Сума донату не важлива — важливо, як ви оцінюєте наш час.</b>\n"
                "Після виконання правил публікації натисніть 'Умови виконані'."
            )
            await query.message.reply_text(text, parse_mode="HTML")
        else:
            await query.message.reply_text(
                "\U0001F4E3 Поширте посилання на групу серед людей, з якими ви обмінювались підписами (10–15 чатів).\n"
                "Скопіюйте посилання та поширте:\n"
                "\U0001F517 https://t.me/Save_Ukraine_UA\n\n"
                "Після виконання правил публікації натисніть 'Умови виконані'."
            )

        await query.message.reply_text(
            "Після виконання правил публікації натисніть кнопку нижче:",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Умови виконані", callback_data="confirm_done")]])
        )

    elif query.data == "confirm_done":
        user_state = user_states.get(user_id, {})
        if user_state.get("proof_photos"):
            for photo in user_state["proof_photos"]:
                await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo)
            user_state["step"] = "awaiting_photo"
            await query.message.reply_text("✍️ Надішліть фото Героя.")
        else:
            await query.message.reply_text("❗ Будь ласка, спершу надішліть скріншоти, які підтверджують виконання умови.")

async def handle_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user_id = update.message.from_user.id
    user_state = user_states.setdefault(user_id, {})

    if user_state.get("step") == "awaiting_proof":
        user_state.setdefault("proof_photos", []).append(update.message.photo[-1].file_id)
        await update.message.reply_text("Після виконання правил публікації натисніть 'Умови виконані'.")

    elif user_state.get("step") == "awaiting_photo":
        user_state["hero_photo"] = update.message.photo[-1].file_id
        user_state["step"] = "awaiting_hero_name"
        await update.message.reply_text("✍️ Напишіть ім’я та по батькові Героя.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    user_id = update.message.from_user.id
    user_state = user_states.setdefault(user_id, {})
    text = update.message.text

    if user_state.get("step") == "awaiting_hero_name":
        user_state["hero_name"] = clean_text(text)
        user_state["step"] = "awaiting_petition_link"
        await update.message.reply_text("🔗 Надішліть посилання на петицію.")

    elif user_state.get("step") == "awaiting_petition_link":
        user_state["petition_link"] = clean_text(text)
        user_state["step"] = "awaiting_exchange_contacts"
        await update.message.reply_text("🔁 Надішліть контакти для обміну петиціями.")

    elif user_state.get("step") == "awaiting_exchange_contacts":
        user_state["exchange_contacts"] = clean_text(text)
        user_state["step"] = "completed"

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Схвалити петицію", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("❌ Відхилити", callback_data=f"reject_{user_id}")
            ]
        ])

        caption = (
            f"📝 <b>Герой:</b> {user_state['hero_name']}\n"
            f"🔗 <b>Петиція:</b> {user_state['petition_link']}\n"
            f"🔁 <b>Обмін:</b> {user_state['exchange_contacts']}\n\n"
            f"🔗 <b>Приєднуйтесь до нашої спільноти:</b> https://t.me/Save_Ukraine_UA\n"
            f"📣 <b>Поширте петицію — кожен голос має значення!</b>"
        )

        message = await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=user_state['hero_photo'],
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        user_state['admin_message_id'] = message.message_id
        await update.message.reply_text("✅ Дякуємо! Петицію надіслано на перевірку.")

async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = int(data.split("_")[1])
    user_state = user_states.get(user_id)

    if not user_state:
        await query.edit_message_caption(caption=query.message.caption + "\n\n⚠️ Дані користувача не знайдено.", reply_markup=None, parse_mode="HTML")
        return

    if data.startswith("approve_"):
        await query.edit_message_caption(caption=query.message.caption + "\n\n✅ Петицію схвалено та опубліковано!", reply_markup=None, parse_mode="HTML")

        await context.bot.send_photo(
            chat_id=CHANNEL_USERNAME,
            photo=user_state['hero_photo'],
            caption=(
                f"📝 <b>Герой:</b> {user_state['hero_name']}\n"
                f"🔗 <b>Петиція:</b> {user_state['petition_link']}\n"
                f"🔁 <b>Обмін:</b> {user_state['exchange_contacts']}\n\n"
                f"🔗 <b>Приєднуйтесь до нашої спільноти:</b> https://t.me/Save_Ukraine_UA\n"
                f"📣 <b>Поширте петицію — кожен голос має значення!</b>"
            ),
            parse_mode="HTML"
        )

    elif data.startswith("reject_"):
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ Петицію відхилено.", reply_markup=None, parse_mode="HTML")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons, pattern="^(submit_petition|share_group|donate|confirm_done)$"))
    app.add_handler(CallbackQueryHandler(handle_admin_buttons, pattern="^(approve_|reject_).*"))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photos))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()
