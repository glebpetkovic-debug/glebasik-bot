
import os
import sqlite3
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

db = sqlite3.connect("glebasik.db", check_same_thread=False)

db.execute("""
CREATE TABLE IF NOT EXISTS searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    gift TEXT,
    price INTEGER,
    details TEXT
)
""")
db.commit()

users = {}

def menu():
    kb = types.InlineKeyboardMarkup()

    kb.add(types.InlineKeyboardButton(
        "🎁 Добавить подарок", callback_data="add"))

    kb.add(types.InlineKeyboardButton(
        "📋 Мои поиски", callback_data="list"))

    kb.add(types.InlineKeyboardButton(
        "ℹ️ О боте", callback_data="about"))

    return kb


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🤖 Добро пожаловать в Glebasik Bot!\n\n"
        "⭐ Персональный помощник для поиска Telegram-подарков.",
        reply_markup=menu()
    )


@bot.callback_query_handler(func=lambda c: c.data == "add")
def add(call):
    users[call.from_user.id] = {"step": "gift"}

    bot.send_message(
        call.message.chat.id,
        "🎁 Напиши название подарка или коллекции:"
    )

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "list")
def show_list(call):
    rows = db.execute(
        "SELECT id,gift,price,details FROM searches WHERE user_id=?",
        (call.from_user.id,)
    ).fetchall()

    if not rows:
        text = "У тебя пока нет сохранённых поисков."
    else:
        text = "📋 Твои поиски:\n\n"

        for r in rows:
            text += (
                f"🎁 {r[1]}\n"
                f"⭐ До {r[2]} Stars\n"
                f"🔎 {r[3] or 'Без деталей'}\n\n"
            )

    bot.send_message(
        call.message.chat.id,
        text,
        reply_markup=menu()
    )

    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda c: c.data == "about")
def about(call):
    bot.send_message(
        call.message.chat.id,
        "Glebasik Bot ⭐\n"
        "Версия 1.0\n"
        "Сохранение поисков Telegram-подарков."
    )

    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda m: m.from_user.id in users)
def process(message):
    uid = message.from_user.id
    data = users[uid]
    step = data["step"]

    if step == "gift":
        data["gift"] = message.text
        data["step"] = "price"

        bot.send_message(
            message.chat.id,
            "⭐ Напиши максимальную цену в Stars:"
        )

    elif step == "price":
        if not message.text.isdigit() or int(message.text) <= 0:
            bot.send_message(
                message.chat.id,
                "Введи положительное целое число."
            )
            return

        data["price"] = int(message.text)
        data["step"] = "details"

        bot.send_message(
            message.chat.id,
            "🔎 Напиши модель, фон, символ или другие детали.\n"
            "Если не нужны, отправь точку."
        )

    elif step == "details":
        details = "" if message.text == "." else message.text

        db.execute(
            "INSERT INTO searches(user_id,gift,price,details) "
            "VALUES(?,?,?,?)",
            (uid, data["gift"], data["price"], details)
        )

        db.commit()
        del users[uid]

        bot.send_message(
            message.chat.id,
            "✅ Поиск сохранён!\n\n"
            f"🎁 {data['gift']}\n"
            f"⭐ До {data['price']} Stars\n"
            f"🔎 {details or 'Любые детали'}",
            reply_markup=menu()
        )


print("Glebasik Bot запущен!")

bot.infinity_polling()
