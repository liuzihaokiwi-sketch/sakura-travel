"""Debug: test order status transition"""
import asyncio
import uuid
from app.db.session import AsyncSessionLocal
from app.db.models.business import Order, TripRequest
from sqlalchemy import select


async def main():
    async with AsyncSessionLocal() as session:
        order = await session.get(Order, uuid.UUID("6b4b270f-3b15-4962-8399-75049d47a2f0"))
        print(f"Before: status='{order.status}'")
        
        order.status = "sample_viewed"
        await session.flush()
        print(f"After flush: status='{order.status}'")
        
        await session.commit()
        print("✅ Committed successfully")
        
        # Verify
        await session.refresh(order)
        print(f"Verified: status='{order.status}'")

asyncio.run(main())