import time

from pyrogram import Client
from config import settings
from utils.scraper import Scraper
from utils.data_manager import Data_Manager
import time
from loguru import logger as ll


async def login_to_session(session_name):
    time.sleep(2)
    SESSION_NAME = session_name
    if Data_Manager().check_session(SESSION_NAME) == False:
        ll.error(f'Session {SESSION_NAME} is not in accounts list')
        return False
    acc = Scraper(session_name=SESSION_NAME)
    scraper = acc.get_account_session()
    ll.info(f"Start login to session {SESSION_NAME} ...")


    PROXY = {
        "scheme": "socks5",
        "hostname": acc.proxy_domain,
        "port": int(acc.proxy_port),
        "username": acc.proxy_username,
        "password": acc.proxy_password
    }
    app = Client(SESSION_NAME, api_id=settings.API_ID, api_hash=settings.API_HASH, proxy=PROXY, workdir="telegram/sessions/")

    # Start the client
    async with app:
        try:
            if not app.is_connected:
                await app.connect()

            ll.success("Connected to telegram successfully!")

            me = await app.get_me()
            if me:
                return app, scraper
            else:
                print('Cant loggin')
                return False

        except Exception as e:
            print(f"An error occurred: {e}")
            return False