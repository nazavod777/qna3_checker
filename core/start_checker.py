from uuid import uuid4

import aiohttp
from eth_account import Account
from eth_account.account import LocalAccount
from eth_account.messages import encode_defunct
from loguru import logger
from pyuseragents import random as random_useragent
from web3.auto import w3

from utils import loader, append_file, get_proxy

Account.enable_unaudited_hdwallet_features()


class Checker:
    def __init__(self,
                 account: LocalAccount) -> None:
        self.account: LocalAccount = account

    def get_signed_hash(self,
                        sign_message: str) -> str:
        sign = w3.eth.account.sign_message(encode_defunct(
            text=sign_message), private_key=self.account.key).signature.hex()

        return sign

    async def do_auth(self,
                      client: aiohttp.ClientSession,
                      sign_hash: str) -> str:
        response_text: None = None

        while True:
            proxy: str | None = get_proxy()

            try:
                r: aiohttp.ClientResponse = await client.post(
                    url='https://api.qna3.ai/api/v2/auth/login',
                    params={
                        'via': 'wallet'
                    },
                    json={
                        'signature': sign_hash,
                        'wallet_address': self.account.address
                    },
                    headers={
                        'x-id': str(uuid4())
                    },
                    proxy=proxy
                )

                response_text: str = await r.text()
                response_json: dict = await r.json(content_type=None)

                return response_json['data']['accessToken']

            except Exception as error:
                if response_text:
                    logger.error(
                        f'{self.account.address} | Unexpected Error When Do Auth: {error}, response text: '
                        f'{response_text}'
                    )

                else:
                    logger.error(
                        f'{self.account.address} | Unexpected Error When Do Auth: {error}'
                    )

    async def get_balance(self,
                          client: aiohttp.ClientSession) -> float:
        response_text: None = None

        while True:
            proxy: str | None = get_proxy()

            try:
                r: aiohttp.ClientResponse = await client.post(url='https://api.qna3.ai/api/v2/graphql',
                                                              json={
                                                                  'query': 'query loadAirDrop {\n  airdrop {\n    binance_claim {\n      amount\n      binance_address\n      id\n    }\n    current {\n      contract\n      end_at\n      start_at\n    }\n    claim {\n      amount\n      claimed\n      proof\n      id\n    }\n    claimed {\n      amount\n      updated_at\n    }\n  }\n}',
                                                                  'variables': {}
                                                              },
                                                              proxy=proxy)
                response_text: str = await r.text()
                response_json: dict = await r.json(content_type=None)

                claim_balance: dict | None = response_json['data']['airdrop']['claim']

                return claim_balance['amount'] if claim_balance else 0

            except Exception as error:
                if response_text:
                    logger.error(
                        f'{self.account.address} | Unexpected Error When Getting Balance: {error}, response text: '
                        f'{response_text}'
                    )

                else:
                    logger.error(
                        f'{self.account.address} | Unexpected Error When Getting Balance: {error}'
                    )

    async def start_checker(self) -> None:
        # noinspection PyTypeChecker
        async with aiohttp.ClientSession(
                headers={
                    'accept': 'application/json, text/plain, */*',
                    'accept-language': 'ru,en;q=0.9,vi;q=0.8,es;q=0.7,cy;q=0.6',
                    'content-type': 'application/json',
                    'origin': 'https://staging.qna3.ai',
                    'user-agent': random_useragent()
                },
                connector=aiohttp.TCPConnector(
                    verify_ssl=None,
                    ssl=False,
                    use_dns_cache=False,
                    ttl_dns_cache=300,
                    limit=None
                ),
                timeout=aiohttp.ClientTimeout(10)
        ) as client:
            sign_hash: str = self.get_signed_hash(sign_message='AI + DYOR = Ultimate Answer to Unlock Web3 Universe')

            auth_token: str = await self.do_auth(client=client,
                                                 sign_hash=sign_hash)
            client.headers['Authorization']: str = f'Bearer {auth_token}'

            account_balance: float = await self.get_balance(client=client)

            if account_balance > 0:
                logger.success(
                    f'{self.account.address} | Account Balance: {account_balance}'
                )

                await append_file(
                    file_folder='result/with_balance.txt',
                    file_content=f'{self.account.key.hex()} | {self.account.address} - {account_balance}\n'
                )

            else:
                logger.error(
                    f'{self.account.address} | Zero Balance'
                )

                await append_file(
                    file_folder='result/zero_balance.txt',
                    file_content=f'{self.account.key.hex()} | {self.account.address} - {account_balance}\n'
                )


async def start_checker(account_data: str) -> None:
    async with loader.semaphore:
        account_formatted: None = None

        try:
            account_formatted: LocalAccount = Account.from_key(private_key=account_data)

        except Exception:
            pass

        if not account_formatted:
            try:
                account_formatted: LocalAccount = Account.from_mnemonic(mnemonic=account_data)

            except Exception:
                logger.error(f'{account_data} | Not Key And not Mnemonic')

                await append_file(file_folder='result/errors.txt',
                                  file_content=f'{account_data}\n')
                return

        try:
            await Checker(account=account_formatted).start_checker()

        except Exception as error:
            logger.error(f'{account_data} | Unexpected Error: {error}')

            await append_file(file_folder='result/errors.txt',
                              file_content=f'{account_data}\n')
