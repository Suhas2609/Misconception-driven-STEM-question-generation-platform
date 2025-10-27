"""Quick validation script to test Stage 1 & 2 implementations."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

print("🔍 Testing Stage 1 & 2 Implementations\n")
print("=" * 50)

# Test 1: Import semantic_search
try:
    from app.services.semantic_search import SemanticSearchService
    print("✅ Test 1: semantic_search imports successfully")
except Exception as e:
    print(f"❌ Test 1 FAILED: {e}")
    sys.exit(1)

# Test 2: Import misconception_service
try:
    from app.services.misconception_service import MisconceptionService
    print("✅ Test 2: misconception_service imports successfully")
except Exception as e:
    print(f"❌ Test 2 FAILED: {e}")
    sys.exit(1)

# Test 3: Import admin routes
try:
    from app.routes import admin
    print("✅ Test 3: admin routes import successfully")
except Exception as e:
    print(f"❌ Test 3 FAILED: {e}")
    sys.exit(1)

# Test 4: Check topic_question_generation has new function
try:
    from app.services.topic_question_generation import (
        generate_questions_for_topics_with_semantic_context
    )
    print("✅ Test 4: semantic context function exists")
except Exception as e:
    print(f"❌ Test 4 FAILED: {e}")
    sys.exit(1)

# Test 5: Check pdf_upload uses new import
try:
    from app.routes.pdf_upload import router
    print("✅ Test 5: pdf_upload routes load successfully")
except Exception as e:
    print(f"❌ Test 5 FAILED: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("🎉 ALL IMPORT TESTS PASSED!")
print("\nNext steps:")
print("1. Start Docker Desktop")
print("2. Run: docker-compose up -d")
print("3. Test PDF upload with semantic search")
print("4. Test misconception seeding via API")
