    document.addEventListener('DOMContentLoaded', function() {
    const chatFab = document.getElementById('chat-fab-toggle');
    const chatWidget = document.getElementById('chat-widget');
    const closeBtn = document.getElementById('chat-widget-close');
    const suggestionChips = document.querySelectorAll('.suggestion-chip');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send-btn');
    const chatBody = document.getElementById('chat-widget-body');
    const messagesContainer = document.getElementById('chat-messages-container');

    // ==================================================
    // === HÀM MỚI: Chuyển đổi Markdown sang HTML ===
    // ==================================================
    function markdownToHtml(text) {
        // 1. Chuyển đổi **bold** thành <strong>bold</strong>
        let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // 2. Chuyển đổi ký tự xuống dòng \n thành thẻ <br>
        html = html.replace(/\n/g, '<br>');
        return html;
    }

    // Hàm để thêm tin nhắn vào giao diện
    function appendMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message', sender);

        const formattedHtml = markdownToHtml(text);
        messageDiv.innerHTML = formattedHtml; // Dùng innerHTML để render các thẻ HTML

        messagesContainer.appendChild(messageDiv);

        chatBody.scrollTop = chatBody.scrollHeight;
    }

    // Hàm hiển thị chỉ báo "đang gõ..." (giữ nguyên)
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('chat-message', 'assistant', 'typing-indicator');
        typingDiv.innerHTML = '<span></span><span></span><span></span>';
        messagesContainer.appendChild(typingDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    // Hàm xóa chỉ báo "đang gõ..." (giữ nguyên)
    function removeTypingIndicator() {
        const indicator = messagesContainer.querySelector('.typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

     function loadInitialHistory() {
        // Lấy thẻ body
        const bodyElement = document.querySelector('body');
        // Đọc chuỗi JSON từ thuộc tính data-chat-history
        const historyJson = bodyElement.dataset.chatHistory;
        // Chuyển đổi chuỗi JSON thành một đối tượng JavaScript
        const initialHistory = JSON.parse(historyJson);

        // Phần còn lại của hàm giữ nguyên
        messagesContainer.innerHTML = '';
        if (initialHistory && initialHistory.length > 0) {
            initialHistory.forEach(message => {
                appendMessage(message.text, message.sender);
            });
        } else {
            appendMessage('Chào bạn, Kymie có thể giúp gì cho bạn hôm nay?', 'assistant');
        }
    }

    loadInitialHistory();


    // Hàm chính để gửi tin nhắn (giữ nguyên)
    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        appendMessage(message, 'user');
        chatInput.value = '';
        showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message }),
            });

            const data = await response.json();
            const aiReply = data.reply;

            removeTypingIndicator();
            appendMessage(aiReply, 'assistant');

        } catch (error) {
            console.error('Lỗi khi gọi API chat:', error);
            removeTypingIndicator();
            appendMessage('Rất xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.', 'assistant');
        }
    }

    // Gán sự kiện cho các nút (giữ nguyên)
    if (chatFab) {
        chatFab.addEventListener('click', () => chatWidget.classList.toggle('active'));
    }
    if (closeBtn) {
        closeBtn.addEventListener('click', () => chatWidget.classList.remove('active'));
    }
    suggestionChips.forEach(chip => {
        chip.addEventListener('click', () => {
            chatInput.value = chip.textContent;
            sendMessage();
        });
    });
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    if (chatInput) {
        chatInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });
    }
});
