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
import time
from pathlib import Path
from datetime import datetime

try:
    from packaging import version
except ImportError:
    print("Error: packaging is required. Install it with: pip install packaging")
    print("Or install all requirements with: pip install -r requirements.txt")
    print("\nIf you're using a virtual environment, make sure it's activated:")
    print("  Windows PowerShell: .\\.venv\\Scripts\\Activate.ps1")
    print("  Windows CMD: .venv\\Scripts\\activate.bat")
    print("  Linux/Mac: source .venv/bin/activate")
    print("\nOr use the provided run scripts: run.bat (Windows) or run.ps1 (PowerShell)")
    exit(1)

try:
    import pyfiglet
except ImportError:
    print("Error: pyfiglet is required. Install it with: pip install pyfiglet")
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

# Store API key in memory for current session (not saved to disk)
_SESSION_API_KEY = None
CHAT_COMPLETIONS_TIMEOUT = int(os.getenv("CHAT_COMPLETIONS_TIMEOUT", "60"))
CHAT_COMPLETIONS_RETRIES = int(os.getenv("CHAT_COMPLETIONS_RETRIES", "2"))

# Current version
CURRENT_VERSION = "0.9.0"




def _hex_gradient(start_hex: str, end_hex: str, steps: int) -> list:
    """Create a list of hex colors forming a gradient from start to end."""
    sh = start_hex.lstrip('#')
    eh = end_hex.lstrip('#')
    sr, sg, sb = int(sh[0:2], 16), int(sh[2:4], 16), int(sh[4:6], 16)
    er, eg, eb = int(eh[0:2], 16), int(eh[2:4], 16), int(eh[4:6], 16)
    colors = []
    for i in range(max(steps, 1)):
        t = i / max(steps - 1, 1)
        r = int(sr + (er - sr) * t)
        g = int(sg + (eg - sg) * t)
        b = int(sb + (eb - sb) * t)
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    return colors


def _build_gradient_logo(title: str) -> Text:
    """Return a horizontally gradient-colored ASCII logo for headings."""
    # Prefer a sleek font; fall back gracefully
    try:
        ascii_logo = pyfiglet.figlet_format(title, font="ansi_shadow")
    except Exception:
        ascii_logo = pyfiglet.figlet_format(title, font="big")

    lines = ascii_logo.splitlines()
    max_len = max((len(l) for l in lines), default=0)
    palette = _hex_gradient("#ff00cc", "#00e5ff", max_len)

    styled = Text()
    for line in lines:
        for idx, ch in enumerate(line.ljust(max_len)):
            if ch == ' ':
                styled.append(ch)
            else:
                styled.append(ch, style=f"bold {palette[idx]}")
        styled.append("\n")
    return styled


def save_model_preferences(text_model: str, image_model: str) -> None:
    """Save the selected models to configuration file."""
    try:
        # Load existing config
        config = load_config()
        config["text_model"] = text_model
        config["image_model"] = image_model
        config["last_updated"] = datetime.now().isoformat()
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
            
    except Exception as e:
        console.print(f"[dim]Could not save model preferences: {e}[/dim]")


def load_config() -> dict:
    """Load the configuration file."""
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        console.print(f"[dim]Could not load config: {e}[/dim]")
    
    return {}


def load_model_preferences() -> dict:
    """Load the saved model preferences from configuration file."""
    try:
        config = load_config()
        
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


def save_api_key(api_key: str) -> None:
    """Persist the API key to the configuration file."""
    try:
        config = load_config()
        config["api_key"] = api_key
        config["api_key_saved_at"] = datetime.now().isoformat()
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        console.print(f"[dim]Could not save API key: {e}[/dim]")


def load_saved_api_key() -> str:
    """Load the API key from configuration."""
    try:
        config = load_config()
        return config.get("api_key", "")
    except Exception as e:
        console.print(f"[dim]Could not load API key: {e}[/dim]")
        return ""


def is_publishable_key(api_key: str) -> bool:
    """Return True if the key looks like a publishable/client-side key."""
    if not api_key:
        return False
    lowered = api_key.lower()
    return lowered.startswith("pk_") or lowered.startswith("plln_pk")


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


def get_api_key() -> str:
    """Get the API key from session or config."""
    global _SESSION_API_KEY
    if _SESSION_API_KEY:
        return _SESSION_API_KEY
    saved_key = load_saved_api_key()
    if saved_key:
        _SESSION_API_KEY = saved_key
    return _SESSION_API_KEY or ""


def prompt_for_api_key(force: bool = False) -> str:
    """Prompt user to enter their Pollinations API key and store it."""
    global _SESSION_API_KEY
    console.print()
    console.print("[bold cyan]🔑 API Key Setup[/bold cyan]")
    console.print("=" * 50)
    console.print()
    console.print("[yellow]To use XIBE-CHAT, you need an API key from enter.pollinations.ai[/yellow]")
    console.print("[dim]Get your API key at: https://enter.pollinations.ai[/dim]")
    console.print()
    
    while True:
        try:
            api_key = console.input("[bold cyan]Enter your Pollinations API key[/bold cyan]: ").strip()
            
            if not api_key:
                console.print("[red]API key is required. Please enter a valid API key.[/red]")
                continue
            
            # Validate API key format (basic check)
            if len(api_key) < 10:
                console.print("[red]API key seems too short. Please check and try again.[/red]")
                continue
            
            # Store in memory and persist
            _SESSION_API_KEY = api_key
            save_api_key(api_key)
            console.print("[green]✅ API key saved![/green]")
            console.print()
            return api_key
            
        except KeyboardInterrupt:
            console.print("\n[red]API key entry cancelled.[/red]")
            existing_key = get_api_key()
            if force and not existing_key:
                console.print("[red]API key is required to use XIBE-CHAT. Exiting...[/red]")
                exit(1)
            return existing_key
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            console.print("[red]Please try again.[/red]")
            continue


