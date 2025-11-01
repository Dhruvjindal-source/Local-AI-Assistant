import speech_recognition as sr
import webbrowser
import pyttsx3
import requests
from openai import OpenAI
from gtts import gTTS
import pygame
import os
import re
import datetime
import shutil
import subprocess
import word2number
import wikipedia
import geocoder
import time
import winsound
import threading
import urllib.parse
import logging
import pyautogui
from ctypes import cast, POINTER, c_ulong
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import tempfile
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
from urllib.parse import urlparse, parse_qs
import webbrowser
import atexit

logging.basicConfig(level=logging.DEBUG, format="%(message)s")

# ---------- CONFIG ----------
newsapi = "19a6e5ef5793448e84afbee5e8778d98"
PORT = 8080
# ----------------------------

# Global state management
class BuddyState:
    def __init__(self):
        self.is_listening = False
        self.is_speaking = False
        self.is_processing = False
        self.is_mic_active = True
        self.is_standby = True
        self.server_running = False
        self.status_file = tempfile.mktemp(suffix='.json')
        self.update_status()
    
    def update_status(self):
        """Update status file that HTML can read"""
        status = {
            'listening': self.is_listening,
            'speaking': self.is_speaking,
            'processing': self.is_processing,
            'mic_active': self.is_mic_active,
            'standby': self.is_standby,
            'timestamp': time.time()
        }
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status, f)
        except:
            pass
    
    def set_listening(self, state):
        self.is_listening = state
        self.is_speaking = False
        self.is_processing = False
        self.is_standby = not state
        self.update_status()
        print(f"Status: {'LISTENING' if state else 'READY'}")
    
    def set_processing(self):
        self.is_listening = False
        self.is_speaking = False
        self.is_processing = True
        self.is_standby = False
        self.update_status()
        print("Status: PROCESSING")
    
    def set_speaking(self, state):
        self.is_speaking = state
        self.is_listening = False
        self.is_processing = False
        self.is_standby = not state
        self.update_status()
        print(f"Status: {'SPEAKING' if state else 'READY'}")
    
    def set_standby(self):
        self.is_listening = False
        self.is_speaking = False
        self.is_processing = False
        self.is_standby = True
        self.update_status()
        print("Status: STANDBY")

# Initialize global state
buddy_state = BuddyState()

recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = False
recognizer.energy_threshold = 300
engine = pyttsx3.init()
ALARMS = {}
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

