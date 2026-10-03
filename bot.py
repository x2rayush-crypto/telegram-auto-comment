import os
import asyncio

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

channel = None
comment = None
running = False
selected_entity = None
post_handler = None


user_client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH
)


def is_owner(update: Update):
    return update.effective_user and update.effective_user.id == OWNER_ID


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


async def new_post(event):
    global running, comment, selected_entity

    if not running or not comment or selected_entity is None:
        return

    try:
        print(f"New post detected: {event.message.id}")

        await user_client.send_message(
            selected_entity,
            comment,
            comment_to=event.message.id
        )

        print(f"Comment posted on message {event.message.id}")

    except Exception as e:
        print(f"Comment error: {e}")


async def startcomment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running, selected_entity, post_handler

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
        selected_entity = await user_client.get_entity(channel)

        if post_handler is not None:
            user_client.remove_event_handler(post_handler)
            post_handler = None

        post_handler = user_client.add_event_handler(
            new_post,
            events.NewMessage(chats=selected_entity)
        )

        running = True

        title = getattr(selected_entity, "title", channel)

        print(
            f"Monitoring channel: {title} "
            f"(id={getattr(selected_entity, 'id', 'unknown')})"
        )

        await update.message.reply_text(
            f"🟢 Auto-comment STARTED\n\n"
            f"Channel: {channel}\n"
            f"Comment: {comment}"
        )

    except Exception as e:
        running = False
        selected_entity = None
        post_handler = None

        await update.message.reply_text(
            f"❌ Cannot access channel.\n\n{e}"
        )


async def stopcomment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running, post_handler, selected_entity

    if not is_owner(update):
        return

    running = False

    if post_handler is not None:
        user_client.remove_event_handler(post_handler)
        post_handler = None

    selected_entity = None

    await update.message.reply_text(
        "🔴 Auto-comment STOPPED"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    await update.message.reply_text(
        f"📊 STATUS\n\n"
        f"Channel: {channel or 'Not set'}\n"
        f"Comment: {comment or 'Not set'}\n"
        f"Running: {'YES 🟢' if running else 'NO 🔴'}"
    )


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