def check_for_updates() -> tuple[str, str]:
    """Check for available updates on PyPI."""
    try:
        # Get package info from PyPI
        url = "https://pypi.org/pypi/xibe-chat-cli/json"
        headers = {"User-Agent": "XIBE-CHAT-CLI/1.0"}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        latest_version = data["info"]["version"]
        
        # Compare versions
        current_ver = version.parse(CURRENT_VERSION)
        latest_ver = version.parse(latest_version)
        
        if latest_ver > current_ver:
            return latest_version, "update_available"
        else:
            return latest_version, "up_to_date"
            
    except Exception as e:
        console.print(f"[dim]Could not check for updates: {e}[/dim]")
        return CURRENT_VERSION, "check_failed"


def show_update_notification(latest_version: str) -> None:
    """Show update notification to user."""
    update_panel = Panel(
        f"🔄 [bold yellow]New Version Available![/bold yellow]\n\n"
        f"📦 [bold]Current Version:[/bold] {CURRENT_VERSION}\n"
        f"🚀 [bold]Latest Version:[/bold] {latest_version}\n\n"
        f"💡 [bold]To update, run:[/bold]\n"
        f"   [cyan]pip install --upgrade xibe-chat-cli[/cyan]\n\n"
        f"✨ [dim]Update includes new features, bug fixes, and improvements![/dim]",
        style="yellow",
        title="[bold white]🔄 Update Available[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="yellow"
    )
    console.print(update_panel)
    console.print()


def build_system_message(text_model: str = "", image_model: str = "") -> str:
    """Describe the runtime so the AI knows it's running inside a CLI and brand wrapper."""
    try:
        os_name = platform.system()
        os_ver = platform.release()
        py_ver = platform.python_version()
        cwd = os.getcwd()
        term = os.environ.get("TERM", "unknown")
    except Exception:
        os_name, os_ver, py_ver, cwd, term = "unknown", "unknown", "unknown", "", "unknown"

    model_tag = text_model or os.getenv('TEXT_MODEL', 'unknown')
    image_tag = image_model or os.getenv('IMAGE_MODEL', 'unknown')

    return (
        f"You are the {model_tag} language model operating via XIBE CHAT — a friendly terminal assistant by R3AP3R. "
        f"You're helping users through a beautiful CLI interface. Image generation is handled by the '{image_tag}' model when users type 'img:'. "
        "Your environment: "
        f"OS={os_name} {os_ver}; Python={py_ver}; Terminal={term}; Working in {cwd}. "
        "Be conversational, helpful, and engaging. Use terminal-friendly markdown formatting, proper code blocks, "
        "and avoid suggesting GUI actions since this is a CLI interface. Keep responses concise but thorough, "
        "and always aim to be genuinely helpful and friendly in your interactions."
    )


def main() -> None:
    """Main function to run the AI CLI application."""
    show_splash_screen()
    
    # Prompt for API key on first run (persisted to config)
    if not get_api_key():
        prompt_for_api_key(force=True)
    
    # Check for updates in background
    with console.status("[bold green]Checking for updates...[/bold green]", spinner="dots"):
        latest_version, status = check_for_updates()
    
    # Show update notification if available
    if status == "update_available":
        show_update_notification(latest_version)
    elif status == "up_to_date":
        console.print(f"[dim]✅ XIBE-CHAT is up to date (v{CURRENT_VERSION})[/dim]")
        console.print()
    
    run_chat_interface()


def _show_brand() -> None:
    """Render only the brand logo and subtitle."""
    logo = _build_gradient_logo("XIBE CHAT")
    subtitle = Panel(
        "[italic]AI-powered terminal assistant — Text and Image generation[/italic]",
        style="bright_black",
        title="[bold cyan]Welcome[/bold cyan]",
        title_align="center",
        padding=(1, 2)
    )
    console.print(logo, justify="center")
    console.print(subtitle, justify="center")
    console.print()


def show_splash_screen() -> None:
    """Display the AI CLI splash screen (brand only)."""
    console.clear()
    _show_brand()


def show_clear_screen(selected_models: dict = None) -> None:
    """Clear terminal and display only the brand (logo + subtitle)."""
    console.clear()
    _show_brand()


