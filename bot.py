
import sys
import glob
import importlib
from pathlib import Path
from pyrogram import idle
import logging
import logging.config


# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)



from pyrogram import Client, __version__
from pyrogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat
from pyrogram.raw.all import layer
from config import LOG_CHANNEL, ON_HEROKU, CLONE_MODE, PORT, ADMINS
from typing import Union, Optional, AsyncGenerator
from pyrogram import types
from Script import script 
from datetime import date, datetime 
import pytz
from aiohttp import web
from TechVJ.server import web_server


import asyncio
import time
from pyrogram import idle
from pyrogram.errors import FloodWait
from plugins.clone import restart_bots
from TechVJ.bot import StreamBot
from TechVJ.utils.keepalive import ping_server
from TechVJ.bot.clients import initialize_clients



ppath = "plugins/*.py"
files = glob.glob(ppath)

# FloodWait-safe Telegram authorization.
# Telegram may temporarily rate-limit bot authorization after repeated restarts.
# Keep the Railway process alive and wait for the exact server-provided delay
# instead of crashing and entering a restart loop.
while True:
    try:
        StreamBot.start()
        break
    except FloodWait as e:
        wait_seconds = int(getattr(e, "value", 0) or 0)
        if wait_seconds <= 0:
            wait_seconds = 60
        print(f"Telegram FloodWait during startup. Waiting {wait_seconds} seconds before retrying...")
        time.sleep(wait_seconds)

loop = asyncio.get_event_loop()



async def setup_command_menu():
    """Register Telegram command menus for users and admins."""
    public_commands = [
        BotCommand("start", "Start bot / receive files"),
        BotCommand("link", "Generate a shareable file link"),
        BotCommand("batch", "Generate a batch link"),
        BotCommand("base_site", "Set your shortener domain"),
        BotCommand("api", "Set your shortener API key"),
    ]

    admin_commands = public_commands + [
        BotCommand("settings", "Open bot settings"),
        BotCommand("setstart", "Set start message"),
        BotCommand("setpic", "Set start image"),
        BotCommand("setabout", "Set About text"),
        BotCommand("sethelp", "Set Help text"),
        BotCommand("setyoutube", "Set YouTube button"),
        BotCommand("setsupport", "Set Support button"),
        BotCommand("setupdates", "Set Updates button"),
        BotCommand("setdeveloper", "Set Developer button"),
        BotCommand("resetsettings", "Reset bot settings"),
        BotCommand("broadcast", "Broadcast a message"),
    ]

    if CLONE_MODE:
        public_commands.extend([
            BotCommand("clone", "Create a clone bot"),
            BotCommand("deletecloned", "Delete your clone bot"),
        ])
        admin_commands.extend([
            BotCommand("clone", "Create a clone bot"),
            BotCommand("deletecloned", "Delete your clone bot"),
        ])

    await StreamBot.set_bot_commands(
        public_commands,
        scope=BotCommandScopeAllPrivateChats()
    )

    for admin_id in ADMINS:
        try:
            admin_id = int(admin_id)
            await StreamBot.set_bot_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id)
            )
        except Exception as e:
            print(f"Could not set admin command menu for {admin_id}: {e}")


async def start():
    print('\n')
    print('Initializing File Store Bot')
    bot_info = await StreamBot.get_me()
    StreamBot.username = bot_info.username
    await initialize_clients()
    await setup_command_menu()
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = "plugins.{}".format(plugin_name)
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["plugins." + plugin_name] = load
            print("Plugin Imported => " + plugin_name)
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    me = await StreamBot.get_me()
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")
    app = web.AppRunner(await web_server())
    await StreamBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()
    if CLONE_MODE == True:
        await restart_bots()
    print("Bot Started Successfully")
    await idle()


if __name__ == '__main__':
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')


