# plugins/youtube.py
import os
import asyncio
import json

# Use yt-dlp instead of youtube_dl
from yt_dlp import YoutubeDL
from pyrogram import enums
from pyrogram.types import Message
from pyrogram import Client, filters

from config import Config
from plugins.functions.help_ytdl import get_file_extension_from_url, get_resolution

YTDL_REGEX = r"^((?:https?:)?\/\/)"


def load_cookies():
    """Load cookies from file if it exists"""
    if os.path.exists(Config.COOKIE_FILE):
        # Check if it's a Netscape format cookie file or JSON
        with open(Config.COOKIE_FILE, 'r') as f:
            content = f.read().strip()
            
        if content.startswith('#'):  # Netscape format
            return Config.COOKIE_FILE
        elif content.startswith('[') or content.startswith('{'):  # JSON format
            # yt-dlp expects Netscape format, convert if needed
            try:
                cookies_data = json.loads(content)
                # You might want to convert JSON to Netscape format here
                # For simplicity, we'll just return the file path
                # and let yt-dlp handle it if it supports JSON
                return Config.COOKIE_FILE
            except json.JSONDecodeError:
                pass
        return Config.COOKIE_FILE
    return None


@Client.on_callback_query(filters.regex("^ytdl_audio$"))
async def callback_query_ytdl_audio(_, callback_query):
    try:
        url = callback_query.message.reply_to_message.text
        
        # Base ydl options
        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": "%(title)s - %(extractor)s-%(id)s.%(ext)s",
            "writethumbnail": True,
            "quiet": True,
            "no_warnings": True,
        }
        
        # Add cookies if available
        cookie_file = load_cookies()
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file
            print(f"Using cookies from: {cookie_file}")  # Optional: for debugging
        
        with YoutubeDL(ydl_opts) as ydl:
            message = callback_query.message
            await message.reply_chat_action(enums.ChatAction.TYPING)
            info_dict = ydl.extract_info(url, download=False)
            # download
            await callback_query.edit_message_text("**Downloading audio...**")
            ydl.process_info(info_dict)
            # upload
            audio_file = ydl.prepare_filename(info_dict)
            task = asyncio.create_task(send_audio(message, info_dict, audio_file))
            while not task.done():
                await asyncio.sleep(3)
                await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
            await message.reply_chat_action(enums.ChatAction.CANCEL)
            await message.delete()
    except Exception as e:
        await message.reply_text(str(e))
    await callback_query.message.reply_to_message.delete()
    await callback_query.message.delete()


async def send_audio(message: Message, info_dict, audio_file):
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
    title = info_dict["title"] or ""
    caption = f'<b><a href="{webpage_url}">{title}</a></b>'
    duration = int(float(info_dict["duration"]))
    performer = info_dict["uploader"] or ""
    await message.reply_audio(
        audio_file,
        caption=caption,
        duration=duration,
        performer=performer,
        title=title,
        parse_mode=enums.ParseMode.HTML,
        thumb=thumb,
    )

    os.remove(audio_file)
    os.remove(thumbnail_file)


async def send_video(message: Message, info_dict, video_file):
    basename = video_file.rsplit(".", 1)[-2]
    thumbnail_url = info_dict["thumbnail"]
    thumbnail_file = f"{basename}.{get_file_extension_from_url(thumbnail_url)}"
    download_location = f"{Config.DOWNLOAD_LOCATION}/{message.from_user.id}.jpg"
    thumb = download_location if os.path.isfile(download_location) else None
    webpage_url = info_dict["webpage_url"]
    title = info_dict["title"] or ""
    caption = f'<b><a href="{webpage_url}">{title}</a></b>'
    duration = int(float(info_dict["duration"]))
    width, height = get_resolution(info_dict)
    await message.reply_video(
        video_file,
        caption=caption,
        duration=duration,
        width=width,
        height=height,
        parse_mode=enums.ParseMode.HTML,
        thumb=thumb,
    )

    os.remove(video_file)
    os.remove(thumbnail_file)


@Client.on_callback_query(filters.regex("^ytdl_video$"))
async def callback_query_ytdl_video(_, callback_query):
    try:
        url = callback_query.message.reply_to_message.text
        
        # Base ydl options
        ydl_opts = {
            "format": "best[ext=mp4]",
            "outtmpl": "%(title)s - %(extractor)s-%(id)s.%(ext)s",
            "writethumbnail": True,
            "quiet": True,
            "no_warnings": True,
        }
        
        # Add cookies if available
        cookie_file = load_cookies()
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file
            print(f"Using cookies from: {cookie_file}")  # Optional: for debugging
        
        with YoutubeDL(ydl_opts) as ydl:
            message = callback_query.message
            await message.reply_chat_action(enums.ChatAction.TYPING)
            info_dict = ydl.extract_info(url, download=False)
            # download
            await callback_query.edit_message_text("**Downloading video...**")
            ydl.process_info(info_dict)
            # upload
            video_file = ydl.prepare_filename(info_dict)
            task = asyncio.create_task(send_video(message, info_dict, video_file))
            while not task.done():
                await asyncio.sleep(3)
                await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
            await message.reply_chat_action(enums.ChatAction.CANCEL)
            await message.delete()
    except Exception as e:
        await message.reply_text(str(e))
    await callback_query.message.reply_to_message.delete()
    await callback_query.message.delete()


# Optional: Add a command to reload cookies
@Client.on_message(filters.command("cookies") & filters.user(Config.OWNER_ID))
async def set_cookies(client, message: Message):
    """Command to update cookies file from document"""
    if message.reply_to_message and message.reply_to_message.document:
        try:
            # Download the cookie file
            cookie_file_path = await message.reply_to_message.download(
                file_name=Config.COOKIE_FILE
            )
            await message.reply_text("✅ Cookies file updated successfully!")
        except Exception as e:
            await message.reply_text(f"❌ Error updating cookies: {str(e)}")
    else:
        await message.reply_text("Please reply to a cookie file with /cookies")
