let chatId = null;
let captchaToken = localStorage.getItem('captchaToken');
let currentCaptchaId = null;

const chatContainer = document.getElementById('chat-container');
const chatForm = document.getElementById('chat-form');
const queryInput = document.getElementById('query-input');
const submitBtn = document.getElementById('submit-btn');
const chatList = document.getElementById('chat-list');
const newChatBtn = document.getElementById('new-chat-btn');
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('sidebar');

const captchaModal = document.getElementById('captcha-modal');
const captchaForm = document.getElementById('captcha-form');
const captchaText = document.getElementById('captcha-text');
const captchaInput = document.getElementById('captcha-input');
const captchaError = document.getElementById('captcha-error');

async function showCaptcha() {
    captchaModal.classList.add('show');
    captchaInput.value = '';
    captchaError.textContent = '';
    try {
        const res = await fetch('/api/captcha');
        const data = await res.json();
        currentCaptchaId = data.captcha_id;
        captchaText.textContent = data.text;
        captchaInput.focus();
    } catch (e) {
        captchaText.textContent = 'Error cargando captcha.';
    }
}

captchaForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const answer = captchaInput.value.trim();
    if (!answer || !currentCaptchaId) return;

    try {
        const res = await fetch('/api/verify_captcha', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ captcha_id: currentCaptchaId, answer })
        });
        const data = await res.json();
        
        if (res.ok) {
            captchaToken = data.token;
            localStorage.setItem('captchaToken', captchaToken);
            captchaModal.classList.remove('show');
        } else {
            captchaError.textContent = data.error || 'Respuesta incorrecta.';
            showCaptcha();
        }
    } catch (err) {
        captchaError.textContent = 'Error verificando captcha.';
    }
});

async function loadSidebar() {
    try {
        const res = await fetch('/api/chats');
        if (res.ok) {
            const chats = await res.json();
            chatList.innerHTML = '';
            chats.forEach(chat => {
                const div = document.createElement('div');
                div.className = 'chat-item' + (chat.id === chatId ? ' active' : '');
                div.textContent = chat.title;
                div.onclick = () => selectChat(chat.id);
                chatList.appendChild(div);
            });
        }
    } catch (e) {
    }
}

async function selectChat(id) {
    chatId = id;
    chatContainer.innerHTML = '';
    await loadSidebar();
    await loadHistory();
    if (window.innerWidth <= 768) {
        sidebar.classList.remove('show-mobile');
    }
}

newChatBtn.onclick = () => {
    chatId = null;
    chatContainer.innerHTML = '';
    loadSidebar();
    queryInput.focus();
    if (window.innerWidth <= 768) {
        sidebar.classList.remove('show-mobile');
    }
};

if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('show-mobile');
    });
}

document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768 && 
        sidebar.classList.contains('show-mobile') && 
        !sidebar.contains(e.target) && 
        e.target !== sidebarToggle) {
        sidebar.classList.remove('show-mobile');
    }
});

async function loadHistory() {
    if (!chatId) return;
    try {
        const res = await fetch(`/api/history/${chatId}`);
        if (res.ok) {
            const history = await res.json();
            history.forEach(msg => appendMessage(msg.role, msg.content));
        }
    } catch (e) {
    }
}

function appendMessage(role, content) {
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper ${role}`;
    
    const roleDiv = document.createElement('div');
    roleDiv.className = 'message-role';
    roleDiv.textContent = role === 'user' ? 'USUARIO' : 'SISTEMA';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (role === 'bot') {
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }
    
    wrapper.appendChild(roleDiv);
    wrapper.appendChild(contentDiv);
    chatContainer.appendChild(wrapper);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function appendThinking() {
    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper bot';
    wrapper.id = 'thinking-indicator';
    
    const roleDiv = document.createElement('div');
    roleDiv.className = 'message-role';
    roleDiv.textContent = 'SISTEMA';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content thinking';
    contentDiv.textContent = 'Pensando...';
    
    wrapper.appendChild(roleDiv);
    wrapper.appendChild(contentDiv);
    chatContainer.appendChild(wrapper);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function removeThinking() {
    const indicator = document.getElementById('thinking-indicator');
    if (indicator) {
        indicator.remove();
    }
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!captchaToken) {
        showCaptcha();
        return;
    }

    const query = queryInput.value.trim();
    if (!query) return;

    appendMessage('user', query);
    queryInput.value = '';
    submitBtn.disabled = true;
    
    appendThinking();

    const requestBody = { query };
    if (chatId) {
        requestBody.chat_id = chatId;
    }

    try {
        const headers = { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${captchaToken}`
        };

        const res = await fetch('/api/chat', {
            method: 'POST',
            headers,
            body: JSON.stringify(requestBody)
        });
        
        removeThinking();
        
        if (res.status === 403) {
            const data = await res.json();
            if (data.needs_captcha) {
                captchaToken = null;
                localStorage.removeItem('captchaToken');
                showCaptcha();
                chatContainer.lastChild.remove(); 
            } else {
                appendMessage('bot', data.error || 'Error de autorización');
            }
        } else if (res.ok) {
            const data = await res.json();
            if (data.chat_id !== chatId) {
                chatId = data.chat_id;
            }
            appendMessage('bot', data.response);
            loadSidebar();
        } else {
            appendMessage('bot', 'Ocurrió un error inesperado.');
        }
    } catch (err) {
        removeThinking();
        appendMessage('bot', 'Error de red al conectar con el servidor.');
    } finally {
        submitBtn.disabled = false;
        queryInput.focus();
    }
});

loadSidebar();
