import asyncio
from os import mkdir
from os.path import exists
from sys import stderr

from loguru import logger

from core import start_checker
from utils import loader

logger.remove()
logger.add(stderr, format='<white>{time:HH:mm:ss}</white>'
                          ' | <level>{level: <8}</level>'
                          ' | <cyan>{line}</cyan>'
                          ' - <white>{message}</white>')


async def main() -> None:
    loader.semaphore = asyncio.Semaphore(value=threads)

    tasks: list[asyncio.Task] = [
        asyncio.create_task(coro=start_checker(account_data=current_account_data))
        for current_account_data in accounts_list
    ]

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    if not exists(path='result'):
        mkdir(path='result')

    with open(file='data/accounts.txt',
              mode='r',
              encoding='utf-8-sig') as file:
        accounts_list: list[str] = [row.strip() for row in file]

    logger.info(f'Loaded {len(accounts_list)} accounts')

    threads: int = int(input('\nThreads: '))
    print()

    try:
        import uvloop

        uvloop.run(main())

    except ModuleNotFoundError:
        asyncio.run(main())

    logger.success('The Work Has Been Successfuly Completed')
    input('\nPress Enter to Exit..')
