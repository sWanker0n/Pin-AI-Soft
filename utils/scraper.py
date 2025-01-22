import fake_useragent
import cloudscraper
from loguru import logger as ll
from utils.data_manager import Data_Manager


class Scraper():
    def __init__(self, session_name=None):
        self.session_name = session_name
        self.UA = fake_useragent.UserAgent().random
        self.s = cloudscraper.create_scraper()
        self.proxy = ""
        self.proxy_domain = ""
        self.proxy_port = ""
        self.proxy_username = ""
        self.proxy_password = ""
        self.Data = Data_Manager()


    def split_proxy(self):
        self.proxy = self.Data.get_proxy(session_name=self.session_name)
        p = self.proxy.split(":")
        self.proxy_domain = p[0]
        self.proxy_port = p[1]
        self.proxy_username = p[2]
        self.proxy_password = p[3]



    def check_proxy(self):
        # FORMAT http://{proxy_username}:{proxy_password}@{http_proxy_url}
        self.split_proxy()
        url = 'https://jsonip.com'
        for i in range(1, 6):
            p = f'{self.proxy_username}:{self.proxy_password}@{self.proxy_domain}:{self.proxy_port}'
            proxy = {
                'socks5': f'socks5://{p}'
            }
            try:
                self.s.proxies.update(proxy)
                response = self.s.get(url=url)
                if response.status_code == 200:
                    ll.info(f'proxy ip: {response.json().get("ip")}')
                    return True
                else:
                    ll.warning('Proxy Error')
                    if self.session_name == None:
                        self.proxy = self.Data.get_proxy()
                        self.split_proxy()
                    else:
                        self.proxy = self.Data.change_proxy_for_existing_accounts(self.session_name)
                        self.split_proxy()

            except Exception as err:
                ll.warning(f'{err}')
                if self.session_name == None:
                    self.proxy = self.Data.get_proxy()
                    self.split_proxy()
                else:
                    self.proxy = self.Data.change_proxy_for_existing_accounts(self.session_name)
                    self.split_proxy()

        ll.error(f'[Wallet {self.session_name}] changing proxy didnt help')
        return False

    def get_account_session(self):
        status = self.check_proxy()
        if status:
            return self.s
        else:
            return False



