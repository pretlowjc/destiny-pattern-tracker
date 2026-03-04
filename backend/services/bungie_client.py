import os
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

api_key = os.getenv("BUNGIE_API_KEY")
url = "https://www.bungie.net/Platform/Destiny2/Manifest/"
headers = {"X-API-Key": api_key}
client_id = os.getenv("BUNGIE_CLIENT_ID")
client_secret = os.getenv("BUNGIE_CLIENT_SECRET")

async def fetch_manifest_version():
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data['Response']['version']
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch manifest version")

async def fetch_item_definitions():
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
    
def get_bungie_auth_url() -> str:
    auth_url = f"https://www.bungie.net/en/OAuth/Authorize?client_id={client_id}&response_type=code&state=capstone123"
    return auth_url

async def exchange_code_for_token(auth_code: str) -> dict:
    token_url = "https://www.bungie.net/Platform/App/OAuth/Token"

    # Bungie requires token exchange to be sent as form-encoded data, NOT JSON.
    payload = {
        "grant_type": "authorization_code",
        "code": auth_code
    }

    encoded_payload = urllib.parse.urlencode(payload)

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "DestinyPatternTracker/1.0"
    }

    # We explicitly tell httpx it is allowed to follow the 307 Redirect
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.post(
            token_url, 
            content=encoded_payload, 
            headers=headers,
            auth=(client_id, client_secret) 
        )
        
        if response.status_code != 200:
            print(f"Bungie Token Error ({response.status_code}): {response.text}")
            raise HTTPException(status_code=401, detail="Failed to authenticate with Bungie")
            
        return response.json()