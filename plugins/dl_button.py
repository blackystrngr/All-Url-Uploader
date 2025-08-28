"""Module for handling download callback and related functions"""

import asyncio
from datetime import datetime
import logging
import os
import time
import aiohttp
from plugins.functions.display_progress import (
    progress_for_pyrogram,
    humanbytes,
    TimeFormatter,
)
from plugins.script import Translation
from plugins.utitles import Mdata01, Mdata02, Mdata03
from config import Config

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def get_file_type_from_extension(filename):
    """Determine file type based on extension"""
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    # Video extensions
    video_extensions = ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v', '3gp', 'ogv']
    # Audio extensions  
    audio_extensions = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'opus']
    # Archive/Document extensions that should always be documents
    document_extensions = ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'pdf', 'doc', 'docx', 
                         'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'json', 'xml', 'bin',
                         'deb', 'rpm', 'dmg', 'exe', 'msi', 'apk', 'jar', 'war']
    
    if ext in video_extensions:
        return 'video'
    elif ext in audio_extensions:
        return 'audio'
    elif ext in document_extensions:
        return 'document'
    else:
        # For unknown extensions, default to document instead of video
        return 'document'

async def ddl_call_back(bot, update):
    cb_data = update.data
    tg_send_type, youtube_dl_format, youtube_dl_ext = cb_data.split("=")
    youtube_dl_url = update.message.reply_to_message.text
    custom_file_name = os.path.basename(youtube_dl_url)

    if " " in youtube_dl_url:
        url_parts = youtube_dl_url.split(" * ")
        if len(url_parts) == 2:
            youtube_dl_url = url_parts[0]
            custom_file_name = url_parts[1]
        else:
            for entity in update.message.reply_to_message.entities:
                if entity.type == "text_link":
                    youtube_dl_url = entity.url
                elif entity.type == "url":
                    o = entity.offset
                    length = entity.length
                    youtube_dl_url = youtube_dl_url[o: o + length]
        if youtube_dl_url is not None:
            youtube_dl_url = youtube_dl_url.strip()
        if custom_file_name is not None:
            custom_file_name = custom_file_name.strip()
    else:
        for entity in update.message.reply_to_message.entities:
            if entity.type == "text_link":
                youtube_dl_url = entity.url
            elif entity.type == "url":
                o = entity.offset
                length = entity.length
                youtube_dl_url = youtube_dl_url[o: o + length]

    description = custom_file_name

    if f".{youtube_dl_ext}" not in custom_file_name:
        custom_file_name += f".{youtube_dl_ext}"

    # Detect actual file type from filename
    actual_file_type = get_file_type_from_extension(custom_file_name)
    
    # Override tg_send_type if it's incorrectly set to video for non-video files
    if tg_send_type == "video" and actual_file_type != "video":
        logger.info(f"Correcting file type from {tg_send_type} to {actual_file_type} for {custom_file_name}")
        tg_send_type = actual_file_type

    logger.info(f"URL: {youtube_dl_url}")
    logger.info(f"Filename: {custom_file_name}")
    logger.info(f"Detected file type: {actual_file_type}")
    logger.info(f"Send type: {tg_send_type}")

    start = datetime.now()

    await bot.edit_message_text(
        text=Translation.DOWNLOAD_START.format(custom_file_name),
        chat_id=update.message.chat.id,
        message_id=update.message.id,
    )

    tmp_directory_for_each_user = (
        f"{Config.DOWNLOAD_LOCATION}/{str(update.from_user.id)}"
    )

    if not os.path.isdir(tmp_directory_for_each_user):
        os.makedirs(tmp_directory_for_each_user)

    download_directory = f"{tmp_directory_for_each_user}/{custom_file_name}"

    async with aiohttp.ClientSession() as session:
        c_time = time.time()
        try:
            await download_coroutine(
                bot,
                session,
                youtube_dl_url,
                download_directory,
                update.message.chat.id,
                update.message.id,
                c_time,
            )

        except asyncio.TimeoutError:
            await bot.edit_message_text(
                text=Translation.SLOW_URL_DECED,
                chat_id=update.message.chat.id,
                message_id=update.message.id,
            )
            return False

    if os.path.exists(download_directory):
        save_ytdl_json_path = (
            f"{Config.DOWNLOAD_LOCATION}/{str(update.message.chat.id)}.json"
        )
        download_location = f"{Config.DOWNLOAD_LOCATION}/{update.from_user.id}.jpg"
        thumb = download_location if os.path.isfile(download_location) else None

        if os.path.exists(save_ytdl_json_path):
            os.remove(save_ytdl_json_path)

        end_one = datetime.now()

        await bot.edit_message_text(
            text=Translation.UPLOAD_START,
            chat_id=update.message.chat.id,
            message_id=update.message.id,
        )

        file_size = Config.TG_MAX_FILE_SIZE + 1

        try:
            file_size = os.stat(download_directory).st_size
        except FileNotFoundError:
            download_directory = f"{os.path.splitext(download_directory)[0]}.mkv"
            file_size = os.stat(download_directory).st_size

        if file_size > Config.TG_MAX_FILE_SIZE:
            await bot.edit_message_text(
                chat_id=update.message.chat.id,
                text=Translation.RCHD_TG_API_LIMIT,
                message_id=update.message.id,
            )

        else:
            start_time = time.time()

            # Use the corrected file type for uploading
            if tg_send_type == "video":
                width, height, duration = await Mdata01(download_directory)
                await bot.send_video(
                    chat_id=update.message.chat.id,
                    video=download_directory,
                    thumb=thumb,
                    caption=description,
                    duration=duration,
                    width=width,
                    height=height,
                    supports_streaming=True,
                    reply_to_message_id=update.message.reply_to_message.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time,
                    ),
                )

            elif tg_send_type == "audio":
                duration = await Mdata03(download_directory)
                await bot.send_audio(
                    chat_id=update.message.chat.id,
                    audio=download_directory,
                    thumb=thumb,
                    caption=description,
                    duration=duration,
                    reply_to_message_id=update.message.reply_to_message.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time,
                    ),
                )

            elif tg_send_type == "vm":
                width, duration = await Mdata02(download_directory)
                await bot.send_video_note(
                    chat_id=update.message.chat.id,
                    video_note=download_directory,
                    thumb=thumb,
                    duration=duration,
                    length=width,
                    reply_to_message_id=update.message.reply_to_message.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time,
                    ),
                )

            else:  # Default to document for everything else
                await bot.send_document(
                    chat_id=update.message.chat.id,
                    document=download_directory,
                    thumb=thumb,
                    caption=description,
                    reply_to_message_id=update.message.reply_to_message.id,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        Translation.UPLOAD_START,
                        update.message,
                        start_time,
                    ),
                )

            end_two = datetime.now()

            try:
                os.remove(download_directory)
            except Exception:
                pass

            time_taken_for_download = (end_one - start).seconds
            time_taken_for_upload = (end_two - end_one).seconds

            await bot.edit_message_text(
                text=Translation.AFTER_SUCCESSFUL_UPLOAD_MSG_WITH_TS.format(
                    time_taken_for_download, time_taken_for_upload
                ),
                chat_id=update.message.chat.id,
                message_id=update.message.id,
                disable_web_page_preview=True,
            )

            logger.info("Downloaded in: %s", str(time_taken_for_download))
            logger.info("Uploaded in: %s", str(time_taken_for_upload))
    else:
        await bot.edit_message_text(
            text=Translation.NO_VOID_FORMAT_FOUND.format("File not found after download"),
            chat_id=update.message.chat.id,
            message_id=update.message.id,
            disable_web_page_preview=True,
        )