def show_help_commands() -> None:
    """Show detailed help information for all commands."""
    help_panel = Panel(
        "📚 Complete guide to all XIBE-CHAT commands and features",
        style="blue",
        title="[bold white]📖 XIBE-CHAT Help Center[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="blue"
    )
    console.print(help_panel)
    
    # Chat Commands
    chat_commands = Panel(
        "💬 [bold]Chat Commands:[/bold]\n\n"
        "  [cyan]/help[/cyan] - Show this help screen\n"
        "  [cyan]/clear[/cyan] - Clear screen and show logo\n"
        "  [cyan]/new[/cyan] - Start fresh chat session\n"
        "  [cyan]/reset[/cyan] - Reset model preferences\n"
        "  [cyan]/image-settings[/cyan] - View image generation settings\n"
        "  [cyan]/agent[/cyan] - Switch to Agent Mode\n"
        "  [cyan]/check-updates[/cyan] - Check for updates\n"
        "  [cyan]/api-key[/cyan] - Update saved API key",
        style="green",
        title="[bold white]💬 Chat Commands[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="green"
    )
    console.print(chat_commands)
    
    # Model Commands
    model_commands = Panel(
        "🤖 [bold]Model Commands:[/bold]\n\n"
        "  [cyan]models[/cyan] - View available AI models\n"
        "  [cyan]switch[/cyan] - Change text/image models\n\n"
        "[dim]Models preserve chat history when switching[/dim]",
        style="cyan",
        title="[bold white]🤖 Model Commands[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="cyan"
    )
    console.print(model_commands)
    
    # Input Methods
    input_methods = Panel(
        "⌨️ [bold]Input Methods:[/bold]\n\n"
        "  [yellow]Natural Language[/yellow] - AI analyzes and responds conversationally\n"
        "  [yellow]img: prompt[/yellow] - Direct image generation with AI acknowledgment\n"
        "  [yellow]Multiline[/yellow] - Ctrl+N for new lines\n\n"
        "[dim]Smart Examples:[/dim]\n"
        "[dim]• \"show me Paris\" → \"Sure! Here's Paris...\" + Image[/dim]\n"
        "[dim]• \"what's quantum physics?\" → Text explanation[/dim]\n"
        "[dim]• \"draw a dragon\" → \"Great idea! Creating...\" + Image[/dim]\n"
        "[dim]• \"explain AI\" → Text explanation[/dim]\n"
        "[dim]• \"img: sunset\" → \"Beautiful choice!...\" + Fast Image[/dim]",
        style="yellow",
        title="[bold white]💬 Conversational AI[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="yellow"
    )
    console.print(input_methods)
    
    # Session Commands
    session_commands = Panel(
        "🚪 [bold]Session Commands:[/bold]\n\n"
        "  [cyan]exit[/cyan] or [cyan]quit[/cyan] - End session\n\n"
        "[dim]All commands are case-insensitive[/dim]",
        style="bright_black",
        title="[bold white]🚪 Session Commands[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="bright_black"
    )
    console.print(session_commands)
    
    # Tips
    tips_panel = Panel(
        "💡 [bold]Pro Tips:[/bold]\n\n"
        "  • [bold]Conversational AI:[/bold] AI responds naturally before generating images\n"
        "  • [bold]Smart Image Prompts:[/bold] AI enhances your requests with vivid details\n"
        "  • [bold]Natural Interaction:[/bold] Chat like with a human assistant\n"
        "  • [bold]Fast 'img:' prefix:[/bold] Direct generation with AI acknowledgment\n"
        "  • Models change daily - use 'models' for current availability\n"
        "  • Conversation history limited to 10 exchanges for memory\n"
        "  • Generated images saved in 'generated_images' folder",
        style="magenta",
        title="[bold white]💬 AI Conversations[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="magenta"
    )
    console.print(tips_panel)
    
    console.print()


def show_image_settings() -> None:
    """Show current image generation settings."""
    console.print("\n[bold blue]🖼️ Image Generation Settings[/bold blue]")
    console.print("=" * 50)
    
    console.print("\n[bold green]Current Settings:[/bold green]")
    console.print("  [cyan]Width:[/cyan] 1024 pixels")
    console.print("  [cyan]Height:[/cyan] 1024 pixels") 
    console.print("  [cyan]Seed:[/cyan] 42 (for reproducible results)")
    console.print("  [cyan]Enhance:[/cyan] true (AI-enhanced prompts)")
    console.print("  [cyan]Safe:[/cyan] true (Content filtering)")
    console.print("  [cyan]Private:[/cyan] true (Not in public feed)")
    console.print("  [cyan]No Watermark:[/cyan] true (Premium feature)")
    
    console.print("\n[bold green]Features:[/bold green]")
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
    
    console.print()


def switch_to_agent_mode() -> None:
    """Switch to agent mode."""
    try:
        # Add current directory to Python path to find agent_mode module
        import sys
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Try to import agent_mode with better error handling
        try:
            import agent_mode
            agent_mode.run_agent_mode()
        except ImportError as import_error:
            # Try alternative import methods
            import importlib.util
            agent_mode_path = os.path.join(current_dir, "agent_mode.py")
            
            if os.path.exists(agent_mode_path):
                # Load module from file path
                spec = importlib.util.spec_from_file_location("agent_mode", agent_mode_path)
                agent_mode = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(agent_mode)
                agent_mode.run_agent_mode()
            else:
                raise import_error
                
    except ImportError as e:
        console.print(f"[red]Agent mode not available: {e}[/red]")
        console.print("[red]Make sure agent_mode.py exists in the same directory as ai_cli.py[/red]")
        console.print(f"[red]Current directory: {current_dir}[/red]")
        console.print(f"[red]Looking for: {os.path.join(current_dir, 'agent_mode.py')}[/red]")
    except Exception as e:
        console.print(f"[red]Error switching to agent mode: {e}[/red]")


