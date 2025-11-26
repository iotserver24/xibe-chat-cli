import requests
import json
import os

def get_models():
    url = "https://enter.pollinations.ai/api/generate/text/models"
    try:
        response = requests.get(url, timeout=10)
        print("Available Models:")
        print(json.dumps(response.json(), indent=2))
        return response.json()
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

def test_api():
    url = "https://enter.pollinations.ai/api/generate/v1/chat/completions"
    
    # Simulate the payload from analyze_query_with_ai
    system_message = "You are an AI assistant."
    user_input = "hi"
    
    models_to_test = ["gemini", "gemini-2.5-flash-lite", "openai"]

    for model in models_to_test:
        print(f"\nTesting model: {model}")
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ]

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 200,
            "temperature": 0.1
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "XIBE-CHAT-CLI/1.0"
        }

        print(f"Sending payload to {url} with model {model}:")
        # print(json.dumps(payload, indent=2))

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print("Response Body:")
                print(response.text)
            else:
                print("Success!")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    get_models()
    test_api()
