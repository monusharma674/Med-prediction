import asyncio
import httpx
from app.main import app

async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        print("HEALTH CHECK RESULT:", res.json())

if __name__ == "__main__":
    asyncio.run(run())
