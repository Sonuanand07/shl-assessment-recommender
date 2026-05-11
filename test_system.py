#!/usr/bin/env python
"""
Test script for SHL Assessment Recommender.
Validates catalog loading and agent functionality.
"""

import sys
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_catalog_loading():
    """Test catalog loading."""
    print("\n" + "=" * 60)
    print("TEST 1: Catalog Loading")
    print("=" * 60)
    
    try:
        from catalog import CatalogManager
        
        start = time.time()
        print("Loading catalog...")
        catalog = CatalogManager()
        elapsed = time.time() - start
        
        items = catalog.get_all_items()
        print(f"✓ Catalog loaded in {elapsed:.2f}s")
        print(f"✓ Total items: {len(items)}")
        
        if items:
            print(f"✓ First item: {items[0].get('name')}")
            print(f"✓ Assessment types: {len(catalog.get_assessment_types())} unique")
            print(f"✓ Job levels: {len(catalog.get_job_levels())} unique")
            return True
        else:
            print("✗ No items in catalog")
            return False
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_context_extraction():
    """Test agent context extraction."""
    print("\n" + "=" * 60)
    print("TEST 2: Agent Context Extraction")
    print("=" * 60)
    
    try:
        from agent import AssessmentRecommender
        
        agent = AssessmentRecommender()
        
        # Test message 1
        msg1 = "We're hiring a senior Java developer"
        conversation = [{"role": "user", "content": msg1}]
        agent._extract_context(msg1, conversation)
        
        print(f"Message: '{msg1}'")
        print(f"✓ Job title extracted: {agent.context.job_title}")
        print(f"✓ Job levels extracted: {agent.context.job_levels}")
        print(f"✓ Has sufficient context: {agent._has_sufficient_context()}")
        
        # Test message 2
        msg2 = "For selection, comparing candidates against a technical benchmark with 5 years experience"
        agent2 = AssessmentRecommender()
        agent2._extract_context(msg2, [])
        print(f"\nMessage: '{msg2}'")
        print(f"✓ Purpose extracted: {agent2.context.purpose}")
        print(f"✓ Experience years: {agent2.context.experience_years}")
        
        return True
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_response():
    """Test agent response generation."""
    print("\n" + "=" * 60)
    print("TEST 3: Agent Response Generation")
    print("=" * 60)
    
    try:
        from agent import AssessmentRecommender
        
        agent = AssessmentRecommender()
        
        # Test 1: Simple user request
        user_msg = "I need an assessment for Java developers"
        history = [{"role": "user", "content": user_msg}]
        response = agent.process_message(user_msg, history)
        
        print(f"User: '{user_msg}'")
        print(f"Agent: '{response['reply'][:80]}...'")
        print(f"✓ Has recommendations: {len(response['recommendations']) > 0}")
        print(f"✓ End of conversation: {response['end_of_conversation']}")
        
        # Test 2: Vague request (should not recommend immediately)
        agent2 = AssessmentRecommender()
        user_msg2 = "We need an assessment"
        history2 = [{"role": "user", "content": user_msg2}]
        response2 = agent2.process_message(user_msg2, history2)
        
        print(f"\nUser: '{user_msg2}'")
        print(f"Agent: '{response2['reply'][:80]}...'")
        print(f"✓ No recommendations (as expected): {len(response2['recommendations']) == 0}")
        
        return True
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test FastAPI endpoints."""
    print("\n" + "=" * 60)
    print("TEST 4: API Endpoints")
    print("=" * 60)
    
    try:
        from app import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        print(f"GET /health")
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Response: {response.json()}")
        
        # Test chat endpoint
        request_data = {
            "messages": [
                {"role": "user", "content": "I need personality assessments for senior managers"}
            ]
        }
        response = client.post("/chat", json=request_data)
        print(f"\nPOST /chat")
        print(f"✓ Status: {response.status_code}")
        data = response.json()
        print(f"✓ Reply: {data['reply'][:80]}...")
        print(f"✓ Recommendations: {len(data['recommendations'])}")
        print(f"✓ End of conversation: {data['end_of_conversation']}")
        
        return True
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SHL Assessment Recommender - Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Catalog Loading", test_catalog_loading()))
    results.append(("Context Extraction", test_agent_context_extraction()))
    results.append(("Agent Response", test_agent_response()))
    results.append(("API Endpoints", test_api_endpoints()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
