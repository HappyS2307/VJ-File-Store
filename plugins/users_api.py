# © Telegram :  , GitHub : @FileStore

# Don't Remove Credit Tg - 
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/
# Ask Doubt on telegram 

import aiohttp
import json
from motor.motor_asyncio import AsyncIOMotorClient
from plugins.clone import mongo_db

# Don't Remove Credit Tg - 
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/
# Ask Doubt on telegram 

async def get_short_link(user, link):
    api_key = user["shortener_api"]
    base_site = user["base_site"]
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://{base_site}/api",
                params={"api": api_key, "url": link},
                timeout=aiohttp.ClientTimeout(total=10),
                ssl=False,
            ) as response:
                data = await response.json(content_type=None)
        if data.get("status") == "success" and data.get("shortenedUrl"):
            return data["shortenedUrl"]
        return link
    except Exception:
        return link

# Don't Remove Credit Tg - 
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/
# Ask Doubt on telegram 

async def get_user(user_id):
    user_id = int(user_id)
    user = mongo_db.user.find_one({"user_id": user_id})
    if not user:
        res = {
            "user_id": user_id,
            "shortener_api": None,
            "base_site": None,
        }
        mongo_db.user.insert_one(res)
        user = mongo_db.user.find_one({"user_id": user_id})
    return user

# Don't Remove Credit Tg - 
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/
# Ask Doubt on telegram 

async def update_user_info(user_id, value:dict):
    user_id = int(user_id)
    myquery = {"user_id": user_id}
    newvalues = { "$set": value }
    mongo_db.user.update_one(myquery, newvalues)

# Don't Remove Credit Tg - 
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/
# Ask Doubt on telegram 
