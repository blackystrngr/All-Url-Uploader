import os
import asyncio

from yt_dlp import YoutubeDL  # Use yt-dlp for better support and maintenance
from pyrogram import enums
from pyrogram.types import Message
from pyrogram import Client, filters

from config import Config
from plugins.functions.help_ytdl import get_file_extension_from_url, get_resolution
YTDL_REGEX = r"^((?:https?:)?\/\/)"

@Client.on_callback_query(filters.regex("^ytdl_audio$"))
async def callback_query_ytdl_audio(_, callback_query):
    try:
        url = callback_query.message.reply_to_message.text
        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": "%(title)s - %(extractor)s-%(id)s.%(ext)s",
            "writethumbnail": True,
            'cookiefile': 'cookies.txt',  # For bypassing YouTube restrictions
        }
        with YoutubeDL(ydl_opts) as ydl:
            message = callback_query.message
            await message.reply_chat_action(enums.ChatAction.TYPING)
            info_dict = ydl.extract_info(url, download=False)
            await callback_query.edit_message_text("**Downloading audio...**")
            ydl.process_info(info_dict)
            audio_file = ydl.prepare_filename(info_dict)
            task = asyncio.create_task(send_audio(message, info_dict, audio_file))
            while not task.done():
                await asyncio.sleep(3)
                await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
            await message.reply_chat_action(enums.ChatAction.CANCEL)
            await message.delete()
    except Exception as e:
        await callback_query.message.reply_text(str(e))
    await callback_query.message.reply_to_message.delete()
    await callback_query.message.delete()

async def send_audio(message: Message, info_dict, audio_file):
    basename = audio_file.rsplit(".", 1)[-2]
    if info_dict.get("ext") == "webm":
        audio_file_weba = f"{basename}.weba"
        os.rename(audio_file, audio_file_weba)
        audio_file = audio_file_weba
    thumbnail_url = info_dict.get("thumbnail")
    if thumbnail_url:
        thumbnail_file = f"{basename}.{get_file_extension_from_url(thumbnail_url)}"
    else:
        thumbnail_file = None
    download_location = f"{Config.DOWNLOAD_LOCATION}/{message.from_user.id}.jpg"
    thumb = download_location if os.path.isfile(download_location) else None
    webpage_url = info_dict.get("webpage_url", "")
    title = info_dict.get("title", "")
    caption = f'<b><a href="{webpage_url}">{title}</a></b>'
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
    try:
        os.remove(audio_file)
        if thumbnail_file:
            os.remove(thumbnail_file)
    except FileNotFoundError:
        pass  # Ignore if file not found

async def send_video(message: Message, info_dict, video_file):
    basename = video_file.rsplit(".", 1)[-2]
    thumbnail_url = info_dict.get("thumbnail")
    if thumbnail_url:
        thumbnail_file = f"{basename}.{get_file_extension_from_url(thumbnail_url)}"
    else:
        thumbnail_file = None
    download_location = f"{Config.DOWNLOAD_LOCATION}/{message.from_user.id}.jpg"
    thumb = download_location if os.path.isfile(download_location) else None
    webpage_url = info_dict.get("webpage_url", "")
    title = info_dict.get("title", "")
    caption = f'<b><a href="{webpage_url}">{title}</a></b>'
    duration = int(float(info_dict.get("duration", 0)))
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
    try:
        os.remove(video_file)
        if thumbnail_file:
            os.remove(thumbnail_file)
    except FileNotFoundError:
        pass  # Ignore if file not found

@Client.on_callback_query(filters.regex("^ytdl_video$"))
async def callback_query_ytdl_video(_, callback_query):
    try:
        url = callback_query.message.reply_to_message.text
        ydl_opts = {
            "format": "best[ext=mp4]",
            "outtmpl": "%(title)s - %(extractor)s-%(id)s.%(ext)s",
            "writethumbnail": True,
            'cookiefile': 'cookies.txt',  # For bypassing YouTube restrictions
        }
        with YoutubeDL(ydl_opts) as ydl:
            message = callback_query.message
            await message.reply_chat_action(enums.ChatAction.TYPING)
            info_dict = ydl.extract_info(url, download=False)
            await callback_query.edit_message_text("**Downloading video...**")
            ydl.process_info(info_dict)
            video_file = ydl.prepare_filename(info_dict)
            task = asyncio.create_task(send_video(message, info_dict, video_file))
            while not task.done():
                await asyncio.sleep(3)
                await message.reply_chat_action(enums.ChatAction.UPLOAD_DOCUMENT)
            await message.reply_chat_action(enums.ChatAction.CANCEL)
            await message.delete()
    except Exception as e:
        await callback_query.message.reply_text(str(e))
    await callback_query.message.reply_to_message.delete()
    await callback_query.message.delete()
