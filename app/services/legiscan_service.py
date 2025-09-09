import httpx
from app.core.config import settings

class LegiScanService:
    def __init__(self):
        self.base_url = "https://api.legiscan.com"
        self.api_key = settings.LEGISCAN_API_KEY

    async def get_bill(self, bill_id: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/?key={self.api_key}&op=getBill&id={bill_id}"
            )
            if response.status_code == 200:
                return response.json()
            return {"error": "Failed to fetch bill"}

    async def get_bills_for_state(self, state: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/?key={self.api_key}&op=getMasterList&state={state}"
            )
            print(f"LegiScan response status: {response.status_code}")
            if response.status_code == 200:
                return response.json()
            return {"error": "Failed to fetch bills"}

legiscan = LegiScanService()