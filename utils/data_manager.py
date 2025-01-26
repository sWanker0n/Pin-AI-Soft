import json
from loguru import logger as ll
import cloudscraper
from utils.agents import generate_random_user_agent

class Data_Manager:
    def __init__(self):
        self.proxies_path = 'data/proxies.txt'
        self.accounts_path = 'data/accounts.json'
    def write_to_file_txt(self, file_path, data):
        file = open(file_path, "w")
        for d in data:
            file.write(d + "\n")
        file.close()

    def check_session(self, session_name):
        data = self.get_data_from_file_json(self.accounts_path)
        if session_name in list(data.keys()):
            return True
        else:
            return False


    def get_data_from_file_json(self, path):
        with open(path, 'r') as file:
            data = json.load(file)
        return data

    def get_data_from_accounts(self, session_name, proxy=False, ua=False):
        data = self.get_data_from_file_json(self.accounts_path)
        if proxy:
            if session_name in list(data.keys()):
                proxy = data.get(session_name).get('proxy')
                return proxy
            else:
                ll.warning(f"Session {session_name} is not in accounts list")
                return False
        elif ua:
            if session_name in list(data.keys()):
                ua = data.get(session_name).get('user-agent')
                return ua
            else:
                ll.warning(f"Session {session_name} is not in accounts list")
                return False

    def get_useragent(self, session_name):
        ua = self.get_data_from_accounts(session_name=session_name, ua=True)
        if ua == '':
            ll.info(f"Session {session_name} dont have User-Agent | will generage new one")
            ua = self.change_ua_for_existing_accounts(session_name=session_name)
            ll.info(f"User-Agent for session {session_name} changed to {ua}")
            return ua
        else:
            return ua


    def get_proxy(self, find_in_accounts=True, session_name=None):
        if find_in_accounts == True and session_name is not None:
            proxy = self.get_data_from_accounts(session_name=session_name, proxy=True)
            if proxy == False:
                with open(self.proxies_path, 'r') as file:
                    data = [row.strip() for row in file]
                    proxy = data.pop(0)
                    self.write_to_file_txt(self.proxies_path, data)
                    return proxy
            return proxy
        else:
            with open(self.proxies_path, 'r') as file:
                data = [row.strip() for row in file]
                proxy = data.pop(0)
                self.write_to_file_txt(self.proxies_path, data)
                return proxy

    def change_proxy_for_existing_accounts(self, session_name):
        data = self.get_data_from_file_json(self.accounts_path)
        proxy = self.get_proxy()
        if session_name in list(data.keys()):
            with open(self.accounts_path, 'w') as file:
                ll.info(f"{session_name} in accounts list")
                data[session_name]['proxy'] = proxy
                data = json.dumps(data, indent=4)
                file.write(data)
                return proxy
        else:
            ll.warning(f"{session_name} is not in accounts list")
            return False

    def change_ua_for_existing_accounts(self, session_name):
        data = self.get_data_from_file_json(self.accounts_path)
        ua = generate_random_user_agent()
        with open(self.accounts_path, 'w') as file:
            if session_name in list(data.keys()):
                ll.info(f"{session_name} in accounts list")
                data[session_name]['user-agent'] = ua
                data = json.dumps(data, indent=4)
                file.write(data)
                return ua
            else:
                ll.warning(f"{session_name} is not in accounts list")
                return False

    def change_data_for_existing_accounts(self, session_name, var, value):
        data = self.get_data_from_file_json(self.accounts_path)
        if session_name in list(data.keys()):
            if data.get(session_name).get(var) != value:
                with open(self.accounts_path, 'w') as file:
                    if var == 'access_token' or var == 'refresh_token':
                        ll.info(f"For session {session_name} changed | {var} | from | {data.get(session_name).get(var)[:6]}...{data.get(session_name).get(var)[-3:]} | to | {value[:6]}...{value[-3:]}")
                    else:
                        ll.info(f"For session {session_name} changed | {var} | from | {data.get(session_name).get(var)} | to | {value}")
                    data[session_name][var] = value
                    data = json.dumps(data, indent=4)
                    file.write(data)
                    return value
            else:
                return None
        else:
            ll.warning(f"{session_name} is not in accounts list")
            return False

    def change_data_for_existing_pinai_accounts(self, session_name, var, value):
        data = self.get_data_from_file_json(self.accounts_path)
        if session_name in list(data.keys()):
            if data.get(session_name).get('pin_ai').get(var) != value:
                with open(self.accounts_path, 'w') as file:
                    ll.info(
                        f"For session {session_name} changed | {var} | from | {data.get(session_name).get('pin_ai').get(var)} | to | {value}")
                    data[session_name]['pin_ai'][var] = value
                    data = json.dumps(data, indent=4)
                    file.write(data)
                    return value
            else:
                return None
        else:
            ll.warning(f"{session_name} is not in accounts list")
            return False


    def change_enter_tasks_data_for_existing_pinai_accounts(self, session_name, task, value):
        data = self.get_data_from_file_json(self.accounts_path)
        if session_name in list(data.keys()):
            try:
                if data.get(session_name).get('pin_ai').get('enter_tasks').get(task) != value:
                    with open(self.accounts_path, 'w') as file:
                        ll.info(f"For session {session_name} changed | {task} | from | {data.get(session_name).get('pin_ai').get('enter_tasks').get(task)} | to | {value}")
                        data[session_name]['pin_ai']['enter_tasks'][task] = value
                        data = json.dumps(data, indent=4)
                        file.write(data)
                        return value
                else:
                    return None
            except AttributeError:
                with open(self.accounts_path, 'w') as file:
                    try:
                        data[session_name]['pin_ai']['enter_tasks'][task] = value
                    except KeyError as err:
                        if str(err) == "'enter_tasks'":
                            ll.info(1)
                            data[session_name]['pin_ai']['enter_tasks'] = {"Follow us on X": False, "Join our Telegram group": False, 'Join our Discord server': False}
                            data[session_name]['pin_ai']['enter_tasks'][task] = value
                    ll.info(f"For session {session_name} changed | {task} | from | None | to | {value}")
                    data = json.dumps(data, indent=4)
                    file.write(data)
                    return value

        else:
            ll.warning(f"{session_name} is not in accounts list")
            return False


    def add_new_tg_session(self, session_name, session_pass, session_proxy):
        data = self.get_data_from_file_json(self.accounts_path)
        with open(self.accounts_path, 'w') as file:
            if session_name not in list(data.keys()):
                d = {
                    'proxy': session_proxy,
                    'app_pass': session_pass,
                    'user-agent': '',
                    "invite_code": "",
                    "inviter": None,
                    "access_token": "",
                    "refresh_token": "",
                    "pin_ai": {
                        "points": 0,
                        "level": 1,
                        "is_today_checkin": False,
                        "coins_left": 0
                    }
                }
                data[session_name] = d
                data = json.dumps(data, indent=4)
                file.write(data)
                return True
            else:
                ll.warning(f"{session_name}.session already in list with such data: {data.get(session_name)}")
                data = json.dumps(data, indent=4)
                file.write(data)
                return False

