import asyncio
from services.bungie_client import fetch_manifest_version

async def test_handshake():
    print("--- TESTING BUNGIE API HANDSHAKE ---")
    try:
        version = await fetch_manifest_version()
        print("Successfully connected to Bungie API.")
        print(f"Current Destiny 2 Manifest Version: {version}")
    except Exception as e:
        print(f"Error during handshake: {e}")

if __name__ == "__main__":
    asyncio.run(test_handshake())