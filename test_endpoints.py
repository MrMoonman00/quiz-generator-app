import requests
import json
import time

def test_endpoint(url, method='GET', data=None, expected_status=200):
    print(f"\nTesting {method} {url}")
    try:
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            response = requests.post(url, json=data)
        
        print(f"Status Code: {response.status_code} (Expected: {expected_status})")
        print("Response:")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text[:200] + "..." if len(response.text) > 200 else response.text)
        
        return response
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def run_tests(base_url):
    print("Starting API Tests...")
    
    # Test 1: Home Page
    print("\n=== Testing Home Page ===")
    test_endpoint(base_url)
    
    # Test 2: Quiz Generation with valid URL
    print("\n=== Testing Quiz Generation (Valid URL) ===")
    valid_data = {
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "num_questions": 5,
        "language": "en"
    }
    response = test_endpoint(f"{base_url}/generate_quiz", 'POST', valid_data)
    
    if response and response.status_code == 200:
        quiz_data = response.json()
        if quiz_data.get('quiz_id'):
            # Test 3: Share URL
            print("\n=== Testing Share URL ===")
            test_endpoint(f"{base_url}/quiz/{quiz_data['quiz_id']}")
    
    # Test 4: Invalid URL
    print("\n=== Testing Quiz Generation (Invalid URL) ===")
    invalid_data = {
        "video_url": "https://invalid-url",
        "num_questions": 5,
        "language": "en"
    }
    test_endpoint(f"{base_url}/generate_quiz", 'POST', invalid_data, 400)
    
    # Test 5: Out of range questions
    print("\n=== Testing Quiz Generation (Out of Range Questions) ===")
    invalid_questions_data = {
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "num_questions": 25,
        "language": "en"
    }
    test_endpoint(f"{base_url}/generate_quiz", 'POST', invalid_questions_data, 400)

if __name__ == "__main__":
    # Test local server first
    base_url = "http://127.0.0.1:5004"
    print(f"Testing local server at {base_url}")
    run_tests(base_url)
