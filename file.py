import os
import requests
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackContext, ConversationHandler
)

# States for ConversationHandler
UPLOAD_FILE, DOWNLOAD_FILE = range(2)

# /start Command
async def start_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Welcome to the FileEase!\n\n"
        "You can use this bot to upload and retrieve files easily.\n"
        "Commands:\n"
        "/upload - Upload a file (≤500MB)\n"
        "/getfile - Retrieve a file using link or ID\n"
        "/about - About the bot\n"
        "/donate - Support the bot\n"
        "/cancel - Cancel the current operation"
    )

# /upload Command
async def upload_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Please upload the file :")
    return UPLOAD_FILE

# Handle file upload and storage via GoFile
async def handle_file_upload(update: Update, context: CallbackContext):
    if update.message.document:
        file = update.message.document

        if file.file_size > 500 * 1024 * 1024:
            await update.message.reply_text("File too large!")
            return UPLOAD_FILE

        telegram_file = await file.get_file()
        local_path = f"temp_{file.file_name}"
        await telegram_file.download_to_drive(local_path)

        try:
            with open(local_path, "rb") as f:
                response = requests.post("https://store1.gofile.io/uploadFile", files={"file": f})

            os.remove(local_path)

            if response.status_code == 200 and response.json()["status"] == "ok":
                link = response.json()["data"]["downloadPage"]
                await update.message.reply_text(f"File uploaded\nDownload Link:\n{link}")
            else:
                await update.message.reply_text("Failed to upload file. Try again later.")
        except Exception as e:
            await update.message.reply_text(f"Error uploading file: {str(e)}")
    else:
        await update.message.reply_text("Please upload a valid file.")
        return UPLOAD_FILE

    return ConversationHandler.END

# /getfile Command
async def getfile_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Please enter the specific link or File ID:")
    return DOWNLOAD_FILE

# Handle file retrieval
async def handle_file_download(update: Update, context: CallbackContext):
    user_input = update.message.text.strip()

    if user_input.startswith("https://gofile.io/d/"):
        await update.message.reply_text(f"Here’s your file:\n{user_input}")
    else:
        await update.message.reply_text(f"Your file might be at:\nhttps://gofile.io/d/{user_input}")
    
    return ConversationHandler.END

# /cancel Command
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Operation canceled.")
    return ConversationHandler.END

async def about_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "About File Uploader Bot\n\n"
        "This bot allows you to upload files securely to the cloud and get a shareable download link instantly.\n"
        "You can also retrieve files using an ID or link!\n\n"
        "Built with love by:[Aman Rembersu](https://t.me/erenjeagerer)\n"
        "Minimal, fast, and private.\n\n"
        "Type /upload to get started._",
        parse_mode='Markdown'
    )

async def donate_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Support File Uploader Bot\n\n"
        "If you find this bot useful, consider supporting its development!\n"
        "Your donations help keep the server running and improve features.\n\n"
        "Donate via UPI: `buymeacoffee.com/amanrembersu\n"
        "\n"
        "Thanks you",
        parse_mode='Markdown'
    )


# Main function
def main():
    application = Application.builder().token("YOUR_BOT_TOKEN_HERE").build()

    # Upload & Download Conversation Handlers
    file_handler = ConversationHandler(
        entry_points=[
            CommandHandler("upload", upload_command),
            CommandHandler("getfile", getfile_command),
        ],
        states={
            UPLOAD_FILE: [MessageHandler(filters.Document.ALL, handle_file_upload)],
            DOWNLOAD_FILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_file_download)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(file_handler)
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("donate", donate_command))


    application.run_polling()

if __name__ == "__main__":
    main()
