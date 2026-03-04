from fastapi import FastAPI, Depends
from typing import List
from sqlalchemy.orm import Session
from models import WeaponPattern, WeaponPatternDB
from services.bungie_client import fetch_manifest_version
from database import engine, Base, get_db
from fastapi.responses import RedirectResponse
from services.bungie_client import get_bungie_auth_url, exchange_code_for_token

from database import engine, Base
from models import WeaponPatternDB

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Destiny 2 Pattern Tracker API")

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

# The endpoint the Angular frontend will call
@app.get("/api/patterns", response_model=List[WeaponPattern])
async def get_weapon_patterns(db: Session = Depends(get_db)):
    weapons = db.query(WeaponPatternDB).all()
    return weapons

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
    Endpoint 2: Bungie sendt hs user back here with the secret 'code'.
    """
    # Security check to ensure the request acutally came from our login flow
    if state != "capstone123":
        return {"error": "Invalid state parameter"}
    
    # Trade the code for the VIP Access Token
    token_data = await exchange_code_for_token(code)

    # In a production app, we would save this token to the database or an encrpytion cookie.
    # For testing right now, we will just return it to the screen to prove it works.
    return {
        "message": "OAuth 2.0 Handshake Complete!",
        "access_token": token_data.get("access_token"),
        "membership_id": token_data.get("membership_id")
    }
