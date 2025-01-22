import time

from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded
from config import settings
from utils.scraper import Scraper
from utils.data_manager import Data_Manager
import time
from loguru import logger as ll


def login_to_session(session_name):
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
    with app:
        try:
            if not app.is_connected:
                app.connect()

            ll.success("Connected successfully!")

            me = app.get_me()
            if me:
                ll.info(f"Logged in as {me.first_name} ({me.username})")
                return app, scraper
            else:
                print('Cant loggin')
                return False

        except Exception as e:
            print(f"An error occurred: {e}")
            return False