# Custom HTTP Handler for the web interface
class BuddyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_buddy_html()
        elif parsed_path.path == '/status':
            self.send_status()
        elif parsed_path.path == '/control':
            self.handle_control(parsed_path.query)
        else:
            super().do_GET()
    
    def send_buddy_html(self):
        """Serve the enhanced HTML with status integration"""
        html_content = self.get_enhanced_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', len(html_content.encode()))
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def send_status(self):
        """Send current status as JSON"""
        try:
            with open(buddy_state.status_file, 'r') as f:
                status_data = f.read()
        except:
            status_data = json.dumps({
                'listening': buddy_state.is_listening,
                'speaking': buddy_state.is_speaking,
                'mic_active': buddy_state.is_mic_active,
                'standby': buddy_state.is_standby
            })
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(status_data.encode())
    
    def handle_control(self, query):
        """Handle control commands from the web interface"""
        params = parse_qs(query)
        action = params.get('action', [''])[0]
        
        if action == 'toggle_mic':
            buddy_state.is_mic_active = not buddy_state.is_mic_active
            buddy_state.update_status()
            print(f"Microphone {'activated' if buddy_state.is_mic_active else 'muted'}")
        elif action == 'activate':
            if buddy_state.is_mic_active:
                # Simulate voice activation
                threading.Thread(target=simulate_voice_command, daemon=True).start()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode())
    
    def get_enhanced_html(self):
        """Return the HTML with JavaScript integration for real-time status updates"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buddy - Your Friendly Voice Assistant</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');
        
        :root {
            --primary-orange: #ff9a3c;
            --secondary-yellow: #ffd93d;
            --accent-green: #6bcf7f;
            --accent-blue: #4ecdc4;
            --background-warm: #2a1810;
            --background-darker: #1a0f08;
            --processing-pink: #ff6b9d;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, var(--background-warm) 0%, var(--background-darker) 50%, #0a0504 100%);
            background-attachment: fixed;
            font-family: 'Poppins', sans-serif;
            height: 100vh;
            overflow: hidden;
            position: relative;
            color: rgba(255, 255, 255, 0.95);
        }
        
        .particles {
            position: absolute;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            z-index: 1;
        }
        
        .particle {
            position: absolute;
            background: var(--primary-orange);
            border-radius: 50%;
            opacity: 0;
            animation: float 6s infinite;
        }
        
        .particle.warm {
            background: var(--secondary-yellow);
            box-shadow: 0 0 8px var(--secondary-yellow);
        }
        
        .particle.cool {
            background: var(--accent-blue);
            box-shadow: 0 0 6px var(--accent-blue);
        }
        
        @keyframes float {
            0%, 100% { opacity: 0; transform: translateY(0) scale(0.5); }
            50% { opacity: 0.6; transform: translateY(-100px) scale(1); }
        }
        
        .glow-overlay {
            position: absolute;
            width: 100%;
            height: 100%;
            top: 0;
            left: 0;
            z-index: 2;
            background: 
                radial-gradient(ellipse at 30% 30%, rgba(255, 154, 60, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 70% 60%, rgba(107, 207, 127, 0.06) 0%, transparent 50%);
            animation: glow-shift 20s ease-in-out infinite;
        }
        
        @keyframes glow-shift {
            0%, 100% { opacity: 0.8; transform: translateX(0) translateY(0); }
            50% { opacity: 1; transform: translateX(15px) translateY(-10px); }
        }
        
        .container {
            position: relative;
            z-index: 10;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        
        .title {
            position: absolute;
            top: 70px;
            color: var(--primary-orange);
            font-size: clamp(42px, 9vw, 64px);
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: clamp(6px, 2.5vw, 12px);
            text-shadow: 
                0 0 30px rgba(255, 154, 60, 0.9),
                0 0 60px rgba(255, 154, 60, 0.5),
                0 0 90px rgba(255, 154, 60, 0.3);
            animation: title-glow 3s ease-in-out infinite;
        }
        
        @keyframes title-glow {
            0%, 100% { text-shadow: 
                0 0 30px rgba(255, 154, 60, 0.9),
                0 0 60px rgba(255, 154, 60, 0.5); }
            50% { text-shadow: 
                0 0 40px rgba(255, 154, 60, 1),
                0 0 80px rgba(255, 154, 60, 0.7),
                0 0 120px rgba(255, 154, 60, 0.4); }
        }
        
        .subtitle {
            position: absolute;
            top: 145px;
            color: rgba(255, 217, 61, 0.85);
            font-size: clamp(14px, 3.5vw, 18px);
            font-weight: 400;
            letter-spacing: clamp(3px, 1.2vw, 5px);
            text-transform: lowercase;
            opacity: 0;
            animation: fade-in 2s ease-out 1s forwards;
        }
        
        .top-status {
            position: absolute;
            top: 190px;
            left: 50%;
            transform: translateX(-50%);
            color: rgba(255, 255, 255, 0.7);
            font-weight: 400;
            text-transform: lowercase;
            letter-spacing: 4px;
            font-size: 13px;
            transition: all 0.5s ease;
            pointer-events: none;
            background: rgba(0, 0, 0, 0.4);
            padding: 10px 20px;
            border-radius: 25px;
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 154, 60, 0.3);
            min-width: 140px;
            text-align: center;
        }
        
        @keyframes fade-in {
            to { opacity: 1; }
        }
        
        .buddy-orb {
            position: relative;
            width: 320px;
            height: 320px;
            border-radius: 50%;
            background: 
                radial-gradient(
                    circle at 25% 25%,
                    rgba(255, 255, 255, 0.95) 0%,
                    rgba(255, 255, 255, 0.15) 35%,
                    transparent 65%
                ),
                radial-gradient(
                    circle at 60% 60%,
                    rgba(255, 154, 60, 0.7) 0%,
                    rgba(255, 154, 60, 0.3) 30%,
                    transparent 55%
                ),
                radial-gradient(
                    circle at 80% 30%,
                    rgba(255, 217, 61, 0.6) 0%,
                    rgba(255, 217, 61, 0.2) 35%,
                    transparent 65%
                ),
                radial-gradient(
                    circle at 30% 75%,
                    rgba(107, 207, 127, 0.5) 0%,
                    rgba(107, 207, 127, 0.15) 40%,
                    transparent 75%
                ),
                radial-gradient(
                    circle at 70% 50%,
                    rgba(78, 205, 196, 0.4) 0%,
                    rgba(78, 205, 196, 0.1) 45%,
                    transparent 85%
                );
            display: flex;
            justify-content: center;
            align-items: center;
            transition: all 1.5s ease-in-out;
            cursor: pointer;
            box-shadow: 
                0 0 40px rgba(255, 154, 60, 0.4),
                inset 0 0 60px rgba(255, 154, 60, 0.1);
        }
        
        .buddy-orb::before {
            content: '';
            position: absolute;
            top: -35px;
            left: -35px;
            right: -35px;
            bottom: -35px;
            border-radius: 50%;
            background: radial-gradient(
                circle,
                transparent 0%,
                transparent 70%,
                rgba(255, 154, 60, 0.15) 80%,
                rgba(255, 154, 60, 0.08) 100%
            );
            transition: all 1.5s ease-in-out;
            pointer-events: none;
        }
        
        .listening::before {
            background: radial-gradient(
                circle,
                transparent 0%,
                transparent 60%,
                rgba(255, 154, 60, 0.5) 70%,
                rgba(255, 154, 60, 0.9) 80%,
                rgba(255, 154, 60, 1.0) 88%,
                rgba(255, 154, 60, 0.7) 94%,
                rgba(255, 154, 60, 0.3) 100%
            ) !important;
            animation: buddy-pulse 2s ease-in-out infinite;
        }
        
        .processing::before {
            background: radial-gradient(
                circle,
                transparent 0%,
                transparent 60%,
                rgba(255, 107, 157, 0.5) 70%,
                rgba(255, 107, 157, 0.9) 80%,
                rgba(255, 107, 157, 1.0) 88%,
                rgba(255, 107, 157, 0.7) 94%,
                rgba(255, 107, 157, 0.3) 100%
            ) !important;
            animation: buddy-spin 1.8s linear infinite;
        }
        
        .speaking::before {
            background: radial-gradient(
                circle,
                transparent 0%,
                transparent 60%,
                rgba(107, 207, 127, 0.5) 70%,
                rgba(107, 207, 127, 0.9) 80%,
                rgba(107, 207, 127, 1.0) 88%,
                rgba(107, 207, 127, 0.7) 94%,
                rgba(107, 207, 127, 0.3) 100%
            ) !important;
            animation: buddy-waves 0.9s ease-in-out infinite;
        }
        
        @keyframes buddy-pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.06); opacity: 0.9; }
        }
        
        @keyframes buddy-spin {
            0% { transform: scale(1) rotate(0deg); }
            25% { transform: scale(1.04) rotate(90deg); }
            50% { transform: scale(1.08) rotate(180deg); }
            75% { transform: scale(1.04) rotate(270deg); }
            100% { transform: scale(1) rotate(360deg); }
        }
        
        @keyframes buddy-waves {
            0% { transform: scale(1); opacity: 1; }
            25% { transform: scale(1.06); opacity: 0.9; }
            50% { transform: scale(1.12); opacity: 0.85; }
            75% { transform: scale(1.06); opacity: 0.9; }
            100% { transform: scale(1); opacity: 1; }
        }
        
        .wake-word-hint {
            position: absolute;
            bottom: 180px;
            color: rgba(255, 217, 61, 0.7);
            font-size: 14px;
            font-weight: 400;
            letter-spacing: 3px;
            text-align: center;
            background: rgba(42, 24, 16, 0.6);
            padding: 14px 28px;
            border-radius: 30px;
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 154, 60, 0.3);
            transition: all 0.4s ease;
        }
        
        .controls {
            position: fixed;
            bottom: 90px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 30px;
            z-index: 20;
            background: rgba(42, 24, 16, 0.5);
            padding: 18px 30px;
            border-radius: 60px;
            backdrop-filter: blur(18px);
            border: 1px solid rgba(255, 154, 60, 0.3);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
        }
        
        .control-btn {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            border: 2px solid rgba(255, 154, 60, 0.5);
            background: rgba(42, 24, 16, 0.8);
            color: var(--primary-orange);
            font-size: 24px;
            cursor: pointer;
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            overflow: hidden;
        }
        
        .control-btn:hover {
            background: rgba(255, 154, 60, 0.2);
            box-shadow: 
                0 0 30px rgba(255, 154, 60, 0.5),
                inset 0 0 20px rgba(255, 154, 60, 0.15);
            transform: translateY(-4px) scale(1.08);
            border-color: rgba(255, 154, 60, 0.9);
        }
        
        .mic-muted {
            background: rgba(220, 53, 69, 0.8) !important;
            color: #ffffff !important;
            border-color: rgba(220, 53, 69, 0.7) !important;
        }
        
        /* Status-specific styling */
        .status-listening {
            color: rgba(255, 154, 60, 1) !important;
            text-shadow: 0 0 20px rgba(255, 154, 60, 0.8);
            border-color: rgba(255, 154, 60, 0.5);
            background: rgba(255, 154, 60, 0.15);
        }
        
        .status-processing {
            color: rgba(255, 107, 157, 1) !important;
            text-shadow: 0 0 20px rgba(255, 107, 157, 0.8);
            border-color: rgba(255, 107, 157, 0.5);
            background: rgba(255, 107, 157, 0.15);
        }
        
        .status-speaking {
            color: rgba(107, 207, 127, 1) !important;
            text-shadow: 0 0 20px rgba(107, 207, 127, 0.8);
            border-color: rgba(107, 207, 127, 0.5);
            background: rgba(107, 207, 127, 0.15);
        }
        
        .status-muted {
            color: rgba(220, 53, 69, 1) !important;
            text-shadow: 0 0 20px rgba(220, 53, 69, 0.8);
            border-color: rgba(220, 53, 69, 0.5);
            background: rgba(220, 53, 69, 0.15);
        }
    </style>
</head>
<body>
    <div class="particles" id="particles"></div>
    <div class="glow-overlay"></div>
    
    <div class="container">
        <div class="title">BUDDY</div>
        <div class="subtitle">your friendly voice assistant</div>
        <div class="top-status" id="status">STANDBY</div>
        
        <div class="buddy-orb" id="buddyorb"></div>
        
        <div class="wake-word-hint">
            Say "Hey Buddy" to activate
        </div>
    </div>
    
    <div class="controls">
        <button class="control-btn" id="micBtn" title="Toggle Microphone">🎤</button>
        <button class="control-btn" id="settingsBtn" title="Settings">⚙️</button>
        <button class="control-btn" id="infoBtn" title="Info">ℹ️</button>
    </div>

    <script>
        let currentStatus = {
            listening: false,
            speaking: false,
            processing: false,
            mic_active: true,
            standby: true
        };

        // Create floating particles
        function createParticles() {
            const particlesContainer = document.getElementById('particles');
            const particleCount = 80;
            
            for (let i = 0; i < particleCount; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                
                const rand = Math.random();
                if (rand < 0.3) {
                    particle.classList.add('warm');
                } else if (rand < 0.5) {
                    particle.classList.add('cool');
                }
                
                particle.style.left = Math.random() * 100 + '%';
                particle.style.top = Math.random() * 100 + '%';
                particle.style.width = Math.random() * 5 + 2 + 'px';
                particle.style.height = particle.style.width;
                particle.style.animationDelay = Math.random() * 6 + 's';
                particle.style.animationDuration = (Math.random() * 4 + 4) + 's';
                particlesContainer.appendChild(particle);
            }
        }

        // Update UI based on status
        function updateUI(status) {
            const buddyOrb = document.getElementById('buddyorb');
            const statusIndicator = document.getElementById('status');
            const micBtn = document.getElementById('micBtn');

            // Remove all status classes
            buddyOrb.classList.remove('listening', 'speaking', 'processing');
            statusIndicator.className = 'top-status';

            if (!status.mic_active) {
                micBtn.classList.add('mic-muted');
                micBtn.textContent = '🚫';
                micBtn.title = 'Microphone Muted - Click to Activate';
                statusIndicator.textContent = 'MUTED';
                statusIndicator.classList.add('status-muted');
            } else {
                micBtn.classList.remove('mic-muted');
                micBtn.textContent = '🎤';
                micBtn.title = 'Microphone Active - Click to Mute';

                if (status.listening) {
                    buddyOrb.classList.add('listening');
                    statusIndicator.textContent = 'LISTENING...';
                    statusIndicator.classList.add('status-listening');
                } else if (status.processing) {
                    buddyOrb.classList.add('processing');
                    statusIndicator.textContent = 'PROCESSING...';
                    statusIndicator.classList.add('status-processing');
                } else if (status.speaking) {
                    buddyOrb.classList.add('speaking');
                    statusIndicator.textContent = 'SPEAKING...';
                    statusIndicator.classList.add('status-speaking');
                } else {
                    statusIndicator.textContent = status.standby ? 'STANDBY' : 'READY';
                }
            }
        }
        
        // Poll for status updates
        function pollStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(status => {
                    if (JSON.stringify(status) !== JSON.stringify(currentStatus)) {
                        currentStatus = status;
                        updateUI(status);
                    }
                })
                .catch(error => console.log('Status poll failed:', error));
        }

        // Control functions
        function toggleMic() {
            fetch('/control?action=toggle_mic')
                .then(response => response.json())
                .catch(error => console.log('Toggle mic failed:', error));
        }

        function activateVoice() {
            if (!currentStatus.mic_active) return;
            
            fetch('/control?action=activate')
                .then(response => response.json())
                .catch(error => console.log('Activate failed:', error));
        }

        // Event listeners
        document.getElementById('micBtn').addEventListener('click', toggleMic);
        document.getElementById('buddyorb').addEventListener('click', activateVoice);
        
        document.getElementById('infoBtn').addEventListener('click', () => {
            alert('BUDDY - Your Friendly Voice Assistant\\n\\nConnected to Python backend\\nSay "Hey Buddy" to activate voice commands\\n\\nClick the orb or press Space to activate manually');
        });

        document.getElementById('settingsBtn').addEventListener('click', () => {
            alert('Settings panel would open here\\n(Enhanced settings UI can be added)');
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && e.target === document.body) {
                e.preventDefault();
                activateVoice();
            } else if (e.code === 'KeyM') {
                toggleMic();
            }
        });

        // Initialize
        createParticles();
        pollStatus();
        setInterval(pollStatus, 500); // Poll every 500ms for real-time updates

        console.log('Buddy Web Interface Loaded - Connected to Python Backend');
    </script>
</body>
</html>'''

    def log_message(self, format, *args):
        """Suppress HTTP request logging"""
        pass

def simulate_voice_command():
    """Simulate voice activation for testing"""
    if not buddy_state.is_mic_active:
        return
    
    buddy_state.set_listening(True)
    time.sleep(2)  # Simulate listening time
    buddy_state.set_speaking(True) 
    time.sleep(3)  # Simulate speaking time
    buddy_state.set_standby()

def start_web_server():
    """Start the web server for the HTML interface"""
    try:
        with socketserver.TCPServer(("", PORT), BuddyHandler) as httpd:
            buddy_state.server_running = True
            print(f"Buddy web interface running at http://localhost:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Failed to start web server: {e}")

# ---------- TTS helpers ----------
def speak(text):
    buddy_state.set_speaking(True)
    try:
        tts = gTTS(text)
        temp_file = tempfile.mktemp(suffix='.mp3')
        tts.save(temp_file)
        pygame.mixer.init()
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        os.remove(temp_file)
    except Exception as e:
        print(f"TTS Error: {e}")
    finally:
        buddy_state.set_standby()

# ---------- AI ----------
def aiProcess(command):
    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"
    )
    completion = client.chat.completions.create(
        model="llama3.1",
        messages=[
            {"role": "system", "content": "You are a virtual assistant named Buddy. Give short, helpful, and friendly answers."},
            {"role": "user", "content": command}
        ])
    return completion.choices[0].message.content

# ---------- POWER ----------
def power_action(action: str):
    action = action.lower()
    if action == "shutdown":
        subprocess.run(["shutdown", "/s", "/t", "0"])
    elif action == "restart":
        subprocess.run(["shutdown", "/r", "/t", "0"])
    elif action == "sleep":
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])

# ---------- APP LAUNCHER ----------
def open_app(app_name: str):
    app_name = app_name.strip()
    exe_path = shutil.which(app_name) or shutil.which(app_name + ".exe")
    if exe_path:
        subprocess.Popen([exe_path])
    else:
        subprocess.Popen(["start", "", app_name], shell=True)

# ---------- WEATHER ----------
def get_weather():
    try:
        g = geocoder.ip('me')
        lat, lon = g.latlng
        url = (f"https://api.open-meteo.com/v1/forecast"
               f"?latitude={lat}&longitude={lon}"
               f"&current_weather=true"
               f"&hourly=temperature_2m,relativehumidity_2m,windspeed_10m,winddirection_10m,weathercode"
               f"&forecast_days=1")
        data = requests.get(url, timeout=6).json()
        cw = data["current_weather"]
        temp = cw["temperature"]
        wind = cw["windspeed"]
        wind_dir = cw["winddirection"]
        wmo = {0:"clear", 1:"mainly clear", 2:"partly cloudy", 3:"overcast",
               45:"foggy", 48:"depositing rime fog", 51:"light drizzle",
               53:"moderate drizzle", 55:"heavy drizzle", 61:"slight rain",
               63:"moderate rain", 65:"heavy rain", 71:"slight snow",
               73:"moderate snow", 75:"heavy snow"}
        desc = wmo.get(cw["weathercode"], "unknown")
        next_temps = ", ".join(map(str, [round(v) for v in data["hourly"]["temperature_2m"][:3]]))
        humidity = data["hourly"]["relativehumidity_2m"][0]
        speak(f"Currently {temp}°C and {desc}. Humidity {humidity}%. Wind {wind} km/h from {wind_dir}°. Next 3-hour temps: {next_temps}°C.")
    except Exception:
        speak("Sorry, I could not fetch the weather right now.")

# ---------- NOTES ----------
def note_to_file(text, filename="buddy_note.txt"):
    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
    path = os.path.join(desktop, filename)
    with open(path, "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        f.write(f"{timestamp} - {text}\n")
    speak(f"Saved to {filename} on the desktop")

# ---------- WIKI ----------
def wiki_summary(topic):
    try:
        summary = wikipedia.summary(topic, sentences=2)
        speak(summary)
    except Exception:
        speak("I could not find any information on that topic.")

# ---------- CALCULATOR ----------
def calculate(expr):
    try:
        expr = re.sub(r'\bmultiplied by\b|\btimes\b', '*', expr, flags=re.I)
        expr = re.sub(r'\bdivided by\b', '/', expr, flags=re.I)
        expr = re.sub(r'\bplus\b', '+', expr, flags=re.I)
        expr = re.sub(r'\bminus\b', '-', expr, flags=re.I)
        tokens = re.findall(r'\w+|\S', expr)
        converted = []
        for tok in tokens:
            try:
                converted.append(str(word2number.w2n(tok)))
            except:
                converted.append(tok)
        expr = ''.join(converted)
        expr = re.sub(r'[^0-9+\-*/(). ]', '', expr)
        result = eval(expr)
        speak(f"The result is {result}")
    except Exception:
        speak("I could not evaluate that expression.")

def play_on_youtube(query):
    original_query = query.strip()
    encoded_query = urllib.parse.quote_plus(query)
    url = f"https://duckduckgo.com/?q=!ducky+site:youtube.com+{encoded_query}&kp=-1&kl=us-en&ia=web"
    webbrowser.open(url)
    speak(f"Playing {original_query} on YouTube.")

def set_volume(level):
    level = max(0, min(100, level))
    volume.SetMasterVolumeLevelScalar(level / 100.0, None)
    speak(f"Volume set to {level} percent")

def change_volume(delta):
    current = int(volume.GetMasterVolumeLevelScalar() * 100)
    new_level = max(0, min(100, current + delta))
    set_volume(new_level)

def take_screenshot():
    path = os.path.join(os.environ["USERPROFILE"], "Desktop", f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    pyautogui.screenshot(path)
    speak("Screenshot saved to desktop")

def tell_time():
    now = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"It is {now}")

def alarm_worker():
    while True:
        now = datetime.datetime.now().time().replace(second=0, microsecond=0)
        for t, event in list(ALARMS.items()):
            if now == t and not event.is_set():
                speak("Alarm! Alarm!")
                while not event.is_set():
                    winsound.Beep(1000, 1000)
                    time.sleep(2)
            elif event.is_set():
                ALARMS.pop(t, None)
        time.sleep(30)

threading.Thread(target=alarm_worker, daemon=True).start()

def set_alarm(time_str):
    time_str = time_str.strip().lower().replace("o'clock", "").replace("oclock", "")
    for fmt in ["%I %M %p", "%I:%M %p", "%I%p", "%H %M", "%H:%M", "%H"]:
        try:
            t = datetime.datetime.strptime(time_str, fmt).time()
            ALARMS[t] = threading.Event()
            speak(f"Alarm set for {t.strftime('%I:%M %p')}")
            return
        except ValueError:
            continue
    speak("I didn't understand the time. Try 7 30 pm or 19 30")

def stop_alarm():
    for ev in ALARMS.values():
        ev.set()
    ALARMS.clear()
    speak("Alarm stopped")

WAKE_WORDS = ["buddy", "hey buddy", "ok buddy", "hello buddy"]

def processCommand(c):
    # Set processing state before doing any work
    buddy_state.set_processing()
    
    c_low = c.lower().strip()
    if c_low.startswith("open google"):
        webbrowser.open("https://google.com")
        speak("Opening Google")
    elif c_low.startswith("open facebook"):
        webbrowser.open("https://facebook.com")
        speak("Opening Facebook")
    elif c_low.startswith("open youtube"):
        webbrowser.open("https://youtube.com")
        speak("Opening YouTube")
    elif c_low.startswith("open linkedin"):
        webbrowser.open("https://linkedin.com")
        speak("Opening LinkedIn")
    elif c_low.startswith("open instagram"):
        webbrowser.open("https://www.instagram.com")
        speak("Opening Instagram")
    elif c_low.startswith("open twitter") or c_low.startswith("open x"):
        webbrowser.open("https://x.com")
        speak("Opening X")

    elif c_low.startswith("play"):
        play_on_youtube(c[5:].strip())

    elif "news" in c_low:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={newsapi}"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            articles = r.json().get("articles", [])
            headlines = [a["title"] for a in articles[:5] if a.get("title")]
            speak("Here are the top news headlines:")
            for h in headlines:
                speak(h)
        else:
            speak("News service returned an error.")

    elif any(x in c_low for x in ["shutdown", "restart", "sleep"]):
        action = c_low.split()[-1]
        power_action(action)
        speak(f"Okay, {action} in 3 seconds.")

    elif c_low.startswith("set volume"):
        match = re.search(r"\d+", c_low)
        if match:
            lvl = int(match.group())
            set_volume(lvl)
    elif c_low.startswith("volume up"):
        match = re.search(r"\d+", c_low)
        step = int(match.group()) if match else 10
        change_volume(+step)
    elif c_low.startswith("volume down"):
        match = re.search(r"\d+", c_low)
        step = int(match.group()) if match else 10
        change_volume(-step)

    elif re.search(r"\bweather\b", c_low):
        get_weather()

    elif "screenshot" in c_low:
        take_screenshot()

    elif any(p in c_low for p in ["write this down", "add to my notes", "jot down", "save a note", "set a reminder"]):
        for p in ["write this down", "add to my notes", "jot down", "save a note", "set a reminder"]:
            if p in c_low:
                content = c.split(p, 1)[-1].strip()
                break
        if content:
            note_to_file(content)
        else:
            speak("I didn't catch what to write.")

    elif "what time is it" in c_low:
        tell_time()
    elif "what date is today" in c_low or "today's date" in c_low:
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        speak(f"Today is {today}")

    elif c_low.startswith("set alarm"):
        time_str = re.sub(r"^set alarm(?:\s+for)?\s*", "", c, flags=re.I).strip()
        set_alarm(time_str)

    elif "stop alarm" in c_low:
        stop_alarm()

    elif c_low.startswith("open app"):
        app = re.sub(r"^open app\s*", "", c, flags=re.I).strip()
        open_app(app)
        speak(f"Opening {app}")

    elif c_low.startswith("tell me something about"):
        topic = re.sub(r"^tell me something about\s*", "", c, flags=re.I).strip()
        if topic:
            wiki_summary(topic)

    elif c_low.startswith("calculate") or c_low.startswith("math"):
        expr = re.sub(r"^(calculate|math)\s*", "", c, flags=re.I).strip()
        calculate(expr)

    else:
        output = aiProcess(c)
        speak(output)

def voice_recognition_loop():
    """Main voice recognition loop running in background"""
    while True:
        if not buddy_state.is_mic_active:
            time.sleep(0.5)
            continue
            
        try:
            with sr.Microphone() as source:
                print("Listening for wake-word…")
                buddy_state.set_standby()
                audio = recognizer.listen(source, timeout=2, phrase_time_limit=1.5)
                word = recognizer.recognize_google(audio)
                print("Heard:", word)
                
                if any(w in word.lower() for w in WAKE_WORDS):
                    speak("Hey there, I'm listening!")
                    buddy_state.set_listening(True)
                    
                    with sr.Microphone() as source:
                        print("Buddy active...")
                        try:
                            audio = recognizer.listen(source, timeout=4, phrase_time_limit=4)
                            command = recognizer.recognize_google(audio)
                            print(f"Command: {command}")
                            processCommand(command)
                        except sr.WaitTimeoutError:
                            speak("I didn't hear anything. Try again.")
                        except sr.UnknownValueError:
                            speak("I didn't understand. Please repeat.")
                        
        except sr.WaitTimeoutError:
            continue
        except Exception as e:
            print("Voice recognition error:", e)
            time.sleep(1)

def cleanup():
    """Cleanup function to remove temporary files"""
    try:
        if os.path.exists(buddy_state.status_file):
            os.remove(buddy_state.status_file)
    except:
        pass

atexit.register(cleanup)

if __name__ == "__main__":
    print("Starting Buddy Voice Assistant...")
    server_thread = threading.Thread(target=start_web_server, daemon=True)
    server_thread.start()
    time.sleep(1)
    try:
        webbrowser.open(f"http://localhost:{PORT}")
        print(f"Opening Buddy interface at http://localhost:{PORT}")
    except Exception as e:
        print(f"Failed to open browser: {e}")
    speak("Hey there! Buddy is online and ready to help!")
    try:
        voice_recognition_loop()
    except KeyboardInterrupt:
        print("\nShutting down Buddy...")
        cleanup()
    except Exception as e:
        print(f"Fatal error: {e}")
        cleanup()