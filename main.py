"""
reza_clock v3 — بدون باگ
─────────────────────────────────────────────────
✅  ساعت زنده در نام (هر دقیقه)
✅  بیوگرافی هکری روزانه
✅  منشی همیشه فعال:
      • ریکشن روی هر پیام ورودی (با retry)
      • پیام اول  → «فعلاً آنلاین نیستم»
      • پیام دوم  → «داداش گفتم آنلاین نیستم...»
      • پیام سوم+ → فقط ریکشن (بدون رپلای)
      • منشی هیچوقت خودکار خاموش نمی‌شه
─────────────────────────────────────────────────
دستورات (در Saved Messages بفرست):
  .online   ← همه منتظران خبر می‌گیرن
  .offline  ← صف ریست می‌شه (شروع دوباره)
  .status   ← چند نفر در صفن
"""

import asyncio
import os
import random
import sys
from collections import defaultdict
from datetime import date, datetime
from zoneinfo import ZoneInfo

from telethon import TelegramClient, events
from telethon.errors import (
    AuthKeyUnregisteredError,
    FloodWaitError,
    ReactionInvalidError,
    SessionRevokedError,
    UserDeactivatedError,
)
from telethon.sessions import StringSession
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji

# ── ENV ───────────────────────────────────────────────────────────────────────
API_ID      = os.environ.get("API_ID")
API_HASH    = os.environ.get("API_HASH")
SESSION     = os.environ.get("SESSION")
TIMEZONE    = os.environ.get("TIMEZONE",    "Asia/Tehran")
NAME_PREFIX = os.environ.get("NAME_PREFIX", "𝑹𝒆𝒛𝒂")

missing = [k for k, v in
           {"API_ID": API_ID, "API_HASH": API_HASH, "SESSION": SESSION}.items()
           if not v]
if missing:
    print("❌ Missing env vars:", ", ".join(missing), flush=True)
    sys.exit(1)

tz     = ZoneInfo(TIMEZONE)
client = TelegramClient(StringSession(SESSION), int(API_ID), API_HASH)

# ── STATE ─────────────────────────────────────────────────────────────────────
# msg_count[user_id] = تعداد پیام‌هایی که این کاربر فرستاده
msg_count: dict[int, int] = defaultdict(int)
last_bio_day: date | None = None
my_id:        int | None  = None

# ── TEXTS ────────────────────────────────────────────────────────────────────
REPLY_FIRST = (
    "🌙 فعلاً آنلاین نیستم\n"
    "به محض آنلاین‌شدن خبرت می‌دم 🐬"
)
REPLY_REPEAT = (
    "داداش گفتم که فعلاً آنلاین نیستم 🌙\n"
    "آنلاین شدم میام بهت پیام می‌دم، نگران نباش 🐬"
)
REPLY_ONLINE = "☀️ آنلاین شدم! بفرما 🐬"

HACKER_BIOS = [
    "𝒉𝒂𝒄𝒌𝒊𝒏𝒈 𝒕𝒉𝒆 𝒑𝒍𝒂𝒏𝒆𝒕 🌐💻",
    "𝓢𝔂𝓼𝓽𝓮𝓶 𝓑𝓻𝓮𝓪𝓴𝓮𝓻 👾",
    "𝕳𝖆𝖈𝖐𝖊𝖗 𝕸𝖔𝖉𝖊: 𝕺𝖓 🖥️⚡",
    "ꜱɪʟᴇɴᴛ ʙᴜᴛ ᴅᴇᴀᴅʟʏ 🌑🗡️",
    "𝐂𝐨𝐝𝐞 𝐢𝐬 𝐦𝐲 𝐥𝐚𝐧𝐠𝐮𝐚𝐠𝐞 🐍💻",
    "𝙳𝚊𝚝𝚊 𝚒𝚜 𝚝𝚑𝚎 𝚗𝚎𝚠 𝚘𝚒𝚕 🛢️🤖",
    "𝗰𝘆𝗯𝗲𝗿 𝘀𝗲𝗰𝘂𝗿𝗶𝘁𝘆 𝗶𝘀 𝗮𝗿𝘁 🎨🛡️",
    "ᴀɴᴏɴʏᴍᴏᴜs · ᴅɪɢɪᴛᴀʟ · ꜰʀᴇᴇ 🕶️",
    "𝔥𝔞𝔠𝔨 𝔱𝔥𝔢 𝔤𝔦𝔤 𝔫𝔬𝔱 𝔱𝔥𝔢 𝔩𝔞𝔴 ⚖️💡",
    "𝚃𝚑𝚎 𝙼𝚊𝚝𝚛𝚒𝚡 𝚒𝚜 𝚛𝚎𝚊𝚕 🕳️🐇",
    "01000111 01001111 01000100 🤖",
    "𝖘𝖊𝖊𝖎𝖓𝖌 𝖊𝖛𝖊𝖗𝖞𝖙𝖍𝖎𝖓𝖌 👁️‍🗨️",
    "𝓷𝓸 𝓼𝔂𝓼𝓽𝓮𝓶 𝓲𝓼 𝓼𝓪𝓯𝓮 🔓🌐",
    "𝒘𝒆 𝒅𝒐 𝒏𝒐𝒕 𝒇𝒐𝒓𝒈𝒆𝒕 🎭⚡",
]

