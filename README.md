# XIBE-CHAT CLI 🚀

> AI-powered terminal assistant for text and image generation

[![PyPI version](https://badge.fury.io/py/xibe-chat-cli.svg)](https://badge.fury.io/py/xibe-chat-cli)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A beautiful, feature-rich CLI application that brings AI text and image generation directly to your terminal. Built with Python and featuring a rich interface powered by Rich library.

## ✨ Features

### 🤖 AI Text Generation
- **Multiple AI Models**: Choose from various text generation models
- **Conversation Memory**: Maintains context across multiple exchanges
- **Rich Formatting**: Beautiful markdown rendering with syntax highlighting
- **Model Switching**: Change models on the fly without losing chat history

### 🖼️ AI Image Generation
- **Enhanced Prompts**: AI automatically improves your prompts for better results
- **Multiple Models**: Support for flux, kontext, turbo, nanobanana, and more
- **High Quality**: 1024x1024 resolution with safety filtering
- **Private Generation**: Images not shared in public feeds

### 💾 Smart Memory System
- **Model Preferences**: Remembers your preferred AI models
- **Auto-Load**: Uses saved preferences on startup
- **Easy Reset**: Reset preferences anytime with `/reset`

### 🎨 Beautiful Interface
- **Rich Terminal UI**: Beautiful ASCII art logo and colorful interface
- **Multi-line Input**: Support for multi-line messages with `Ctrl+N`
- **Command System**: Intuitive slash commands for all features
- **Cross-Platform**: Works on Windows, macOS, and Linux

## 🚀 Quick Start

### Installation

**Via pip (recommended):**
```bash
pip install xibe-chat-cli
```

**Run the CLI:**
```bash
xibe-chat
# or use the short alias
xibe
```

### One-line Install Script
```bash
# Download and run installer
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/iotserver24/xibe-chat-cli/main/install.py').read())"
```

## 📖 Usage

### Basic Commands

```bash
# Start the CLI
xibe-chat

# Chat with AI
You: Hello! How are you?

# Generate images
You: img: a beautiful sunset over mountains

# Get help
You: /help
```

### Available Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands and usage |
| `/clear` | Clear terminal and show logo |
| `/new` | Start a new chat session |
| `/reset` | Reset saved model preferences |
| `/image-settings` | View image generation settings |
| `models` | Show available AI models |
| `switch` | Change AI models |
| `exit/quit` | End the session |

### Input Methods

- **Normal Text**: Just type and press Enter
- **Multi-line**: Press `Ctrl+N` for new lines, Enter to send
- **Image Generation**: Prefix with `img:` (e.g., `img: cute cat`)

## ⚙️ Configuration

### API Token (Optional but Recommended)

Set your API token for better rate limits and premium features:

```bash
# Windows
set API_TOKEN=your_token_here

# macOS/Linux
export API_TOKEN=your_token_here
```

### Model Preferences

Your preferred models are automatically saved in `xibe_chat_config.json`:

```json
{
  "text_model": "mistral",
  "image_model": "flux",
  "last_updated": "2024-01-15T10:30:45.123456"
}
```

## 🖼️ Image Generation Features

### Enhanced API Parameters
- **Enhance**: AI improves your prompts automatically
- **Safe Mode**: Strict NSFW filtering enabled
- **Private**: Images not shared publicly
- **High Quality**: 1024x1024 resolution
- **No Watermarks**: Clean images (with API token)

### Available Models
- **flux**: High-quality general purpose
- **kontext**: Image-to-image editing
- **turbo**: Fast generation
- **nanobanana**: Advanced image editing
- **gptimage**: GPT-powered generation

## 🔧 Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/iotserver24/xibe-chat-cli.git
cd xibe-chat-cli

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Building from Source

```bash
# Build package
python -m build

# Install locally
pip install dist/xibe_chat_cli-1.0.0-py3-none-any.whl
```

### Creating Executables

```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --name xibe-chat xibe_chat.py
```

## 📦 Requirements

- Python 3.8+
- pyfiglet
- python-dotenv
- requests
- rich
- prompt-toolkit

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Pollinations AI](https://pollinations.ai) for the amazing AI API
- [Rich](https://github.com/Textualize/rich) for the beautiful terminal interface
- [Prompt Toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for advanced input handling

## 📞 Support

- 📧 Email: your-email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/iotserver24/xibe-chat-cli/issues)
- 📖 Documentation: [GitHub Repository](https://github.com/iotserver24/xibe-chat-cli)

---

**Made with ❤️ by iotserver24**

*Star this repository if you find it helpful!*