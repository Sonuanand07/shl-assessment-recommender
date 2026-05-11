#!/usr/bin/env python
"""
Integration test script for SHL Assessment Recommender.
Tests against actual sample conversations.
"""

import requests
import json
import sys
from pathlib import Path

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("\n" + "="*70)
    print("TEST 1: Health Check")
    print("="*70)
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_simple_conversation():
    """Test simple conversation flow."""
    print("\n" + "="*70)
    print("TEST 2: Simple Conversation")
    print("="*70)
    
    conversation = [
        {"role": "user", "content": "We're hiring senior Java developers for our fintech team."}
    ]
    
    print(f"User: {conversation[0]['content']}")
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"messages": conversation},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        data = response.json()
        
        print(f"\nAgent: {data['reply']}")
        print(f"Recommendations: {len(data['recommendations'])}")
        
        if data['recommendations']:
            print("\nFirst recommendation:")
            rec = data['recommendations'][0]
            print(f"  Name: {rec['name']}")
            print(f"  URL: {rec['url']}")
            print(f"  Type: {rec['test_type']}")
            print(f"  Keys: {rec.get('keys', 'N/A')}")
        
        print(f"End of conversation: {data['end_of_conversation']}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_multi_turn_conversation():
    """Test multi-turn conversation."""
    print("\n" + "="*70)
    print("TEST 3: Multi-Turn Conversation (Contact Center)")
    print("="*70)
    
    turns = [
        ("We're screening 500 entry-level contact centre agents. Inbound calls, customer service focus. What should we use?", "Clarification needed"),
        ("English.", "More specifics"),
        ("US.", "Recommendations")
    ]
    
    conversation = []
    
    for i, (user_msg, expected_type) in enumerate(turns, 1):
        print(f"\n--- Turn {i} ---")
        conversation.append({"role": "user", "content": user_msg})
        
        print(f"User: {user_msg}")
        
        try:
            response = requests.post(
                f"{API_URL}/chat",
                json={"messages": conversation},
                timeout=10
            )
            
            data = response.json()
            print(f"Agent: {data['reply'][:100]}...")
            
            if data['recommendations']:
                print(f"Recommendations: {len(data['recommendations'])}")
                for rec in data['recommendations'][:2]:
                    print(f"  - {rec['name']} [{rec['test_type']}]")
            
            # Add agent response to conversation
            conversation.append({"role": "assistant", "content": data['reply']})
            
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    return True


def test_personality_assessments():
    """Test personality assessment recommendations."""
    print("\n" + "="*70)
    print("TEST 4: Personality Assessments")
    print("="*70)
    
    conversation = [
        {"role": "user", "content": "We need personality and behavioral assessments for senior leadership roles."}
    ]
    
    print(f"User: {conversation[0]['content']}")
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"messages": conversation},
            timeout=10
        )
        
        data = response.json()
        print(f"Agent: {data['reply']}")
        
        if data['recommendations']:
            print(f"\nRecommendations ({len(data['recommendations'])}):")
            for rec in data['recommendations']:
                print(f"  - {rec['name']}")
                print(f"    Type: {rec['test_type']}, Keys: {rec.get('keys', 'N/A')}")
        
        # Check for personality assessments
        personality_count = sum(1 for rec in data['recommendations'] if 'P' in rec['test_type'])
        print(f"\nPersonality assessments in recommendations: {personality_count}")
        
        return personality_count > 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_off_topic_refusal():
    """Test refusal of off-topic requests."""
    print("\n" + "="*70)
    print("TEST 5: Off-Topic Refusal")
    print("="*70)
    
    conversation = [
        {"role": "user", "content": "What's the best general hiring advice you can give me?"}
    ]
    
    print(f"User: {conversation[0]['content']}")
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"messages": conversation},
            timeout=10
        )
        
        data = response.json()
        print(f"Agent: {data['reply']}")
        
        # Should refuse and have no recommendations
        is_refusal = len(data['recommendations']) == 0 and 'SHL' in data['reply']
        print(f"\nProperly refused off-topic request: {is_refusal}")
        
        return is_refusal
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_vague_query():
    """Test that vague queries don't get immediate recommendations."""
    print("\n" + "="*70)
    print("TEST 6: Vague Query Handling")
    print("="*70)
    
    conversation = [
        {"role": "user", "content": "We need an assessment"}
    ]
    
    print(f"User: {conversation[0]['content']}")
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"messages": conversation},
            timeout=10
        )
        
        data = response.json()
        print(f"Agent: {data['reply']}")
        
        # Should ask for clarification, not recommend
        no_recommendations = len(data['recommendations']) == 0
        print(f"\nNo recommendations for vague query: {no_recommendations}")
        print(f"End of conversation: {data['end_of_conversation']}")
        
        return no_recommendations
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("SHL ASSESSMENT RECOMMENDER - Integration Tests")
    print("="*70)
    print(f"Testing API at: {API_URL}")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Simple Conversation", test_simple_conversation()))
    results.append(("Multi-Turn Conversation", test_multi_turn_conversation()))
    results.append(("Personality Assessments", test_personality_assessments()))
    results.append(("Off-Topic Refusal", test_off_topic_refusal()))
    results.append(("Vague Query Handling", test_vague_query()))
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! System is working correctly.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