def run_chat_interface() -> None:
    """Run the interactive chat interface."""
    # Get authentication API key
    api_key = get_api_key()
    
    # Initialize conversation history
    conversation_history = []
    
    # Let user choose models (with memory)
    selected_models = choose_models_with_memory()
    
    # Save the selected models for future use
    save_model_preferences(selected_models['text'], selected_models['image'])

    # Simple startup message
    console.print("[green]XIBE-CHAT Ready[/green]")
    console.print("[dim]Type '/help' for commands or start chatting![/dim]")
    console.print()

    while True:
        try:
            # Get user input with multi-line support
            user_input = get_multiline_input()

            # Check for exit conditions
            if user_input.lower() in ['exit', 'quit']:
                goodbye_panel = Panel(
                    "👋 [bold]Thanks for using XIBE-CHAT![/bold]\n\n"
                    "[dim]Your conversation has been a pleasure. Come back anytime![/dim]",
                    style="yellow",
                    title="[bold white]👋 Goodbye![/bold white]",
                    title_align="center",
                    padding=(1, 2),
                    border_style="yellow"
                )
                console.print(goodbye_panel)
                break

            # Check for special commands
            if user_input.lower() == 'models':
                show_available_models()
                continue
            elif user_input.lower() == 'switch':
                switch_panel = Panel(
                    "🔄 Switching AI Models",
                    style="yellow",
                    title="[bold white]⚙️ Model Switch[/bold white]",
                    title_align="center",
                    padding=(0, 2),
                    border_style="yellow"
                )
                console.print(switch_panel)
                selected_models = choose_models()
                # Save the new model preferences
                save_model_preferences(selected_models['text'], selected_models['image'])
                
                # Extract image model name if it's a dict
                image_model_display = selected_models['image']
                if isinstance(image_model_display, dict):
                    image_model_display = image_model_display.get('name', str(image_model_display))
                
                success_panel = Panel(
                    f"✅ [green]Successfully switched models![/green]\n\n"
                    f"🤖 [bold]Text Model:[/bold] {selected_models['text']}\n"
                    f"🎨 [bold]Image Model:[/bold] {image_model_display}\n\n"
                    f"[dim]Chat history preserved • Preferences saved[/dim]",
                    style="green",
                    title="[bold white]🎉 Models Updated[/bold white]",
                    title_align="center",
                    padding=(1, 2),
                    border_style="green"
                )
                console.print(success_panel)
                continue
            elif user_input.lower() == '/new':
                # Extract image model name if it's a dict
                image_model_display = selected_models['image']
                if isinstance(image_model_display, dict):
                    image_model_display = image_model_display.get('name', str(image_model_display))
                
                new_session_panel = Panel(
                    f"🆕 [green]New chat session started![/green]\n\n"
                    f"🤖 [bold]Text Model:[/bold] {selected_models['text']}\n"
                    f"🎨 [bold]Image Model:[/bold] {image_model_display}\n\n"
                    f"[dim]Previous conversation history cleared[/dim]",
                    style="green",
                    title="[bold white]🆕 New Chat Session[/bold white]",
                    title_align="center",
                    padding=(1, 2),
                    border_style="green"
                )
                console.print(new_session_panel)
                conversation_history.clear()
                continue
            elif user_input.lower() == '/clear':
                # Clear terminal and show logo with commands
                show_clear_screen(selected_models)
                continue
            elif user_input.lower() == '/help':
                show_help_commands()
                continue
            elif user_input.lower() == '/reset':
                reset_panel = Panel(
                    "⚠️ Resetting Model Preferences",
                    style="yellow",
                    title="[bold white]🔄 Reset Settings[/bold white]",
                    title_align="center",
                    padding=(0, 2),
                    border_style="yellow"
                )
                console.print(reset_panel)
                try:
                    if CONFIG_FILE.exists():
                        CONFIG_FILE.unlink()
                        success_panel = Panel(
                            "✅ [green]Model preferences reset successfully![/green]\n\n"
                            "[yellow]You will be asked to choose models again next time[/yellow]",
                            style="green",
                            title="[bold white]✅ Reset Complete[/bold white]",
                            title_align="center",
                            padding=(1, 2),
                            border_style="green"
                        )
                        console.print(success_panel)
                    else:
                        info_panel = Panel(
                            "ℹ️ [yellow]No saved preferences found to reset[/yellow]",
                            style="yellow",
                            title="[bold white]ℹ️ No Preferences Found[/bold white]",
                            title_align="center",
                            padding=(1, 2),
                            border_style="yellow"
                        )
                        console.print(info_panel)
                except Exception as e:
                    error_panel = Panel(
                        f"❌ [red]Error resetting preferences: {e}[/red]",
                        style="red",
                        title="[bold white]❌ Reset Failed[/bold white]",
                        title_align="center",
                        padding=(1, 2),
                        border_style="red"
                    )
                    console.print(error_panel)
                continue
            elif user_input.lower() == '/image-settings':
                show_image_settings()
                continue
            elif user_input.lower() == '/agent':
                # Switch to agent mode
                switch_to_agent_mode()
                continue
            elif user_input.lower() == '/check-updates':
                # Manual update check
                with console.status("[bold green]Checking for updates...[/bold green]", spinner="dots"):
                    latest_version, status = check_for_updates()
                
                if status == "update_available":
                    show_update_notification(latest_version)
                elif status == "up_to_date":
                    up_to_date_panel = Panel(
                        f"✅ [green]XIBE-CHAT is up to date![/green]\n\n"
                        f"📦 [bold]Current Version:[/bold] {CURRENT_VERSION}\n"
                        f"🚀 [bold]Latest Version:[/bold] {latest_version}\n\n"
                        f"[dim]No updates needed at this time.[/dim]",
                        style="green",
                        title="[bold white]✅ Up to Date[/bold white]",
                        title_align="center",
                        padding=(1, 2),
                        border_style="green"
                    )
                    console.print(up_to_date_panel)
                else:
                    error_panel = Panel(
                        "❌ [red]Could not check for updates[/red]\n\n"
                        "Please check your internet connection and try again.",
                        style="red",
                        title="[bold white]❌ Update Check Failed[/bold white]",
                        title_align="center",
                        padding=(1, 2),
                        border_style="red"
                    )
                    console.print(error_panel)
                continue
            elif user_input.lower() == '/api-key':
                prompt_for_api_key(force=True)
                api_key = get_api_key()
                console.print("[green]API key updated successfully.[/green]")
                continue

            # Check if empty input
            if not user_input:
                continue

            # Handle image generation requests
            if user_input.startswith('img:'):
                # Direct image generation - fast path with AI acknowledgment
                image_prompt = user_input[4:].strip()
                if image_prompt:
                    # Display user request
                    user_panel = Panel(
                        f"🎨 {image_prompt}",
                        style="blue",
                        title="[bold white]You[/bold white]",
                        title_align="left",
                        padding=(1, 2),
                        border_style="blue"
                    )
                    console.print(user_panel)
                    console.print()

                    # Get AI to provide a conversational acknowledgment
                    with console.status("[bold blue]🤖 Preparing response...[/bold blue]", spinner="dots"):
                        ack_analysis = analyze_query_with_ai(f"I want you to generate an image of: {image_prompt}", api_key, selected_models['text'])

                    ai_acknowledgment = ack_analysis.get('response', f"Sure! I'll generate an image of {image_prompt} for you.")

                    # Add to conversation history
                    conversation_history.append({"role": "user", "content": user_input})
                    conversation_history.append({"role": "assistant", "content": ai_acknowledgment})

                    # Keep only last 10 exchanges to avoid token limits
                    if len(conversation_history) > 20:  # 10 exchanges = 20 messages
                        conversation_history = conversation_history[-20:]

                    # Display AI acknowledgment
                    try:
                        cleaned_ack = clean_response_for_markdown(ai_acknowledgment, user_input)
                        ai_panel = Panel(
                            Markdown(cleaned_ack, code_theme="monokai"),
                            style="green",
                            title=f"[bold white]🤖 AI Assistant ({selected_models['text']})[/bold white]",
                            title_align="right",
                            padding=(1, 2),
                            border_style="green"
                        )
                        console.print(ai_panel)
                    except Exception as e:
                        ai_panel = Panel(
                            ai_acknowledgment,
                            style="green",
                            title=f"[bold white]🤖 AI Assistant ({selected_models['text']})[/bold white]",
                            title_align="right",
                            padding=(1, 2),
                            border_style="green"
                        )
                        console.print(ai_panel)

                    console.print()

                    # Now generate the image
                    console.print(f"[dim]🎨 Generating image: {image_prompt[:60]}...[/dim]")
                    handle_image_generation(image_prompt, api_key, selected_models['image'])
                else:
                    console.print("[red]Please provide a prompt after 'img:'[/red]")
            else:
                # Let AI analyze the query and decide
                with console.status("[bold blue]🤖 Analyzing your request...[/bold blue]", spinner="dots"):
                    analysis = analyze_query_with_ai(user_input, api_key, selected_models['text'])

                if analysis.get('action') == 'image':
                    # AI decided to generate an image - show conversational response first
                    ai_response = analysis.get('response', 'Sure, I\'d be happy to generate that image for you!')
                    image_prompt = analysis.get('image_prompt', user_input)

                    # Display AI's conversational response
                    user_panel = Panel(
                        user_input,
                        style="blue",
                        title="[bold white]You[/bold white]",
                        title_align="left",
                        padding=(1, 2),
                        border_style="blue"
                    )
                    console.print(user_panel)
                    console.print()

                    # Add to conversation history
                    conversation_history.append({"role": "user", "content": user_input})
                    conversation_history.append({"role": "assistant", "content": ai_response})

                    # Keep only last 10 exchanges to avoid token limits
                    if len(conversation_history) > 20:  # 10 exchanges = 20 messages
                        conversation_history = conversation_history[-20:]

                    # Display AI response in a chat bubble
                    try:
                        cleaned_response = clean_response_for_markdown(ai_response, user_input)
                        ai_panel = Panel(
                            Markdown(cleaned_response, code_theme="monokai"),
                            style="green",
                            title=f"[bold white]🤖 AI Assistant ({selected_models['text']})[/bold white]",
                            title_align="right",
                            padding=(1, 2),
                            border_style="green"
                        )
                        console.print(ai_panel)
                    except Exception as e:
                        console.print(f"[dim]Markdown parsing failed: {e}[/dim]")
                        ai_panel = Panel(
                            ai_response,
                            style="green",
                            title=f"[bold white]🤖 AI Assistant ({selected_models['text']})[/bold white]",
                            title_align="right",
                            padding=(1, 2),
                            border_style="green"
                        )
                        console.print(ai_panel)

                    console.print()

                    # Now generate the image
                    console.print(f"[dim]🎨 Generating image: {image_prompt[:60]}...[/dim]")
                    handle_image_generation(image_prompt, api_key, selected_models['image'])
                else:
                    # AI decided to respond with text
                    ai_response = analysis.get('response', 'I understand your request. How can I help you?')

                    # Add to conversation history
                    conversation_history.append({"role": "user", "content": user_input})
                    conversation_history.append({"role": "assistant", "content": ai_response})

                    # Keep only last 10 exchanges to avoid token limits
                    if len(conversation_history) > 20:  # 10 exchanges = 20 messages
                        conversation_history = conversation_history[-20:]

                    # Display AI response in a chat bubble with better styling
                    try:
                        # Clean up the response for better markdown rendering
                        cleaned_response = clean_response_for_markdown(ai_response, user_input)

                        # Create AI response panel with enhanced styling
                        ai_panel = Panel(
                            Markdown(cleaned_response, code_theme="monokai"),
                            style="green",
                            title=f"[bold white]🤖 AI Assistant ({selected_models['text']})[/bold white]",
                            title_align="right",
                            padding=(1, 2),
                            border_style="green"
                        )
                        console.print(ai_panel)

                    except Exception as e:
                        # Fallback to plain text if markdown parsing fails
                        console.print(f"[dim]Markdown parsing failed: {e}[/dim]")
                        ai_panel = Panel(
                            ai_response,
                            style="green",
                            title=f"[bold white]🤖 AI Assistant ({selected_models['text']})[/bold white]",
                            title_align="right",
                            padding=(1, 2),
                            border_style="green"
                        )
                        console.print(ai_panel)

                    # Add spacing after response for better readability
                    console.print()

        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' or 'quit' to end the session[/yellow]")
        except EOFError:
            console.print("\n[yellow]Goodbye! 👋[/yellow]")
            break


