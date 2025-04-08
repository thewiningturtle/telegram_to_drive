import os
import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaDocument

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

import streamlit as st

st.title("📩 Auto Telegram to Google Drive Uploader")

api_id = 29685879
api_hash = 'e2808e2a18c6de8c07a8dd4c1838fc7e'
channel = 'MoneyTimes'
download_dir = './telegram_downloads'
session_file = 'telegram_session'

if not os.path.exists(download_dir):
    os.makedirs(download_dir)

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
    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, resumable=True)
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    st.success(f"✅ Uploaded to Google Drive: {file_path}")

# 🧠 Fix: Streamlit thread has no default asyncio loop
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

client = TelegramClient(session_file, api_id, api_hash)

@client.on(events.NewMessage(chats=channel))
async def handler(event):
    if event.media and isinstance(event.media, MessageMediaDocument):
        filename = event.file.name or f"{event.id}"
        path = os.path.join(download_dir, filename)
        await event.download_media(file=path)
        st.info(f"📥 Downloaded: {filename}")
        upload_to_drive(path)

st.success(f"🚀 Listening for new files on @{channel}...")

client.start()
client.run_until_disconnected()
