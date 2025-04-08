import os
import asyncio
import streamlit as st
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaDocument

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# --- CONFIG ---
api_id = 29685879  # Replace with your actual API ID
api_hash = 'e2808e2a18c6de8c07a8dd4c1838fc7e'  # Replace with your API Hash
channel = 'MoneyTimes'  # Telegram channel without '@'
download_dir = './telegram_downloads'
session_file = 'telegram_session'
drive_folder_id = '1yAm3WCrRzFJ5LTbJUXpxcu_fUlX47OWu'  # Google Drive folder ID

# --- UI ---
st.set_page_config(page_title="📥 Auto Telegram to Google Drive Uploader")
st.title("📥 Auto Telegram to Google Drive Uploader")
st.success("🚀 Listening for new files on @MoneyTimes...")

# --- CREATE DOWNLOAD FOLDER ---
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# --- GOOGLE DRIVE SETUP ---
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_gdrive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

drive_service = get_gdrive_service()

def upload_to_drive(file_path):
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [drive_folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"✅ Uploaded to Google Drive folder: {file_path}")

# --- TELEGRAM LISTENER SETUP ---
client = TelegramClient(session_file, api_id, api_hash)

@client.on(events.NewMessage(chats=channel))
async def handler(event):
    if event.media and isinstance(event.media, MessageMediaDocument):
        filename = event.file.name or f"{event.id}"
        path = os.path.join(download_dir, filename)
        await event.download_media(file=path)
        print(f"📥 Downloaded: {filename}")
        upload_to_drive(path)

# --- ASYNCIO FIX FOR STREAMLIT ---
def run_telegram_client():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with client:
        client.loop.run_until_complete(client.start())
        client.run_until_disconnected()

import threading
threading.Thread(target=run_telegram_client).start()