def handle_text_generation(prompt: str, api_key: str = "", conversation_history: list = None, model: str = None) -> None:
    """Handle text generation request and display response."""
    if conversation_history is None:
        conversation_history = []
    if model is None:
        model = os.getenv('TEXT_MODEL', 'gemini')
    
    # Display user message in a chat bubble
    user_panel = Panel(
        prompt,
        style="blue",
        title="[bold white]You[/bold white]",
        title_align="left",
        padding=(1, 2),
        border_style="blue"
    )
    console.print(user_panel)
    console.print()  # Add spacing
    
    with console.status(f"[bold green]🤖 AI ({model}) is thinking...[/bold green]", spinner="dots"):
        response = generate_text(prompt, api_key, conversation_history, model)

    # Add to conversation history
    conversation_history.append({"role": "user", "content": prompt})
    conversation_history.append({"role": "assistant", "content": response})
    
    # Keep only last 10 exchanges to avoid token limits
    if len(conversation_history) > 20:  # 10 exchanges = 20 messages
        conversation_history = conversation_history[-20:]

    # Display AI response in a chat bubble with better styling
    try:
        # Clean up the response for better markdown rendering
        cleaned_response = clean_response_for_markdown(response, prompt)
        
        # Create AI response panel with enhanced styling
        ai_panel = Panel(
            Markdown(cleaned_response, code_theme="monokai"),
            style="green",
            title=f"[bold white]🤖 AI Assistant ({model})[/bold white]",
            title_align="right",
            padding=(1, 2),
            border_style="green"
        )
        console.print(ai_panel)
        
    except Exception as e:
        # Fallback to plain text if markdown parsing fails
        console.print(f"[dim]Markdown parsing failed: {e}[/dim]")
        ai_panel = Panel(
            response,
            style="green",
            title=f"[bold white]🤖 AI Assistant ({model})[/bold white]",
            title_align="right",
            padding=(1, 2),
            border_style="green"
        )
        console.print(ai_panel)
    
    # Add spacing after response for better readability
    console.print()


