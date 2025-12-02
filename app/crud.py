from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app import models


async def create_user(db: AsyncSession, user_in):
    data = user_in.dict()
    # RBAC: разрешённые роли
    allowed_roles = {'user', 'admin', 'moderator', 'content-manager'}
    role = (data.get('role') or 'user').lower()
    if role not in allowed_roles:
        role = 'user'
    data['role'] = role
    user = models.User(**data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user(db: AsyncSession, user_id: int):
    res = await db.execute(select(models.User).where(models.User.id == user_id))
    return res.scalars().first()


async def get_user_by_external_id(db: AsyncSession, external_id: str):
    res = await db.execute(select(models.User).where(models.User.external_id == external_id))
    return res.scalars().first()


async def create_object(db: AsyncSession, obj_in):
    obj = models.Object(**obj_in.dict())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_objects(db: AsyncSession, limit: int = 100):
    res = await db.execute(select(models.Object).limit(limit))
    return res.scalars().all()


async def create_booking(db: AsyncSession, booking_in):
    b = models.Booking(**booking_in.dict())
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return b


async def list_bookings_by_user(db: AsyncSession, user_id: int, limit: int = 100):
    res = await db.execute(
        select(models.Booking).where(models.Booking.user_id == user_id).limit(limit)
    )
    return res.scalars().all()


async def list_all_bookings(db: AsyncSession, limit: int = 200):
    res = await db.execute(select(models.Booking).limit(limit))
    return res.scalars().all()


async def update_booking_status(db: AsyncSession, booking_id: int, status: str):
    res = await db.execute(select(models.Booking).where(models.Booking.id == booking_id))
    b = res.scalars().first()
    if not b:
        return None
    b.status = status
    await db.commit()
    await db.refresh(b)
    return b


async def create_review(db: AsyncSession, review_in):
    r = models.Review(**review_in.dict())
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return r


async def create_complaint(db: AsyncSession, comp_in):
    c = models.Complaint(**comp_in.dict())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


async def list_complaints(db: AsyncSession, limit: int = 100):
    res = await db.execute(select(models.Complaint).limit(limit))
    return res.scalars().all()


async def set_complaint_status(db: AsyncSession, complaint_id: int, status: str):
    res = await db.execute(select(models.Complaint).where(models.Complaint.id == complaint_id))
    c = res.scalars().first()
    if not c:
        return None
    c.status = status
    await db.commit()
    await db.refresh(c)
    return c


async def create_event(db: AsyncSession, event_in):
    e = models.Event(**event_in.dict())
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return e


async def list_events(db: AsyncSession, limit: int = 100):
    res = await db.execute(select(models.Event).limit(limit))
    return res.scalars().all()
