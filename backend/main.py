import urllib.parse
from fastapi import FastAPI, Depends, Request, HTTPException
from typing import List
from sqlalchemy.orm import Session
from models import WeaponPattern, WeaponPatternDB
from services.bungie_client import fetch_manifest_version
from database import engine, Base, get_db
from fastapi.responses import RedirectResponse
from services.bungie_client import get_bungie_auth_url, exchange_code_for_token, get_user_memberships, get_profile_records, fetch_record_definitions
from fastapi.middleware.cors import CORSMiddleware



from database import engine, Base
from models import WeaponPatternDB

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Destiny 2 Pattern Tracker API")

# --- THE MANIFEST CACHE ---
# We store the Manifest in memory here so it's instantly available to all users
MANIFEST_CACHE = {}

@app.on_event("startup")
async def load_manifest_on_startup():
    global MANIFEST_CACHE
    print("\nStarting up... Downloading Bungie Manifest.")
    MANIFEST_CACHE = await fetch_record_definitions()
    print(f"SUCCESS! Loaded {len(MANIFEST_CACHE)} records into memory.\n")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "https://d2patterntracker.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/api/manifest-version")
async def get_manifest_version():
    version = await fetch_manifest_version()
    return {"status": "success", "manifest_version": version}

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "message": "API is operational"
    }

@app.get("/api/patterns")
async def get_live_weapon_patterns(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    token = auth_header.split(" ", 1)[1]

    # --- STEP 1: Get Identity ---
    bungie_data = await get_user_memberships(token)
    destiny_memberships = bungie_data.get("Response", {}).get("destinyMemberships", [])
    if not destiny_memberships:
        raise HTTPException(status_code=404, detail="No Destiny account found.")
        
    m_id = destiny_memberships[0].get("membershipId")
    m_type = destiny_memberships[0].get("membershipType")

    # --- STEP 2: Fetch Live Records ---
    profile_data = await get_profile_records(m_type, m_id, token)
    profile_records = profile_data.get("Response", {}).get("profileRecords", {}).get("data", {}).get("records", {})

    # --- STEP 3: The Dynamic Manifest Merge ---
    live_weapon_data = []
    weapon_id_counter = 1

    # Look at every single record the user has live data for
    for record_hash_str, user_record in profile_records.items():
        
        # Look up what this record actually is in our massive Manifest dictionary
        manifest_record = MANIFEST_CACHE.get(record_hash_str, {})
        display_props = manifest_record.get("displayProperties", {})
        
        name = display_props.get("name", "")
        description = display_props.get("description", "").lower()
        
        # THE FILTER: Bungie uses the exact phrase "weapon's pattern" or "extract a pattern" for deepsight records!
        if "pattern" in description and "extract" in description:
            
            # Dig into the user's save data for this specific weapon
            objectives = user_record.get("objectives", [])
            current_progress = 0
            completion_value = 5
            
            if objectives:
                current_progress = objectives[0].get("progress", 0)
                completion_value = objectives[0].get("completionValue", 5)

            icon_path = display_props.get("icon", "")
            icon_url = f"https://www.bungie.net{icon_path}" if icon_path else None

            live_weapon_data.append({
                "id": weapon_id_counter,
                "name": name,
                "type": "Craftable Weapon", 
                "progress": current_progress,
                "completionValue": completion_value,
                "icon": icon_url
            })
            weapon_id_counter += 1

    print(f"\n[MERGE COMPLETE] Found {len(live_weapon_data)} craftable weapons for this user!\n")
    return live_weapon_data

@app.get("/api/auth/login")
async def login_to_bungie():
    """
    Endpoint 1: The frontend calls this to get sent to Bungie
    """
    auth_url = get_bungie_auth_url()
    return RedirectResponse(url=auth_url)   

@app.get("/api/auth/callback")
async def bungie_auth_callback(code: str, state: str):
    """
    Endpoint 2: Bungie sent hs user back here with the secret 'code'.
    """
    # Security check to ensure the request acutally came from our login flow
    if state != "capstone123":
        return {"error": "Invalid state parameter"}
    
    # Trade the code for the VIP Access Token
    token_data = await exchange_code_for_token(code)

    # ... your existing token exchange code ...
    access_token = token_data.get("access_token")
    
    # THE FIX: Armor the token so the browser doesn't destroy the special characters
    safe_token = urllib.parse.quote(access_token)
    
    # Send them back to Angular using the safe token
    frontend_url = f"https://d2patterntracker.com/dashboard?token={safe_token}"

    return RedirectResponse(url=frontend_url)

@app.get("/api/auth/profile")
async def get_user_profile(request: Request):
    """
    Endpoint 3: The frontend calls this with the user's token to get their Destiny 2 ID
    """
    # 1. Grab the Authorization header sent by Angular
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authentication token")
    
    # 2. Strip away the word "Bearer " to get just the token string
    # The '1' tells Python to only split on the VERY FIRST space it sees, ignoring the rest
    token = auth_header.split(" ", 1)[1]

    # THE CHECK: Print the first 20 characters of the token to the terminal
    print(f"\n[DEBUG] Received Token: {token[:20]}...\n")

    # 3. Ask Bungie for the user's membership info using the token
    bungie_data = await get_user_memberships(token)

    # 4. Extract the primary Destiny 2 membership info (Bulletproofed)
    response_data = bungie_data.get("Response") or {}
    destiny_memberships = response_data.get("destinyMemberships") or []

    if not destiny_memberships:
        raise HTTPException(status_code=404, detail="No Destiny 2 account found for this user")
    
    primary_membership = destiny_memberships[0]

    # 5. Return the exact data Angular needs (This prevents the 500 crash!)
    return {
        "membershipId": primary_membership.get("membershipId"),
        "membershipType": primary_membership.get("membershipType"),
        "displayName": primary_membership.get("bungieGlobalDisplayName")
    }
