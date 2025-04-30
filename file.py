import os
import requests
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackContext, ConversationHandler
)

# Define conversation states for upload and download
UPLOAD_FILE, DOWNLOAD_FILE = range(2)

# /start command handler
async def start_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Welcome to FileEase!\n\n"
        "This bot helps you upload and retrieve files.\n\n"
        "Available Commands:\n"
        "/upload - Upload a file (up to 500MB)\n"
        "/getfile - Retrieve a file using a link or ID\n"
        "/about - Learn more about this bot\n"
        "/donate - Support the bot\n"
        "/cancel - Cancel the current operation"
    )

# /upload command handler
async def upload_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Please upload the file (maximum size 500MB):")
    return UPLOAD_FILE

# Handle uploaded file and send it to GoFile
async def handle_file_upload(update: Update, context: CallbackContext):
    if update.message.document:
        file = update.message.document

        # Check if file size exceeds 500MB
        if file.file_size > 500 * 1024 * 1024:
            await update.message.reply_text("The file is too large. Maximum allowed size is 500MB.")
            return UPLOAD_FILE

        # Download the file locally
        telegram_file = await file.get_file()
        local_path = f"temp_{file.file_name}"
        await telegram_file.download_to_drive(local_path)

        try:
            # Upload file to GoFile API
            with open(local_path, "rb") as f:
                response = requests.post("https://store1.gofile.io/uploadFile", files={"file": f})
            os.remove(local_path)  # Delete local file after upload

            # Check response and send link
            if response.status_code == 200 and response.json()["status"] == "ok":
                link = response.json()["data"]["downloadPage"]
                await update.message.reply_text(f"File uploaded successfully!\n\nDownload Link:\n{link}")
            else:
                await update.message.reply_text("Failed to upload the file. Please try again later.")
        except Exception as e:
            await update.message.reply_text(f"An error occurred during upload:\n{str(e)}")
    else:
        await update.message.reply_text("Please upload a valid file.")
        return UPLOAD_FILE

    return ConversationHandler.END

# /getfile command handler
async def getfile_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Please enter the File ID or GoFile download link:")
    return DOWNLOAD_FILE

# Handle file retrieval input
async def handle_file_download(update: Update, context: CallbackContext):
    user_input = update.message.text.strip()

    # If user provides a full GoFile URL
    if user_input.startswith("https://gofile.io/d/"):
        await update.message.reply_text(f"Here is your file:\n{user_input}")
    else:
        # Treat input as file ID and generate the link
        await update.message.reply_text(f"Here is the possible download link:\nhttps://gofile.io/d/{user_input}")
    
    return ConversationHandler.END

# /cancel command handler
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# /about command handler
async def about_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "*About the Bot:*\n\n"
        "Developer: *Aman*\n"
        "This bot allows users to upload files (up to 500MB) and retrieve them using download links.\n"
        "Technologies used: Python, SQLite, and GoFile API.\n\n"
        "_Thank you for using FileEase!_",
        parse_mode='Markdown'
    )

# /donate command handler
async def donate_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "*Support File Uploader Bot:*\n\n"
        "If you find this bot helpful, consider donating to support its development.\n"
        "Donation Link:\n"
        "`buymeacoffee.com/amanrembersu`\n\n"
        "Thank you for your support!",
        parse_mode='Markdown'
    )

# Main function to initialize and run the bot
def main():
    # Initialize the bot application with your bot token
    application = Application.builder().token("").build()  # Replace with your actual bot token

    # Create a conversation handler to manage upload and download interactions
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

    # Add all command handlers to the application
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(file_handler)
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("donate", donate_command))

    # Start polling to receive updates from Telegram
    application.run_polling()

# Run the bot if this file is executed
if __name__ == "__main__":
    main()
