from os.path import exists
from random import choice

from better_proxy import Proxy

if exists(path='data/proxies.txt'):
    with open(file='data/proxies.txt',
              mode='r',
              encoding='utf-8-sig') as file:
        proxies_list: list[str] = [Proxy.from_str(proxy=row.strip()).as_url for row in file]

else:
    proxies_list: list[str] = []


def get_proxy() -> str | None:
    return choice(proxies_list) if proxies_list else None
