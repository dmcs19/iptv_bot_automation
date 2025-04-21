from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from form_bot import run_form_process

BOT_TOKEN = "8020314661:AAFUpm4RJPFeMXfZMWYTdpl6LB4BtJGG-KQ"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /run to start the automation.")

async def run(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("Running... Please wait ⏳")
        result = await run_form_process()
        await update.message.reply_text(f"✅ Done:\n\n{result}")
    except Exception as e:
        await update.message.reply_text(f"❌ Something went wrong: {e}")


app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("run", run))
app.run_polling()
