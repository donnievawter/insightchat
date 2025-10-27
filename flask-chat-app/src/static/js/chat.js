// This file contains JavaScript code for the chat functionality, handling user interactions and updating the chat interface dynamically.

document.addEventListener("DOMContentLoaded", function() {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatMessages = document.getElementById("chat-messages");

    chatForm.addEventListener("submit", function(event) {
        event.preventDefault();
        const message = chatInput.value.trim();
        if (message) {
            sendMessage(message);
            chatInput.value = "";
        }
    });

    function sendMessage(message) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", "user-message");
        messageElement.textContent = message;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Simulate a response from the assistant
        setTimeout(() => {
            const responseElement = document.createElement("div");
            responseElement.classList.add("message", "assistant-message");
            responseElement.textContent = "This is a simulated response.";
            chatMessages.appendChild(responseElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 1000);
    }
});