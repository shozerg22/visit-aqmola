import asyncio
from app.database import init_db, AsyncSessionLocal
from app.models import User, Object as Obj, Booking, Review


async def seed():
    async with AsyncSessionLocal() as session:
        # Add sample users
        u1 = User(name="Test User", email="test@example.com", external_id="egov:123")
        u2 = User(name="Traveler", email="traveler@example.com")
        session.add_all([u1, u2])
        await session.flush()

        # Add sample objects
        o1 = Obj(name="Kokshetau Park", description="Demo park", lat=51.2, lon=71.4, rating=4.5)
        o2 = Obj(name="Burabay Lake", description="Scenic lake", lat=52.88, lon=73.45, rating=4.8)
        session.add_all([o1, o2])
        await session.flush()

        # Booking
        b = Booking(user_id=u1.id, object_id=o2.id, start_date="2025-12-01", end_date="2025-12-05", status="confirmed")
        session.add(b)

        # Review
        r = Review(user_id=u2.id, object_id=o2.id, rating=5, text="Amazing place")
        session.add(r)

        await session.commit()
        print("Seed data inserted")


async def main():
    print("Initializing DB (create tables)...")
    await init_db()
    print("Seeding demo data...")
    await seed()


if __name__ == "__main__":
    asyncio.run(main())
