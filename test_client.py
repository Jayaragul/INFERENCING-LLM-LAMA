import httpx
import time
import sys

API_URL = "http://localhost:8000/api"

def main():
    print("--- Ollama API Client Test ---")
    
    # 1. Check if server is running
    try:
        response = httpx.get("http://localhost:8000/health")
        if response.status_code != 200:
            print("Error: Server is not healthy or not running.")
            return
    except httpx.ConnectError:
        print("Error: Could not connect to server. Make sure 'run.py' is running!")
        return

    # 2. List Models
    print("\nFetching available models...")
    try:
        response = httpx.get(f"{API_URL}/models")
        models_data = response.json()
        models = models_data.get("models", [])
        
        if not models:
            print("No models found in Ollama. Please run 'ollama pull llama2' (or another model) first.")
            return

        print("Available models:")
        for i, m in enumerate(models):
            print(f"{i+1}. {m['name']}")
        
        # Select model
        selection = input("\nSelect a model number (default 1): ").strip()
        if not selection:
            selection = 0
        else:
            selection = int(selection) - 1
        
        if selection < 0 or selection >= len(models):
            print("Invalid selection.")
            return
            
        selected_model = models[selection]['name']
        print(f"Selected model: {selected_model}")

    except Exception as e:
        print(f"Error fetching models: {e}")
        return

    # 3. Create Session
    print(f"\nCreating chat session with {selected_model}...")
    try:
        response = httpx.post(f"{API_URL}/sessions", json={"model": selected_model})
        session_data = response.json()
        session_id = session_data["session_id"]
        print(f"Session created! ID: {session_id}")
    except Exception as e:
        print(f"Error creating session: {e}")
        return

    # 4. Chat Loop
    print("\n--- Start Chatting (type 'quit' to exit, 'history' to see memory) ---")
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            break
        
        if user_input.lower() == 'history':
            try:
                hist_response = httpx.get(f"{API_URL}/sessions/{session_id}/history")
                history = hist_response.json()
                print("\n--- Conversation History ---")
                for msg in history:
                    print(f"{msg['role'].upper()}: {msg['content']}")
                print("---------------------------")
            except Exception as e:
                print(f"Error fetching history: {e}")
            continue

        if not user_input:
            continue

        print("Assistant: ", end="", flush=True)
        try:
            # Streaming would be nice, but for now we just wait for the full response
            # We'll print a loading indicator
            sys.stdout.write("...")
            sys.stdout.flush()
            
            start_time = time.time()
            chat_response = httpx.post(
                f"{API_URL}/chat", 
                json={
                    "session_id": session_id,
                    "model": selected_model,
                    "message": user_input
                },
                timeout=60.0 # LLMs can be slow
            )
            
            # Clear loading indicator
            sys.stdout.write("\r           \r")
            sys.stdout.flush()
            
            if chat_response.status_code == 200:
                data = chat_response.json()
                print(data["response"])
                print(f"[{time.time() - start_time:.2f}s]")
            else:
                print(f"Error: {chat_response.text}")

        except httpx.ReadTimeout:
            print("\nError: Response timed out.")
        except Exception as e:
            print(f"\nError: {e}")

    # Cleanup
    print("\nClosing session...")
    try:
        httpx.delete(f"{API_URL}/sessions/{session_id}")
        print("Session deleted.")
    except:
        pass

if __name__ == "__main__":
    main()
