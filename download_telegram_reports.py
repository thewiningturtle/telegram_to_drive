from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaDocument
import os

# Replace with your actual API credentials
api_id = 29685879        # 🔁 Replace with your API ID
api_hash = 'e2808e2a18c6de8c07a8dd4c1838fc7e' # 🔁 Replace with your API Hash
channel_username = 'MoneyTimes'  # e.g. 'mychannel' or 'https://t.me/mychannel'

# Folder to save downloaded files
download_folder = './telegram_downloads'
os.makedirs(download_folder, exist_ok=True)

with TelegramClient('telegram_session', api_id, api_hash) as client:
    for message in client.iter_messages(channel_username):
        if message.media and isinstance(message.media, MessageMediaDocument):
            filename = message.file.name or f"{message.id}"
            print(f"Downloading: {filename}")
            client.download_media(message, file=os.path.join(download_folder, filename))
