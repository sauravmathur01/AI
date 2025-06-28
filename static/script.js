// ==== DOM Elements ====
const startBtn = document.getElementById('start-button');
const stopBtn = document.getElementById('stop-button');
const msgList = document.getElementById('message-list');
const sendBtn = document.getElementById('send-button');
const inputBox = document.getElementById('user-input');
const mic = document.getElementById('mic-icon');
const hourEl = document.getElementById("hour");
const minEl = document.getElementById("minute");
const weekDays = document.querySelector(".week");
const suggestionsBox = document.getElementById("suggestions-container");

let muted = false;
let thinkingLoop;
let recognition;

// ==== Get Mute State from Server ====
fetch('/api/get_mute')
    .then(res => res.json())
    .then(data => muted = data.muted)
    .catch(err => console.error("Mute fetch failed", err));

// ==== Send Message Logic ====
function sendMessage(msg) {
    if (!msg) return;
    showThinking();
    showUserMsg(msg);

    fetch('/api/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
    })
    .then(res => res.json())
    .then(data => {
        hideThinking();
        showBotMsg(data.response);
    })
    .catch(err => {
        console.error("Error from server:", err);
        hideThinking();
    });
}

function showUserMsg(text) {
    renderMessage(text, "user-message", "You");
}

function showBotMsg(text) {
    renderMessage(text, "bot-message", "ZAX");
}

function renderMessage(text, className, sender) {
    const time = formatTime(new Date());
    const li = document.createElement("li");
    li.className = className;
    li.innerHTML = `<strong>${sender} (${time}):</strong> ${text}`;

    const muteBtn = document.createElement("button");
    muteBtn.textContent = muted ? "🔊 Unmute" : "🔇 Mute";
    muteBtn.onclick = () => toggleMute(muteBtn);
    li.appendChild(muteBtn);

    msgList.appendChild(li);
    msgList.scrollTop = msgList.scrollHeight;
}

function formatTime(date) {
    const h = date.getHours();
    const m = date.getMinutes();
    const ampm = h >= 12 ? 'PM' : 'AM';
    return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${ampm}`;
}

// ==== Thinking Animation ====
function showThinking() {
    const el = document.getElementById("thinking");
    el.style.display = "block";
    let dots = 0;
    thinkingLoop = setInterval(() => {
        el.querySelector("em").textContent = "🤔 Zax is thinking" + ".".repeat(dots % 4);
        dots++;
    }, 500);
}

function hideThinking() {
    clearInterval(thinkingLoop);
    const el = document.getElementById("thinking");
    el.style.display = "none";
    el.querySelector("em").textContent = "🤔 Zax is thinking...";
}

// ==== Voice Commands ====
function startListening() {
    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.continuous = true;

    recognition.start();
    toggleMic(true);

    recognition.onresult = e => {
        const msg = e.results[e.results.length - 1][0].transcript;
        sendMessage(msg);
        if (msg.toLowerCase().includes("bye")) {
            stopListening();
            showBotMsg("Bye! Stopping listening.");
        }
    };

    recognition.onend = () => toggleMic(false);
    recognition.onerror = e => console.error("Speech error:", e.error);
}

function stopListening() {
    if (recognition) recognition.stop();
    toggleMic(false);
}

function toggleMic(active) {
    startBtn.style.display = active ? "none" : "inline";
    stopBtn.style.display = active ? "inline" : "none";
    mic.classList.toggle('fa-microphone', active);
    mic.classList.toggle('fa-microphone-slash', !active);
}

// ==== Event Listeners ====
startBtn.onclick = startListening;
stopBtn.onclick = stopListening;

sendBtn.onclick = () => {
    const msg = inputBox.value.trim();
    sendMessage(msg);
    inputBox.value = "";
};

mic.onclick = () => {
    stopBtn.style.display === "none" ? startListening() : stopListening();
};

// ==== Clock ====
function updateClock() {
    const now = new Date();
    hourEl.textContent = String(now.getHours()).padStart(2, "0");
    minEl.textContent = String(now.getMinutes()).padStart(2, "0");

    const day = now.getDay();
    Array.from(weekDays.children).forEach((el, i) => {
        el.style.color = i === day ? "red" : "white";
    });

    const dateStr = now.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
    document.getElementById("current-date").textContent = dateStr;
}
setInterval(updateClock, 1000);
updateClock();

// ==== Suggestions ====
const suggestions = ["hello", "how are you?", "what is your name?", "tell me a joke", "goodbye", "Google", "YouTube"];

inputBox.addEventListener('input', function () {
    const input = this.value.toLowerCase();
    suggestionsBox.innerHTML = '';

    if (input) {
        const matches = suggestions.filter(s => s.includes(input));
        matches.forEach(s => {
            const div = document.createElement('div');
            div.className = "suggestion-item";
            div.textContent = s;
            div.onclick = () => {
                inputBox.value = s;
                suggestionsBox.innerHTML = '';
            };
            suggestionsBox.appendChild(div);
        });
        suggestionsBox.style.display = matches.length ? 'block' : 'none';
    } else {
        suggestionsBox.style.display = 'none';
    }
});

document.addEventListener('click', e => {
    if (!inputBox.contains(e.target)) {
        suggestionsBox.style.display = 'none';
    }
});

// ==== Loader & Welcome ====
window.onload = () => {
    setTimeout(() => showBotMsg("Hi, I'm ZAX! How can I assist you today?"), 500);
};

window.addEventListener('load', () => {
    const loader = document.getElementById('loading-screen');
    loader.style.opacity = '0';
    setTimeout(() => loader.style.display = 'none', 800);
});

// ==== Toggle AI Model ====
function toggleModel() {
    fetch('/api/switch_model', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            document.getElementById("current-model").textContent =
                data.use_huggingface ? "🟢 Server 1" : "🟡 Server 2";
        })
        .catch(err => {
            alert("Could not switch model");
            console.error(err);
        });
}

// ==== Toggle Chat/Knowledge Mode ====
function toggleKnowledgeMode() {
    const btn = document.getElementById("knowledge-toggle-btn");
    const current = btn.getAttribute("data-on") === "true";

    fetch('/api/toggle_knowledge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ on: !current })
    })
    .then(res => res.json())
    .then(data => {
        btn.setAttribute("data-on", data.knowledge_mode);
        btn.textContent = data.knowledge_mode ? "🔍 Search Mode" : "💬 Chat Mode";
    });
}

// ==== Toggle Mute ====
function toggleMute(btn) {
    muted = !muted;

    fetch('/api/toggle_mute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ on: muted })
    })
    .then(res => res.json())
    .then(() => {
        btn.textContent = muted ? "🔊 Unmute" : "🔇 Mute";
    });
}
