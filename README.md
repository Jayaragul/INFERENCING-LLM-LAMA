# 🦙 Ollama Inference Engine & API

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi)
![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-black?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

A professional, production-ready backend API for interacting with local Large Language Models (LLMs) via [Ollama](https://ollama.ai/). This project provides a robust layer on top of Ollama, adding **session management**, **conversation memory**, and a **RESTful API** interface suitable for integrating into web apps, mobile applications, and enterprise workflows.

![Project Screenshot](docs/images/screenshot_placeholder.png)
*(Add a screenshot of your index.html frontend here)*

---

## 🚀 Key Features

- **🧠 Context-Aware Memory**: Maintains conversation history per session, allowing for natural, multi-turn conversations.
- **🔌 RESTful API**: Fully documented FastAPI endpoints for easy integration with React, Vue, iOS, Android, or IoT devices.
- **📋 Model Management**: Dynamically list and switch between available local models (Llama 2, Mistral, Gemma, etc.).
- **⚡ Real-time Inference**: Low-latency communication with the local Ollama instance.
- **🖥️ Included Frontend**: Comes with a lightweight HTML/JS dashboard for immediate testing and demonstration.
- **🐳 Docker Ready**: (Optional) Can be easily containerized for deployment.

---

## 💡 Use Cases

This project is designed to be the backbone for various AI applications:

1.  **🔒 Privacy-First Corporate Chatbots**
    *   Deploy an internal chatbot for employees that runs entirely on-premise. No data leaves your network.
2.  **📚 RAG (Retrieval-Augmented Generation) Systems**
    *   Use this API as the generation engine. Feed retrieved documents into the context window via the chat endpoint.
3.  **🤖 AI Agents & Assistants**
    *   Give your software agents a "brain". The session memory allows agents to retain instructions over a sequence of tasks.
4.  **📱 Mobile App Backend**
    *   Serve LLM features to mobile apps without managing heavy model weights on the device itself.
5.  **🧪 Research & Prototyping**
    *   Quickly test different prompts and models against the same API interface without rewriting code.

---

## 🛠️ Architecture

The system acts as a middleware between your applications and the raw Ollama inference engine.

```mermaid
graph LR
    A[Client App / Frontend] <-->|HTTP REST| B[FastAPI Backend]
    B <-->|Memory Manager| C[(In-Memory Session Store)]
    B <-->|Ollama Library| D[Ollama Service]
    D <-->|Inference| E[Local LLM (Llama2/Mistral)]
```

---

## ⚙️ Installation

### Prerequisites
- **Python 3.8+**
- **[Ollama](https://ollama.ai/)** installed and running.

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/inferencing-llm-lama.git
cd inferencing-llm-lama
```

### 2. Set Up Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Pull a Model
Ensure you have at least one model downloaded in Ollama:
```bash
ollama pull mistral
# or
ollama pull llama2
```

---

## 🚀 Usage

### 1. Start the Ollama Service
Ensure Ollama is running in the background.
```bash
ollama serve
```

### 2. Run the API Server
```bash
python run.py
```
The server will start at `http://localhost:8000`.

### 3. Access the Dashboard
Open `index.html` in your browser, or navigate to the file path.
*   **URL**: `http://localhost:8000/docs` (Swagger UI)
*   **Frontend**: Open `index.html` directly.

---

## 📖 API Documentation

The API is fully documented with Swagger UI. Visit `http://localhost:8000/docs` when the server is running.

### Core Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | **/api/models** | List all available models installed locally. |
| `POST` | **/api/sessions** | Create a new chat session. Returns a `session_id`. |
| `POST` | **/api/chat** | Send a message. Requires `session_id`, `model`, and `message`. |
| `GET` | **/api/sessions/{id}/history** | Retrieve the full conversation history for a specific session. |

### Example Request (Python)

```python
import requests

# 1. Create Session
session = requests.post("http://localhost:8000/api/sessions", json={"model": "mistral"}).json()
session_id = session['session_id']

# 2. Chat
response = requests.post("http://localhost:8000/api/chat", json={
    "session_id": session_id,
    "model": "mistral",
    "message": "Explain quantum computing in simple terms."
}).json()

print(response['response'])
```

---

## 📂 Project Structure

```
INFERENCING LLM LAMA/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI entry point
│   ├── routes.py        # API Route definitions
│   ├── models.py        # Pydantic data models
│   ├── memory.py        # Session state management
│   └── ollama_client.py # Ollama integration logic
├── docs/
│   └── images/          # Documentation assets
├── examples/            # Client examples (Python, JS)
├── index.html           # Web Dashboard
├── requirements.txt     # Dependencies
├── run.py               # Server runner script
└── README.md            # This file
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1.  Fork the project
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
