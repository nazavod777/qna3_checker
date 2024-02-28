import asyncio

import aiofiles


async def append_file(file_folder: str,
                      file_content: str) -> None:
    async with asyncio.Lock():
        async with aiofiles.open(file=file_folder,
                                 mode='a',
                                 encoding='utf-8-sig') as file:
            await file.write(file_content)
