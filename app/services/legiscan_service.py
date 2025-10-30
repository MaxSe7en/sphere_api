import httpx
from app.core.config import settings
from typing import Dict, Any
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

    async def get_master_list(self, state: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(self.base_url, params={
                "key": self.api_key,
                "op": "getMasterList",
                "state": state.upper()
            })
            data = resp.json()
            if data.get("status") != "OK":
                raise ValueError(f"LegiScan: {data}")
            return data["masterlist"]

    async def get_bill(self, bill_id: int) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(self.base_url, params={
                "key": self.api_key,
                "op": "getBill",
                "id": bill_id
            })
            data = resp.json()
            if data.get("status") != "OK":
                raise ValueError(f"LegiScan getBill failed: {data}")
            return data
legiscan = LegiScanService()