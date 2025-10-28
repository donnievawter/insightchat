// Chat functionality for InsightChat application

document.addEventListener("DOMContentLoaded", function () {
    const chatForm = document.getElementById("chat-form");
    const sendButton = chatForm ? chatForm.querySelector('button[type="submit"]') : null;
    const promptInput = chatForm ? chatForm.querySelector('input[name="prompt"]') : null;
    const chatMessages = document.getElementById("chat-messages");

    // Auto-scroll to bottom of messages on page load
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Focus on input field
    if (promptInput) {
        promptInput.focus();
    }

    // Handle form submission
    if (chatForm && sendButton) {
        const originalButtonText = sendButton.textContent;

        chatForm.addEventListener('submit', function (e) {
            const message = promptInput.value.trim();
            if (!message) {
                e.preventDefault();
                return;
            }

            // Disable button and show loading state
            sendButton.disabled = true;
            sendButton.textContent = 'Sending...';

            // Show user message immediately for better UX
            addMessageToChat('user', message);

            // Clear input
            promptInput.value = '';
        });

        // Re-enable button when page loads (after server response)
        window.addEventListener('load', function () {
            if (sendButton) {
                sendButton.disabled = false;
                sendButton.textContent = originalButtonText;
            }
        });
    }

    // Add keyboard shortcut (Enter to submit)
    if (promptInput) {
        promptInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (chatForm && !sendButton.disabled) {
                    chatForm.dispatchEvent(new Event('submit', { cancelable: true }));
                }
            }
        });
    }

    function addMessageToChat(role, content) {
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-role">${role.charAt(0).toUpperCase() + role.slice(1)}</span>
            </div>
            <div class="message-content">${escapeHtml(content)}</div>
        `;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});