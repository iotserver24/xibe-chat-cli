#!/usr/bin/env python3
"""
AI CLI - AI-powered terminal assistant for text and image generation
"""

import os
import platform
import subprocess
import urllib.parse
import re

try:
    import pyfiglet
except ImportError:
    print("Error: pyfiglet is required. Install it with: pip install pyfiglet")
    exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
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


def get_multiline_input() -> str:
    """Get multi-line input from user with Enter to send, Ctrl+Enter for new lines."""
    try:
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.shortcuts import prompt as ptk_prompt
        
        # Create key bindings
        kb = KeyBindings()
        
        @kb.add('enter')
        def _(event):
            """Enter key sends the message."""
            event.app.exit(result=event.app.current_buffer.text)
        
        @kb.add('c-j')  # Ctrl+J for new line
        def _(event):
            """Ctrl+J creates a new line."""
            event.app.current_buffer.insert_text('\n')
        
        # Get input with custom key bindings
        text = ptk_prompt(
            '[bold cyan]You:[/bold cyan] ',
            multiline=True,
            key_bindings=kb,
            mouse_support=True
        )
        
        return text.strip() if text else ""
        
    except ImportError:
        # Fallback to simple input if prompt_toolkit is not available
        console.print("[yellow]For better multi-line input, install prompt-toolkit: pip install prompt-toolkit[/yellow]")
        console.print("[yellow]Using simple input mode (type 'END' to finish multi-line input)[/yellow]")
        
        lines = []
        console.print("[bold cyan]You:[/bold cyan] ", end="")
        
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
    logo_text = pyfiglet.figlet_format("AI CLI", font="slant")
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


def run_chat_interface() -> None:
    """Run the interactive chat interface."""
    # Get API token for authentication
    token = get_api_token()
    
    # Initialize conversation history
    conversation_history = []
    
    # Let user choose models
    selected_models = choose_models()

    console.print("[green]AI CLI Chat Interface[/green]")
    console.print(f"[dim]Using Text Model: {selected_models['text']}[/dim]")
    console.print(f"[dim]Using Image Model: {selected_models['image']}[/dim]")
    console.print("[yellow]Type 'exit' or 'quit' to end the session[/yellow]")
    console.print("[yellow]Use 'img:' prefix for image generation[/yellow]")
    console.print("[yellow]Type 'models' to see available AI models[/yellow]")
    console.print("[yellow]Type 'switch' to change AI models[/yellow]")
    console.print("[yellow]Type '/new' to start a new chat session[/yellow]")
    console.print("[yellow]For multi-line input: press Ctrl+J for new lines, Enter to send message[/yellow]")
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
                console.print(f"[green]✅ Switched to Text Model: {selected_models['text']}[/green]")
                console.print(f"[green]✅ Switched to Image Model: {selected_models['image']}[/green]")
                console.print(f"[dim]Chat history preserved with new models[/dim]")
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
        cleaned_response = clean_response_for_markdown(response)
        
        # Debug: Show what we're trying to render
        console.print(f"[dim]Debug - Original response: {repr(response)}[/dim]")
        console.print(f"[dim]Debug - Cleaned response: {repr(cleaned_response)}[/dim]")
        
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
            "User-Agent": "AI-CLI/1.0"
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

        # Build URL with parameters and optional token
        params = {
            "width": 1024,
            "height": 1024,
            "model": model,
            "seed": 42
        }

        # Use environment variables for API endpoints or defaults
        image_api_url = os.getenv('IMAGE_API_URL', 'https://image.pollinations.ai/prompt')
        url = f"{image_api_url}/{encoded_prompt}"

        # Add token if provided
        if token:
            params["token"] = token

        # Make API request
        headers = {"User-Agent": "AI-CLI/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=60)
        response.raise_for_status()

        # Save the image
        with open(image_path, 'wb') as f:
            f.write(response.content)

        return image_path

    except (ConnectionError, TimeoutError, ValueError, RuntimeError, OSError, requests.RequestException) as e:
        console.print(f"[red]Error generating image: {e}[/red]")
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
        
        headers = {"User-Agent": "AI-CLI/1.0"}
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
        
        headers = {"User-Agent": "AI-CLI/1.0"}
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
        
        headers = {"User-Agent": "AI-CLI/1.0"}
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
        
        headers = {"User-Agent": "AI-CLI/1.0"}
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


def clean_response_for_markdown(response: str) -> str:
    """Clean AI response for better markdown rendering."""
    cleaned = response
    
    # Remove debug output to clean up the interface
    # console.print(f"[dim]Original response: {repr(response[:100])}[/dim]")
    
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
