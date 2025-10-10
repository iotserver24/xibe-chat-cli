# XIBE-CHAT CLI 🚀

> AI-powered terminal assistant for text and image generation

[![PyPI version](https://badge.fury.io/py/xibe-chat-cli.svg)](https://badge.fury.io/py/xibe-chat-cli)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](https://pypi.org/project/xibe-chat-cli/)

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
- **Premium Features**: No watermarks, NO rate limits!

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

### 🎯 No Setup Required!

XIBE-CHAT CLI comes pre-configured with premium API access:

- ✅ **No Watermarks**: Clean images without logos
- ✅ **Enhanced Rate Limits**: Higher usage limits for better performance
- ✅ **Private Generation**: Your images stay private

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
- **No Watermarks**: Clean images included

### Available Models
- **flux**: High-quality general purpose
- **kontext**: Image-to-image editing
- **turbo**: Fast generation
- **nanobanana**: Advanced image editing
- **gptimage**: GPT-powered generation

## 🔧 Technical Details

### Package Information
- **Package**: xibe-chat-cli
- **Version**: 0.5.3
- **PyPI**: [https://pypi.org/project/xibe-chat-cli/](https://pypi.org/project/xibe-chat-cli/)
- **License**: Proprietary
- **Author**: iotserver24

### System Requirements
- Python 3.8+
- Windows, macOS, or Linux
- Internet connection for AI services

## 📦 Requirements

- Python 3.8+
- pyfiglet
- python-dotenv
- requests
- rich
- prompt-toolkit

## 📞 Support & Contact

For support, feature requests, or questions:
- 📧 Email: iotserver24@gmail.com
- 🐛 Issues: Contact via email
- 💬 Feedback: We welcome your suggestions

## 📄 License

This is proprietary software. All rights reserved.

## 🙏 Acknowledgments

- [Pollinations AI](https://pollinations.ai) for the amazing AI API
- [Rich](https://github.com/Textualize/rich) for the beautiful terminal interface
- [Prompt Toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) for advanced input handling

## 📞 Additional Support

- 📖 PyPI Package: [https://pypi.org/project/xibe-chat-cli/](https://pypi.org/project/xibe-chat-cli/)
- 🔄 Updates: `pip install --upgrade xibe-chat-cli`

---

**Made with ❤️ by iotserver24**

*Star this repository if you find it helpful!*