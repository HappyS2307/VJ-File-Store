
import os
import logging
import random
import asyncio
from validators import domain
from Script import script
from plugins.dbusers import db
from pyrogram import Client, filters, enums
from plugins.users_api import get_user, update_user_info
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import *
from utils import verify_user, check_token, check_verification, get_token
from config import *
from plugins.settings_db import get_setting, set_setting, reset_settings
import re
import json
import base64
from urllib.parse import quote_plus
from TechVJ.utils.file_properties import get_name, get_hash, get_media_file_size
logger = logging.getLogger(__name__)

BATCH_FILES = {}



def get_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])

def formate_file_name(file_name):
    chars = ["[", "]", "(", ")"]
    for c in chars:
        file_name.replace(c, "")
    file_name = 'FileStoreBot ' + ' '.join(filter(lambda x: not x.startswith('http') and not x.startswith('@') and not x.startswith('www.'), file_name.split()))
    return file_name





ADMIN_ONLY = filters.user(ADMINS) & filters.private

@Client.on_message(filters.command("settings") & ADMIN_ONLY)
async def settings_command(client, message):
    await message.reply_text(
        "<b>⚙️ BOT SETTINGS</b>\n\n"
        "/setstart — change start message (reply to text)\n"
        "/setpic — change start image (reply to photo)\n"
        "/setabout — change About text (reply to text)\n"
        "/sethelp — change Help text (reply to text)\n"
        "/setyoutube — set YouTube button: <code>/setyoutube text | url</code>\n"
        "/setsupport — set Support button: <code>/setsupport text | url</code>\n"
        "/setupdates — set Updates button: <code>/setupdates text | url</code>\n"
        "/setdeveloper — set Developer text/link: <code>/setdeveloper text | url</code>\n"
        "/resetsettings — restore clean defaults"
    )

async def _reply_text_value(message, key, label):
    if not message.reply_to_message or not message.reply_to_message.text:
        return await message.reply_text(f"Reply to a text message with <code>/{label}</code>.")
    await set_setting(key, message.reply_to_message.text)
    await message.reply_text(f"✅ {label} updated.")

async def _set_button(message, key_text, key_url, command_name):
    if len(message.command) < 2:
        return await message.reply_text(f"Use: <code>/{command_name} Button Text | https://example.com</code>")
    raw = message.text.split(None, 1)[1].strip()
    if " | " not in raw:
        return await message.reply_text(f"Use: <code>/{command_name} Button Text | https://example.com</code>")
    label, url = [x.strip() for x in raw.split(" | ", 1)]
    if not url.startswith(("http://", "https://", "tg://")):
        return await message.reply_text("❌ URL must start with http://, https:// or tg://")
    await set_setting(key_text, label)
    await set_setting(key_url, url)
    await message.reply_text("✅ Button updated.")

@Client.on_message(filters.command("setstart") & ADMIN_ONLY)
async def setstart(client, message):
    await _reply_text_value(message, "start_text", "setstart")

@Client.on_message(filters.command("setabout") & ADMIN_ONLY)
async def setabout(client, message):
    await _reply_text_value(message, "about_text", "setabout")

@Client.on_message(filters.command("sethelp") & ADMIN_ONLY)
async def sethelp(client, message):
    await _reply_text_value(message, "help_text", "sethelp")

@Client.on_message(filters.command("setpic") & ADMIN_ONLY)
async def setpic(client, message):
    r = message.reply_to_message
    if not r or not r.photo:
        return await message.reply_text("Reply to a photo with /setpic.")
    await set_setting("start_photo", str(r.photo.file_id))
    await message.reply_text("✅ Start image updated.")

@Client.on_message(filters.command("setyoutube") & ADMIN_ONLY)
async def setyoutube(client, message):
    await _set_button(message, "youtube_text", "youtube_url", "setyoutube")

@Client.on_message(filters.command("setsupport") & ADMIN_ONLY)
async def setsupport(client, message):
    await _set_button(message, "support_text", "support_url", "setsupport")

@Client.on_message(filters.command("setupdates") & ADMIN_ONLY)
async def setupdates(client, message):
    await _set_button(message, "updates_text", "updates_url", "setupdates")

