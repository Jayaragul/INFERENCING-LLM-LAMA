import ollama
from typing import List, Optional


class OllamaClient:
    """
    Client wrapper for interacting with Ollama API.
    """
    
    def __init__(self, host: Optional[str] = None):
        """
        Initialize the Ollama client.
        
        Args:
            host: Optional Ollama server host (default: http://localhost:11434)
        """
        if host:
            self.client = ollama.Client(host=host)
        else:
            self.client = ollama.Client()
    
    def list_models(self) -> List[dict]:
        """
        Get list of available models from Ollama.
        
        Returns:
            List of model information dictionaries.
        """
        try:
            response = self.client.list()
            models = []
            
            # Handle response being an object or dict
            if hasattr(response, 'models'):
                model_list = response.models
            else:
                model_list = response.get("models", [])

            for model in model_list:
                # Handle model item being an object or dict
                if hasattr(model, 'model'):
                    name = model.model
                    modified_at = str(model.modified_at) if model.modified_at else ""
                    size = model.size
                    digest = model.digest
                else:
                    name = model.get("name") or model.get("model", "")
                    modified_at = str(model.get("modified_at", ""))
                    size = model.get("size", 0)
                    digest = model.get("digest", "")

                models.append({
                    "name": name,
                    "modified_at": modified_at,
                    "size": size,
                    "digest": digest
                })
            return models
        except Exception as e:
            raise Exception(f"Failed to list models: {str(e)}")
    
    def chat(self, model: str, messages: List[dict]) -> str:
        """
        Send a chat request to Ollama with conversation history.
        
        Args:
            model: The model name to use.
            messages: List of message dictionaries with 'role' and 'content'.
        
        Returns:
            The assistant's response content.
        """
        try:
            response = self.client.chat(
                model=model,
                messages=messages
            )
            if hasattr(response, 'message'):
                return response.message.content
            else:
                return response["message"]["content"]
        except Exception as e:
            raise Exception(f"Failed to chat: {str(e)}")
    
    def check_model_exists(self, model_name: str) -> bool:
        """
        Check if a specific model is available.
        
        Args:
            model_name: The name of the model to check.
        
        Returns:
            True if model exists, False otherwise.
        """
        try:
            models = self.list_models()
            model_names = [m["name"] for m in models]
            # Check for exact match or match without tag
            return model_name in model_names or any(
                m.startswith(model_name) for m in model_names
            )
        except Exception:
            return False


# Global client instance
ollama_client = OllamaClient()
