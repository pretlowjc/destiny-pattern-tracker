from database import SessionLocal
from models import WeaponPatternDB

def seed_database():
    db = SessionLocal()
    
    # Safety check: Only seed if the table is empty
    if db.query(WeaponPatternDB).count() == 0:
        print("Seeding database with initial pattern data...")
        
        # We will replace these mock values with live Bungie Profile data later
        initial_weapons = [
            WeaponPatternDB(
                hash_id=3874853227, 
                name="Apex Predator", 
                progress=3, 
                completion_value=5, 
                is_completed=False
            ),
            WeaponPatternDB(
                hash_id=2590192243, 
                name="The Enigma", 
                progress=1, 
                completion_value=1, 
                is_completed=True
            )
        ]
        
        db.add_all(initial_weapons)
        db.commit()
        print("Success! Database is seeded.")
    else:
        print("Database already contains data. Skipping seed.")
        
    db.close()

if __name__ == "__main__":
    seed_database()