def handle_image_generation(prompt: str, api_key: str = "", model: str = None) -> None:
    """Handle image generation request and open the image."""
    if model is None:
        model = os.getenv('IMAGE_MODEL', 'flux')
    
    # Display user image request in a chat bubble
    user_panel = Panel(
        f"🎨 {prompt}",
        style="blue",
        title="[bold white]You[/bold white]",
        title_align="left",
        padding=(1, 2),
        border_style="blue"
    )
    console.print(user_panel)
    console.print()  # Add spacing
    
    with console.status(f"[bold green]🎨 AI ({model}) is creating your image...[/bold green]", spinner="dots"):
        image_path = generate_image(prompt, api_key, model)

    if image_path:
        # Show success message with enhanced styling
        success_panel = Panel(
            f"✅ [green]Image generated successfully![/green]\n\n"
            f"🎯 [bold]Model:[/bold] {model}\n"
            f"💾 [bold]Saved as:[/bold] {image_path}\n"
            f"🚀 [bold]Opening image...[/bold]",
            style="green",
            title="[bold white]🎨 Image Generated Successfully[/bold white]",
            title_align="center",
            padding=(1, 2),
            border_style="green"
        )
        console.print(success_panel)

        # Open the image
        open_image(image_path)
    else:
        error_panel = Panel(
            "❌ [red]Failed to generate image[/red]\n\n"
            "Please try again with a different prompt or check your connection.",
            style="red",
            title="[bold white]⚠️ Image Generation Failed[/bold white]",
            title_align="center",
            padding=(1, 2),
            border_style="red"
        )
        console.print(error_panel)


def generate_text(prompt: str, api_key: str = "", conversation_history: list = None, model: str = None) -> str:
    """Generate text response for the given prompt."""
    if conversation_history is None:
        conversation_history = []
    if model is None:
        model = os.getenv('TEXT_MODEL', 'gemini')
    
    try:
        if is_publishable_key(api_key):
            warning = (
                "Text generation via /v1/chat/completions requires a secret API key "
                "(sk_...). Please create one at https://enter.pollinations.ai and "
                "run /api-key to update your credentials."
            )
            console.print(f"[red]{warning}[/red]")
            return "I’m ready once you provide a secret Pollinations API key (sk_…)."

        if is_publishable_key(api_key):
            warning = (
                "Text generation via /v1/chat/completions requires a secret API key "
                "(sk_...). Please create one at https://enter.pollinations.ai and "
                "run /api-key to update your credentials."
            )
            console.print(f"[red]{warning}[/red]")
            return "I’m ready once you provide a secret Pollinations API key (sk_…)."
        
        api_base_url = os.getenv('POLLINATIONS_API_URL', 'https://enter.pollinations.ai/api')
        messages = [{"role": "system", "content": build_system_message(text_model=model)}]
        for msg in conversation_history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})

        result = call_chat_completions_api(
            messages=messages,
            api_key=api_key,
            model=model,
            timeout=CHAT_COMPLETIONS_TIMEOUT,
            retries=CHAT_COMPLETIONS_RETRIES,
            api_base_url=api_base_url,
        )
        if result:
            return result['choices'][0]['message']['content'].strip()
        raise RuntimeError("Chat completions result is empty.")

    except (requests.HTTPError, ConnectionError, TimeoutError, ValueError, RuntimeError, requests.RequestException) as e:
        console.print(f"[red]Error generating text: {e}[/red]")
        simple_response = generate_simple_text(prompt, api_key)
        if simple_response:
            return simple_response
        return f"I understand you're asking about '{prompt[:50]}...'. However, I'm currently unable to connect to the AI service. Please try again later."


def call_chat_completions_api(
    messages: list,
    api_key: str,
    model: str,
    timeout: int,
    retries: int,
    api_base_url: str,
    payload_overrides: dict | None = None,
) -> dict:
    """Call the chat completions endpoint with retries."""
    url = f"{api_base_url}/generate/v1/chat/completions"

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.7
    }
    if payload_overrides:
        payload.update(payload_overrides)

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "XIBE-CHAT-CLI/1.0"
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    attempt = 0
    last_error = None
    while attempt < max(1, retries):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.Timeout as e:
            last_error = e
            attempt += 1
            if attempt < retries:
                time.sleep(min(2 ** attempt, 10))
            else:
                raise
        except requests.RequestException as e:
            last_error = e
            raise
    if last_error:
        raise last_error
    return {}


