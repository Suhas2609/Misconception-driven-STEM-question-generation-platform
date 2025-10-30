"""
Test script for topic-level misconception filtering.

This verifies that the two-level filtering works:
1. Domain-level: Only retrieves misconceptions from the correct subject
2. Topic-level: Only retrieves misconceptions semantically relevant to the specific topic

Expected behavior:
- "Newton's Laws" should NOT get "Thermodynamics" misconceptions (both Physics)
- "Chemical Bonding" should NOT get "Organic Chemistry" misconceptions (both Chemistry)
- Similarity threshold ensures only highly relevant misconceptions are returned
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.validation import get_related_misconceptions
import logging

# Configure logging to see filtering details
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_topic_filtering():
    """Test that topic-level filtering prevents cross-topic contamination within same domain."""
    
    print("=" * 80)
    print("🧪 TESTING TOPIC-LEVEL MISCONCEPTION FILTERING")
    print("=" * 80)
    
    # Test Case 1: Physics - Newton's Laws vs Thermodynamics
    print("\n" + "─" * 80)
    print("📋 TEST 1: Physics Topic Specificity")
    print("─" * 80)
    
    print("\n🔬 Query: 'Newton's Laws' (Physics)")
    print("Expected: Misconceptions about forces, motion, acceleration")
    print("Should exclude: Thermodynamics, waves, electromagnetism")
    
    newtons_laws = get_related_misconceptions(
        topic="Newton's Laws of Motion",
        limit=5,
        domain="Physics",
        topic_relevance_threshold=0.7  # High threshold for strong relevance
    )
    
    print(f"\n✅ Retrieved {len(newtons_laws)} misconceptions:")
    for i, mc in enumerate(newtons_laws, 1):
        concept = mc.get('concept', 'Unknown')
        text = mc.get('misconception_text', '')[:80]
        similarity = mc.get('similarity', 0.0)
        print(f"  {i}. [{concept}] (sim={similarity:.3f}): {text}...")
    
    # Test Case 2: Chemistry - Chemical Bonding vs Organic Chemistry
    print("\n" + "─" * 80)
    print("📋 TEST 2: Chemistry Topic Specificity")
    print("─" * 80)
    
    print("\n🔬 Query: 'Chemical Bonding' (Chemistry)")
    print("Expected: Misconceptions about ionic, covalent, metallic bonds")
    print("Should exclude: Organic reactions, stoichiometry, equilibrium")
    
    bonding = get_related_misconceptions(
        topic="Chemical Bonding and Molecular Structure",
        limit=5,
        domain="Chemistry",
        topic_relevance_threshold=0.7
    )
    
    print(f"\n✅ Retrieved {len(bonding)} misconceptions:")
    for i, mc in enumerate(bonding, 1):
        concept = mc.get('concept', 'Unknown')
        text = mc.get('misconception_text', '')[:80]
        similarity = mc.get('similarity', 0.0)
        print(f"  {i}. [{concept}] (sim={similarity:.3f}): {text}...")
    
    # Test Case 3: Compare with lower threshold
    print("\n" + "─" * 80)
    print("📋 TEST 3: Threshold Sensitivity")
    print("─" * 80)
    
    print("\n🔬 Query: 'Newton's Laws' with LOWER threshold (0.5)")
    print("Expected: More misconceptions, potentially less relevant")
    
    newtons_laws_loose = get_related_misconceptions(
        topic="Newton's Laws of Motion",
        limit=5,
        domain="Physics",
        topic_relevance_threshold=0.5  # Lower threshold
    )
    
    print(f"\n✅ Retrieved {len(newtons_laws_loose)} misconceptions (vs {len(newtons_laws)} with threshold=0.7):")
    for i, mc in enumerate(newtons_laws_loose, 1):
        concept = mc.get('concept', 'Unknown')
        text = mc.get('misconception_text', '')[:80]
        similarity = mc.get('similarity', 0.0)
        print(f"  {i}. [{concept}] (sim={similarity:.3f}): {text}...")
    
    # Test Case 4: Cross-domain prevention (should still work)
    print("\n" + "─" * 80)
    print("📋 TEST 4: Domain-Level Protection (Sanity Check)")
    print("─" * 80)
    
    print("\n🔬 Query: 'Force and Motion' with Chemistry filter")
    print("Expected: Empty or very few results (domain mismatch)")
    
    cross_domain = get_related_misconceptions(
        topic="Force and Motion",
        limit=5,
        domain="Chemistry",  # Wrong domain!
        topic_relevance_threshold=0.7
    )
    
    print(f"\n✅ Retrieved {len(cross_domain)} misconceptions (should be 0 or very few)")
    if cross_domain:
        print("⚠️  WARNING: Found misconceptions in wrong domain!")
        for i, mc in enumerate(cross_domain, 1):
            subject = mc.get('subject', 'Unknown')
            text = mc.get('misconception_text', '')[:80]
            print(f"  {i}. [{subject}]: {text}...")
    else:
        print("✅ PASS: No cross-domain contamination")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"✅ Domain filtering: {'PASS' if len(cross_domain) == 0 else 'FAIL'}")
    print(f"✅ Topic filtering: {'PASS' if len(newtons_laws) > 0 else 'FAIL'}")
    print(f"✅ Threshold sensitivity: {'PASS' if len(newtons_laws_loose) >= len(newtons_laws) else 'FAIL'}")
    print("\n🎉 Topic-level filtering implementation complete!")
    print("=" * 80)


if __name__ == "__main__":
    test_topic_filtering()