@Client.on_message(filters.command("setdeveloper") & ADMIN_ONLY)
async def setdeveloper(client, message):
    await _set_button(message, "developer_text", "developer_url", "setdeveloper")

@Client.on_message(filters.command("resetsettings") & ADMIN_ONLY)
async def resetsettings(client, message):
    await reset_settings()
    await message.reply_text("✅ Bot settings reset.")

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    username = client.me.username
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT.format(message.from_user.id, message.from_user.mention))
    if len(message.command) != 2:
        youtube_url = await get_setting("youtube_url")
        youtube_text = await get_setting("youtube_text")
        support_url = await get_setting("support_url")
        support_text = await get_setting("support_text")
        updates_url = await get_setting("updates_url")
        updates_text = await get_setting("updates_text")
        start_text = await get_setting("start_text")
        start_photo = await get_setting("start_photo")

        buttons = []
        if youtube_url:
            buttons.append([InlineKeyboardButton(youtube_text, url=youtube_url)])
        row = []
        if support_url:
            row.append(InlineKeyboardButton(support_text, url=support_url))
        if updates_url:
            row.append(InlineKeyboardButton(updates_text, url=updates_url))
        if row:
            buttons.append(row)
        buttons.append([
            InlineKeyboardButton('💁‍♀️ HELP', callback_data='help'),
            InlineKeyboardButton('😊 ABOUT', callback_data='about')
        ])
        if CLONE_MODE == True:
            buttons.append([InlineKeyboardButton('🤖 CREATE CLONE BOT', callback_data='clone')])
        reply_markup = InlineKeyboardMarkup(buttons)
        me = client.me
        caption = start_text.format(message.from_user.mention, me.mention)
        if start_photo:
            await message.reply_photo(photo=start_photo, caption=caption, reply_markup=reply_markup)
        else:
            await message.reply_text(caption, reply_markup=reply_markup)
        return

    
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
    if data.split("-", 1)[0] == "verify":
        userid = data.split("-", 2)[1]
        token = data.split("-", 3)[2]
        if str(message.from_user.id) != str(userid):
            return await message.reply_text(
                text="<b>Invalid link or Expired link !</b>",
                protect_content=True
            )
        is_valid = await check_token(client, userid, token)
        if is_valid == True:
            await message.reply_text(
                text=f"<b>Hey {message.from_user.mention}, You are successfully verified !\nNow you have unlimited access for all files till today midnight.</b>",
                protect_content=True
            )
            await verify_user(client, userid, token)
        else:
            return await message.reply_text(
                text="<b>Invalid link or Expired link !</b>",
                protect_content=True
            )
    elif data.split("-", 1)[0] == "BATCH":
        try:
            if not await check_verification(client, message.from_user.id) and VERIFY_MODE == True:
                btn = [[
                    InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{username}?start="))
                ],[
                    InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)
                ]]
                await message.reply_text(
                    text="<b>You are not verified !\nKindly verify to continue !</b>",
                    protect_content=True,
                    reply_markup=InlineKeyboardMarkup(btn)
                )
                return
        except Exception as e:
            return await message.reply_text(f"**Error - {e}**")
        sts = await message.reply("**🔺 ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ**")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            decode_file_id = base64.urlsafe_b64decode(file_id + "=" * (-len(file_id) % 4)).decode("ascii")
            msg = await client.get_messages(LOG_CHANNEL, int(decode_file_id))
            media = getattr(msg, msg.media.value)
            file_id = media.file_id
            file = await client.download_media(file_id)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs
            
        filesarr = []
        for msg in msgs:
            channel_id = int(msg.get("channel_id"))
            msgid = msg.get("msg_id")
            info = await client.get_messages(channel_id, int(msgid))
            if info.media:
                file_type = info.media
                file = getattr(info, file_type.value)
                f_caption = getattr(info, 'caption', '')
                if f_caption:
                    f_caption = f"{f_caption.html}"
                old_title = getattr(file, "file_name", "")
                title = formate_file_name(old_title)
                size=get_size(int(file.file_size))
                if BATCH_FILE_CAPTION:
                    try:
                        f_caption=BATCH_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                    except:
                        f_caption=f_caption
                if f_caption is None:
                    f_caption = f"{title}"
                if STREAM_MODE == True:
                    if info.video or info.document:
                        log_msg = info
                        fileName = {quote_plus(get_name(log_msg))}
                        stream = f"{URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                        download = f"{URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                        button = [[
                            InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ •", url=download),
                            InlineKeyboardButton('• ᴡᴀᴛᴄʜ •', url=stream)
                        ],[
                            InlineKeyboardButton("• ᴡᴀᴛᴄʜ ɪɴ ᴡᴇʙ ᴀᴘᴘ •", web_app=WebAppInfo(url=stream))
                        ]]
                        reply_markup=InlineKeyboardMarkup(button)
                else:
                    reply_markup = None
                try:
                    msg = await info.copy(chat_id=message.from_user.id, caption=f_caption, protect_content=False, reply_markup=reply_markup)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    msg = await info.copy(chat_id=message.from_user.id, caption=f_caption, protect_content=False, reply_markup=reply_markup)
                except:
                    continue
            else:
                try:
                    msg = await info.copy(chat_id=message.from_user.id, protect_content=False)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    msg = await info.copy(chat_id=message.from_user.id, protect_content=False)
                except:
                    continue
            filesarr.append(msg)
            await asyncio.sleep(1) 
        await sts.delete()
        if AUTO_DELETE_MODE == True:
            k = await client.send_message(chat_id = message.from_user.id, text=f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis Movie File/Video will be deleted in <b><u>{AUTO_DELETE} minutes</u> 🫥 <i></b>(Due to Copyright Issues)</i>.\n\n<b><i>Please forward this File/Video to your Saved Messages and Start Download there</b>")
            await asyncio.sleep(AUTO_DELETE_TIME)
            for x in filesarr:
                try:
                    await x.delete()
                except:
                    pass
            await k.edit_text("<b>Your All Files/Videos is successfully deleted!!!</b>")
        return


    pre, decode_file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
    if not await check_verification(client, message.from_user.id) and VERIFY_MODE == True:
        btn = [[
            InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{username}?start="))
        ],[
            InlineKeyboardButton("How To Open Link & Verify", url=VERIFY_TUTORIAL)
        ]]
        await message.reply_text(
            text="<b>You are not verified !\nKindly verify to continue !</b>",
            protect_content=True,
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return
    try:
        msg = await client.get_messages(LOG_CHANNEL, int(decode_file_id))
        if msg.media:
            media = getattr(msg, msg.media.value)
            title = formate_file_name(media.file_name)
            size=get_size(media.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    return
            if STREAM_MODE == True:
                if msg.video or msg.document:
                    log_msg = msg
                    fileName = {quote_plus(get_name(log_msg))}
                    stream = f"{URL}watch/{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                    download = f"{URL}{str(log_msg.id)}/{quote_plus(get_name(log_msg))}?hash={get_hash(log_msg)}"
                    button = [[
                        InlineKeyboardButton("• ᴅᴏᴡɴʟᴏᴀᴅ •", url=download),
                        InlineKeyboardButton('• ᴡᴀᴛᴄʜ •', url=stream)
                    ],[
                        InlineKeyboardButton("• ᴡᴀᴛᴄʜ ɪɴ ᴡᴇʙ ᴀᴘᴘ •", web_app=WebAppInfo(url=stream))
                    ]]
                    reply_markup=InlineKeyboardMarkup(button)
            else:
                reply_markup = None
            del_msg = await msg.copy(chat_id=message.from_user.id, caption=f_caption, reply_markup=reply_markup, protect_content=False)
        else:
            del_msg = await msg.copy(chat_id=message.from_user.id, protect_content=False)
        if AUTO_DELETE_MODE == True:
            k = await client.send_message(chat_id = message.from_user.id, text=f"<b><u>❗️❗️❗️IMPORTANT❗️️❗️❗️</u></b>\n\nThis Movie File/Video will be deleted in <b><u>{AUTO_DELETE} minutes</u> 🫥 <i></b>(Due to Copyright Issues)</i>.\n\n<b><i>Please forward this File/Video to your Saved Messages and Start Download there</b>")
            await asyncio.sleep(AUTO_DELETE_TIME)
            try:
                await del_msg.delete()
            except:
                pass
            await k.edit_text("<b>Your File/Video is successfully deleted!!!</b>")
        return
    except:
        pass
        

@Client.on_message(filters.command('api') & filters.private)
async def shortener_api_handler(client, m: Message):
    user_id = m.from_user.id
    user = await get_user(user_id)
    cmd = m.command

    if len(cmd) == 1:
        s = script.SHORTENER_API_MESSAGE.format(base_site=user["base_site"], shortener_api=user["shortener_api"])
        return await m.reply(s)

    elif len(cmd) == 2:    
        api = cmd[1].strip()
        await update_user_info(user_id, {"shortener_api": api})
        await m.reply("<b>Shortener API updated successfully to</b> " + api)


@Client.on_message(filters.command("base_site") & filters.private)
async def base_site_handler(client, m: Message):
    user_id = m.from_user.id
    user = await get_user(user_id)
    cmd = m.command
    text = f"`/base_site (base_site)`\n\n<b>Current base site: None\n\n EX:</b> `/base_site shortnerdomain.com`\n\nIf You Want To Remove Base Site Then Copy This And Send To Bot - `/base_site None`"
    if len(cmd) == 1:
        return await m.reply(text=text, disable_web_page_preview=True)
    elif len(cmd) == 2:
        base_site = cmd[1].strip()
        if base_site == None:
            await update_user_info(user_id, {"base_site": base_site})
            return await m.reply("<b>Base Site updated successfully</b>")
            
        if not domain(base_site):
            return await m.reply(text=text, disable_web_page_preview=True)
        await update_user_info(user_id, {"base_site": base_site})
        await m.reply("<b>Base Site updated successfully</b>")


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        start_photo = await get_setting("start_photo")
        if start_photo:
            await client.edit_message_media(
                query.message.chat.id,
                query.message.id,
                InputMediaPhoto(start_photo)
            )
        reply_markup = InlineKeyboardMarkup(buttons)
        me2 = (await client.get_me()).mention
        about_text = await get_setting("about_text")
        await query.message.edit_text(
            text=about_text.format(me2),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    
    elif query.data == "start":
        youtube_url = await get_setting("youtube_url")
        youtube_text = await get_setting("youtube_text")
        support_url = await get_setting("support_url")
        support_text = await get_setting("support_text")
        updates_url = await get_setting("updates_url")
        updates_text = await get_setting("updates_text")
        buttons = []
        if youtube_url:
            buttons.append([InlineKeyboardButton(youtube_text, url=youtube_url)])
        row = []
        if support_url:
            row.append(InlineKeyboardButton(support_text, url=support_url))
        if updates_url:
            row.append(InlineKeyboardButton(updates_text, url=updates_url))
        if row:
            buttons.append(row)
        buttons.append([
            InlineKeyboardButton('💁‍♀️ HELP', callback_data='help'),
            InlineKeyboardButton('😊 ABOUT', callback_data='about')
        ])
        if CLONE_MODE == True:
            buttons.append([InlineKeyboardButton('🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄʟᴏɴᴇ ʙᴏᴛ', callback_data='clone')])
        reply_markup = InlineKeyboardMarkup(buttons)
        start_photo = await get_setting("start_photo")
        me2 = (await client.get_me()).mention
        start_text = await get_setting("start_text")
        if start_photo:
            await client.edit_message_media(
                query.message.chat.id,
                query.message.id,
                InputMediaPhoto(start_photo)
            )
            await query.message.edit_text(
                text=start_text.format(query.from_user.mention, me2),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await query.message.delete()
            await client.send_message(
                query.message.chat.id,
                text=start_text.format(query.from_user.mention, me2),
                reply_markup=reply_markup,
                parse_mode=enums.ParseMode.HTML
            )

    
    elif query.data == "clone":
        buttons = [[
            InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CLONE_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )          

    
    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start'),
            InlineKeyboardButton('🔒 Cʟᴏsᴇ', callback_data='close_data')
        ]]
        start_photo = await get_setting("start_photo")
        if start_photo:
            await client.edit_message_media(
                query.message.chat.id,
                query.message.id,
                InputMediaPhoto(start_photo)
            )
        reply_markup = InlineKeyboardMarkup(buttons)
        help_text = await get_setting("help_text")
        await query.message.edit_text(
            text=help_text,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )  
        
