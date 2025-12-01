from pydantic import BaseModel, conint, constr
from typing import Optional, Literal


class UserCreate(BaseModel):
    external_id: Optional[str]
    name: str
    email: Optional[str]
    role: Optional[str] = None  # будет принудительно 'user' если не admin


class UserOut(BaseModel):
    id: int
    external_id: Optional[str]
    name: str
    email: Optional[str]
    role: Optional[str]

    class Config:
        orm_mode = True


class ObjectCreate(BaseModel):
    name: constr(min_length=1, max_length=200)
    description: Optional[str]
    lat: Optional[float]
    lon: Optional[float]


class ObjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    rating: Optional[float]

    class Config:
        orm_mode = True


class BookingCreate(BaseModel):
    user_id: int
    object_id: int
    start_date: Optional[str]
    end_date: Optional[str]
    payment_order_id: Optional[str]


class BookingOut(BaseModel):
    id: int
    user_id: int
    object_id: int
    start_date: Optional[str]
    end_date: Optional[str]
    status: str
    payment_order_id: Optional[str]

    class Config:
        orm_mode = True


class ReviewCreate(BaseModel):
    user_id: int
    object_id: int
    rating: conint(ge=1, le=5)
    text: Optional[str]


class ReviewOut(BaseModel):
    id: int
    user_id: int
    object_id: int
    rating: int
    text: Optional[str]

    class Config:
        orm_mode = True


# --- AI assistant ---

class AIRequest(BaseModel):
    prompt: str
    lang: Optional[str] = "RU"  # RU/KZ/EN


class AIResponse(BaseModel):
    reply: str


# --- Complaints ---

class ComplaintCreate(BaseModel):
    user_id: Optional[int]
    object_id: Optional[int]
    category: constr(min_length=1, max_length=64)
    text: str
    photo_url: Optional[str]
    lat: Optional[float]
    lon: Optional[float]


class ComplaintOut(BaseModel):
    id: int
    user_id: Optional[int]
    object_id: Optional[int]
    category: str
    text: str
    photo_url: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    status: str

    class Config:
        orm_mode = True


class ComplaintStatusUpdate(BaseModel):
    status: Literal['new', 'in_review', 'resolved', 'rejected']


# --- Booking status update ---

class BookingStatusUpdate(BaseModel):
    status: Literal['pending', 'confirmed', 'paid', 'cancelled', 'failed', 'refunded']


# --- Events ---

class EventCreate(BaseModel):
    title: constr(min_length=1, max_length=200)
    description: Optional[str]
    start_at: Optional[str]
    end_at: Optional[str]
    lat: Optional[float]
    lon: Optional[float]


class EventOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_at: Optional[str]
    end_at: Optional[str]
    lat: Optional[float]
    lon: Optional[float]

    class Config:
        orm_mode = True


# --- RAG ---

class RAGDocumentIn(BaseModel):
    title: str
    text: str
    lang: Optional[str] = None  # RU/KZ/EN
    tags: Optional[list[str]] = None

class RAGDocumentsBatch(BaseModel):
    items: list[RAGDocumentIn]
