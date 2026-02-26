import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BUNGIE_API_KEY")

async def test_handshake():
    url = "https://www.bungie.net/Platform/Destiny2/Manifest/"
    headers = {"X-API-Key": API_KEY}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(response.json()['Response']['version'])

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_handshake())
