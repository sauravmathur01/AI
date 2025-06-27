// ==== Element References ====
const startButton = document.getElementById('start-button');
const stopButton = document.getElementById('stop-button');
const messageList = document.getElementById('message-list');
const sendButton = document.getElementById('send-button');
const userInput = document.getElementById('user-input');
const micIcon = document.getElementById('mic-icon');
const hour = document.getElementById("hour");
const minute = document.getElementById("minute");
const week = document.querySelector(".week");
const suggestionsContainer = document.getElementById
let muted = false;

// Fetch real mute state from backend on load
fetch('/api/get_mute')
    .then(res => res.json())
    .then(data => {
        muted = data.muted;
    });

// ==== Typing Animation ====
let thinkingInterval;
let recognition;

// ==== Send & Display Chat ====
function sendMessage(message) {
    startThinkingAnimation();
    displayUserMessage(message);

    fetch('/api/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    })
    .then(res => res.json())
    .then(data => {
        stopThinkingAnimation();
        displayBotMessage(data.response);
    })
    .catch(err => {
        console.error(err);
        stopThinkingAnimation();
    });
}

function displayUserMessage(text) {
    createChatMessage(text, "user-message", "You");
}

function displayBotMessage(text) {
    createChatMessage(text, "bot-message", "ZAX");
}

function createChatMessage(text, className, sender) {
    const now = new Date();
    const time = formatTime(now);
    const li = document.createElement("li");
    li.className = className;
    // li.textContent = `${sender} (${time}): ${text}`;
    li.innerHTML = `<strong>${sender} (${time}):</strong> ${text}`;

    messageList.appendChild(li);
    messageList.scrollTop = messageList.scrollHeight;
    // if (text.includes("ZAX")) return; // avoid duplicate mute button on user echo

    // const muteButton = document.createElement("button");
    // muteButton.textContent = "🔇 Mute";
    // muteButton.style.marginLeft = "10px";
    // muteButton.onclick = () => {
    //     fetch('/api/stop_speech', { method: 'POST' })
    //         .then(() => muteButton.disabled = true);
    // };
    // li.appendChild(muteButton);
    const muteButton = document.createElement("button");
    muteButton.textContent = muted ? "🔊 Unmute" : "🔇 Mute";
    muteButton.onclick = () => toggleMute(muteButton);
    li.appendChild(muteButton);

        }

    function formatTime(now) {
    const h = now.getHours();
    const m = now.getMinutes();
    const ampm = h >= 12 ? 'PM' : 'AM';
    return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${ampm}`;
}

// ==== Thinking Animation ====
function startThinkingAnimation() {
    const el = document.getElementById("thinking");
    el.style.display = "block";
    let dots = 0;
    thinkingInterval = setInterval(() => {
        dots = (dots + 1) % 4;
        el.querySelector("em").textContent = "🤔 Zax is thinking" + ".".repeat(dots);
    }, 500);
}

function stopThinkingAnimation() {
    clearInterval(thinkingInterval);
    const el = document.getElementById("thinking");
    el.style.display = "none";
    el.querySelector("em").textContent = "🤔 Zax is thinking...";
}

// ==== Voice Recognition ====
function startListening() {
    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.continuous = true;

    recognition.start();
    updateMicState(true);

    recognition.onresult = event => {
        const text = event.results[event.results.length - 1][0].transcript;
        sendMessage(text);
        if (text.toLowerCase().includes("bye")) {
            stopListening();
            displayBotMessage("Bye! Stopping listening.");
        }
    };

    recognition.onend = () => updateMicState(false);
    recognition.onerror = e => console.error("Speech error:", e.error);
}

function stopListening() {
    if (recognition) {
        recognition.stop();
        updateMicState(false);
    }
}

function updateMicState(active) {
    startButton.style.display = active ? "none" : "inline";
    stopButton.style.display = active ? "inline" : "none";
    micIcon.classList.toggle('fa-microphone', active);
    micIcon.classList.toggle('fa-microphone-slash', !active);
}

// ==== Event Listeners ====
startButton.addEventListener('click', startListening);
stopButton.addEventListener('click', stopListening);

sendButton.addEventListener('click', () => {
    const msg = userInput.value.trim();
    if (msg) {
        sendMessage(msg);
        userInput.value = "";
    }
});

micIcon.addEventListener('click', () => {
    stopButton.style.display === "none" ? startListening() : stopListening();
});

// ==== Clock & Date ====
function updateClock() {
    const now = new Date();
    hour.textContent = String(now.getHours()).padStart(2, "0");
    minute.textContent = String(now.getMinutes()).padStart(2, "0");

    const dayIndex = now.getDay();
    Array.from(week.children).forEach((el, i) => {
        el.style.color = i === dayIndex ? "red" : "white";
    });

    const date = now.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
    document.getElementById("current-date").textContent = date;
}
setInterval(updateClock, 1000);
updateClock();

// ==== Suggestions ====
const suggestions = ["hello", "how are you?", "what is your name?", "tell me a joke", "goodbye", "Google", "YouTube"];

userInput.addEventListener('input', function () {
    const input = this.value.toLowerCase();
    suggestionsContainer.innerHTML = '';
    if (input) {
        const matches = suggestions.filter(s => s.includes(input));
        matches.forEach(s => {
            const div = document.createElement('div');
            div.className = "suggestion-item";
            div.textContent = s;
            div.addEventListener('click', () => {
                userInput.value = s;
                suggestionsContainer.innerHTML = '';
            });
            suggestionsContainer.appendChild(div);
        });
        suggestionsContainer.style.display = matches.length ? 'block' : 'none';
    } else {
        suggestionsContainer.style.display = 'none';
    }
});

document.addEventListener('click', e => {
    if (!userInput.contains(e.target)) {
        suggestionsContainer.style.display = 'none';
    }
});

// ==== Welcome + Loader ====
window.onload = () => {
    setTimeout(() => displayBotMessage("Hi, I'm ZAX! How can I assist you today?"), 500);
};
window.addEventListener('load', () => {
    const loader = document.getElementById('loading-screen');
    loader.style.opacity = '0';
    setTimeout(() => loader.style.display = 'none', 800);
});

// ==== Model Switcher ====
function toggleModel() {
    fetch('/api/switch_model', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            const status = document.getElementById("current-model");
            status.textContent = data.use_huggingface ? "🟢 Server 1" : "🟡 Server 2"; // HUGGING face to Local mode
        })
        .catch(err => {
            alert("Failed to switch model.");
            console.error(err);
        });
}
// function toggleKnowledgeMode() {
//     const toggleBtn = document.getElementById("knowledge-toggle");
//     const isOn = toggleBtn.getAttribute("data-on") === "true";
//     fetch('/api/toggle_knowledge', {
//         method: 'POST',
//         headers: {'Content-Type': 'application/json'},
//         body: JSON.stringify({ on: !isOn })
//     }).then(res => res.json()).then(data => {
//         toggleBtn.setAttribute("data-on", data.knowledge_mode);
//         toggleBtn.textContent = data.knowledge_mode ? "🔍 Knowledge ON" : "💬 Chat Mode";
//     });
// }
function toggleKnowledgeMode() {
    const toggleBtn = document.getElementById("knowledge-toggle-btn");
    const isOn = toggleBtn.getAttribute("data-on") === "true";

    fetch('/api/toggle_knowledge', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ on: !isOn })
    }).then(res => res.json()).then(data => {
        toggleBtn.setAttribute("data-on", data.knowledge_mode);
        toggleBtn.textContent = data.knowledge_mode ? "🔍 Search Mode" : "💬 Chat Mode";
    });
    }

// function toggleMute(button) {
//     muted = !muted;  // Toggle state

//     fetch('/api/toggle_mute', {
//         method: 'POST',
//         headers: {'Content-Type': 'application/json'},
//         body: JSON.stringify({ on: muted })
//     })
//     .then(res => res.json())
//     .then(data => {
//         button.textContent = muted ? "🔊 Unmute" : "🔇 Mute";
//     });

function toggleMute(button) {
    muted = !muted;

    fetch('/api/toggle_mute', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ on: muted })
    })
    .then(res => res.json())
    .then(data => {
        button.textContent = muted ? "🔊 Unmute" : "🔇 Mute";
    });
}


