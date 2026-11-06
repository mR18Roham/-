"""Run this ONCE on your own computer to create the SESSION string.

    pip install telethon
    python generate_session.py

Then put the printed string into Railway as the SESSION variable.
Never commit or share this string: it gives full access to your account.
"""
import os

from telethon.sessions import StringSession
from telethon.sync import TelegramClient

api_id = int(os.environ.get("API_ID") or input("API_ID: ").strip())
api_hash = os.environ.get("API_HASH") or input("API_HASH: ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\nYour SESSION string:\n")
    print(client.session.save())
