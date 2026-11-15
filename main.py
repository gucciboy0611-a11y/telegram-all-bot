
import os
import json
import html
from pathlib import Path

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = Path("members.json")


def load_members():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


members = load_members()


def save_members():
    DATA_FILE.write_text(
        json.dumps(members, ensure_ascii=False),
        encoding="utf-8"
    )


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ("group", "supergroup"):
        await message.reply_text("Команда работает в группе.")
        return

    group = str(chat.id)
    members.setdefault(group, {})
    members[group][str(user.id)] = user.full_name
    save_members()

    await message.reply_text(
        f"{user.first_name}, ты зарегистрирован для уведомлений!"
    )


async def all_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    if chat.type not in ("group", "supergroup"):
        await message.reply_text("Команда работает в группе.")
        return

    group_members = members.get(str(chat.id), {})

    if not group_members:
        await message.reply_text(
            "Пока никто не зарегистрирован. Напишите /register"
        )
        return

    announcement = " ".join(context.args).strip()
    if not announcement:
        await message.reply_text("Напиши сообщение после /all")
        return

    mentions = [
        f'<a href="tg://user?id={user_id}">{html.escape(name)}</a>'
        for user_id, name in group_members.items()
    ]

    chunks = []
    current = []

    for mention in mentions:
        current.append(mention)
        if len(current) >= 15:
            chunks.append(current)
            current = []

    if current:
        chunks.append(current)

    for i, chunk in enumerate(chunks):
        text = " ".join(chunk)
        if i == 0:
            text += "\n\n" + html.escape(announcement)

        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )


def main():
    if not TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("all", all_members))
    app.run_polling()


if __name__ == "__main__":
    main()
