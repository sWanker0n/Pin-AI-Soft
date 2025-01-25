import time
import asyncio
from pyrogram import Client
from config import settings
from utils.scraper import Scraper
from utils.data_manager import Data_Manager
from loguru import logger as ll
import time
import os

import asyncio
from pyrogram import Client
from config import settings
from utils.scraper import Scraper
from utils.data_manager import Data_Manager
from loguru import logger as ll
import os


async def create_session():
    acc = Scraper()
    acc.get_account_session()
    data = Data_Manager()

    await asyncio.sleep(3)
    print("Starting Pyrogram client...")

    # Asynchronously get input from the user
    SESSION_NAME = await asyncio.to_thread(input, "Please enter your session name: ")
    SESSION_NAME_FILE = SESSION_NAME + ".session"
    all_files_and_dirs = os.listdir("telegram/sessions")
    files = [f for f in all_files_and_dirs if os.path.isfile(os.path.join("telegram/sessions", f))]

    if SESSION_NAME_FILE in list(files):
        print(f"{SESSION_NAME_FILE} already exists.")
        return False

    PROXY = {
        "scheme": "socks5",
        "hostname": acc.proxy_domain,
        "port": int(acc.proxy_port),
        "username": acc.proxy_username,
        "password": acc.proxy_password
    }

    app = Client(SESSION_NAME, api_id=settings.API_ID, api_hash=settings.API_HASH, proxy=PROXY,
                 workdir="telegram/sessions/")


    async with app:
        if not app.is_connected:
            await app.connect()
        print("Connected successfully!")
        me = await app.get_me()
        if me:
            print(f"Logged in as {me.first_name} ({me.username})")
            status = data.add_new_tg_session(session_name=SESSION_NAME, session_pass='Gennady',
                                             session_proxy=acc.proxy)
        else:
            print('Can\'t log in.')
    # except Exception as e:
    #     print(f"An error occurred: {e}")

