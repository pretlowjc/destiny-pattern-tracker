from fastapi import FastAPI, Depends
from typing import List
from sqlalchemy.orm import Session
from models import WeaponPattern, WeaponPatternDB
from services.bungie_client import fetch_manifest_version
from database import engine, Base, get_db

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
