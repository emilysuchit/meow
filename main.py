"""
Telegram Bot - CC Filter by MM|YY
Admin သီးသန့်သုံးလို့ရအောင် ပြင်ဆင်ထားပါတယ်
"""

import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ==================== CONFIG ====================
BOT_TOKEN = "8094436736:AAEEizFe5WE9c9aMOHT_--Vw0NIF2zS948Q"           # <--- BotFather ကရတဲ့ Token ထည့်ပါ
ADMIN_IDS = [7132150988, 987654321]           # <--- ကိုယ့် Telegram User ID တွေထည့်ပါ (list အနေနဲ့ အများထည့်လို့ရ)
# =================================================

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# User file cache {user_id: file_path}
user_files = {}


# ==================== HELPERS ====================
def is_admin(user_id: int) -> bool:
    """စစ်ဆေး - Admin ဟုတ်/မဟုတ်"""
    return user_id in ADMIN_IDS


# ==================== HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ ခွင့်မပြုပါ။ Admin များသာ သုံးခွင့်ရှိသည်။")
        return

    await update.message.reply_text(
        "👋 မင်္ဂလာပါ Admin!\n\n"
        "သုံးနည်း:\n"
        "1️⃣ TXT file ပို့ပါ (card_number|MM|YY|CVV format)\n"
        "2️⃣ /filter MM|YY ဆိုပြီး စစ်ထုတ်ပါ\n"
        "   ဥပမာ: /filter 06|26\n\n"
        "အခြား command များ:\n"
        "/count - file ထဲက စုစုပေါင်း ကဒ်အရေအတွက်\n"
        "/clear - သိမ်းထားတဲ့ file ဖျက်မယ်"
    )


async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """TXT file လက်ခံသိမ်းဆည်း"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Admin များသာ သုံးခွင့်ရှိသည်။")
        return

    document = update.message.document

    # TXT file ဟုတ်မဟုတ် စစ်
    if not document.file_name.endswith(".txt"):
        await update.message.reply_text("⚠️ TXT file သာ ပို့ပေးပါ။")
        return

    # File size limit (50MB)
    if document.file_size > 50 * 1024 * 1024:
        await update.message.reply_text("⚠️ File size 50MB ထက် မကျော်ပါစေနဲ့။")
        return

    await update.message.reply_text("📥 File လက်ခံနေသည်...")

    # Download file
    file = await document.get_file()
    file_path = f"data/user_{user_id}.txt"
    os.makedirs("data", exist_ok=True)
    await file.download_to_drive(file_path)

    # Count lines
    with open(file_path, "r") as f:
        line_count = sum(1 for _ in f)

    user_files[user_id] = file_path

    await update.message.reply_text(
        f"✅ File သိမ်းပြီးပါပြီ။\n"
        f"📄 Filename: {document.file_name}\n"
        f"📊 စုစုပေါင်း: {line_count} ကဒ်\n\n"
        f"စစ်ထုတ်ရန်: /filter MM|YY"
    )


async def filter_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """MM|YY နဲ့ ကဒ်တွေစစ်ထုတ်"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Admin များသာ သုံးခွင့်ရှိသည်။")
        return

    # File ရှိမရှိ စစ်
    if user_id not in user_files or not os.path.exists(user_files[user_id]):
        await update.message.reply_text("❌ အရင် TXT file ပို့ပေးပါ။")
        return

    # Argument စစ်
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "❌ ပုံစံမှားနေပါတယ်။\n"
            "သုံးနည်း: /filter 06|26"
        )
        return

    pattern = context.args[0].strip()

    # Pattern format စစ် (e.g. 06|26)
    parts = pattern.split("|")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        await update.message.reply_text(
            "❌ Pattern ပုံစံမှားနေပါတယ်။\n"
            "မှန်: /filter 06|26\n"
            "MM|YY ပုံစံဖြစ်ရပါမယ်။"
        )
        return

    await update.message.reply_text(f"🔍 {pattern} date နဲ့ ကဒ်တွေ ရှာနေသည်...")

    # Read & filter
    try:
        with open(user_files[user_id], "r") as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"File read error: {e}")
        await update.message.reply_text("❌ File ဖတ်မရပါ။ ပြန်ပို့ပေးပါ။")
        return

    # Filter lines containing |MM|YY|
    search_key = f"|{pattern}|"
    filtered = [line for line in lines if search_key in line]

    if not filtered:
        await update.message.reply_text(
            f"❌ {pattern} date နဲ့ ကဒ်တစ်ခုမှ မတွေ့ပါ။\n"
            f"စုစုပေါင်း file ထဲမှာ {len(lines)} ကဒ်ရှိပါတယ်။"
        )
        return

    # Save to output file
    safe_pattern = pattern.replace("|", "_")
    output_path = f"data/filtered_{user_id}_{safe_pattern}.txt"
    with open(output_path, "w") as f:
        f.writelines(filtered)

    # Send result
    caption = (
        f"📁 Filter: {pattern}\n"
        f"📊 တွေ့ရှိ: {len(filtered)} ကဒ်\n"
        f"📄 File ထဲမှာ စုစုပေါင်း: {len(lines)} ကဒ်"
    )
    await update.message.reply_document(
        document=open(output_path, "rb"),
        filename=f"filtered_{safe_pattern}.txt",
        caption=caption,
    )

    logger.info(f"User {user_id} filtered {pattern}: {len(filtered)} results")


async def count_lines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """File ထဲက စာကြောင်းရေတွက်"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    if user_id not in user_files or not os.path.exists(user_files[user_id]):
        await update.message.reply_text("❌ အရင် TXT file ပို့ပေးပါ။")
        return

    with open(user_files[user_id], "r") as f:
        count = sum(1 for _ in f)

    await update.message.reply_text(f"📊 စုစုပေါင်း: {count} ကဒ်")


async def clear_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """သိမ်းထားတဲ့ file ဖျက်"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    if user_id in user_files:
        try:
            os.remove(user_files[user_id])
        except:
            pass
        del user_files[user_id]

    await update.message.reply_text("🗑️ သိမ်းထားတဲ့ File ဖျက်ပြီးပါပြီ။")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """သိပ်မသိတဲ့ command တွေအတွက်"""
    await update.message.reply_text("❓ မသိတဲ့ command ပါ။ /start နဲ့ ကြည့်ပါ။")


# ==================== MAIN ====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("filter", filter_cards))
    app.add_handler(CommandHandler("count", count_lines))
    app.add_handler(CommandHandler("clear", clear_file))

    # File handler (TXT only)
    app.add_handler(MessageHandler(filters.Document.TXT, handle_file))

    # Unknown command fallback
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    logger.info("Bot started...")
    print("🤖 Bot is running... Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