async def download_coroutine(bot, session, url, file_name, chat_id, message_id, start):
    downloaded = 0
    display_message = ""

    async with session.get(url, timeout=Config.PROCESS_MAX_TIMEOUT) as response:
        total_length = int(response.headers.get("Content-Length", 0))
        content_type = response.headers.get("Content-Type", "")

        if "text" in content_type and total_length < 500:
            return await response.release()

        with open(file_name, "wb") as f_handle:
            while True:
                chunk = await response.content.read(Config.CHUNK_SIZE)

                if not chunk:
                    break

                f_handle.write(chunk)
                downloaded += Config.CHUNK_SIZE
                now = time.time()
                diff = now - start

                if round(diff % 5.0) == 0 or downloaded == total_length:
                    percentage = downloaded * 100 / total_length if total_length > 0 else 0
                    speed = downloaded / diff if diff > 0 else 0
                    elapsed_time = round(diff) * 1000
                    time_to_completion = (
                        round((total_length - downloaded) / speed) * 1000 if speed > 0 else 0
                    )
                    estimated_total_time = elapsed_time + time_to_completion

                    try:
                        current_message = f"""**Download Status**
Percentage : {percentage:.1f}%
URL: {url}
File Size: {humanbytes(total_length)}
Downloaded: {humanbytes(downloaded)}
ETA: {TimeFormatter(estimated_total_time)}"""

                        if current_message != display_message:
                            await bot.edit_message_text(
                                chat_id, message_id, text=current_message
                            )

                            display_message = current_message

                    except Exception as e:
                        logger.info(str(e))

        return await response.release()
