from typing import List, Dict, Any, Optional

# Заглушечные адаптеры интеграций. Замените на реальные вызовы API.

class BookingAdapter:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def search(self, query: str) -> List[Dict[str, Any]]:
        # TODO: Реализовать вызов Booking API (при наличии разрешения и ключей)
        return [
            {"id": "bk1", "name": "Booking Hotel A", "rating": 8.6, "price": 24000, "currency": "KZT"},
            {"id": "bk2", "name": "Booking Resort B", "rating": 9.1, "price": 38000, "currency": "KZT"},
        ]

    async def detail(self, item_id: str) -> Dict[str, Any]:
        return {"id": item_id, "name": "Booking Item", "details": "Mock details"}


class TripAdvisorAdapter:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def search(self, query: str) -> List[Dict[str, Any]]:
        # TODO: Реализовать вызов TripAdvisor API
        return [
            {"id": "ta1", "name": "TripAdvisor Hotel C", "rating": 4.3, "reviews": 124},
            {"id": "ta2", "name": "TripAdvisor Attraction D", "rating": 4.7, "reviews": 512},
        ]

    async def detail(self, item_id: str) -> Dict[str, Any]:
        return {"id": item_id, "name": "TripAdvisor Item", "details": "Mock details"}


class FreedomTravelAdapter:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    async def search(self, query: str) -> List[Dict[str, Any]]:
        # TODO: Реализовать вызов Freedom Travel API
        return [
            {"id": "ft1", "name": "Freedom Travel Tour E", "duration": "3 days", "price": 120000, "currency": "KZT"},
            {"id": "ft2", "name": "Freedom Travel Tour F", "duration": "5 days", "price": 210000, "currency": "KZT"},
        ]

    async def detail(self, item_id: str) -> Dict[str, Any]:
        return {"id": item_id, "name": "Freedom Travel Item", "details": "Mock details"}


def get_adapter(platform: str, api_key: Optional[str] = None):
    p = platform.lower()
    if p in ("booking", "booking.com"):
        return BookingAdapter(api_key)
    if p in ("tripadvisor", "trip-advisor"):
        return TripAdvisorAdapter(api_key)
    if p in ("freedom", "freedomtravel", "freedom travel"):
        return FreedomTravelAdapter(api_key)
    raise ValueError(f"Unsupported platform: {platform}")
