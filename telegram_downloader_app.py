import streamlit as st
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaDocument
import os

# Streamlit UI
st.title("📥 Telegram File Downloader")
api_id = st.text_input("API ID")
api_hash = st.text_input("API Hash", type="password")
channel = st.text_input("Channel Username (e.g., @mychannel)")
file_type = st.selectbox("File Type", ["All", "PDF", "Excel", "Images"])
download_button = st.button("Download Files")

if download_button:
    if not all([api_id, api_hash, channel]):
        st.error("Please fill in all fields.")
    else:
        download_folder = "./downloads"
        os.makedirs(download_folder, exist_ok=True)

        with TelegramClient("streamlit_session", int(api_id), api_hash) as client:
            count = 0
            for msg in client.iter_messages(channel):
                if msg.media and isinstance(msg.media, MessageMediaDocument):
                    filename = msg.file.name or f"{msg.id}"

                    if file_type == "PDF" and not filename.endswith(".pdf"):
                        continue
                    elif file_type == "Excel" and not filename.endswith((".xls", ".xlsx")):
                        continue
                    elif file_type == "Images" and not filename.endswith((".jpg", ".jpeg", ".png")):
                        continue

                    client.download_media(msg, file=os.path.join(download_folder, filename))
                    st.write(f"✅ Downloaded: {filename}")
                    count += 1

            if count == 0:
                st.warning("No files matched your criteria.")
            else:
                st.success(f"Downloaded {count} file(s).")
