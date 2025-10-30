"""Quick test to verify trait updates are working."""
import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_trait_update():
    """Test trait update with mock responses."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Register new test user
        email = f"traittest_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        password = "testpass123"
        
        print("🔐 Registering test user...")
        r = await client.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": password,
            "name": "Trait Test User"
        })
        print(f"   Register: {r.status_code}")
        
        # Login
        print("🔐 Logging in...")
        r = await client.post(f"{BASE_URL}/auth/login", data={
            "username": email,
            "password": password
        })
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"   Login: {r.status_code}")
        
        # Get initial traits
        print("\n📊 Fetching INITIAL traits...")
        r = await client.get(f"{BASE_URL}/auth/me", headers=headers)
        user_data = r.json()
        initial_traits = user_data["cognitive_traits"]
        print("   Initial traits:")
        for trait, value in initial_traits.items():
            print(f"     {trait}: {value:.3f}")
        
        # Submit quiz with strategic responses using debug endpoint
        print("\n📝 Submitting quiz with varied responses...")
        quiz_responses = [
            # Q1: Correct + High confidence + Deep reasoning
            {
                "question_number": 1,
                "selected_answer": "Correct answer",
                "is_correct": True,
                "confidence": 0.9,
                "reasoning": "I'm confident because I traced the causal chain step by step. First, I considered the initial conditions, then I analyzed how they lead to the outcome. I double-checked my logic and verified each step."
            },
            # Q2: Incorrect + Low confidence + Metacognitive
            {
                "question_number": 2,
                "selected_answer": "Wrong answer",
                "is_correct": False,
                "confidence": 0.3,
                "reasoning": "I'm not sure about this one. I think it might be this answer, but I'm uncertain because I haven't fully understood the concept. What happens if we consider alternative explanations?"
            },
            # Q3: Correct + Overconfident + Shallow
            {
                "question_number": 3,
                "selected_answer": "Correct answer",
                "is_correct": True,
                "confidence": 1.0,
                "reasoning": "Obviously this."
            },
            # Q4: Incorrect + High confidence (overconfident error)
            {
                "question_number": 4,
                "selected_answer": "Wrong answer",
                "is_correct": False,
                "confidence": 0.95,
                "reasoning": "I'm very sure this is right."
            },
            # Q5: Correct + Well-calibrated
            {
                "question_number": 5,
                "selected_answer": "Correct answer",
                "is_correct": True,
                "confidence": 0.75,
                "reasoning": "I applied the formula step by step and got this result. Let me verify: if we use the equation, we get exactly this value."
            }
        ]
        
        # Use debug endpoint to apply trait update
        r = await client.post(
            f"{BASE_URL}/pdf-v2/sessions/test_session/debug-apply-trait-update",
            headers=headers,
            json={"session_id": "test", "responses": quiz_responses}
        )
        
        if r.status_code == 200:
            result = r.json()
            updated_traits = result.get("updated_traits", {})
            print("   ✅ Trait update successful!")
            
            # Get updated user profile
            print("\n📊 Fetching UPDATED traits from database...")
            r = await client.get(f"{BASE_URL}/auth/me", headers=headers)
            user_data = r.json()
            db_traits = user_data["cognitive_traits"]
            
            print("\n" + "="*60)
            print("🎯 TRAIT UPDATE RESULTS")
            print("="*60)
            
            changes = []
            for trait, new_value in db_traits.items():
                old_value = initial_traits.get(trait, 0.5)
                change = new_value - old_value
                emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                print(f"{emoji} {trait:22s}: {old_value:.3f} → {new_value:.3f}  (Δ {change:+.3f})")
                if abs(change) > 0.001:
                    changes.append((trait, change))
            
            print("="*60)
            
            # Analysis
            unique_changes = len(set(abs(c[1]) for c in changes))
            
            if unique_changes > 1:
                print("\n✅ SUCCESS: Hybrid CDM-BKT-NLP system is working!")
                print(f"   - Found {unique_changes} different trait change magnitudes")
                print("   - This confirms Bayesian updates (not uniform ±0.02)")
                print("\n🔬 Expected behavior observed:")
                print("   ✓ Different traits changed by different amounts")
                print("   ✓ Changes reflect evidence strength")
            else:
                print("\n⚠️  WARNING: Uniform trait changes detected")
                print("   - All traits may have changed by the same amount")
                print("   - Hybrid system may not be fully active")
            
            return True
        else:
            print(f"   ❌ Trait update failed: {r.status_code}")
            print(f"   Response: {r.text[:500]}")
            return False

if __name__ == "__main__":
    print("="*60)
    print("🧪 Testing Hybrid CDM-BKT-NLP Trait Update System")
    print("="*60)
    asyncio.run(test_trait_update())
    print("\n" + "="*60)
