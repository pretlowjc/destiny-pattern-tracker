from fastapi import FastAPI
from typing import List
from models import WeaponPattern
from services.bungie_client import fetch_manifest_version

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
async def get_weapon_patterns():
    # MOCK DATA: will replace this with the Bungie API call
    mock_data = [
            {
                "hash_id": 123456789,
                "name": "Apex Predator",
                "progress": 3,
                "completion_value": 5,
                "is_completed": False
            },
            {
                "hash_id": 987654321,
                "name": "The Enigma",
                "progress": 1,
                "completion_value": 1,
                "is_completed": True
            }
    ]
    return mock_data
