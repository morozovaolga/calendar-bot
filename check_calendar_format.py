"""Проверка формата календаря"""

import asyncio
import httpx

async def check():
    url = "https://calendar.yandex.ru/export/html.xml?private_token=<REDACTED>&tz_id=Europe/Moscow&limit=90"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        print("Первые 3000 символов календаря:")
        print("=" * 60)
        print(r.text[:3000])
        print("=" * 60)
        print(f"\nВсего символов: {len(r.text)}")

asyncio.run(check())