def generate_simple_text(prompt: str, api_key: str) -> str:
    """Fallback to the simple text endpoint when chat completions fails."""
    api_base_url = os.getenv('POLLINATIONS_API_URL', 'https://enter.pollinations.ai/api')
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"{api_base_url}/generate/text/{encoded_prompt}"

    headers = {"User-Agent": "XIBE-CHAT-CLI/1.0"}
    params = {}

    if api_key:
        if is_publishable_key(api_key):
            params["key"] = api_key
        else:
            headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        text = response.text.strip()
        if text:
            return text
    except requests.RequestException as e:
        console.print(f"[dim]Simple text fallback failed: {e}[/dim]")
    return ""


def generate_image(prompt: str, api_key: str = "", model: str = None) -> str:
    """Generate image for the given prompt and return file path."""
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

        # URL encode the prompt for the URL path
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Build query parameters (prompt goes in URL path, not params)
        params = {
            "model": model,
            "width": 1024,
            "height": 1024,
            "seed": 42,
            "enhance": "true",  # Enhance prompt using LLM for more detail
            "safe": "true",     # Enable strict NSFW filtering
            "private": "true"   # Prevent image from appearing in public feed
        }

        # Add premium features
        if api_key:
            params["nologo"] = "true"

        # Use new Pollinations API image generation endpoint
        # Format: /generate/image/{prompt}?model=flux&...
        api_base_url = os.getenv('POLLINATIONS_API_URL', 'https://enter.pollinations.ai/api')
        url = f"{api_base_url}/generate/image/{encoded_prompt}"

        # Make request with increased timeout for image generation
        headers = {"User-Agent": "XIBE-CHAT-CLI/1.0"}
        if api_key:
            # Bearer API key authentication required for new API
            headers["Authorization"] = f"Bearer {api_key}"
        else:
            # API key is required for the new API
            console.print("[yellow]Warning: API key is required for the new Pollinations API[/yellow]")
        
        response = requests.get(url, params=params, headers=headers, timeout=300)
        response.raise_for_status()

        # Save the image
        with open(image_path, 'wb') as f:
            f.write(response.content)

        return image_path

    except (ConnectionError, TimeoutError, ValueError, RuntimeError, OSError, requests.RequestException) as e:
        console.print(f"[red]Error generating image: {e}[/red]")
        # Check if response contains error message
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_text = e.response.text
                console.print(f"[dim]Service Error: {error_text}[/dim]")
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
        api_base_url = os.getenv('POLLINATIONS_API_URL', 'https://enter.pollinations.ai/api')
        url = f"{api_base_url}/generate/text/models"
        
        headers = {"User-Agent": "XIBE-CHAT-CLI/1.0"}
        # Add API key if available (may be required for some endpoints)
        api_key = get_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
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
            console.print(f"  🚀 [bold]{model['name']}[/bold]")
            console.print(f"    [dim]{model['description']}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error fetching text models: {e}[/red]")
        console.print("  [yellow]Note: Models change daily, check availability[/yellow]")
        console.print("  🚀 openai - OpenAI GPT-5 Mini")
        console.print("  🚀 mistral - Mistral Small 3.1 24B")
        console.print("  🚀 gemini - Gemini 2.5 Flash Lite")
    
    # Image models
    console.print("\n[bold green]Image Generation Models:[/bold green]")
    try:
        api_base_url = os.getenv('POLLINATIONS_API_URL', 'https://enter.pollinations.ai/api')
        url = f"{api_base_url}/generate/image/models"
        
        headers = {"User-Agent": "XIBE-CHAT-CLI/1.0"}
        # Add API key if available (may be required for some endpoints)
        api_key = get_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        models = response.json()
        
        for model in models:
            if isinstance(model, str):
                if model == 'nanobanana':
                    console.print(f"  🎨 [bold]{model}[/bold] [dim](requires input image for editing)[/dim]")
                else:
                    console.print(f"  🎨 [bold]{model}[/bold]")
            elif isinstance(model, dict):
                # Handle dict response format
                model_name = model.get('name', 'unknown')
                description = model.get('description', '')
                if model_name == 'nanobanana':
                    console.print(f"  🎨 [bold]{model_name}[/bold] [dim]({description})[/dim]")
                else:
                    console.print(f"  🎨 [bold]{model_name}[/bold] [dim]- {description}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error fetching image models: {e}[/red]")
        console.print("  [yellow]Note: Models change daily, check availability[/yellow]")
        console.print("  🎨 flux - High-quality image generation")
        console.print("  🎨 kontext - Image-to-image generation")
        console.print("  🎨 turbo - Fast image generation")
        console.print("  🎨 nanobanana - Image editing (requires input image)")
        console.print("  🎨 gptimage - GPT-powered generation")
    
    console.print(f"\n[dim]Use the 'switch' command to change models interactively[/dim]")
    console.print()
    console.print("[yellow]💡 Models change daily - use the 'models' command for current availability[/yellow]")
    console.print()


