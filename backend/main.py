import urllib.parse
from fastapi import FastAPI, Depends, Request, HTTPException
from typing import List
from sqlalchemy.orm import Session
from models import WeaponPattern, WeaponPatternDB
from services.bungie_client import fetch_manifest_version
from database import engine, Base, get_db
from fastapi.responses import RedirectResponse
from services.bungie_client import get_bungie_auth_url, exchange_code_for_token, get_user_memberships
from fastapi.middleware.cors import CORSMiddleware


from database import engine, Base
from models import WeaponPatternDB

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Destiny 2 Pattern Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
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
    """
    Day 14: The Live Data Pipeline. 
    Intercepts the token, asks Bungie who the user is, and returns their personalized dashboard.
    """
    # 1. Grab the token from Angular's HTTP Request
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    token = auth_header.split(" ", 1)[1]

    # 2. Use our existing function to ask Bungie who this token belongs to
    bungie_data = await get_user_memberships(token)
    
    response_data = bungie_data.get("Response") or {}
    destiny_memberships = response_data.get("destinyMemberships") or []
    
    # Fallback to "Guardian" if something goes wrong
    display_name = "Guardian"
    if destiny_memberships:
        display_name = destiny_memberships[0].get("bungieGlobalDisplayName", "Guardian")

    # 3. Return the personalized weapon data directly to Angular!
    return [
        {
            "id": 1, 
            "name": f"The Enigma (Owned by {display_name})", 
            "type": "Glaive",
            "progress": 5
        },
        {
            "id": 2, 
            "name": f"Ammit AR2 (Live sync for {display_name})", 
            "type": "Auto Rifle",
            "progress": 5
        },
        {
            "id": 3, 
            "name": "BXR-Battler", 
            "type": "Pulse Rifle",
            "progress": 5
        },
        {
            "id": 4, 
            "name": "Taipan-4fr", 
            "type": "Linear Fusion Rifle",
            "progress": 5
        }
    ]

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
    frontend_url = f"http://localhost:4200/dashboard?token={safe_token}"

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
