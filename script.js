// Initialize Socket.IO
const socket = io('http://localhost:8000');
let isSystemActive = false;

// Terminal output handling
const terminalOutput = document.getElementById('terminalOutput');
function addTerminalLine(text, type = 'info') {
    const line = document.createElement('div');
    const timestamp = new Date().toLocaleTimeString();
    line.className = `terminal-line ${type}`;
    line.innerHTML = `[${timestamp}] ${text}`;
    terminalOutput.appendChild(line);
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

// Socket.IO event handlers
socket.on('connect', () => {
    addTerminalLine('WebSocket connection established', 'success');
});

socket.on('disconnect', () => {
    addTerminalLine('WebSocket connection lost', 'error');
    updateStatus(false);
});

socket.on('status_change', (data) => {
    updateStatus(data.active);
});

socket.on('usb_event', (data) => {
    addTerminalLine('🚨 ' + data.message, 'success');
    showNotification('USB Device Detected!');
    
    // Add visual feedback
    document.querySelector('.ninja').style.color = '#00ff00';
    document.querySelector('.ninja').style.transform = 'scale(1.2)';
    setTimeout(() => {
        document.querySelector('.ninja').style.color = '#0f0';
        document.querySelector('.ninja').style.transform = 'scale(1)';
    }, 1000);
});

// Update system status
function updateStatus(active) {
    isSystemActive = active;
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    if (active) {
        statusDot.classList.add('active');
        statusText.textContent = 'SYSTEM ACTIVE';
        addTerminalLine('System activated and monitoring for USB devices');
    } else {
        statusDot.classList.remove('active');
        statusText.textContent = 'SYSTEM OFFLINE';
        addTerminalLine('System deactivated');
    }
}

// Matrix rain effect
function createMatrixRain() {
    const canvas = document.createElement('canvas');
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.zIndex = '-1';
    document.querySelector('.matrix-bg').appendChild(canvas);

    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const katakana = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン';
    const latin = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const nums = '0123456789';
    const alphabet = katakana + latin + nums;

    const fontSize = 16;
    const columns = canvas.width/fontSize;
    const rainDrops = Array(Math.floor(columns)).fill(canvas.height);

    function draw() {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        ctx.fillStyle = '#0F0';
        ctx.font = fontSize + 'px monospace';

        for(let i = 0; i < rainDrops.length; i++) {
            const text = alphabet.charAt(Math.floor(Math.random() * alphabet.length));
            ctx.fillText(text, i*fontSize, rainDrops[i]*fontSize);
            
            if(rainDrops[i]*fontSize > canvas.height && Math.random() > 0.975) {
                rainDrops[i] = 0;
            }
            rainDrops[i]++;
        }
    }

    return setInterval(draw, 30);
}

// Initialize matrix effect
let matrixInterval = createMatrixRain();

// Handle window resize
window.addEventListener('resize', () => {
    clearInterval(matrixInterval);
    matrixInterval = createMatrixRain();
});

// Show notification
function showNotification(message, isError = false) {
    const notification = document.createElement('div');
    notification.className = `notification ${isError ? 'error' : 'success'}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => notification.classList.add('show'), 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

// Function to activate system
async function activateSystem() {
    const button = document.getElementById('activateBtn');
    if (button) button.disabled = true;
    
    try {
        const response = await fetch('http://localhost:8000/launch', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(data.message);
            addTerminalLine(data.message, 'success');
            
            // Add visual feedback
            document.querySelector('.ninja').style.color = '#00ff00';
            document.querySelector('.ninja').style.transform = 'scale(1.2)';
            setTimeout(() => {
                document.querySelector('.ninja').style.color = '#0f0';
                document.querySelector('.ninja').style.transform = 'scale(1)';
            }, 1000);
        } else {
            showNotification(data.message, true);
            addTerminalLine(data.message, 'error');
        }
    } catch (error) {
        const errorMessage = 'Failed to connect to server';
        showNotification(errorMessage, true);
        addTerminalLine(errorMessage, 'error');
    } finally {
        if (button) button.disabled = false;
    }
}

// Initial status check and auto-activation
window.addEventListener('load', () => {
    fetch('http://localhost:8000/status')
        .then(response => response.json())
        .then(data => {
            updateStatus(data.active);
            if (!data.active) {
                activateSystem();
            }
        })
        .catch(() => addTerminalLine('Failed to get initial system status', 'error'));
});

// Button click handler
document.getElementById('activateBtn').addEventListener('click', activateSystem);

// Add some initial terminal output
addTerminalLine('Ninja Jacky Chain v2.0 initialized');
addTerminalLine('Waiting for system activation...');
