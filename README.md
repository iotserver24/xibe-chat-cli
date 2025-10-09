# AI CLI

AI-powered terminal assistant for text and image generation.

## Features

- **Interactive Chat Interface**: Gemini-style splash screen with beautiful ASCII art
- **Real Text Generation**: Send prompts and receive AI responses
- **Real Image Generation**: Generate images with `img:` prefix
- **Multi-line Input Support**: Type multi-line messages with proper formatting
- **Enhanced Markdown Rendering**: Improved display of bold text, links, lists, and blockquotes
- **Token Authentication**: Support for API tokens for better rate limits
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Direct API Integration**: Uses REST APIs for AI services

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. **Set up API Token (Recommended):**
   - Copy the example file: `cp .env.example .env`
   - Edit `.env` file and replace `your_token_here` with your actual API token
   - This provides better rate limits and access to advanced features

3. Run the application:
```bash
python ai_cli.py
```

## Usage

1. **Splash Screen**: Welcome screen displays automatically
2. **Model Selection**: Choose your preferred AI models for text and image generation
3. **Text Generation**: Simply type your prompt and press Enter
4. **Multi-line Input**: Press Ctrl+J for new lines, Enter to send message
5. **Image Generation**: Type `img:` followed by your prompt (e.g., `img: a beautiful sunset`)
6. **View Models**: Type `models` to see available AI models
7. **Switch Models**: Type `switch` to change AI models during the chat
8. **New Chat**: Type `/new` to start fresh (clears conversation history)
9. **Exit**: Type `exit` or `quit` to end the session

### Special Commands

- **`models`** - Show available AI models for text and image generation (fetched live from API)
- **`switch`** - Change your selected AI models during the chat session
- **`/new`** - Start a new chat session (clears conversation history)
- **`img: prompt`** - Generate images with the specified prompt
- **`exit` / `quit`** - End the chat session

### Important Notes

- **Models Change Daily**: Available models are fetched live from the API, so they may change frequently
- **nanobanana Model**: This image model requires an input image for editing - it's not for text-to-image generation
- **Model Discovery**: Use the `models` command to see what's currently available

### Authentication

The app supports both anonymous and authenticated access:

- **Anonymous**: Works immediately without any setup
- **Authenticated**: Set your token in the `.env` file for:
  - Higher rate limits (5 seconds vs 15 seconds)
  - Access to advanced models
  - Priority support

## Examples

```
You: Tell me about artificial intelligence
AI Response: [Panel with improved markdown rendering showing bold text, links, and lists]

You: Write a paragraph with different formatting
[Ctrl+J for new line]
with **bold text** and [links](https://example.com)
[Enter to send]
AI Response: [Properly rendered markdown with bold text and clickable links]

You: img: a beautiful sunset
Image Generated: [Success message and image opens automatically]

You: img: a futuristic city skyline at night with neon lights
Image Generated: [Another image opens with the new prompt]

You: exit
Goodbye! 👋
```

## Dependencies

- `pyfiglet`: For ASCII art logo
- `rich`: For beautiful terminal formatting and colors
- `requests`: For HTTP API calls to AI services
- `prompt-toolkit`: For advanced multi-line input with keyboard shortcuts

## Technical Details

- **Text Generation**: Uses AI service REST API
- **Image Generation**: Uses AI service REST API (1024x1024px)
- **Authentication**: Supports both anonymous and token-based access
- **Rate Limits**: Anonymous (15s), Authenticated (5s)
- **Error Handling**: Robust error handling with user-friendly messages
- **File Management**: Images saved to `generated_images/` directory with unique filenames

## Configuration

Edit the `.env` file to set your API token for authenticated access:
```bash
# .env file
API_TOKEN=your_actual_token_here
```

You can also optionally customize models and API endpoints:
```bash
# .env file
# Choose different AI models
TEXT_MODEL=mistral              # Options: openai, mistral, claude-hybridspace, etc.
IMAGE_MODEL=kontext             # Options: flux, kontext, etc.

# Custom API endpoints
TEXT_API_URL=https://your-custom-text-api.com
IMAGE_API_URL=https://your-custom-image-api.com/prompt
```

## Note

This application uses AI service REST APIs for real text and image generation. Anonymous access is supported, but setting up an API token provides better rate limits and access to advanced features.
