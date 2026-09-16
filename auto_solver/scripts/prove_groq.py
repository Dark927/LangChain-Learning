import sys, requests, json
sys.path.append('src')
from provider_registry import get_key

def test_groq():
    key = get_key('GROQ_API_KEY')
    print("Testing Groq API Models...")
    
    # 1. Check which models Groq ACTUALLY supports right now
    r = requests.get('https://api.groq.com/openai/v1/models', headers={'Authorization': f'Bearer {key}'})
    supported_models = [m['id'] for m in r.json().get('data', [])]
    
    print("\n--- Currently Supported Groq Models ---")
    for m in supported_models:
        print(f" - {m}")
        
    print("\n--- Testing Old Model ID ---")
    # 2. Test the old model ID that is failing
    old_model = 'gemma2-9b-it'
    data = {'model': old_model, 'messages': [{'role': 'user', 'content': 'hi'}]}
    r_old = requests.post('https://api.groq.com/openai/v1/chat/completions', headers={'Authorization': f'Bearer {key}'}, json=data)
    print(f"Requesting '{old_model}': {r_old.status_code} {r_old.text}")
    
    print("\n--- Testing New Model ID ---")
    # 3. Test a new model ID that is supported
    new_model = 'openai/gpt-oss-120b'
    data_new = {'model': new_model, 'messages': [{'role': 'user', 'content': 'hi'}]}
    r_new = requests.post('https://api.groq.com/openai/v1/chat/completions', headers={'Authorization': f'Bearer {key}'}, json=data_new)
    print(f"Requesting '{new_model}': {r_new.status_code}")
    if r_new.status_code == 200:
        print("Success! Output:", r_new.json()['choices'][0]['message']['content'])

if __name__ == "__main__":
    test_groq()
