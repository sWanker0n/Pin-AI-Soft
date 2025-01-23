import random
import time

from telegram.login_session import login_to_session
from loguru import logger as ll
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.types import InputBotAppShortName
from pyrogram.raw.functions.messages import RequestAppWebView
from urllib.parse import unquote
from data.headers import headers, auth_headers
from utils.agents import generate_random_user_agent, fetch_version
from utils.data_manager import Data_Manager


end_point = "https://prod-api.pinai.tech/"
auth_api = f"{end_point}passport/login/telegram"
home_api = f"{end_point}home"
farm_api = f"{end_point}home/collect"

class PinAi:
    def __init__(self, session_name):
        self.session_name = session_name
        self.data_manager = Data_Manager()
        self.peer = "hi_PIN_bot"
        self.short_name = 'app'
        self.ref_link = 'pDV5RYv'
        self.log_data = login_to_session(session_name=self.session_name)
        self.tg_client = self.log_data[0]
        self.scraper = self.log_data[1]
        self.auth_token = ''
        self.access_token = ''
        self.points = ""
        self.level = ""
        self.coins = ""
        self.check_in = ""


    def get_tg_web_data(self):
        try:
            if not self.tg_client.is_connected:
                try:
                    self.tg_client.connect()
                    start_command_found = False
                    for message in self.tg_client.get_chat_history(self.peer):
                        if (message.text and message.text.startswith('/start')) or (message.caption and message.caption.startswith('/start')):
                            start_command_found = True
                            ll.info(f"Session {self.session_name} already have messages with PinAI bot")
                            break
                    if not start_command_found:
                        self.tg_client.send_message(self.peer, "/start")
                        ll.info(f'Session {self.session_name} succesfully started PinAI bot')
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    ll.error(f'session {self.session_name} Invailed')

            while True:
                try:
                    peer = self.tg_client.resolve_peer(self.peer)
                    break
                except FloodWait as fl:
                    fls = fl.value

                    ll.warning(f"<light-yellow>{self.session_name}</light-yellow> | FloodWait {fl}")
                    ll.info(f"<light-yellow>{self.session_name}</light-yellow> | Sleep {fls}s")

                    time.sleep(fls + 3)

            web_view = self.tg_client.invoke(RequestAppWebView(
                peer=peer,
                app=InputBotAppShortName(bot_id=peer, short_name=self.short_name),
                platform='android',
                write_allowed=True,
                start_param=self.ref_link
            ))
            auth_url = web_view.url
            tg_web_data = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
            if self.tg_client.is_connected:
                self.tg_client.disconnect()

            return tg_web_data

        except Exception as err:
            ll.error(err)


    def login(self, retry=1):
        if retry == 0:
            return None
        ua = self.data_manager.get_useragent(session_name=self.session_name)
        auth_headers["User-Agent"] = ua
        chrome_ver = fetch_version(auth_headers['User-Agent'])
        auth_headers['Sec-Ch-Ua'] = f'"Chromium";v="{chrome_ver}", "Android WebView";v="{chrome_ver}", "Not.A/Brand";v="99"'
        try:
            payload = {
                "init_data": self.auth_token,
                "referralCode": self.ref_link
            }
            login = self.scraper.post(url=auth_api, json=payload, headers=auth_headers)
            if login.status_code == 200:
                res = login.json()
                self.access_token  = res['access_token']
                refresh_token = res['refresh_token']
                inviter = res['inviter']
                invite_code = res['invite_code']
                self.data_manager.change_data_for_existing_accounts(session_name=self.session_name, var='access_token', value=self.access_token)
                self.data_manager.change_data_for_existing_accounts(session_name=self.session_name, var='refresh_token', value=refresh_token)
                self.data_manager.change_data_for_existing_accounts(session_name=self.session_name, var='inviter', value=inviter)
                self.data_manager.change_data_for_existing_accounts(session_name=self.session_name, var='invite_code', value=invite_code)
                headers['authorization'] = f'Bearer {self.access_token}'
                ll.success(f"Session {self.session_name} | Successfully logged in!")
                return True
            else:
                print(login.text)
                ll.warning(
                    f"{self.session_name} | Failed to login: {login.status_code}, retry in 3-5 seconds")
                time.sleep(random.randint(3, 5))
                self.login(retry - 1)
                return None
        except Exception as e:
            # traceback.print_exc()
            ll.error(f"{self.session_name} | Unknown error while trying to login: {e}")
            return None


    def home(self):
        response = self.scraper.get(url=home_api, headers=headers).json()
        self.points = response.get('pin_points_in_number')
        self.level = response.get('current_model').get('current_level')
        self.coins = response.get('total_coins')[0].get('count')
        self.check_in = response.get("is_today_checkin")
        self.data_manager.change_data_for_existing_pinai_accounts(session_name=self.session_name, var='points', value=self.points)
        self.data_manager.change_data_for_existing_pinai_accounts(session_name=self.session_name, var='level', value=self.level)
        self.data_manager.change_data_for_existing_pinai_accounts(session_name=self.session_name, var='coins_left', value=self.coins)
        self.data_manager.change_data_for_existing_pinai_accounts(session_name=self.session_name, var='is_today_checkin', value=self.check_in)

    def farm(self):
        if self.coins >= 10:
            ll.info(f"FARM | Session {self.session_name} | have {self.coins} coins to farm")
            i = 0
            while True:
                i = i + 1
                if self.coins <= 50 and self.coins != 0:
                    ll.info(f"FARM | Session {self.session_name} | № {i} | will farm {self.coins} coins")
                    time.sleep(random.randint(3, 5))
                    data = [{
                        "type": "Telegram",
                        "count": self.coins
                    }]
                    response = self.scraper.post(url=farm_api, json=data, headers=headers)
                    if response.status_code == 200:
                        ll.success(f"FARM | Session {self.session_name} | № {i} | received {response.json().get('pin_points_in_number') - self.points} pin_points")
                        time.sleep(random.randint(1, 5))
                        self.home()
                    else:
                        ll.error(f"FARM | Session {self.session_name} | № {i} | received {response.status_code} status code")
                        return False
                    return True
                elif self.coins > 50:
                    a = random.randint(1, 10)
                    if a >= 8:
                        count = random.randint(1, 50)
                    elif a >=5 and a < 8 and self.coins <= 100:
                        count = random.randint(50, self.coins)
                    elif a >=5 and a < 8 and self.coins <= 200:
                        count = random.randint(50, self.coins - 50)
                    elif a == 1:
                        count = self.coins
                        time.sleep(8)
                    else:
                        count = 50
                    ll.info(f"FARM | Session {self.session_name} | № {i} | will farm {count} coins")
                    time.sleep(random.randint(3, 5))
                    data = [{
                        "type": "Telegram",
                        "count": count
                    }]
                    response = self.scraper.post(url=farm_api, json=data, headers=headers)
                    if response.status_code == 200:
                        ll.success(f"FARM | Session {self.session_name} | № {i} | received {response.json().get('pin_points_in_number') - self.points} pin_points")
                        time.sleep(random.randint(1, 5))
                        self.home()
                    else:
                        ll.error(f"FARM | Session {self.session_name} | № {i} | received {response.status_code} status code")
                        return False
                time.sleep(random.randint(1, 30))
        else:
            ll.warning(f"FARM | Session {self.session_name} | Dont have at least 10 coints to start module FARM")
            return False





    def run(self):
        access_token_created_time = 0
        ua = self.data_manager.get_useragent(session_name=self.session_name)
        headers["User-Agent"] = ua
        chrome_ver = fetch_version(headers['User-Agent'])
        headers['Sec-Ch-Ua'] = f'"Chromium";v="{chrome_ver}", "Android WebView";v="{chrome_ver}", "Not.A/Brand";v="99"'
        token_live_time = random.randint(5000, 7000)
        while True:
            can_run = True
            try:
                if can_run:
                    if time.time() - access_token_created_time >= token_live_time:
                        tg_web_data = self.get_tg_web_data()
                        self.auth_token = tg_web_data
                        access_token_created_time = time.time()
                        token_live_time = random.randint(5000, 7000)
                    ll.info(f"Session {self.session_name} start login to PinAI App ...")
                    a = self.login()
                    if a:
                        return True
                    else:
                        return False

            except Exception as err:
                ll.error(err)
                break

    def start(self, task):
        status = self.run()
        if status:
            if task == "farm":
                self.home()
                status = self.farm()
                if status:
                    ll.success(f"Session {self.session_name} | FARM finished")
            elif task == 'level_up':
                self.home()
                ll.info('level up')
            elif task == "stats":
                ll.info('stats')
            else:
                ll.error(f"Dont have such task: {task} ")
        else:
            ll.error(f"Stop session {self.session_name}")



