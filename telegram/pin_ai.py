import random
import asyncio
from urllib.parse import unquote

from telegram.login_session import login_to_session
from loguru import logger as ll
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.types import InputBotAppShortName
from pyrogram.raw.functions.messages import RequestAppWebView
from data.headers import headers, auth_headers
from utils.agents import generate_random_user_agent, fetch_version
from utils.data_manager import Data_Manager
from config import settings
import time

end_point = "https://prod-api.pinai.tech/"
auth_api = f"{end_point}passport/login/telegram"
home_api = f"{end_point}home"
farm_api = f"{end_point}home/collect"
check_in_api = f"{end_point}task/1001/v1/complete"
task_v4_list_api = f'{end_point}task/v4/list'

class PinAi:
    def __init__(self, session_name):
        self.session_name = session_name
        self.data_manager = Data_Manager()
        self.peer = "hi_PIN_bot"
        self.short_name = 'app'
        self.ref_link = settings.REF_CODE
        self.log_data = ""
        self.tg_client = ""
        self.scraper = ""
        self.auth_token = ''
        self.access_token = ''
        self.points = ""
        self.level = ""
        self.coins = ""
        self.check_in = ""

    async def get_tg_web_data(self):
        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                    start_command_found = False
                    async for message in self.tg_client.get_chat_history(self.peer):
                        if (message.text and message.text.startswith('/start')) or (message.caption and message.caption.startswith('/start')):
                            start_command_found = True
                            ll.info(f"Session {self.session_name} | already have messages with PinAI bot")
                            break
                    if not start_command_found:
                        await self.tg_client.send_message(self.peer, "/start")
                        ll.info(f'Session {self.session_name} successfully started PinAI bot')
                        await asyncio.sleep(random.randint(15, 25))

                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    ll.error(f'session {self.session_name} Invalid')

            while True:
                try:
                    peer = await self.tg_client.resolve_peer(self.peer)
                    break
                except FloodWait as fl:
                    fls = fl.value

                    ll.warning(f"<light-yellow>{self.session_name}</light-yellow> | FloodWait {fl}")
                    ll.info(f"<light-yellow>{self.session_name}</light-yellow> | Sleep {fls}s")

                    await asyncio.sleep(fls + 3)

            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=peer,
                app=InputBotAppShortName(bot_id=peer, short_name=self.short_name),
                platform='android',
                write_allowed=True,
                start_param=self.ref_link
            ))
            auth_url = web_view.url
            tg_web_data = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return tg_web_data

        except Exception as err:
            ll.error(err)

    async def login(self, retry=3):
        if retry == 0:
            return False
        ua = self.data_manager.get_useragent(session_name=self.session_name)
        auth_headers["User-Agent"] = ua
        chrome_ver = fetch_version(auth_headers['User-Agent'])
        auth_headers['Sec-Ch-Ua'] = f'"Chromium";v="{chrome_ver}", "Android WebView";v="{chrome_ver}", "Not.A/Brand";v="99"'
        # try:
        payload = {
            "init_data": self.auth_token,
            "referralCode": self.ref_link
        }
        with self.scraper.post(url=auth_api, json=payload, headers=auth_headers) as login:
            if login.status_code == 200:
                res = login.json()
                self.access_token = res['access_token']
                refresh_token = res['refresh_token']
                inviter = res['inviter']
                invite_code = res['invite_code']
                self.data_manager.change_data_for_existing_accounts(session_name=self.session_name, var='access_token', value=self.access_token)
                self.data_manager.change_data_for_existing_accounts(session_name=self.session_name, var='refresh_token', value=refresh_token)
                self.data_manager.change_data_for_existing_accounts(session_name=self.session_name, var='inviter', value=inviter)
                self.data_manager.change_data_for_existing_accounts(session_name=self.session_name, var='invite_code', value=invite_code)
                headers['authorization'] = f'Bearer {self.access_token}'
                ll.success(f"Session {self.session_name} | Successfully logged in PinAi App!")
                return True
            else:
                ll.warning(f"{self.session_name} | Failed to login: {login.status_code}, retry in 3-5 seconds")
                await asyncio.sleep(random.randint(3, 5))
                return await self.login(retry - 1)
        # except Exception as e:
        #     ll.error(f"{self.session_name} | Unknown error while trying to login: {e}")
        #     return None

    def home(self):
        with self.scraper.get(url=home_api, headers=headers) as response:
            res = response.json()
            self.points = res.get('pin_points_in_number')
            self.level = res.get('current_model').get('current_level')
            self.coins = res.get('total_coins')[0].get('count')
            self.check_in = res.get("is_today_checkin")
            self.data_manager.change_data_for_existing_pinai_accounts(session_name=self.session_name, var='points', value=self.points)
            self.data_manager.change_data_for_existing_pinai_accounts(session_name=self.session_name, var='level', value=self.level)
            self.data_manager.change_data_for_existing_pinai_accounts(session_name=self.session_name, var='coins_left', value=self.coins)
            self.data_manager.change_data_for_existing_pinai_accounts(session_name=self.session_name, var='is_today_checkin', value=self.check_in)

    def v4_list(self, retry=2, task_name=None):
        if retry == 0:
            return False
        if task_name == None:
            try:
                with self.scraper.get(url=task_v4_list_api, headers=headers) as response:
                    if response.status_code == 200:
                        tasks = response.json().get('tasks')
                        for task in tasks:
                            self.data_manager.change_enter_tasks_data_for_existing_pinai_accounts(session_name=self.session_name, task=task.get('task_name'), value=task.get('is_complete'))
                        return tasks
                    else:
                        ll.warning(f"{self.session_name} | Failed to get v4_list data | Status code {response.status_code}, retry in 3-5 seconds")
                        time.sleep(random.randint(3, 5))
                        return self.v4_list(retry - 1)

            except Exception as err:
                ll.error(f"Session {self.session_name} | {err}")
                return False
        else:
            try:
                with self.scraper.get(url=task_v4_list_api, headers=headers) as response:
                    if response.status_code == 200:
                        tasks = response.json().get('tasks')
                        for task in tasks:
                            if task.get('task_name') == task_name:
                                self.data_manager.change_enter_tasks_data_for_existing_pinai_accounts(
                                    session_name=self.session_name, task=task.get('task_name'),
                                    value=task.get('is_complete'))
                                return task
                        ll.error(f"Cant find task in response with name {task_name}")
                        return False
                    else:
                        ll.warning(
                            f"{self.session_name} | Failed to get v4_list data | Status code {response.status_code}, retry in 3-5 seconds")
                        time.sleep(random.randint(3, 5))
                        return self.v4_list(retry - 1)

            except Exception as err:
                ll.error(f"Session {self.session_name} | {err}")
                return False


    async def complete_enter_task(self, task, retry=2):
        if retry == 0:
            return False
        try:
            url = f"{end_point}task/{task.get('task_id')}/v2/complete"
            with self.scraper.post(url=url, headers=headers, json={}) as response:
                if response.status_code == 200:
                    if response.json().get('status') == "success":
                        return True
                    else:
                        ll.warning(f'Session {self.session_name} | Dont receive success in response | received: {response.json()} | will retry in 5 sec')
                        await asyncio.sleep(random.randint(1, 5))
                        return await self.complete_enter_task(retry - 1)
                else:
                    ll.warning(f'Session {self.session_name} | received: {response.status_code} status code |  will retry in 5 sec')
                    await asyncio.sleep(random.randint(1, 5))
                    return await self.complete_enter_task(retry - 1)
        except Exception as err:
            ll.error(f"Session {self.session_name} | {err} |  will retry in 5 sec")
            await asyncio.sleep(random.randint(1, 5))
            return await self.complete_enter_task(retry - 1)


    async def claim_enter_task(self, task, retry=2):
        if retry == 0:
            return False
        try:
            url = f"{end_point}task/{task.get('task_id')}/claim"
            with self.scraper.post(url=url, headers=headers, json={}) as response:
                if response.status_code == 200:
                    if response.json().get('status') == "success":
                        return True
                    else:
                        ll.warning(f'Session {self.session_name} | Dont receive seccess in response | received: {response.json()} | will retry in 5 sec')
                        await asyncio.sleep(random.randint(1, 5))
                        return await self.claim_enter_task(retry - 1)
                else:
                    ll.warning(f'Session {self.session_name} | received: {response.status_code} status code | will retry in 5 sec')
                    await asyncio.sleep(random.randint(1, 5))
                    return await self.claim_enter_task(retry - 1)
        except Exception as err:
            ll.error(f"Session {self.session_name} | {err} | will retry in 5 sec")
            await asyncio.sleep(random.randint(1, 5))
            return await self.claim_enter_task(retry - 1)


    async def enter_tasks(self, ):
            tasks = self.v4_list()
            module_status = False
            if tasks:
                try:
                    tasks = [x for x in tasks if x.get('is_complete') == False]
                    need_to_claim_tasks = [x for x in tasks if x.get('can_claim') == True]
                    need_to_complete_tasks = [x for x in tasks if x.get('can_claim') == False]
                    if len(need_to_complete_tasks) == 0 and len(need_to_claim_tasks) == 0:
                        ll.warning(f"Session {self.session_name} | don't have tasks to make or claim")
                        return module_status

                    for task in need_to_complete_tasks:
                        if task.get('task_name') in ('Follow us on X', "Join our Discord server"):
                            ll.info(f"Session {self.session_name} | Try to complete task {task.get('task_name')}...")
                            status = await self.complete_enter_task(task=task)
                            await asyncio.sleep(random.randint(15, 30))
                            if status:
                                task = self.v4_list(task_name=task.get('task_name'))
                                if task.get('can_claim') == True:
                                    status = await self.claim_enter_task(task=task)
                                    if status:
                                        task = self.v4_list(task_name=task.get('task_name'))
                                        if task.get('is_complete') == True:
                                            ll.success(f"Session {self.session_name} | Complete task {task.get('task_name')}")
                                            self.home()
                                            module_status = True
                                        else:
                                            ll.error(f"Session {self.session_name} | Will skip task {task.get('task_name')}")
                                    else:
                                        ll.error(f"Session {self.session_name} | Will skip task {task.get('task_name')}")
                                else:
                                    ll.error(f"Session {self.session_name} | Will skip task {task.get('task_name')}")
                            else:
                                ll.error(f"Session {self.session_name} | Will skip task {task.get('task_name')}")

                    if len(need_to_claim_tasks) != 0:
                        for task in need_to_claim_tasks:
                            status = await self.claim_enter_task(task=task)
                            if status:
                                task = self.v4_list(task_name=task.get('task_name'))
                                if task.get('is_complete') == True:
                                    ll.success(f"Session {self.session_name} | Complete task {task.get('task_name')}")
                                    self.home()
                                    module_status = True
                                else:
                                    ll.error(f"Session {self.session_name} | Will skip task {task.get('task_name')}")
                            else:
                                ll.error(f"Session {self.session_name} | Will skip task {task.get('task_name')}")
                    if module_status == False:
                        ll.warning(f"Session {self.session_name} | don't have tasks that can make or claim")
                        return module_status

                except Exception as err:
                    ll.error(f"Session {self.session_name} | {err}")
                    return False
            else:
                ll.error(f"Session {self.session_name} | Dont received tasks")
                return False


    async def run(self):
        self.log_data = await login_to_session(session_name=self.session_name)
        self.tg_client = self.log_data[0]
        self.scraper = self.log_data[1]
        access_token_created_time = 0
        ua = self.data_manager.get_useragent(session_name=self.session_name)
        headers["User-Agent"] = ua
        chrome_ver = fetch_version(headers['User-Agent'])
        headers['Sec-Ch-Ua'] = f'"Chromium";v="{chrome_ver}", "Android WebView";v="{chrome_ver}", "Not.A/Brand";v="99"'
        token_live_time = random.randint(5000, 7000)
        while True:
            # try:
            if time.time() - access_token_created_time >= token_live_time:
                tg_web_data = await self.get_tg_web_data()
                self.auth_token = tg_web_data
                access_token_created_time = time.time()
                token_live_time = random.randint(5000, 7000)
            ll.info(f"{self.session_name} | start login to PinAI App ...")
            if await self.login():
                return True
            else:
                return False
            # except Exception as err:
            #     ll.error(err)
            #     break

    async def farm(self):
        if self.coins >= 10:
            ll.info(f"FARM | Session {self.session_name} | have {self.coins} coins to farm")
            i = 0
            while True:
                i += 1
                if self.coins <= 50 and self.coins != 0:
                    ll.info(f"FARM | Session {self.session_name} | № {i} | will farm {self.coins} coins")
                    await asyncio.sleep(random.randint(3, 5))
                    data = [{
                        "type": "Telegram",
                        "count": self.coins
                    }]
                    with self.scraper.post(url=farm_api, json=data, headers=headers) as response:
                        if response.status_code == 200:
                            res = response.json()
                            ll.success(f"FARM | Session {self.session_name} | № {i} | received {res.get('pin_points_in_number') - self.points} pin_points")
                            await asyncio.sleep(random.randint(1, 5))
                            self.home()
                        else:
                            ll.error(f"FARM | Session {self.session_name} | № {i} | received {response.status_code} status code")
                            return False
                        return True
                elif self.coins > 50:
                    a = random.randint(1, 10)
                    if a >= 8:
                        count = random.randint(1, 50)
                    elif a >= 5 and a < 8 and self.coins <= 100:
                        count = random.randint(50, self.coins)
                    elif a >= 5 and a < 8 and self.coins <= 200:
                        count = random.randint(50, self.coins - 50)
                    elif a < 3:
                        count = self.coins
                        await asyncio.sleep(random.randint(1, 10))
                    else:
                        count = 50
                    ll.info(f"FARM | Session {self.session_name} | № {i} | will farm {count} coins")
                    await asyncio.sleep(random.randint(3, 5))
                    data = [{
                        "type": "Telegram",
                        "count": count
                    }]
                    with self.scraper.post(url=farm_api, json=data, headers=headers) as response:
                        if response.status_code == 200:
                            res = response.json()
                            ll.success(f"FARM | Session {self.session_name} | № {i} | received {res.get('pin_points_in_number') - self.points} pin_points")
                            await asyncio.sleep(random.randint(1, 5))
                            self.home()
                        else:
                            ll.error(f"FARM | Session {self.session_name} | № {i} | received {response.status_code} status code")
                            return False
                else:
                    await asyncio.sleep(random.randint(1, 30))
                    return True
        else:
            ll.warning(f"FARM | Session {self.session_name} | Don't have at least 10 coins to start module FARM")
            return False

    async def check_in_task(self):
        if not self.check_in:
            try:
                ll.info(f"CHECK IN | Session {self.session_name} | try to send check-in")
                with self.scraper.post(url=check_in_api, headers=headers, json={}) as response:
                    await asyncio.sleep(random.randint(1, 3))
                    self.home()
                    if self.check_in and response.json().get('status') == 'success':
                        ll.success(f"CHECK IN | Session {self.session_name} | check-in sent | {response.status_code} Status code")
                        return True
                    else:
                        ll.error(f"CHECK IN | Session {self.session_name} | check-in failed | {response.status_code} Status code")
                        return False
            except Exception as err:
                ll.error(err)
                return False
        else:
            ll.warning(f"CHECK IN | Session {self.session_name} | already sent check-in")

    async def start(self, task):
        status = await self.run()
        if status:
            if task == "farm":
                self.home()
                status = await self.farm()
                if status:
                    ll.success(f"Session {self.session_name} | module FARM finished")
                    print("----------------------------------------------------------------------------")
                    await asyncio.sleep(random.randint(settings.SLEEP_ACCOUNTS_MIN, settings.SLEEP_ACCOUNTS_MAX))
                print("----------------------------------------------------------------------------")
            elif task == "check in":
                self.home()
                status = await self.check_in_task()
                if status:
                    print("----------------------------------------------------------------------------")
                    await asyncio.sleep(random.randint(settings.SLEEP_ACCOUNTS_MIN, settings.SLEEP_ACCOUNTS_MAX))
                print("----------------------------------------------------------------------------")
            elif task == "enter_tasks":
                status = await self.enter_tasks()
                if status:
                    ll.success(f"Session {self.session_name} | module ENTER TASKS finished")
                    print("----------------------------------------------------------------------------")
                    await asyncio.sleep(random.randint(settings.SLEEP_ACCOUNTS_MIN, settings.SLEEP_ACCOUNTS_MAX))
                print("----------------------------------------------------------------------------")


            # elif task == 'level_up':
            #     self.home()
            #     ll.info('level up')
            # elif task == "stats":
            #     ll.info('stats')
            else:
                ll.error(f"Don't have such task: {task}")
        else:
            ll.error(f"Stop session {self.session_name}")
