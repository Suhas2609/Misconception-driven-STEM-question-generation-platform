"""Simple test to verify enhanced NLP is working."""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Register
        email = f"simple_test_{datetime.now().strftime('%Y%m%d%H%M%S')}@test.com"
        r = await client.post(f"{BASE_URL}/auth/register", json={
            "name": "Simple Test",
            "username": "simpletest",
            "email": email,
            "password": "testpass123"
        })
        print(f"Register: {r.status_code}")
        
        # Login
        r = await client.post(f"{BASE_URL}/auth/login", data={
            "username": email,
            "password": "testpass123"
        })
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"Login: {r.status_code}")
        
        # Test analytical depth response with rich causal reasoning
        analytical_response = {
            "session_id": "test",
            "responses": [{
                "question_number": 1,
                "selected_answer": "A",
                "is_correct": True,
                "confidence": 0.9,
                "reasoning": """First, I analyzed the problem systematically. The initial velocity is zero 
                because the object starts from rest. Therefore, using the kinematic equation v² = u² + 2as, 
                I can substitute u=0. This leads to v² = 2as. Because acceleration is 5 m/s² and 
                displacement is 40m, this results in v² = 2(5)(40) = 400, thus v = 20 m/s."""
            }]
        }
        
        print("\n=== Testing Enhanced NLP Analyzer ===")
        r = await client.post(
            f"{BASE_URL}/pdf-v2/sessions/test/debug-apply-trait-update",
            headers=headers,
            json=analytical_response
        )
        
        print(f"\nStatus: {r.status_code}")
        if r.status_code == 200:
            result = r.json()
            print("\n=== FULL RESPONSE ===")
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {r.text}")

if __name__ == "__main__":
    asyncio.run(main())
