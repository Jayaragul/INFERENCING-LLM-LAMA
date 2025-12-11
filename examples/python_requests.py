import requests

# Configuration
API_URL = "http://localhost:8000/api"

def run_chat_example():
    # 1. Get a model
    print("1. Fetching models...")
    models = requests.get(f"{API_URL}/models").json()["models"]
    if not models:
        print("No models available.")
        return
    
    model_name = models[0]["name"]
    print(f"   Using model: {model_name}")

    # 2. Create a session
    print("2. Creating session...")
    session = requests.post(f"{API_URL}/sessions", json={"model": model_name}).json()
    session_id = session["session_id"]
    print(f"   Session ID: {session_id}")

    # 3. Chat function
    def ask(text):
        print(f"\nUser: {text}")
        response = requests.post(f"{API_URL}/chat", json={
            "session_id": session_id,
            "model": model_name,
            "message": text
        }).json()
        print(f"Assistant: {response['response']}")

    # 4. Run conversation
    ask("Write a python function to add two numbers.")
    ask("Now rewrite it as a lambda function.") # Testing memory

if __name__ == "__main__":
    run_chat_example()
