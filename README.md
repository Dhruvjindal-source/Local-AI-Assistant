# 🎙️ Buddy - Your Friendly Voice Assistant

A powerful, locally-hosted voice assistant with a beautiful web interface that brings AI capabilities to your desktop. Buddy combines speech recognition, natural language processing, and a stunning visual interface to create an interactive assistant experience.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## ✨ Features

### 🎯 Core Capabilities
- **Wake Word Activation**: Responds to "Hey Buddy" and similar phrases
- **Voice Recognition**: Advanced speech-to-text using Google Speech Recognition
- **AI-Powered Responses**: Integration with Ollama's LLaMA 3.1 for intelligent conversations
- **Natural Text-to-Speech**: High-quality voice synthesis using gTTS

### 🌐 Web Interface
- **Real-Time Status Updates**: Live visualization of listening, processing, and speaking states
- **Interactive Orb Animation**: Dynamic visual feedback with state-specific animations
- **Responsive Design**: Beautiful gradient backgrounds with floating particles
- **Manual Controls**: Click-to-activate and microphone toggle buttons

### 🛠️ Functionality
- **Web Navigation**: Open Google, YouTube, Facebook, LinkedIn, Instagram, Twitter/X
- **Media Control**: Play YouTube videos via voice command
- **System Control**: Shutdown, restart, sleep commands
- **Volume Management**: Set, increase, or decrease system volume
- **Weather Reports**: Real-time weather with humidity and wind information
- **News Updates**: Latest headlines from NewsAPI
- **Wikipedia Integration**: Quick information lookup
- **Calculator**: Natural language math expressions
- **Note Taking**: Voice-to-text note saving on desktop
- **Alarms**: Set and manage voice-activated alarms
- **Screenshots**: Capture screen on command
- **Time & Date**: Quick time and date queries
- **App Launcher**: Open applications by voice

## 📋 Prerequisites

- Python 3.8 or higher
- Microphone for voice input
- Internet connection for AI and web features
- Windows OS (for some system control features)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/buddy-voice-assistant.git
cd buddy-voice-assistant
```

### 2. Install Required Packages
```bash
pip install speechrecognition
pip install pyttsx3
pip install gtts
pip install pygame
pip install requests
pip install openai
pip install wikipedia
pip install geocoder
pip install word2number
pip install pyautogui
pip install pycaw
pip install comtypes
pip install pywin32
```

### 3. Set Up Ollama
1. Install [Ollama](https://ollama.ai/)
2. Pull the LLaMA model:
```bash
ollama pull llama3.1
```
3. Start Ollama server:
```bash
ollama serve
```

### 4. Configure API Keys
Edit the configuration section in the code:
```python
newsapi = "YOUR_NEWSAPI_KEY_HERE"  # Get from https://newsapi.org/
PORT = 8080  # Web interface port
```

## 🎮 Usage

### Starting Buddy
```bash
python buddy.py
```

The web interface will automatically open at `http://localhost:8080`

### Voice Commands

#### Web Navigation
- "Open Google"
- "Open YouTube"
- "Open Facebook/LinkedIn/Instagram"

#### Media
- "Play [song/video name] on YouTube"

#### System Control
- "Shutdown/Restart/Sleep"
- "Set volume to 50"
- "Volume up/down"
- "Take a screenshot"

#### Information
- "What's the weather?"
- "Tell me the news"
- "What time is it?"
- "What date is today?"
- "Tell me something about [topic]"

#### Productivity
- "Write this down [your note]"
- "Set alarm for 7:30 PM"
- "Stop alarm"
- "Calculate 25 times 4 plus 10"

#### General AI Chat
Ask Buddy anything! It uses LLaMA 3.1 for natural conversation.

## 🎨 Web Interface Features

### Status Indicators
- **🟠 Orange Pulse**: Listening for commands
- **🔴 Pink Spin**: Processing your request
- **🟢 Green Wave**: Speaking response
- **⚪ Standby**: Ready and waiting

### Controls
- **🎤 Microphone Button**: Toggle voice input on/off
- **⚙️ Settings**: Access configuration (expandable)
- **ℹ️ Info**: View help and keyboard shortcuts

### Keyboard Shortcuts
- **Space**: Activate voice recognition
- **M**: Toggle microphone

## 🏗️ Architecture

### Core Components
```
buddy.py
├── BuddyState: Global state management
├── BuddyHandler: HTTP server for web interface
├── Voice Recognition Loop: Continuous listening
├── Command Processing: Intent detection and execution
└── TTS Engine: Response generation
```

### Technology Stack
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python 3.8+
- **AI Model**: Ollama LLaMA 3.1
- **Speech Recognition**: Google Speech Recognition
- **TTS**: Google Text-to-Speech (gTTS)
- **Audio**: PyGame mixer
- **System Integration**: PyAutoGUI, PyCaw

## 🔧 Configuration

### Adjusting Wake Word Sensitivity
```python
recognizer.energy_threshold = 300  # Increase for noisy environments
```

### Customizing Wake Words
```python
WAKE_WORDS = ["buddy", "hey buddy", "ok buddy", "hello buddy"]
# Add your own wake words here
```

### Changing Port
```python
PORT = 8080  # Change to your preferred port
```

## 🐛 Troubleshooting

### Microphone Not Working
- Check system microphone permissions
- Verify microphone is set as default input device
- Adjust `energy_threshold` in code

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve`
- Verify model is installed: `ollama list`
- Check port 11434 is not blocked

### Web Interface Not Loading
- Verify port 8080 is available
- Check firewall settings
- Try accessing `http://127.0.0.1:8080`

### Voice Recognition Errors
- Ensure internet connection (uses Google Speech API)
- Speak clearly and reduce background noise
- Check microphone quality

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- OpenAI for inspiring AI assistant development
- Ollama team for local LLM capabilities
- Google for Speech Recognition and TTS services
- The open-source community for amazing Python libraries

## 📧 Contact

Your Name - [@JindalDhru71462](https://x.com/JindalDhru71462)

Project Link: [https://github.com/DhruvJindal-source/buddy-voice-assistant](https://github.com/DhruvJindal-source/buddy-voice-assistant)

## 🗺️ Roadmap

- [ ] Multi-language support
- [ ] Custom wake word training
- [ ] Mobile app integration
- [ ] Plugin system for extensions
- [ ] Voice profile customization
- [ ] Offline mode support
- [ ] Cross-platform compatibility (macOS, Linux)

---

**Made with ❤️ by Dhruv**

*Say "Hey Buddy" and start your journey with your personal voice assistant!*
