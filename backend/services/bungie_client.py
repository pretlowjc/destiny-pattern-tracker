import os
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

async def fetch_manifest_version():
    api_key = os.getenv("BUNGIE_API_KEY")
    url = "https://www.bungie.net/Platform/Destiny2/Manifest/"
    headers = {"X-API-Key": api_key}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data['Response']['version']
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch manifest version")

