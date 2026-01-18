import os
import asyncio

from yt_dlp import YoutubeDL
from pyrogram import enums
from pyrogram.types import Message
from pyrogram import Client, filters

from config import Config
from plugins.functions.help_ytdl import get_file_extension_from_url, get_resolution
YTDL_REGEX = r"^((?:https?:)?\/\/)"

@Client.on_callback_query(filters.regex("^ytdl_audio$"))
async def callback_query_ytdl_audio(_, callback_query):
    print("Audio callback triggered")  # Log start
    try:
        url = callback_query.message.reply_to_message.text
        print(f"URL: {url}")  # Log URL
        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": "%(title)s - %(extractor)s-%(id)s.%(ext)s",
            "writethumbnail": True,
            'cookiefile': 'cookies.txt',
        }
        with YoutubeDL(ydl_opts) as ydl:
            message = callback_query.message
            await message.reply_chat_action(enums.ChatAction.TYPING)
            info_dict = ydl.extract_info(url, download=False)
            print("Info extracted")  # Log info step
            await callback_query.edit_message_text("**Downloading audio...**")
            ydl.process_info(info_dict)
            print("Download complete")  # Log download
            audio_file = ydl.prepare_filename(info_dict)
            print(f"Audio file: {audio_file}")  # Log file path
            task = asyncio.create_task(send_audio(message, info_dict, audio_file))
            while not task.done():
                await asyncio.sleep(3)
                await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
            await message.reply_chat_action(enums.ChatAction.CANCEL)
            await message.delete()
    except Exception as e:
        print(f"Error in audio: {str(e)}")  # Log error
        await callback_query.message.reply_text(str(e))
    await callback_query.message.reply_to_message.delete()
    await callback_query.message.delete()

async def send_audio(message: Message, info_dict, audio_file):
    print("Sending audio")  # Log upload start
    basename = audio_file.rsplit(".", 1)[-2]
    if info_dict["ext"] == "webm":
        audio_file_weba = f"{basename}.weba"
        os.rename(audio_file, audio_file_weba)
        audio_file = audio_file_weba
    thumbnail_url = info_dict["thumbnail"]
    thumbnail_file = f"{basename}.{get_file_extension_from_url(thumbnail_url)}"
    download_location = f"{Config.DOWNLOAD_LOCATION}/{message.from_user.id}.jpg"
    thumb = download_location if os.path.isfile(download_location) else None
    webpage_url = info_dict["webpage_url"]
    title = info_dict.get("title", "")
    caption = f"[{title}]({webpage_url})"
    duration = int(float(info_dict.get("duration", 0)))
    performer = info_dict.get("uploader", "")
    await message.reply_audio(
        audio_file,
        caption=caption,
        duration=duration,
        performer=performer,
        title=title,
        parse_mode=enums.ParseMode.HTML,
        thumb=thumb,
    )
    print("Audio sent")  # Log upload success
    os.remove(audio_file)
    os.remove(thumbnail_file)

# Similar additions for send_video and callback_query_ytdl_video...
# (Copy the pattern: add print statements for key steps and errors)
