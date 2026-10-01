import motor.motor_asyncio
from config import DB_NAME, DB_URI

class SettingsDB:
    def __init__(self, uri, database_name):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.col = self.client[database_name].bot_settings

    async def get(self, key, default=None):
        item = await self.col.find_one({"_id": key})
        return default if not item else item.get("value", default)

    async def set(self, key, value):
        await self.col.update_one(
            {"_id": key},
            {"$set": {"value": value}},
            upsert=True
        )

    async def delete(self, key):
        await self.col.delete_one({"_id": key})

settings = SettingsDB(DB_URI, DB_NAME)

DEFAULTS = {
    "start_text": "<b>ʜᴇʟʟᴏ {}, ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ {} 👋</b>\n\n<b>📂 Permanent File Store</b>\n\nSend a file or use a file link to get started.",
    "about_text": "<b>ʜɪ {} 👋</b>\n\n<b>📂 Permanent File Store Bot</b>\nBuilt for simple and fast file sharing.",
    "help_text": "<b>💢 HOW TO USE</b>\n\n🔻 <code>/link</code> — Reply to a file/video to generate a shareable link.\n\n🔻 <code>/batch</code> — Generate a link for multiple channel posts.\n\n🔻 <code>/clone</code> — Create a clone bot (if enabled).",
    "youtube_url": "",
    "youtube_text": "📺 YouTube",
    "support_url": "",
    "support_text": "💬 Support",
    "updates_url": "",
    "updates_text": "📢 Updates",
    "developer_url": "",
    "developer_text": "👨‍💻 Developer",
    "start_photo": ""
}

async def get_setting(key):
    value = await settings.get(key, DEFAULTS.get(key))
    # Ignore legacy template branding accidentally saved in MongoDB.
    if key in {"start_text", "about_text", "help_text"} and value:
        legacy = ("Tech VJ", "TECH VJ", "Tech_VJ", "VJ_Bots", "KingVJ01", "𝐕𝐉", "VJ Support", "VJ Update")
        if any(x.lower() in str(value).lower() for x in legacy):
            return DEFAULTS.get(key)
    return value

async def set_setting(key, value):
    await settings.set(key, value)

async def reset_settings():
    await settings.col.delete_many({})
