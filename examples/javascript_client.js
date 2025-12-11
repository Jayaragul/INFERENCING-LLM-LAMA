// Example of how to use the Ollama Backend API from a JavaScript/Node.js application

const API_BASE_URL = 'http://localhost:8000/api';

async function chatWithOllama() {
    try {
        // 1. List Models
        console.log("Fetching models...");
        const modelsResponse = await fetch(`${API_BASE_URL}/models`);
        const modelsData = await modelsResponse.json();
        
        if (!modelsData.models || modelsData.models.length === 0) {
            console.error("No models found!");
            return;
        }

        const modelName = modelsData.models[0].name;
        console.log(`Using model: ${modelName}`);

        // 2. Create a Session
        console.log("Creating session...");
        const sessionResponse = await fetch(`${API_BASE_URL}/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: modelName })
        });
        const sessionData = await sessionResponse.json();
        const sessionId = sessionData.session_id;
        console.log(`Session ID: ${sessionId}`);

        // 3. Send a Message
        const userMessage = "Why is the sky blue?";
        console.log(`\nUser: ${userMessage}`);
        
        const chatResponse = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                model: modelName,
                message: userMessage
            })
        });
        
        const chatData = await chatResponse.json();
        console.log(`Assistant: ${chatData.response}`);

        // 4. Follow up (Memory Test)
        const followUp = "Tell me more about that.";
        console.log(`\nUser: ${followUp}`);
        
        const followUpResponse = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                model: modelName,
                message: followUp
            })
        });
        
        const followUpData = await followUpResponse.json();
        console.log(`Assistant: ${followUpData.response}`);

    } catch (error) {
        console.error("Error:", error);
    }
}

chatWithOllama();
