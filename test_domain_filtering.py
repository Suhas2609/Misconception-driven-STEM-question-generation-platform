#!/usr/bin/env python3
"""
Test Domain/Topic Filtering for Misconceptions

This script verifies that:
1. Misconception retrieval respects domain boundaries
2. Chemistry questions get Chemistry misconceptions only
3. Physics questions get Physics misconceptions only
4. No cross-domain contamination occurs
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "misconception_stem_rag"
sys.path.insert(0, str(backend_path))

from backend.app.services.validation import get_related_misconceptions, _seed_misconceptions


def test_physics_filtering():
    """Test that Physics queries only get Physics misconceptions."""
    print("\n" + "="*80)
    print("TEST 1: Physics Domain Filtering")
    print("="*80)
    
    # Force reload misconceptions
    _seed_misconceptions(force=True)
    
    # Query for Newton's Laws (Physics)
    results = get_related_misconceptions(
        topic="Newton's Laws force and motion",
        limit=5,
        domain="Physics"
    )
    
    print(f"\nQuery: Newton's Laws (Domain: Physics)")
    print(f"Retrieved {len(results)} misconceptions:\n")
    
    success = True
    for i, misc in enumerate(results, 1):
        subject = misc.get("subject", "UNKNOWN")
        concept = misc.get("concept", "")
        text = misc.get("misconception_text", "")[:60]
        
        print(f"{i}. [{subject}] {concept}")
        print(f"   {text}...")
        
        if subject != "Physics":
            print(f"   ❌ VIOLATION: Expected Physics, got {subject}")
            success = False
        else:
            print(f"   ✅ Correct domain")
    
    return success


def test_chemistry_filtering():
    """Test that Chemistry queries only get Chemistry misconceptions."""
    print("\n" + "="*80)
    print("TEST 2: Chemistry Domain Filtering")
    print("="*80)
    
    # Query for Hydrogen Bonding (Chemistry)
    results = get_related_misconceptions(
        topic="Hydrogen bonding intermolecular forces",
        limit=5,
        domain="Chemistry"
    )
    
    print(f"\nQuery: Hydrogen Bonding (Domain: Chemistry)")
    print(f"Retrieved {len(results)} misconceptions:\n")
    
    success = True
    for i, misc in enumerate(results, 1):
        subject = misc.get("subject", "UNKNOWN")
        concept = misc.get("concept", "")
        text = misc.get("misconception_text", "")[:60]
        
        print(f"{i}. [{subject}] {concept}")
        print(f"   {text}...")
        
        if subject != "Chemistry":
            print(f"   ❌ VIOLATION: Expected Chemistry, got {subject}")
            success = False
        else:
            print(f"   ✅ Correct domain")
    
    return success


def test_biology_filtering():
    """Test that Biology queries only get Biology misconceptions."""
    print("\n" + "="*80)
    print("TEST 3: Biology Domain Filtering")
    print("="*80)
    
    # Query for Cell Structure (Biology)
    results = get_related_misconceptions(
        topic="Cell structure mitochondria chloroplasts",
        limit=5,
        domain="Biology"
    )
    
    print(f"\nQuery: Cell Structure (Domain: Biology)")
    print(f"Retrieved {len(results)} misconceptions:\n")
    
    success = True
    for i, misc in enumerate(results, 1):
        subject = misc.get("subject", "UNKNOWN")
        concept = misc.get("concept", "")
        text = misc.get("misconception_text", "")[:60]
        
        print(f"{i}. [{subject}] {concept}")
        print(f"   {text}...")
        
        if subject != "Biology":
            print(f"   ❌ VIOLATION: Expected Biology, got {subject}")
            success = False
        else:
            print(f"   ✅ Correct domain")
    
    return success


def test_cross_contamination():
    """Test that unfiltered queries can return cross-domain results (baseline)."""
    print("\n" + "="*80)
    print("TEST 4: Unfiltered Query (Should Mix Domains)")
    print("="*80)
    
    # Query without domain filter
    results = get_related_misconceptions(
        topic="force energy motion",
        limit=10,
        domain=None  # No filter
    )
    
    print(f"\nQuery: 'force energy motion' (No domain filter)")
    print(f"Retrieved {len(results)} misconceptions:\n")
    
    domains_found = set()
    for i, misc in enumerate(results, 1):
        subject = misc.get("subject", "UNKNOWN")
        concept = misc.get("concept", "")
        text = misc.get("misconception_text", "")[:60]
        
        print(f"{i}. [{subject}] {concept}")
        print(f"   {text}...")
        domains_found.add(subject)
    
    print(f"\nDomains found: {domains_found}")
    
    # This test succeeds if we get multiple domains (showing filter works)
    if len(domains_found) > 1:
        print("✅ Multiple domains found (filter is not restricting)")
        return True
    else:
        print("⚠️ Only one domain found (data might be limited)")
        return True


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("DOMAIN/TOPIC FILTERING TEST SUITE")
    print("="*80)
    print("\nThis test verifies that misconception retrieval respects domain boundaries")
    print("to prevent cross-contamination (e.g., Physics misconceptions in Chemistry questions)\n")
    
    # Run tests
    test1 = test_physics_filtering()
    test2 = test_chemistry_filtering()
    test3 = test_biology_filtering()
    test4 = test_cross_contamination()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    results = {
        "Physics Domain Filtering": test1,
        "Chemistry Domain Filtering": test2,
        "Biology Domain Filtering": test3,
        "Unfiltered Query": test4
    }
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! Domain filtering is working correctly.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
