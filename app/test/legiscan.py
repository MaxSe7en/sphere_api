import asyncio
from app.services.legiscan_service import LegiScanService

async def test_legiscan():
    legiscan = LegiScanService()
    
    # Test with a known bill ID (e.g., CA SB 1 from 2023)
    bill_data = await legiscan.get_bill("1923442")  # Use a real bill ID if you have one
    print(f"------------> {bill_data}")
    return
    if bill_data:
        print("✅ LegiScan API connected successfully!")
        print(f"Bill title: {bill_data.get('title', 'No title')}")
    else:
        print("❌ LegiScan API test failed - using mock data for now")
        # Return mock data for testing
        mock_bill = {
            "id": "CA_SB_1",
            "state": "CA",
            "title": "Test Bill - Education Funding",
            "status": "Pending",
            "raw_data": {"mock": True}
        }
        return mock_bill

if __name__ == "__main__":
    result = asyncio.run(test_legiscan())
    print(result)