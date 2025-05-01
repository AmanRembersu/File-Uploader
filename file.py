import os # os is a module used to interact with operating system but here i have used it for file deleting
import requests # requests is a lobrary used to send http requests to other external servers
from telegram import Update #update is a class represents an incoming update from tele
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackContext, ConversationHandler
)# CallbackContext is used to pass context to the callback functions
# Define the conversation states
# The states are used to manage the conversation flow
#message handler is used to handle the incoming messages
# filters is used to filter the incoming messages based on certain criteria
# and ConversationHandler is used to manage the conversation flow
# and handle the different states of the conversation

# Define conversation states for upload and download
# these are thje constants that represent states of converstaion
UPLOAD_FILE, DOWNLOAD_FILE = range(2)
unique_users = set() # this is a set that stores the unique users who have interacted with the bot
# to store the unique users who have interacted with the bot

# /start command handler
async def start_command(update: Update, context: CallbackContext):
    # Add the user to the unique users set
    user_id = update.effective_user.id
    username = update.effective_user.username or "no_username"

    unique_users.add(user_id)

    print(f"User interacting : {user_id} (@{username})")
    print(f"total users traffic: {len(unique_users)}")

    await update.message.reply_text(
        "Welcome to FileEase!\n\n"
        "This bot helps you upload and retrieve files.\n\n"
        "Available Commands:\n"
        "/upload - Upload a file (up to 500MB)\n"
        "/getfile - Retrieve a file using a link or ID\n"
        "/about - Learn more about this bot\n"
        "/donate - Support the bot\n"
        "/cancel - Cancel the current operation"
    ) # sends this messahge when the user starts the bot

# /upload command handler
async def upload_command(update: Update, context: CallbackContext):#it asks the user to upload the file
    await update.message.reply_text("Please upload the file (maximum size 500MB):")#  after uploading file returns to upload file state
    return UPLOAD_FILE

# Handle uploaded file and send it to GoFile
async def handle_file_upload(update: Update, context: CallbackContext):
    if update.message.document: # checks the file uploaded by the user
        file = update.message.document

        # Check if file size exceeds 500MB
        if file.file_size > 500 * 1024 * 1024: # simple validation of the size
            await update.message.reply_text("The file is too large. Maximum allowed size is 500MB.")
            return UPLOAD_FILE # returns to upload file state

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

# /getfile command handler to retirenve the file
async def getfile_command(update: Update, context: CallbackContext):
    await update.message.reply_text("Please enter the File ID or GoFile download link:")
    return DOWNLOAD_FILE

# Handle file retrieval input after uploading
async def handle_file_download(update: Update, context: CallbackContext):
    user_input = update.message.text.strip()

    # If user provides a full GoFile URL
    if user_input.startswith("https://gofile.io/d/"):
        await update.message.reply_text(f"Here is your file:\n{user_input}")
    else:
        # Treat input as file ID and generate the link
        await update.message.reply_text(f"Here is the possible download link:\nhttps://gofile.io/d/{user_input}")
    
    return ConversationHandler.END

# /cancel command handler to cancel anu process just timepass
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# /about command handler to shoq about this bot
async def about_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "*About the Bot:*\n\n"
        "Developer: *Aman*\n"
        "This bot allows users to upload files (up to 500MB) and retrieve them using download links.\n"
        "Technologies used: Python, SQLite, and GoFile API.\n\n"
        "_Thank you for using FileEase!_",
        parse_mode='Markdown'
    )

# /donate command handler to 
async def donate_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "*Support File Uploader Bot:*\n\n"
        "If you find this bot helpful, consider donating to support its development.\n"
        "`buymeacoffee.com/amanrembersu`\n\n"
        "Thank you for your support!",
        parse_mode='Markdown'
    )

# Main function to initialize and run the bot
def main():
    # Initialize the bot application with your bot token to run the bot
    # Replace with your actual bot token here ...
    application = Application.builder().token("").build()  # Replace with your actual bot token

    # Create a conversation handler to manage upload and download interactions when . /upload and /get file is used
    file_handler = ConversationHandler(
        entry_points=[
            CommandHandler("upload", upload_command),
            CommandHandler("getfile", getfile_command),
        ],
        states={
            UPLOAD_FILE: [MessageHandler(filters.Document.ALL, handle_file_upload)],
            DOWNLOAD_FILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_file_download)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],# to cancel the process return the state to the initial state
    )

    # Add all command handlers to the application used commands and functions according to their purpose
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(file_handler)
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("donate", donate_command))

    # Start polling to receive updates from Telegram
    application.run_polling() # to run the bot and receive  from telegram

# Run the bot if this file is executed
if __name__ == "__main__":
    main()