def choose_models_with_memory() -> dict:
    """Choose models with memory of last used models."""
    # Try to load saved preferences first
    saved_models = load_model_preferences()
    
    if saved_models:
        # Auto-use saved models silently
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
        console.print(f"  {i}. 🚀 {model['name']} - {model['description']}")
    
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
        if isinstance(model, str):
            if model == 'nanobanana':
                console.print(f"  {i}. 🎨 {model} (requires input image for editing)")
            else:
                console.print(f"  {i}. 🎨 {model}")
        elif isinstance(model, dict):
            # Handle dict response format
            model_name = model.get('name', 'unknown')
            description = model.get('description', '')
            if model_name == 'nanobanana':
                console.print(f"  {i}. 🎨 {model_name} (requires input image for editing)")
            else:
                console.print(f"  {i}. 🎨 {model_name} - {description}")
    
    while True:
        try:
            choice = console.input(f"\n[bold cyan]Choose image model (1-{len(image_models)}):[/bold cyan] ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(image_models):
                selected_model = image_models[int(choice) - 1]
                # Extract model name if it's a dict
                if isinstance(selected_model, dict):
                    selected_image = selected_model.get('name', selected_model)
                else:
                    selected_image = selected_model
                break
            else:
                console.print("[red]Invalid choice. Please enter a valid number.[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Using default image model: flux[/yellow]")
            selected_image = "flux"
            break
    
    # Extract image model name if it's a dict for display
    image_model_display = selected_image
    if isinstance(selected_image, dict):
        image_model_display = selected_image.get('name', str(selected_image))
        # Store just the name for saving
        selected_image = image_model_display
    
    console.print(f"\n[green]Selected Text Model: {selected_text}[/green]")
    console.print(f"[green]Selected Image Model: {image_model_display}[/green]")
    console.print()
    
    return {"text": selected_text, "image": selected_image}


def get_available_text_models() -> list:
    """Get list of available text models."""
    try:
        api_base_url = os.getenv('POLLINATIONS_API_URL', 'https://enter.pollinations.ai/api')
        url = f"{api_base_url}/generate/text/models"
        
        headers = {"User-Agent": "XIBE-CHAT-CLI/1.0"}
        # Add API key if available (may be required for some endpoints)
        api_key = get_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
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
            {'name': 'gemini', 'description': 'Gemini 2.5 Flash Lite', 'tier': 'seed'},
            {'name': 'openai', 'description': 'OpenAI GPT-5 Mini', 'tier': 'anonymous'},
            {'name': 'mistral', 'description': 'Mistral Small 3.1 24B', 'tier': 'anonymous'}
        ]


def get_available_image_models() -> list:
    """Get list of available image models."""
    try:
        api_base_url = os.getenv('POLLINATIONS_API_URL', 'https://enter.pollinations.ai/api')
        url = f"{api_base_url}/generate/image/models"
        
        headers = {"User-Agent": "XIBE-CHAT-CLI/1.0"}
        # Add API key if available (may be required for some endpoints)
        api_key = get_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
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


def analyze_query_with_ai(user_input: str, api_key: str, text_model: str) -> dict:
    """Ask the AI to analyze if the query should generate an image or respond with text."""
    try:
        if is_publishable_key(api_key):
            console.print(
                "[red]Query analysis requires a secret API key (sk_…). "
                "Create one at https://enter.pollinations.ai and run /api-key to update it.[/red]"
            )
            return {
                "action": "text",
                "response": "I’m here to help once you switch to a secret Pollinations API key (sk_…)."
            }

        api_base_url = os.getenv('POLLINATIONS_API_URL', 'https://enter.pollinations.ai/api')
        system_message = (
            "You are an AI assistant that analyzes user queries to determine if they should generate images or respond with text. "
            "Your task is to respond with a JSON object in this exact format:\n\n"
            'For images: {"action": "image", "response": "your conversational reply here", "image_prompt": "detailed image description here"}'
            '\n\nFor text: {"action": "text", "response": "your text response here"}'
            '\n\nRules:'
            '\n- If the user is asking to see, show, generate, create, draw, paint, or visualize something visual, set action to "image"'
            '\n- If the user is asking questions about appearance, looks, or what something looks like, set action to "image"'
            '\n- For image generation: provide a friendly, conversational "response" acknowledging the request, then a detailed "image_prompt"'
            '\n- Keep responses conversational and helpful, like "Sure, I\'d be happy to generate an image of..."'
            '\n- For image generation, create a detailed, vivid prompt that captures what the user wants to see (under 100 words)'
            '\n- If the query is about information, explanation, opinion, or non-visual content, set action to "text"'
            '\n- Do not add extra text or explanation outside the JSON object'
        )

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ]
        result = call_chat_completions_api(
            messages=messages,
            api_key=api_key,
            model=text_model,
            timeout=CHAT_COMPLETIONS_TIMEOUT,
            retries=CHAT_COMPLETIONS_RETRIES,
            api_base_url=api_base_url,
            payload_overrides={"max_tokens": 200, "temperature": 0.1},
        )
        ai_response = result['choices'][0]['message']['content'].strip()

        # Parse the JSON response
        try:
            parsed_response = json.loads(ai_response)
            return parsed_response
        except json.JSONDecodeError:
            # If AI didn't return valid JSON, assume text response
            return {
                "action": "text",
                "response": ai_response
            }

    except requests.HTTPError as e:
        console.print(f"[red]HTTP error in query analysis: {e}[/red]")
        
        # If 400 Bad Request, it might be the model or payload. Try fallback to simple text.
        if e.response.status_code == 400:
             console.print("[yellow]Falling back to simple text response due to API error...[/yellow]")
             return {
                "action": "text",
                "response": "I'm here to help! What would you like to know or discuss?"
            }

        # Fallback to simple text response if analysis fails
        return {
            "action": "text",
            "response": "I'm here to help! What would you like to know or discuss?"
        }
    except Exception as e:
        console.print(f"[red]Error in query analysis: {e}[/red]")
        # Fallback to simple text response if analysis fails
        return {
            "action": "text",
            "response": "I'm here to help! What would you like to know or discuss?"
        }


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
    # Quick test of AI analysis (uncomment to test)
    # test_queries = [
    #     "show me a picture of Paris",
    #     "what does quantum physics mean?",
    #     "draw a futuristic city",
    #     "explain machine learning",
    #     "generate an image of a sunset"
    # ]
    # token = get_api_token()
    # for query in test_queries:
    #     result = analyze_query_with_ai(query, token, "openai")
    #     print(f"'{query}' -> Action: {result.get('action', 'unknown')}")

    main()
