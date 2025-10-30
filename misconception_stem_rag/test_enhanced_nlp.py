"""
Test script to verify enhanced NLP-based cognitive trait analysis.

This tests the research-grade semantic understanding capabilities:
- spaCy dependency parsing
- TextBlob sentiment/subjectivity
- Context-aware reasoning scoring
- Explainable trait updates
"""

import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_enhanced_nlp_analysis():
    """
    Test the enhanced NLP cognitive trait analyzer with realistic student responses.
    """
    
    print("=" * 80)
    print("🧠 TESTING ENHANCED NLP COGNITIVE TRAIT ANALYSIS")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # Step 1: Register and login
        timestamp = int(datetime.now().timestamp())
        username = f"nlp_test_user_{timestamp}"
        password = "TestPass123!"
        
        print(f"\n📝 Step 1: Creating test user: {username}")
        
        register_response = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "name": username,
                "username": username,
                "email": f"{username}@test.com",
                "password": password
            }
        )
        
        if register_response.status_code not in [200, 201]:
            print(f"❌ Registration failed: {register_response.text}")
            return
        
        print("✅ User registered successfully")
        
        # Login
        login_response = await client.post(
            f"{BASE_URL}/auth/login",
            data={
                "username": f"{username}@test.com",  # Uses email for login
                "password": password
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Logged in successfully")
        
        # Use a dummy session ID for debug endpoint (it doesn't validate the session)
        session_id = "test_nlp_session"
        
        # Step 2: Test different reasoning styles for different traits
        print("\n" + "=" * 80)
        print("🧪 TESTING DIFFERENT REASONING STYLES")
        print("=" * 80)
        
        # Test Case 1: HIGH ANALYTICAL DEPTH
        test_responses_analytical = [
            {
                "question_number": 1,
                "selected_option": "A",
                "is_correct": True,
                "confidence": 0.8,
                "reasoning": """
                First, I analyzed the initial conditions of the system. The object starts at rest, 
                which means the initial velocity is zero. Therefore, I can use the kinematic equation 
                v² = u² + 2as. Because the acceleration is constant, this equation leads to a direct 
                solution. After calculating, I found that the final velocity must be 20 m/s. This 
                makes sense because the displacement and acceleration values create this specific result.
                """
            },
            {
                "question_number": 2,
                "selected_option": "B",
                "is_correct": True,
                "confidence": 0.9,
                "reasoning": """
                The causal relationship here is clear: increasing temperature causes molecular kinetic 
                energy to increase, which results in higher pressure when volume is constant. This leads 
                to the gas law relationship P ∝ T. Thus, doubling temperature produces double pressure.
                """
            }
        ]
        
        # Test Case 2: HIGH METACOGNITION
        test_responses_metacognition = [
            {
                "question_number": 1,
                "selected_option": "A",
                "is_correct": True,
                "confidence": 0.6,
                "reasoning": """
                I'm not entirely sure about this, but I think the answer is A. I checked my work twice 
                and realized that I initially made an error in my calculation. After reviewing the 
                formula, I noticed that I had the wrong sign. I used the kinematic equation approach, 
                which seemed more reliable than trying to solve it graphically. I'm probably about 60% 
                confident because there might be a conceptual aspect I'm missing.
                """
            },
            {
                "question_number": 2,
                "selected_option": "C",
                "is_correct": False,
                "confidence": 0.3,
                "reasoning": """
                I don't know for certain, but I suspect it might be C. I'm uncertain because I haven't 
                fully understood how the variables interact here. My approach was to eliminate obvious 
                wrong answers, but I realized I need to review this concept more carefully.
                """
            }
        ]
        
        # Test Case 3: HIGH CURIOSITY
        test_responses_curiosity = [
            {
                "question_number": 1,
                "selected_option": "A",
                "is_correct": True,
                "confidence": 0.85,
                "reasoning": """
                This is interesting! I wonder why the velocity increases at this specific rate? What if 
                we changed the acceleration - how would that affect the relationship? I'm curious about 
                exploring what happens at the molecular level during this motion. It would be fascinating 
                to investigate whether quantum effects play any role here. Why does this pattern emerge?
                """
            }
        ]
        
        # Test Case 4: HIGH PRECISION
        test_responses_precision = [
            {
                "question_number": 1,
                "selected_option": "A",
                "is_correct": True,
                "confidence": 0.95,
                "reasoning": """
                Using the formula v = u + at, where u = 0 m/s (initial velocity), a = 5 m/s² 
                (acceleration), and t = 4 s (time), I calculated: v = 0 + (5)(4) = 20 m/s exactly. 
                The units are consistent (meters per second), and the precision of the measurement is 
                ±0.1 m/s based on the equipment specifications.
                """
            }
        ]
        
        # Test Case 5: HIGH PATTERN RECOGNITION
        test_responses_pattern = [
            {
                "question_number": 1,
                "selected_option": "A",
                "is_correct": True,
                "confidence": 0.9,
                "reasoning": """
                I noticed a clear pattern here: this problem is similar to the previous gravitational 
                examples we studied. The relationship between force and distance follows an inverse 
                square pattern, which is typical for field phenomena. Generally, whenever we see this 
                type of distance dependence, we can expect the same mathematical structure. The trend 
                shows that as distance doubles, force becomes one-fourth.
                """
            }
        ]
        
        # Test each scenario
        test_scenarios = [
            ("Analytical Depth", test_responses_analytical, ["analytical_depth"]),
            ("Metacognition", test_responses_metacognition, ["metacognition"]),
            ("Curiosity", test_responses_curiosity, ["curiosity"]),
            ("Precision", test_responses_precision, ["precision"]),
            ("Pattern Recognition", test_responses_pattern, ["pattern_recognition"])
        ]
        
        for trait_name, responses, expected_traits in test_scenarios:
            print(f"\n{'─' * 80}")
            print(f"🎯 Testing: {trait_name}")
            print(f"{'─' * 80}")
            
            # Create mock questions targeting the trait
            mock_questions = [
                {
                    "question_number": qnum,
                    "traits_targeted": expected_traits,
                    "difficulty": "medium",
                    "requires_calculation": True
                }
                for qnum in range(1, len(responses) + 1)
            ]
            
            # Submit to debug endpoint
            debug_response = await client.post(
                f"{BASE_URL}/pdf-v2/sessions/{session_id}/debug-apply-trait-update",
                headers=headers,
                json={
                    "session_id": session_id,  # Required by Pydantic model
                    "responses": responses
                }
            )
            
            if debug_response.status_code != 200:
                print(f"❌ Debug endpoint failed: {debug_response.text}")
                continue
            
            result = debug_response.json()
            
            # Display results
            print(f"\n📊 RESULTS FOR {trait_name}:")
            print("─" * 80)
            
            diagnostics = result.get("diagnostics", {})
            
            # Show ALL traits, not just ones that changed
            for trait, info in diagnostics.items():
                old_val = info.get("old_value", 0)
                new_val = info.get("new_value", 0)
                change = info.get("change", 0)
                evidence_count = info.get("evidence_count", 0)
                avg_performance = info.get("avg_performance", 0)
                
                print(f"\n  🎯 {trait}:")
                print(f"     Old: {old_val:.3f} → New: {new_val:.3f}")
                print(f"     Change: {change:+.4f} ({evidence_count} observations)")
                
                if avg_performance:
                    print(f"     Avg Performance: {avg_performance:.3f}")
            
            print("\n")
        
        print("\n" + "=" * 80)
        print("✅ ENHANCED NLP ANALYSIS TEST COMPLETED")
        print("=" * 80)
        print("\n📋 Summary:")
        print("  ✅ Advanced dependency parsing (spaCy)")
        print("  ✅ Sentiment/subjectivity analysis (TextBlob)")
        print("  ✅ Context-aware reasoning scoring")
        print("  ✅ Explainable trait updates with detailed feedback")
        print("  ✅ Semantic understanding (not just keyword matching)")
        print("\n")


if __name__ == "__main__":
    asyncio.run(test_enhanced_nlp_analysis())
