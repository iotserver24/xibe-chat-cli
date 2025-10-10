#!/usr/bin/env python3
"""
XIBE-CHAT CLI - AI-powered terminal assistant for text and image generation
"""

import os
import platform
import subprocess
import urllib.parse
import re
import json
from pathlib import Path
from datetime import datetime

try:
    import pyfiglet
except ImportError:
    print("Error: pyfiglet is required. Install it with: pip install pyfiglet")
    exit(1)

try:
    from dotenv import load_dotenv
    # Load environment variables from .env file
    # First try current directory, then package directory
    if os.path.exists('.env'):
        load_dotenv('.env')
    else:
        # Try to find .env in the package directory
        package_dir = Path(__file__).parent
        env_path = package_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()  # Fallback to default behavior
except ImportError:
    print("Error: python-dotenv is required. Install it with: pip install python-dotenv")
    exit(1)

import requests
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown


# Initialize Rich console
console = Console()

# Configuration file path
CONFIG_FILE = Path("xibe_chat_config.json")


def save_model_preferences(text_model: str, image_model: str) -> None:
    """Save the selected models to configuration file."""
    try:
        config = {
            "text_model": text_model,
            "image_model": image_model,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
            
    except Exception as e:
        console.print(f"[dim]Could not save model preferences: {e}[/dim]")


def load_model_preferences() -> dict:
    """Load the saved model preferences from configuration file."""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                
            # Validate that both models are present
            if "text_model" in config and "image_model" in config:
                return {
                    "text": config["text_model"],
                    "image": config["image_model"]
                }
    except Exception as e:
        console.print(f"[dim]Could not load model preferences: {e}[/dim]")
    
    # Return None if no valid config found
    return None


def get_multiline_input() -> str:
    """Get multi-line input from user with Enter to send, Ctrl+N for new lines."""
    try:
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.shortcuts import prompt as ptk_prompt
        from prompt_toolkit.styles import Style
        
        # Create key bindings
        kb = KeyBindings()
        
        @kb.add('enter')
        def _(event):
            """Enter key sends the message."""
            event.app.exit(result=event.app.current_buffer.text)
        
        @kb.add('c-n')  # Ctrl+N for new line
        def _(event):
            """Ctrl+N creates a new line."""
            event.current_buffer.insert_text('\n')
        
        # Define the style for the prompt
        style = Style.from_dict({
            'prompt': 'ansiblue bold',
        })
        
        # Get input with custom key bindings and styling
        text = ptk_prompt(
            [('class:prompt', 'You: ')],
            multiline=True,
            key_bindings=kb,
            style=style,
            mouse_support=True
        )
        
        return text.strip() if text else ""
        
    except ImportError:
        # Fallback to simple input if prompt_toolkit is not available
        console.print("[yellow]For better multi-line input, install prompt-toolkit: pip install prompt-toolkit[/yellow]")
        console.print("[yellow]Using simple input mode (type 'END' to finish multi-line input)[/yellow]")
        
        lines = []
        console.print("[blue]You:[/blue] ", end="")
        
        while True:
            try:
                line = input()
                if line.strip() == "END" and len(lines) > 0:
                    break
                lines.append(line)
                if len(lines) == 1 and not line.strip():
                    return ""
            except (KeyboardInterrupt, EOFError):
                return ""
        
        full_input = "\n".join(lines).strip()
        return full_input


def get_api_token() -> str:
    """Get the API token from environment variable."""
    token = os.getenv('API_TOKEN')
    if not token:
        console.print("[yellow]No API_TOKEN environment variable found.[/yellow]")
        console.print("[yellow]For better rate limits, set your token:[/yellow]")
        console.print("[dim]export API_TOKEN=your_token_here[/dim]")
        console.print()
        token = ""  # Use empty string for anonymous access
    return token


def main() -> None:
    """Main function to run the AI CLI application."""
    show_splash_screen()
    run_chat_interface()


def show_splash_screen() -> None:
    """Display the AI CLI splash screen."""
    # Clear the screen for a clean start
    console.clear()

    # Create ASCII art logo using pyfiglet
    logo_text = pyfiglet.figlet_format("XIBE-CHAT CLI", font="slant")
    logo = Text(logo_text, style="bold cyan")

    # Create subtitle panel
    subtitle = Panel(
        "[italic]AI-powered terminal assistant | Text & Image generation[/italic]",
        style="blue",
        title="[bold blue]Welcome[/bold blue]",
        title_align="center",
        padding=(1, 2)
    )

    # Display the splash screen
    console.print(logo, justify="center")
    console.print(subtitle, justify="center")
    console.print()  # Just add some space, no "Press Enter" prompt


def show_clear_screen(selected_models: dict) -> None:
    """Clear terminal and display logo with current commands and models."""
    # Clear the screen completely
    console.clear()
    
    # Show the logo
    logo_text = pyfiglet.figlet_format("XIBE-CHAT CLI", font="slant")
    logo = Text(logo_text, style="bold cyan")
    console.print(logo, justify="center")
    
    # Show current models and commands
    console.print("[green]XIBE-CHAT CLI Interface[/green]")
    console.print(f"[dim]Using Text Model: {selected_models['text']}[/dim]")
    console.print(f"[dim]Using Image Model: {selected_models['image']}[/dim]")
    console.print()
    console.print("[bold blue]Available Commands:[/bold blue]")
    console.print("  [cyan]/help[/cyan] - Show all commands and their uses")
    console.print("  [cyan]/clear[/cyan] - Clear terminal and show this screen")
    console.print("  [cyan]/new[/cyan] - Start a new chat session")
    console.print("  [cyan]/reset[/cyan] - Reset saved model preferences")
    console.print("  [cyan]/image-settings[/cyan] - View image generation settings")
    console.print("  [cyan]models[/cyan] - Show available AI models")
    console.print("  [cyan]switch[/cyan] - Change AI models")
    console.print("  [cyan]exit/quit[/cyan] - End the session")
    console.print()
    console.print("[bold blue]Usage:[/bold blue]")
    console.print("  • Type your message normally for AI chat")
    console.print("  • Use [yellow]img:[/yellow] prefix for image generation")
    console.print("  • Press [yellow]Ctrl+N[/yellow] for new lines, [yellow]Enter[/yellow] to send")
    console.print()
    console.print("[blue]" + "="*50 + "[/blue]\n")


def show_help_commands() -> None:
    """Show detailed help information for all commands."""
    console.print("\n[bold blue]XIBE-CHAT CLI Help - All Commands & Usage[/bold blue]")
    console.print("=" * 60)
    
    # Chat Commands
    console.print("\n[bold green]💬 Chat Commands:[/bold green]")
    console.print("  [cyan]/help[/cyan]")
    console.print("    [dim]Shows this help screen with all available commands and usage[/dim]")
    console.print()
    console.print("  [cyan]/clear[/cyan]")
    console.print("    [dim]Clears the terminal screen and shows the logo with quick command reference[/dim]")
    console.print()
    console.print("  [cyan]/new[/cyan]")
    console.print("    [dim]Starts a fresh chat session (clears conversation history)[/dim]")
    console.print()
    console.print("  [cyan]/reset[/cyan]")
    console.print("    [dim]Resets saved model preferences - you'll choose models again next time[/dim]")
    console.print()
    console.print("  [cyan]/image-settings[/cyan]")
    console.print("    [dim]Shows current image generation settings and API parameters[/dim]")
    console.print()
    
    # Model Commands
    console.print("[bold green]🤖 Model Commands:[/bold green]")
    console.print("  [cyan]models[/cyan]")
    console.print("    [dim]Shows all available AI models for text and image generation[/dim]")
    console.print()
    console.print("  [cyan]switch[/cyan]")
    console.print("    [dim]Allows you to change your current text and image models[/dim]")
    console.print("    [dim]Preserves your chat history when switching models[/dim]")
    console.print()
    
    # Session Commands
    console.print("[bold green]🚪 Session Commands:[/bold green]")
    console.print("  [cyan]exit[/cyan] or [cyan]quit[/cyan]")
    console.print("    [dim]Ends the current AI CLI session[/dim]")
    console.print()
    
    # Input Methods
    console.print("[bold green]⌨️ Input Methods:[/bold green]")
    console.print("  [yellow]Normal Text Input[/yellow]")
    console.print("    [dim]Just type your message and press Enter to chat with AI[/dim]")
    console.print()
    console.print("  [yellow]img: prompt[/yellow]")
    console.print("    [dim]Generate images by prefixing your prompt with 'img:'[/dim]")
    console.print("    [dim]Example: img: a beautiful sunset over mountains[/dim]")
    console.print()
    console.print("  [yellow]Multiline Input[/yellow]")
    console.print("    [dim]Press Ctrl+N to create new lines within your message[/dim]")
    console.print("    [dim]Press Enter to send your complete multiline message[/dim]")
    console.print()
    
    # Tips
    console.print("[bold green]💡 Tips:[/bold green]")
    console.print("  • [dim]Models change daily - use 'models' to see current availability[/dim]")
    console.print("  • [dim]Free models (🆓) don't require API tokens[/dim]")
    console.print("  • [dim]Premium models (🔑) may require API tokens for better rate limits[/dim]")
    console.print("  • [dim]Conversation history is limited to last 10 exchanges to manage memory[/dim]")
    console.print("  • [dim]Generated images are saved in the 'generated_images' folder[/dim]")
    console.print()
    
    console.print("[blue]" + "="*60 + "[/blue]")
    console.print("[dim]Type any command or start chatting to continue![/dim]\n")


def show_image_settings() -> None:
    """Show current image generation settings and API parameters."""
    console.print("\n[bold blue]🖼️ Image Generation Settings[/bold blue]")
    console.print("=" * 50)
    
    console.print("\n[bold green]Current API Parameters:[/bold green]")
    console.print("  [cyan]Width:[/cyan] 1024 pixels")
    console.print("  [cyan]Height:[/cyan] 1024 pixels") 
    console.print("  [cyan]Seed:[/cyan] 42 (for reproducible results)")
    console.print("  [cyan]Enhance:[/cyan] true (LLM-enhanced prompts)")
    console.print("  [cyan]Safe:[/cyan] true (NSFW filtering)")
    console.print("  [cyan]Private:[/cyan] true (not in public feed)")
    
    console.print("\n[bold green]API Features:[/bold green]")
    console.print("  • [yellow]Enhanced Prompts[/yellow] - AI improves your prompts for better results")
    console.print("  • [yellow]Safe Mode[/yellow] - Strict content filtering enabled")
    console.print("  • [yellow]Private Generation[/yellow] - Images not shared publicly")
    console.print("  • [yellow]Consistent Results[/yellow] - Same seed for reproducible images")
    
    console.print("\n[bold green]Available Models:[/bold green]")
    console.print("  • [yellow]flux[/yellow] - High-quality general purpose")
    console.print("  • [yellow]kontext[/yellow] - Image-to-image editing")
    console.print("  • [yellow]turbo[/yellow] - Fast generation")
    console.print("  • [yellow]nanobanana[/yellow] - Advanced image editing")
    console.print("  • [yellow]gptimage[/yellow] - GPT-powered generation")
    
    console.print("\n[bold green]Usage:[/bold green]")
    console.print("  [cyan]img: your prompt here[/cyan]")
    console.print("  [dim]Example: img: a beautiful sunset over mountains[/dim]")
    
    console.print(f"\n[dim]API Endpoint: https://image.pollinations.ai/prompt/{{prompt}}[/dim]")
    console.print(f"[dim]Rate Limit: 1 concurrent request / 5 sec interval[/dim]")
    console.print()


def run_chat_interface() -> None:
    """Run the interactive chat interface."""
    # Get API token for authentication
    token = get_api_token()
    
    # Initialize conversation history
    conversation_history = []
    
    # Let user choose models (with memory)
    selected_models = choose_models_with_memory()
    
    # Save the selected models for future use
    save_model_preferences(selected_models['text'], selected_models['image'])

    console.print("[green]XIBE-CHAT CLI Interface[/green]")
    console.print(f"[dim]Using Text Model: {selected_models['text']}[/dim]")
    console.print(f"[dim]Using Image Model: {selected_models['image']}[/dim]")
    console.print("[yellow]Type 'exit' or 'quit' to end the session[/yellow]")
    console.print("[yellow]Use 'img:' prefix for image generation[/yellow]")
    console.print("[yellow]Type 'models' to see available AI models[/yellow]")
    console.print("[yellow]Type 'switch' to change AI models[/yellow]")
    console.print("[yellow]Type '/new' to start a new chat session[/yellow]")
    console.print("[yellow]Type '/clear' to clear terminal and show logo[/yellow]")
    console.print("[yellow]Type '/help' to see all commands and usage[/yellow]")
    console.print("[yellow]Type '/reset' to reset saved model preferences[/yellow]")
    console.print("[yellow]Type '/image-settings' to view image generation settings[/yellow]")
    console.print("[yellow]For multi-line input: press Ctrl+N for new lines, Enter to send message[/yellow]")
    console.print("[blue]" + "="*50 + "[/blue]\n")

    while True:
        try:
            # Get user input with multi-line support
            user_input = get_multiline_input()

            # Check for exit conditions
            if user_input.lower() in ['exit', 'quit']:
                console.print("[yellow]Goodbye! 👋[/yellow]")
                break

            # Check for special commands
            if user_input.lower() == 'models':
                show_available_models()
                continue
            elif user_input.lower() == 'switch':
                console.print("\n[bold blue]Switching AI Models[/bold blue]")
                selected_models = choose_models()
                # Save the new model preferences
                save_model_preferences(selected_models['text'], selected_models['image'])
                console.print(f"[green]✅ Switched to Text Model: {selected_models['text']}[/green]")
                console.print(f"[green]✅ Switched to Image Model: {selected_models['image']}[/green]")
                console.print(f"[dim]Chat history preserved with new models[/dim]")
                console.print(f"[dim]New preferences saved for future use[/dim]")
                console.print()
                continue
            elif user_input.lower() == '/new':
                console.print("\n[bold blue]Starting New Chat Session[/bold blue]")
                conversation_history.clear()
                console.print("[green]✅ Chat history cleared[/green]")
                console.print(f"[dim]Using Text Model: {selected_models['text']}[/dim]")
                console.print(f"[dim]Using Image Model: {selected_models['image']}[/dim]")
                console.print()
                continue
            elif user_input.lower() == '/clear':
                # Clear terminal and show logo with commands
                show_clear_screen(selected_models)
                continue
            elif user_input.lower() == '/help':
                show_help_commands()
                continue
            elif user_input.lower() == '/reset':
                console.print("\n[bold blue]Reset Model Preferences[/bold blue]")
                try:
                    if CONFIG_FILE.exists():
                        CONFIG_FILE.unlink()
                        console.print("[green]✅ Model preferences reset[/green]")
                        console.print("[yellow]You will be asked to choose models again next time[/yellow]")
                    else:
                        console.print("[yellow]No saved preferences found to reset[/yellow]")
                except Exception as e:
                    console.print(f"[red]Error resetting preferences: {e}[/red]")
                console.print()
                continue
            elif user_input.lower() == '/image-settings':
                show_image_settings()
                continue

            # Check if empty input
            if not user_input:
                continue

            # Handle image generation requests
            if user_input.startswith('img:'):
                image_prompt = user_input[4:].strip()  # Remove 'img:' prefix
                if image_prompt:
                    handle_image_generation(image_prompt, token, selected_models['image'])
                else:
                    console.print("[red]Please provide a prompt after 'img:'[/red]")
            else:
                # Handle text generation with conversation history
                handle_text_generation(user_input, token, conversation_history, selected_models['text'])

        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' or 'quit' to end the session[/yellow]")
        except EOFError:
            console.print("\n[yellow]Goodbye! 👋[/yellow]")
            break


def handle_text_generation(prompt: str, token: str = "", conversation_history: list = None, model: str = None) -> None:
    """Handle text generation request and display response."""
    if conversation_history is None:
        conversation_history = []
    if model is None:
        model = os.getenv('TEXT_MODEL', 'openai')
    
    with console.status(f"[bold green]AI ({model}) is thinking...[/bold green]"):
        response = generate_text(prompt, token, conversation_history, model)

    # Add to conversation history
    conversation_history.append({"role": "user", "content": prompt})
    conversation_history.append({"role": "assistant", "content": response})
    
    # Keep only last 10 exchanges to avoid token limits
    if len(conversation_history) > 20:  # 10 exchanges = 20 messages
        conversation_history = conversation_history[-20:]

    # Display AI response with improved markdown rendering
    console.print(f"[bold magenta]AI Response ({model}):[/bold magenta]")
    
    # Try to render as markdown with improved formatting
    try:
        # Clean up the response for better markdown rendering
        cleaned_response = clean_response_for_markdown(response, prompt)
        
        # Debug output removed for cleaner interface
        
        # Create a panel with the markdown content for better visual separation
        markdown = Markdown(cleaned_response, code_theme="monokai")
        
        # Wrap in a panel for better visual presentation
        response_panel = Panel(
            markdown,
            style="magenta",
            padding=(1, 2),
            border_style="magenta"
        )
        console.print(response_panel)
        
    except Exception as e:
        # Fallback to plain text if markdown parsing fails
        console.print(f"[dim]Markdown parsing failed: {e}[/dim]")
        console.print(Panel.fit(response, style="magenta", padding=(1, 2)))


def handle_image_generation(prompt: str, token: str = "", model: str = None) -> None:
    """Handle image generation request and open the image."""
    if model is None:
        model = os.getenv('IMAGE_MODEL', 'flux')
    
    with console.status(f"[bold green]Generating image with {model}...[/bold green]"):
        image_path = generate_image(prompt, token, model)

    if image_path:
        # Show success message
        success_panel = Panel(
            f"[green]Image generated successfully![/green]\n[blue]Model:[/blue] {model}\n[blue]Saved as:[/blue] {image_path}\n[dim]Opening image...[/dim]",
            style="green",
            title=f"[bold green]Image Generated ({model})[/bold green]",
            padding=(1, 2)
        )
        console.print(success_panel)

        # Open the image
        open_image(image_path)
    else:
        console.print("[red]Failed to generate image[/red]")


def generate_text(prompt: str, token: str = "", conversation_history: list = None, model: str = None) -> str:
    """Generate text response for the given prompt using AI service API."""
    if conversation_history is None:
        conversation_history = []
    if model is None:
        model = os.getenv('TEXT_MODEL', 'openai')
    
    try:
        # Use OpenAI-compatible POST endpoint for conversation history
        text_api_url = os.getenv('TEXT_API_URL', 'https://text.pollinations.ai')
        
        url = f"{text_api_url}/openai"
        
        # Build messages array with conversation history
        messages = []
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Build request payload
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "XIBE-CHAT-CLI/1.0"
        }
        
        # Add token if provided
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        # Make API request
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()

    except (ConnectionError, TimeoutError, ValueError, RuntimeError, requests.RequestException) as e:
        console.print(f"[red]Error generating text: {e}[/red]")
        # Fallback to a simple response if API fails
        return f"I understand you're asking about '{prompt[:50]}...'. However, I'm currently unable to connect to the AI service. Please try again later."


