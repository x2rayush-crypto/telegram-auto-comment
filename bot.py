import os
import asyncio

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# =========================
# RAILWAY VARIABLES
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# =========================
# SETTINGS
# =========================

channel = None
comment = None
running = False

# =========================
# TELEGRAM USER SESSION
# =========================

user_client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH
)


# =========================
# OWNER CHECK
# =========================

def is_owner(update: Update):
    return update.effective_user and update.effective_user.id == OWNER_ID


# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    await update.message.reply_text(
        "🤖 Auto Comment Bot\n\n"
        "/setchannel @channel\n"
        "/setcomment Your comment\n"
        "/startcomment\n"
        "/stopcomment\n"
        "/status"
    )


# =========================
# /setchannel
# =========================

async def setchannel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global channel

    if not is_owner(update):
        return

    if not context.args:
        await update.message.reply_text(
            "Example:\n/setchannel @yourchannel"
        )
        return

    channel = context.args[0]

    await update.message.reply_text(
        f"✅ Channel set:\n{channel}"
    )


# =========================
# /setcomment
# =========================

async def setcomment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global comment

    if not is_owner(update):
        return

    if not context.args:
        await update.message.reply_text(
            "Example:\n/setcomment 🏏🔥 Great post!"
        )
        return

    comment = " ".join(context.args)

    await update.message.reply_text(
        f"✅ Comment set:\n{comment}"
    )


# =========================
# /startcomment
# =========================

async def startcomment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running

    if not is_owner(update):
        return

    if not channel:
        await update.message.reply_text(
            "❌ First set channel:\n/setchannel @channel"
        )
        return

    if not comment:
        await update.message.reply_text(
            "❌ First set comment:\n/setcomment Your comment"
        )
        return

    try:
        entity = await user_client.get_entity(channel)

        running = True

        await update.message.reply_text(
            f"🟢 Auto-comment STARTED\n\n"
            f"Channel: {channel}\n"
            f"Comment: {comment}"
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Cannot access channel.\n\n{e}"
        )


# =========================
# /stopcomment
# =========================

async def stopcomment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running

    if not is_owner(update):
        return

    running = False

    await update.message.reply_text(
        "🔴 Auto-comment STOPPED"
    )


# =========================
# /status
# =========================

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    await update.message.reply_text(
        f"📊 STATUS\n\n"
        f"Channel: {channel or 'Not set'}\n"
        f"Comment: {comment or 'Not set'}\n"
        f"Running: {'YES 🟢' if running else 'NO 🔴'}"
    )


# =========================
# NEW CHANNEL POST
# =========================

@user_client.on(events.NewMessage())
async def new_post(event):
    global running

    if not running:
        return

    if not channel or not comment:
        return

    try:
        entity = await user_client.get_entity(channel)

        if event.chat_id != entity.id:
            return

        # Comment only when Telegram allows the account
        await user_client.send_message(
            entity,
            comment,
            comment_to=event.message.id
        )

        print(
            f"Comment posted on message {event.message.id}"
        )

    except Exception as e:
        print(f"Comment error: {e}")


# =========================
# MAIN
# =========================

async def main():

    await user_client.start()

    print("Telegram user session connected")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setchannel", setchannel))
    app.add_handler(CommandHandler("setcomment", setcomment))
    app.add_handler(CommandHandler("startcomment", startcomment))
    app.add_handler(CommandHandler("stopcomment", stopcomment))
    app.add_handler(CommandHandler("status", status))

    print("Control bot is running")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    await user_client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