REACTIONS = ["👀", "🤙", "🐬", "🦋", "⚡", "🔥", "💫", "🌊", "🎯", "🧠", "🕶️", "🌑"]

# ── HELPERS ───────────────────────────────────────────────────────────────────
def log(*args):
    print(*args, flush=True)

async def update_bio(text: str):
    try:
        await client(UpdateProfileRequest(about=text))
        log("Bio →", text)
    except Exception as e:
        log("Bio fail:", repr(e))

async def add_reaction(chat_id: int, msg_id: int):
    """ریکشن با retry خودکار روی flood wait"""
    for attempt in range(3):
        try:
            await client(SendReactionRequest(
                peer=chat_id,
                msg_id=msg_id,
                reaction=[ReactionEmoji(emoticon=random.choice(REACTIONS))],
            ))
            return  # موفق
        except FloodWaitError as e:
            log(f"Reaction FloodWait {e.seconds}s")
            await asyncio.sleep(e.seconds + 1)
        except ReactionInvalidError:
            return  # این پیام ریکشن نمی‌گیره، skip
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(2)
            else:
                log("Reaction fail:", repr(e))

# ── HANDLERS ──────────────────────────────────────────────────────────────────

@client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
async def handle_incoming(event):
    """پیام خصوصی ورودی — منشی همیشه فعاله"""
    uid   = event.sender_id
    count = msg_count[uid]
    msg_count[uid] += 1

    # رپلای بر اساس تعداد پیام
    if count == 0:
        await event.reply(REPLY_FIRST)
        log(f"First reply → {uid}")
    elif count == 1:
        await event.reply(REPLY_REPEAT)
        log(f"Repeat reply → {uid}")
    # count >= 2 → فقط ریکشن، بدون رپلای

    # همیشه ریکشن (بعد از رپلای)
    await add_reaction(event.chat_id, event.id)


@client.on(events.NewMessage(outgoing=True, func=lambda e: e.is_private))
async def handle_outgoing(event):
    """دستورات کنترلی — فقط در Saved Messages"""
    if not (my_id and event.chat_id == my_id):
        return  # فقط Saved Messages

    cmd = (event.raw_text or "").strip()

    if cmd == ".online":
        waiting = list(msg_count.keys())
        msg_count.clear()
        log(f"Online → notifying {len(waiting)} user(s)")
        for uid in waiting:
            try:
                await client.send_message(uid, REPLY_ONLINE)
            except Exception as e:
                log(f"Notify fail {uid}:", repr(e))
        await client.send_message(my_id,
            f"☀️ آنلاین شدی\n"
            f"✅ {len(waiting)} نفر خبر گرفتن"
        )
        await event.delete()

    elif cmd == ".offline":
        count = len(msg_count)
        msg_count.clear()
        await client.send_message(my_id,
            f"🌙 صف ریست شد ({count} نفر پاک شدن)\n"
            f"منشی همچنان فعاله ✅"
        )
        await event.delete()
        log(f"Queue cleared ({count} users)")

    elif cmd == ".status":
        await client.send_message(my_id,
            f"🤖 وضعیت منشی:\n"
            f"👥 {len(msg_count)} نفر در صف منتظرن\n"
            f"🌙 منشی: همیشه فعال"
        )
        await event.delete()

# ── LOOPS ─────────────────────────────────────────────────────────────────────

async def clock_loop():
    """ساعت زنده در نام — هر ۱۵ ثانیه چک، هر دقیقه آپدیت"""
    last_clock = None
    while True:
        clock = datetime.now(tz).strftime("%H:%M")
        if clock != last_clock:
            try:
                await client(UpdateProfileRequest(
                    first_name=f"{NAME_PREFIX} | {clock}"
                ))
                last_clock = clock
                log("Name →", clock)
            except FloodWaitError as e:
                log(f"Name FloodWait {e.seconds}s")
                await asyncio.sleep(e.seconds + 2)
                continue
            except (AuthKeyUnregisteredError, SessionRevokedError, UserDeactivatedError):
                log("Session revoked — exiting")
                sys.exit(1)
            except Exception as e:
                log("Name fail:", repr(e))
                await asyncio.sleep(10)
                continue
        await asyncio.sleep(15)


async def bio_loop():
    """بیوگرافی هکری روزانه — هر ۱۰ دقیقه چک"""
    global last_bio_day
    while True:
        today = datetime.now(tz).date()
        if today != last_bio_day:
            bio = HACKER_BIOS[today.timetuple().tm_yday % len(HACKER_BIOS)]
            await update_bio(bio)
            last_bio_day = today
        await asyncio.sleep(600)

# ── MAIN ──────────────────────────────────────────────────────────────────────

async def main():
    global my_id

    await client.connect()
    if not await client.is_user_authorized():
        log("❌ Session invalid — run generate_session.py first")
        sys.exit(1)

    me = await client.get_me()
    my_id = me.id
    log(f"✅ Logged in: {me.first_name} (id={me.id})")
    log("🌙 Secretary: ALWAYS ON")
    log("📋 Commands → Saved Messages: .online | .offline | .status")

    await asyncio.gather(
        clock_loop(),
        bio_loop(),
        client.run_until_disconnected(),
    )


if __name__ == "__main__":
    try:
        client.loop.run_until_complete(main())
    finally:
        client.loop.run_until_complete(client.disconnect())