def generate_image(prompt: str, token: str = "", model: str = None) -> str:
    """Generate image for the given prompt and return file path using AI service API."""
    if model is None:
        model = os.getenv('IMAGE_MODEL', 'flux')
    
    try:
        # Create images directory if it doesn't exist
        images_dir = "generated_images"
        os.makedirs(images_dir, exist_ok=True)

        # Generate filename based on prompt and model
        import hashlib
        prompt_hash = hashlib.md5(f"{prompt}_{model}".encode()).hexdigest()[:8]
        filename = f"ai_image_{prompt_hash}.jpg"
        image_path = os.path.join(images_dir, filename)

        # URL encode the prompt
        encoded_prompt = urllib.parse.quote(prompt)

        # Build parameters according to API documentation
        params = {
            "width": 1024,
            "height": 1024,
            "model": model,
            "seed": 42,
            "enhance": "true",  # Enhance prompt using LLM for more detail
            "safe": "true",     # Enable strict NSFW filtering
            "private": "true"   # Prevent image from appearing in public feed
        }

        # Add token-based features if provided (for registered users)
        if token:
            params["nologo"] = "true"
            params["token"] = token

        # Use the correct API endpoint format from documentation
        image_api_url = os.getenv('IMAGE_API_URL', 'https://image.pollinations.ai')
        url = f"{image_api_url}/prompt/{encoded_prompt}"

        # Make API request with increased timeout for image generation
        headers = {"User-Agent": "XIBE-CHAT-CLI/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=300)
        response.raise_for_status()

        # Save the image
        with open(image_path, 'wb') as f:
            f.write(response.content)

        return image_path

    except (ConnectionError, TimeoutError, ValueError, RuntimeError, OSError, requests.RequestException) as e:
        console.print(f"[red]Error generating image: {e}[/red]")
        # Check if response contains error message from API
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_text = e.response.text
                console.print(f"[dim]API Error: {error_text}[/dim]")
            except:
                pass
        return ""




def open_image(image_path: str) -> None:
    """Open the image using the default system image viewer."""
    try:
        if platform.system() == "Windows":
            os.startfile(image_path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", image_path], check=True)
        else:  # Linux and other Unix-like
            subprocess.run(["xdg-open", image_path], check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        console.print(f"[red]Error opening image: {e}[/red]")


def show_available_models() -> None:
    """Show available AI models to the user."""
    console.print("\n[bold blue]Available AI Models[/bold blue]")
    console.print("=" * 50)
    
    # Text models
    console.print("\n[bold green]Text Generation Models:[/bold green]")
    try:
        text_api_url = os.getenv('TEXT_API_URL', 'https://text.pollinations.ai')
        url = f"{text_api_url}/models"
        
        headers = {"User-Agent": "XIBE-CHAT-CLI/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        models = response.json()
        
        # Filter and display text models
        text_models = []
        for model in models:
            if isinstance(model, dict):
                # Skip audio models and uncensored models
                if (model.get('audio', False) or 
                    model.get('uncensored', False) or
                    model.get('name') in ['openai-audio', 'evil', 'unity']):
                    continue
                
                name = model.get('name', 'unknown')
                description = model.get('description', 'No description')
                tier = model.get('tier', 'unknown')
                
                text_models.append({'name': name, 'description': description, 'tier': tier})
        
        # Sort by tier (anonymous first)
        text_models.sort(key=lambda x: (x['tier'] != 'anonymous', x['name']))
        
        for model in text_models:
            tier_indicator = "🆓" if model['tier'] == 'anonymous' else "🔑"
            console.print(f"  {tier_indicator} [bold]{model['name']}[/bold]")
            console.print(f"    [dim]{model['description']}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error fetching text models: {e}[/red]")
        console.print("  [yellow]Note: Models change daily, check the API directly[/yellow]")
        console.print("  🆓 openai - OpenAI GPT-5 Mini")
        console.print("  🆓 mistral - Mistral Small 3.1 24B")
        console.print("  🔑 gemini - Gemini 2.5 Flash Lite")
    
    # Image models
    console.print("\n[bold green]Image Generation Models:[/bold green]")
    try:
        image_api_url = os.getenv('IMAGE_API_URL', 'https://image.pollinations.ai')
        url = f"{image_api_url}/models"
        
        headers = {"User-Agent": "XIBE-CHAT-CLI/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        models = response.json()
        
        for model in models:
            if isinstance(model, str):
                if model == 'nanobanana':
                    console.print(f"  🎨 [bold]{model}[/bold] [dim](requires input image for editing)[/dim]")
                else:
                    console.print(f"  🎨 [bold]{model}[/bold]")
        
    except Exception as e:
        console.print(f"[red]Error fetching image models: {e}[/red]")
        console.print("  [yellow]Note: Models change daily, check the API directly[/yellow]")
        console.print("  🎨 flux - High-quality image generation")
        console.print("  🎨 kontext - Image-to-image generation")
        console.print("  🎨 turbo - Fast image generation")
        console.print("  🎨 nanobanana - Image editing (requires input image)")
        console.print("  🎨 gptimage - GPT-powered generation")
    
    console.print(f"\n[dim]To use a different model, set it in your .env file:[/dim]")
    console.print(f"[dim]TEXT_MODEL=model_name[/dim]")
    console.print(f"[dim]IMAGE_MODEL=model_name[/dim]")
    console.print()
    console.print("[yellow]💡 Models change daily - use the 'models' command for current availability[/yellow]")
    console.print()


def choose_models_with_memory() -> dict:
    """Choose models with memory of last used models."""
    # Try to load saved preferences first
    saved_models = load_model_preferences()
    
    if saved_models:
        console.print(f"\n[green]📝 Found saved model preferences:[/green]")
        console.print(f"[dim]Text Model: {saved_models['text']}[/dim]")
        console.print(f"[dim]Image Model: {saved_models['image']}[/dim]")
        console.print()
        
        # Ask user if they want to use saved models
        try:
            choice = console.input("[bold cyan]Use saved models? (y/n/s to switch):[/bold cyan] ").strip().lower()
            
            if choice in ['y', 'yes', '']:
                console.print("[green]✅ Using saved model preferences[/green]")
                return saved_models
            elif choice in ['s', 'switch']:
                console.print("[yellow]🔄 Switching to model selection...[/yellow]")
                return choose_models()
            else:
                console.print("[yellow]🔄 Choosing new models...[/yellow]")
                return choose_models()
        except KeyboardInterrupt:
            console.print("\n[yellow]Using saved model preferences[/yellow]")
            return saved_models
    
    # No saved preferences found, ask user to choose
    console.print("\n[bold blue]First time setup - Choose your AI Models[/bold blue]")
    console.print("[dim]Your preferences will be saved for future use[/dim]")
    return choose_models()


def choose_models() -> dict:
    """Let user choose text and image models interactively."""
    console.print("\n[bold blue]Choose AI Models[/bold blue]")
    console.print("=" * 30)
    
    # Get available models
    text_models = get_available_text_models()
    image_models = get_available_image_models()
    
    # Choose text model
    console.print(f"\n[bold green]Text Generation Models:[/bold green]")
    for i, model in enumerate(text_models, 1):
        tier_indicator = "🆓" if model.get('tier') == 'anonymous' else "🔑"
        console.print(f"  {i}. {tier_indicator} {model['name']} - {model['description']}")
    
    while True:
        try:
            choice = console.input(f"\n[bold cyan]Choose text model (1-{len(text_models)}):[/bold cyan] ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(text_models):
                selected_text = text_models[int(choice) - 1]['name']
                break
            else:
                console.print("[red]Invalid choice. Please enter a valid number.[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Using default text model: openai[/yellow]")
            selected_text = "openai"
            break
    
    # Choose image model
    console.print(f"\n[bold green]Image Generation Models:[/bold green]")
    for i, model in enumerate(image_models, 1):
        if model == 'nanobanana':
            console.print(f"  {i}. 🎨 {model} (requires input image for editing)")
        else:
            console.print(f"  {i}. 🎨 {model}")
    
    while True:
        try:
            choice = console.input(f"\n[bold cyan]Choose image model (1-{len(image_models)}):[/bold cyan] ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(image_models):
                selected_image = image_models[int(choice) - 1]
                break
            else:
                console.print("[red]Invalid choice. Please enter a valid number.[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Using default image model: flux[/yellow]")
            selected_image = "flux"
            break
    
    console.print(f"\n[green]Selected Text Model: {selected_text}[/green]")
    console.print(f"[green]Selected Image Model: {selected_image}[/green]")
    console.print()
    
    return {"text": selected_text, "image": selected_image}


def get_available_text_models() -> list:
    """Get list of available text models."""
    try:
        text_api_url = os.getenv('TEXT_API_URL', 'https://text.pollinations.ai')
        url = f"{text_api_url}/models"
        
        headers = {"User-Agent": "XIBE-CHAT-CLI/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        models = response.json()
        
        # Filter and return text models
        text_models = []
        for model in models:
            if isinstance(model, dict):
                # Skip audio models and uncensored models
                if (model.get('audio', False) or 
                    model.get('uncensored', False) or
                    model.get('name') in ['openai-audio', 'evil', 'unity']):
                    continue
                
                text_models.append({
                    'name': model.get('name', 'unknown'),
                    'description': model.get('description', 'No description'),
                    'tier': model.get('tier', 'unknown')
                })
        
        # Sort by tier (anonymous first)
        text_models.sort(key=lambda x: (x['tier'] != 'anonymous', x['name']))
        return text_models
        
    except Exception as e:
        console.print(f"[red]Error fetching text models: {e}[/red]")
        # Return default models
        return [
            {'name': 'openai', 'description': 'OpenAI GPT-5 Mini', 'tier': 'anonymous'},
            {'name': 'mistral', 'description': 'Mistral Small 3.1 24B', 'tier': 'anonymous'},
            {'name': 'gemini', 'description': 'Gemini 2.5 Flash Lite', 'tier': 'seed'}
        ]


def get_available_image_models() -> list:
    """Get list of available image models."""
    try:
        image_api_url = os.getenv('IMAGE_API_URL', 'https://image.pollinations.ai')
        url = f"{image_api_url}/models"
        
        headers = {"User-Agent": "XIBE-CHAT-CLI/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        models = response.json()
        
        if isinstance(models, list):
            return models
        else:
            return list(models.keys())
        
    except Exception as e:
        console.print(f"[red]Error fetching image models: {e}[/red]")
        # Return default models
        return ['flux', 'kontext', 'turbo', 'nanobanana', 'gptimage']


def clean_response_for_markdown(response: str, user_prompt: str = "") -> str:
    """Clean AI response for better markdown rendering."""
    cleaned = response
    
    # Remove debug output to clean up the interface
    # console.print(f"[dim]Original response: {repr(response[:100])}[/dim]")
    
    # Apply formatting based on user request if AI didn't provide markdown
    formatting_applied = False
    if user_prompt and not re.search(r'\*{1,2}|\_{1,2}|`{1,3}', cleaned):
        # Check if user requested italic formatting first (more specific)
        if re.search(r'\b(italic|italics|emphasize with italics)\b', user_prompt.lower()):
            # Apply italic formatting to the entire response if it's short and simple
            if len(cleaned.strip()) < 50 and '\n' not in cleaned:
                cleaned = f"*{cleaned.strip()}*"
                formatting_applied = True
        # Check if user requested bold formatting (broader terms)
        elif re.search(r'\b(bold|boldly|emphasize|highlight)\b', user_prompt.lower()):
            # Apply bold formatting to the entire response if it's short and simple
            if len(cleaned.strip()) < 50 and '\n' not in cleaned:
                cleaned = f"**{cleaned.strip()}**"
                formatting_applied = True
    
    # Only apply automatic formatting fixes if we didn't apply user-requested formatting
    if not formatting_applied:
        # Fix bold text - ensure proper ** format
        cleaned = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'**\1**', cleaned)
        
        # Fix italic text - ensure proper * format
        cleaned = re.sub(r'(?<!\*)_([^_\n]+?)_(?!\*)', r'*\1*', cleaned)
    
    # Fix links - ensure proper [text](url) format
    # Handle cases where links might have extra spaces or formatting issues
    cleaned = re.sub(r'\[([^\]]+)\]\s*\(\s*([^)]+)\s*\)', r'[\1](\2)', cleaned)
    
    # Fix blockquotes - ensure proper > format with line breaks
    lines = cleaned.split('\n')
    fixed_lines = []
    for line in lines:
        # Handle blockquote lines that start with > but might have other formatting
        if line.strip().startswith('>'):
            # Clean up the blockquote line
            content = line.strip()[1:].strip()
            if content:
                fixed_lines.append(f"> {content}")
            else:
                fixed_lines.append(">")
        else:
            fixed_lines.append(line)
    cleaned = '\n'.join(fixed_lines)
    
    # Fix unordered lists - ensure proper * format with spacing
    cleaned = re.sub(r'^\s*\*\s+(.+)$', r'* \1', cleaned, flags=re.MULTILINE)
    
    # Fix ordered lists - ensure proper 1. format with spacing
    cleaned = re.sub(r'^\s*(\d+)\.\s+(.+)$', r'\1. \2', cleaned, flags=re.MULTILINE)
    
    # Fix code blocks - ensure proper ``` format
    cleaned = re.sub(r'```(\w+)?\n', r'\n```\1\n', cleaned)
    cleaned = re.sub(r'```\n', r'\n```\n', cleaned)
    
    # Fix headers - ensure proper spacing
    cleaned = re.sub(r'\n(#+\s)', r'\n\n\1', cleaned)
    
    # Ensure proper line breaks between different elements
    cleaned = re.sub(r'\n\n+', '\n\n', cleaned)  # Remove excessive line breaks
    
    # Remove debug output to clean up the interface
    # console.print(f"[dim]Cleaned response: {repr(cleaned[:100])}[/dim]")
    
    return cleaned


if __name__ == "__main__":
    main()
