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
    
async def fetch_record_definitions() -> dict:
    """
    Downloads the JSON slice of the Manifest containing Triumph and Pattern text.
    """
    url = "https://www.bungie.net/Platform/Destiny2/Manifest/"
    
    # We don't need the user token for the Manifest, just the API key
    raw_api_key = os.getenv("BUNGIE_API_KEY", "")
    headers = {"X-API-Key": raw_api_key.strip(' "\'\r\n\ufeff')}

    async with httpx.AsyncClient() as client:
        # 1. Ask Bungie where the latest Manifest is
        manifest_resp = await client.get(url, headers=headers)
        if manifest_resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch manifest paths")
        
        manifest_data = manifest_resp.json()

        # 2. Get the specific URL for the English 'DestinyRecordDefinition'
        record_path = manifest_data['Response']['jsonWorldComponentContentPaths']['en']['DestinyRecordDefinition']
        full_record_url = f"https://www.bungie.net{record_path}"

        # 3. Download the actual data dictionary
        print(f"\n[MANIFEST] Downloading Manifest Records from: {full_record_url} ...")
        record_resp = await client.get(full_record_url)
        
        return record_resp.json()
    
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
    
async def get_user_memberships(access_token: str) -> dict:
    """
    Uses the OAuth token to get the user's Destiny 2 Membership ID and Type.
    """
    # Note: Putting the trailing slash back, as Bungie's official docs request it for this specific endpoint
    url = "https://www.bungie.net/Platform/User/GetMembershipsForCurrentUser/"
    
    # 1. Strip everything, including the invisible Windows BOM (\ufeff)
    raw_api_key = os.getenv("BUNGIE_API_KEY", "")
    clean_api_key = raw_api_key.strip(' "\'\r\n\ufeff')
    clean_token = access_token.strip(' "\'\r\n\ufeff')

    # ==========================================
    # THE X-RAY: Let's see exactly what we are sending
    print("\n=== OUTGOING BUNGIE REQUEST ===")
    print(f"API Key Length: {len(clean_api_key)} characters (A valid Bungie key MUST be exactly 32)")
    print(f"API Key Starts With: {clean_api_key[:4]}...")
    print(f"Token Length: {len(clean_token)} characters")
    print("===============================\n")
    # ==========================================

    headers = {
        "X-API-Key": clean_api_key,
        "Authorization": f"Bearer {clean_token}",
        "User-Agent": "DestinyPatternTracker/1.0"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        
        if response.status_code != 200:
            print("\n=== BUNGIE API REJECTED THE REQUEST ===")
            print(f"Bungie Status Code: {response.status_code}")
            print(f"Bungie Error: {repr(response.text[:250])}") 
            print("=======================================\n")
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch user profile")
            
        return response.json()
    
async def get_profile_records(membership_type: int, membership_id: str, access_token: str) -> dict:
    url = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=900"

    raw_api_key = os.getenv("BUNGIE_API_KEY", "")
    clean_api_key = raw_api_key.strip(' "\'\r\n\ufeff')
    clean_token = access_token.strip(' "\'\r\n\ufeff')

    headers = {
        "X-API-Key": clean_api_key,
        "Authorization": f"Bearer {clean_token}",
        "User-Agent": "DestinyPatternTracker/1.0"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
          
        if response.status_code != 200:
            print("\n=== BUNGIE API REJECTED THE REQUEST ===")
            print(f"Bungie Status Code: {response.status_code}")
            print(f"Bungie Error: {repr(response.text[:250])}") 
            print("=======================================\n")
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch user records")
                
        return response.json()