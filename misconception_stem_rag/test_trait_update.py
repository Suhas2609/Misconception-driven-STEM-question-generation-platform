"""
Test script to validate hybrid CDM-BKT-NLP trait update system.
"""

import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_trait_updates():
    """Test the hybrid trait update system with a real quiz submission."""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 0. Register test user if doesn't exist
        print("📝 Step 0: Registering test user (if needed)...")
        test_email = f"traittest_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
        test_password = "testpass123"
        
        register_response = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": test_email,
                "password": test_password,
                "name": "Trait Test User"
            }
        )
        
        if register_response.status_code == 201:
            print("✅ Test user created successfully")
        elif register_response.status_code == 400:
            print("ℹ️  Test user already exists")
        else:
            print(f"⚠️  Registration response: {register_response.status_code}")
        
        # 1. Login as test user
        print("🔐 Step 1: Logging in...")
        login_response = await client.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": test_email,
                "password": test_password
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(login_response.text)
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✅ Logged in successfully")
        
        # 2. Get user's current traits
        print("\n📊 Step 2: Fetching current cognitive traits...")
        user_response = await client.get(
            f"{BASE_URL}/auth/me",
            headers=headers
        )
        
        if user_response.status_code != 200:
            print(f"❌ Failed to get user info: {user_response.status_code}")
            return
        
        user_data = user_response.json()
        current_traits = user_data.get("cognitive_traits", {})
        user_id = user_data.get("id")
        print(f"✅ Current traits (User ID: {user_id}):")
        for trait, value in current_traits.items():
            print(f"   {trait}: {value:.3f}")
        
        # 3. Use web UI to create session (manual step)
        print("\n📁 Step 3: Checking for existing sessions...")
        print("⚠️  To test trait updates, you need to:")
        print("   1. Go to http://localhost:5173")
        print("   2. Login with:")
        print(f"      Email: {test_email}")
        print(f"      Password: {test_password}")
        print("   3. Upload a PDF and generate questions")
        print("   4. Come back here and run the test again")
        print("\n💡 For now, let's use mock data to test the core logic...\n")
        
        # Create a minimal mock session for testing
        # We'll submit directly without checking if session exists in DB
        session_id = "mock_test_session"
        test_questions = [
            {
                "question_number": 1,
                "stem": "If force equals mass times acceleration (F=ma), what happens to acceleration if mass doubles while force remains constant?",
                "options": [
                    {"text": "Acceleration is halved", "type": "correct"},
                    {"text": "Acceleration doubles", "type": "misconception"},
                    {"text": "Acceleration remains the same", "type": "plausible_distractor"},
                    {"text": "Acceleration quadruples", "type": "plausible_distractor"}
                ],
                "difficulty": "medium",
                "requires_calculation": True
            },
            {
                "question_number": 2,
                "stem": "What is the primary cause of seasons on Earth?",
                "options": [
                    {"text": "Earth's tilt on its axis", "type": "correct"},
                    {"text": "Earth's distance from the Sun", "type": "misconception"},
                    {"text": "Solar flares", "type": "plausible_distractor"},
                    {"text": "Moon's gravitational pull", "type": "plausible_distractor"}
                ],
                "difficulty": "easy",
                "misconception_target": "Distance misconception"
            },
            {
                "question_number": 3,
                "stem": "In a perfectly elastic collision between two objects, which quantity is conserved?",
                "options": [
                    {"text": "Both momentum and kinetic energy", "type": "correct"},
                    {"text": "Only momentum", "type": "misconception"},
                    {"text": "Only kinetic energy", "type": "plausible_distractor"},
                    {"text": "Neither momentum nor kinetic energy", "type": "plausible_distractor"}
                ],
                "difficulty": "hard"
            }
        ]
        
        print(f"✅ Using mock session with {len(test_questions)} test questions")
        print("   (Note: For full test, create a real session via web UI)")
        
        questions = test_questions
        
        # 4. Create quiz submission with varied performance
        print("\n📝 Step 4: Submitting quiz with mixed performance...")
        
        # Create responses with different patterns to test trait updates
        quiz_responses = []
        
        for i, question in enumerate(questions[:3]):  # Test with first 3 questions
            # Find correct answer
            correct_answer = None
            wrong_answer = None
            for option in question["options"]:
                if option["type"] == "correct":
                    correct_answer = option["text"]
                elif option["type"] in ["misconception", "plausible_distractor"]:
                    wrong_answer = option["text"]
            
            # Pattern 1: Correct + high confidence + metacognitive reasoning
            if i == 0:
                quiz_responses.append({
                    "question_number": question["question_number"],
                    "selected_answer": correct_answer,
                    "confidence": 0.9,
                    "reasoning": "I'm confident this is correct because I can trace the causal chain: if A causes B and B causes C, then A indirectly causes C. I double-checked my logic."
                })
            
            # Pattern 2: Incorrect + low confidence + metacognitive awareness
            elif i == 1:
                quiz_responses.append({
                    "question_number": question["question_number"],
                    "selected_answer": wrong_answer if wrong_answer else question["options"][1]["text"],
                    "confidence": 0.3,
                    "reasoning": "I'm not sure about this one. I think it might be this answer, but I'm uncertain because I haven't fully understood the concept. What happens if we consider edge cases?"
                })
            
            # Pattern 3: Correct + overconfident
            elif i == 2:
                quiz_responses.append({
                    "question_number": question["question_number"],
                    "selected_answer": correct_answer,
                    "confidence": 1.0,
                    "reasoning": "Obviously this."
                })
        
        print(f"   Created {len(quiz_responses)} responses:")
        print(f"   - Response 1: Correct, high confidence, deep reasoning")
        print(f"   - Response 2: Incorrect, low confidence, metacognitive")
        print(f"   - Response 3: Correct, overconfident, shallow reasoning")
        
        # Submit quiz
        submit_response = await client.post(
            f"{BASE_URL}/pdf/sessions/{session_id}/submit-quiz",
            headers=headers,
            json={"responses": quiz_responses}
        )
        
        if submit_response.status_code != 200:
            print(f"❌ Quiz submission failed: {submit_response.status_code}")
            print(submit_response.text)
            return
        
        print(f"✅ Quiz submitted successfully")
        
        # 5. Get updated traits
        print("\n📊 Step 5: Fetching updated cognitive traits...")
        await asyncio.sleep(2)  # Wait for database update
        
        updated_user_response = await client.get(
            f"{BASE_URL}/auth/me",
            headers=headers
        )
        
        if updated_user_response.status_code != 200:
            print(f"❌ Failed to get updated user info")
            return
        
        updated_user_data = updated_user_response.json()
        updated_traits = updated_user_data.get("cognitive_traits", {})
        
        print(f"✅ Updated traits:")
        for trait, value in updated_traits.items():
            old_value = current_traits.get(trait, 0.5)
            change = value - old_value
            emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            print(f"   {emoji} {trait}: {old_value:.3f} → {value:.3f} (Δ{change:+.3f})")
        
        # 6. Analyze results
        print("\n🔬 Step 6: Analysis")
        print("Expected behavior with hybrid CDM-BKT-NLP system:")
        print("✓ Traits should update based on Bayesian inference (not simple ±0.02)")
        print("✓ Metacognitive Awareness should increase (response 2 shows 'I'm not sure')")
        print("✓ Precision should penalize overconfidence (response 3: 100% confidence)")
        print("✓ Analytical Depth should reward deep reasoning (response 1: causal chain)")
        print("✓ Different traits should change by DIFFERENT amounts (not uniform)")
        
        # Check if updates are differentiated
        changes = [updated_traits.get(t, 0.5) - current_traits.get(t, 0.5) 
                   for t in current_traits.keys()]
        unique_changes = len(set(changes))
        
        if unique_changes > 1:
            print(f"\n✅ SUCCESS: Hybrid system working! ({unique_changes} different trait changes)")
        else:
            print(f"\n⚠️ WARNING: All traits changed uniformly - hybrid system may not be active")

if __name__ == "__main__":
    print("="*60)
    print("🧪 Testing Hybrid CDM-BKT-NLP Trait Update System")
    print("="*60)
    asyncio.run(test_trait_updates())
    print("\n" + "="*60)
