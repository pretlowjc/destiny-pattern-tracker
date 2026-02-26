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

async def fetch_item_definitions():
    api_key = os.getenv("BUNGIE_API_KEY")
    url = "https://www.bungie.net/Platform/Destiny2/Manifest/"
    headers = {"X-API-Key": api_key}

    async with httpx.AsyncClient() as client:
        manifest_resp = await client.get(url, headers=headers)
        if manifest_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch manifest")
        
        manifest_data = manifest_resp.json()

        item_path = manifest_data['Response']['jsonWorldComponentContentPaths']['en']['DestinyInventoryItemDefinition']
        full_item_url = f"https://www.bungie.net{item_path}"

        print(f"Downloading item definitions from: {full_item_url}")

        item_resp = await client.get(full_item_url)
        if item_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch item definitions")
        
        return item_resp.json()

