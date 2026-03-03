print("--- SCRIPT IS AWAKE ---")

import asyncio
from database import SessionLocal
from models import WeaponPatternDB
from services.bungie_client import fetch_item_definitions

async def run_etl_pipeline():
    print("Step 1: Extracting data from Bungie (This may take a moment)...")
    manifest_data = await fetch_item_definitions()

    print("Step 2: Transforming data (Filtering for weapons)...")
    weapons_to_insert = []

    for hash_id, item_data in manifest_data.items():
        # itemType 3 corresponds to weapons in Destiny 2's manifest.
        if item_data.get('itemType') == 3:

            inventory = item_data.get('inventory', {})
            is_craftable = inventory.get('recipeItemHash') is not None

            name = item_data.get('displayProperties', {}).get('name', 'Unknown')

            if is_craftable:
                weapon = WeaponPatternDB(
                    hash_id=hash_id,
                    name=name,
                    progress=0,
                    completion_value=5,
                    is_completed=False
                )
                weapons_to_insert.append(weapon)
                
    print(f"Found {len(weapons_to_insert)} valid weapons. \nStep 3: Loading into database...")

    db = SessionLocal()
    try:
        db.query(WeaponPatternDB).delete()
        db.bulk_save_objects(weapons_to_insert)
        db.commit()
        print("Success! ETL Pipeline Complete. Database is updated.")
    except Exception as e:
        db.rollback()
        print(f"CRITICAL ERROR during database load: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_etl_pipeline())