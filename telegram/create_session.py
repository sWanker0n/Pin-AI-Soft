import time

from pyrogram import Client
from config import settings
from utils.scraper import Scraper
from utils.data_manager import Data_Manager
import time
import os


def create_session():
    acc = Scraper()
    acc.get_account_session()
    data = Data_Manager()
    time.sleep(2)
    print("Starting Pyrogram client...")

    SESSION_NAME = input("Please enter your session name: ")
    SESSION_NAME_FILE = SESSION_NAME + ".session"

    folder_path = "telegram/sessions"

    all_files_and_dirs = os.listdir(folder_path)

    # Фильтруем только файлы
    files = [f for f in all_files_and_dirs if os.path.isfile(os.path.join(folder_path, f))]
    if SESSION_NAME_FILE in list(files):
        print(f"{SESSION_NAME_FILE} already exist")
        return False


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

            print("Connected successfully!")

            # Check if user is already authorized
            me = app.get_me()
            if me:
                print(f"Logged in as {me.first_name} ({me.username})")
                status = data.add_new_tg_session(session_name=SESSION_NAME, session_pass='Gennady', session_proxy=acc.proxy)
                print(status)
            else:
                print('Cant loggin')

        except Exception as e:
            print(f"An error occurred: {e}")