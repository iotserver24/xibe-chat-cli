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
import threading
import time
import uuid
from pathlib import Path
from datetime import datetime

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

#API token for premium features
API_TOKEN = "uNoesre5jXDzjhiY"

# Global agent sessions
agent_sessions = {}
active_agent_session = None


class CLIAgent:
    """Manages CLI sessions for agent mode."""
    
    def __init__(self, session_id: str, cli_type: str, working_dir: str = None):
        self.session_id = session_id
        self.cli_type = cli_type.lower()
        self.working_dir = working_dir or os.getcwd()
        self.process = None
        self.is_active = False
        self.command_history = []
        self.last_output = ""
        self.created_at = datetime.now()
        
    def start_session(self, visible_window: bool = False) -> bool:
        """Start the CLI session."""
        try:
            if self.cli_type == "powershell":
                if visible_window:
                    # Open visible PowerShell window
                    if platform.system() == "Windows":
                        subprocess.Popen([
                            "start", "powershell", "-NoExit", 
                            "-Command", f"cd '{self.working_dir}'; Write-Host 'XIBE Agent PowerShell Session' -ForegroundColor Green; Write-Host 'Working Directory: {self.working_dir}' -ForegroundColor Yellow"
                        ], shell=True)
                    else:
                        # For non-Windows systems, try to open terminal
                        subprocess.Popen(["gnome-terminal", "--", "powershell"], cwd=self.working_dir)
                    self.is_active = True
                    return True
                else:
                    # Background PowerShell session
                    self.process = subprocess.Popen(
                        ["powershell", "-NoExit", "-Command", "cd '{}'".format(self.working_dir)],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=self.working_dir
                    )
            elif self.cli_type == "cmd":
                if visible_window:
                    # Open visible CMD window
                    if platform.system() == "Windows":
                        subprocess.Popen([
                            "start", "cmd", "/k", 
                            f"cd /d {self.working_dir} && echo XIBE Agent CMD Session && echo Working Directory: {self.working_dir}"
                        ], shell=True)
                    else:
                        subprocess.Popen(["gnome-terminal", "--", "cmd"], cwd=self.working_dir)
                    self.is_active = True
                    return True
                else:
                    # Background CMD session
                    self.process = subprocess.Popen(
                        ["cmd", "/k"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=self.working_dir
                    )
            elif self.cli_type in ["bash", "sh"]:
                if visible_window:
                    # Open visible bash terminal
                    subprocess.Popen(["gnome-terminal", "--", "bash"], cwd=self.working_dir)
                    self.is_active = True
                    return True
                else:
                    # Background bash session
                    self.process = subprocess.Popen(
                        ["bash"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        cwd=self.working_dir
                    )
            else:
                return False
                
            self.is_active = True
            return True
            
        except Exception as e:
            console.print(f"[red]Error starting {self.cli_type} session: {e}[/red]")
            return False
    
    def execute_command(self, command: str) -> str:
        """Execute a command in the CLI session."""
        if not self.is_active or not self.process:
            return "Error: Session not active"
            
        try:
            # Add command to history
            self.command_history.append(command)
            
            # Send command to process
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
            
            # Read output (with timeout)
            output = ""
            try:
                # Simple read with timeout simulation
                time.sleep(0.5)  # Give command time to execute
                if self.process.poll() is None:  # Process still running
                    # For now, return a simulated response
                    output = f"Executed: {command}\nWorking directory: {self.working_dir}"
                else:
                    output = "Process ended"
            except:
                output = f"Command executed: {command}"
                
            self.last_output = output
            return output
            
        except Exception as e:
            return f"Error executing command: {e}"
    
    def get_status(self) -> dict:
        """Get session status information."""
        return {
            "session_id": self.session_id,
            "cli_type": self.cli_type,
            "working_dir": self.working_dir,
            "is_active": self.is_active,
            "command_count": len(self.command_history),
            "created_at": self.created_at.isoformat(),
            "last_command": self.command_history[-1] if self.command_history else None
        }
    
    def close_session(self):
        """Close the CLI session."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
        self.is_active = False


def create_agent_session(cli_type: str, working_dir: str = None, visible_window: bool = False) -> str:
    """Create a new agent session."""
    session_id = f"session_{len(agent_sessions) + 1}_{cli_type}"
    session = CLIAgent(session_id, cli_type, working_dir)
    
    if session.start_session(visible_window):
        agent_sessions[session_id] = session
        global active_agent_session
        active_agent_session = session_id
        return session_id
    else:
        return None


def get_active_agent_session() -> CLIAgent:
    """Get the currently active agent session."""
    if active_agent_session and active_agent_session in agent_sessions:
        return agent_sessions[active_agent_session]
    return None


def close_all_agent_sessions():
    """Close all agent sessions."""
    global active_agent_session
    for session in agent_sessions.values():
        session.close_session()
    agent_sessions.clear()
    active_agent_session = None


def build_agent_system_message(cli_session: CLIAgent, task: str) -> str:
    """Build system message for agent mode AI."""
    return f"""You are an AI agent controlling a {cli_session.cli_type} CLI session. Your task is to help the user complete: "{task}"

Current context:
- CLI Type: {cli_session.cli_type}
- Working Directory: {cli_session.working_dir}
- Commands executed so far: {len(cli_session.command_history)}
- Last command: {cli_session.command_history[-1] if cli_session.command_history else 'None'}

Your job is to:
1. Break down the user's task into specific CLI commands
2. Execute commands one by one
3. Analyze the output of each command
4. Continue until the task is complete
5. Provide clear feedback about what you're doing

Available commands for {cli_session.cli_type}:
- Directory operations: cd, mkdir, rmdir, dir (Windows) / ls (Unix)
- File operations: echo, type (Windows) / cat (Unix), copy (Windows) / cp (Unix)
- Other: pwd, whoami, date, etc.

Respond with ONLY the next command to execute, or "TASK_COMPLETE" if finished, or "ERROR: description" if something went wrong."""


def execute_agent_task(task: str, conversation_history: list = None) -> None:
    """Execute a task using the agent system."""
    if conversation_history is None:
        conversation_history = []
    
    # Get active session
    session = get_active_agent_session()
    if not session:
        console.print("[red]No active agent session. Start one with 'agent: open <cli_type>'[/red]")
        return
    
    # Display task
    task_panel = Panel(
        f"🎯 [bold]Task:[/bold] {task}\n"
        f"🤖 [bold]AI Agent:[/bold] Analyzing and executing...\n"
        f"🖥️ [bold]CLI:[/bold] {session.cli_type}\n"
        f"📂 [bold]Directory:[/bold] {session.working_dir}",
        style="cyan",
        title="[bold white]🤖 XIBE Agent Mode[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="cyan"
    )
    console.print(task_panel)
    
    # Execute task step by step
    max_steps = 10  # Prevent infinite loops
    step = 1
    
    while step <= max_steps:
        # Get AI's next command
        with console.status(f"[bold green]🤖 AI Agent thinking... (Step {step}/{max_steps})[/bold green]", spinner="dots"):
            ai_response = generate_agent_command(task, session, conversation_history)
        
        # Check if task is complete
        if "TASK_COMPLETE" in ai_response.upper():
            success_panel = Panel(
                f"✅ [green]Task completed successfully![/green]\n\n"
                f"📊 [bold]Steps taken:[/bold] {step}\n"
                f"📝 [bold]Commands executed:[/bold] {len(session.command_history)}\n"
                f"🎯 [bold]Task:[/bold] {task}",
                style="green",
                title="[bold white]🎉 Task Complete[/bold white]",
                title_align="center",
                padding=(1, 2),
                border_style="green"
            )
            console.print(success_panel)
            break
            
        # Check for errors
        if "ERROR:" in ai_response.upper():
            error_panel = Panel(
                f"❌ [red]Agent encountered an error:[/red]\n\n"
                f"{ai_response}\n\n"
                f"[dim]Task stopped at step {step}[/dim]",
                style="red",
                title="[bold white]⚠️ Agent Error[/bold white]",
                title_align="center",
                padding=(1, 2),
                border_style="red"
            )
            console.print(error_panel)
            break
        
        # Execute the command
        command = ai_response.strip()
        
        # Display what AI is doing
        action_panel = Panel(
            f"⚡ [bold]Step {step}:[/bold] {command}\n"
            f"🖥️ [bold]Executing in {session.cli_type}...[/bold]",
            style="yellow",
            title="[bold white]🤖 AI Agent Action[/bold white]",
            title_align="left",
            padding=(1, 2),
            border_style="yellow"
        )
        console.print(action_panel)
        
        # Execute command
        output = session.execute_command(command)
        
        # Display result
        result_panel = Panel(
            f"📤 [bold]Command:[/bold] {command}\n"
            f"📥 [bold]Output:[/bold]\n{output}",
            style="blue",
            title="[bold white]📋 Command Result[/bold white]",
            title_align="left",
            padding=(1, 2),
            border_style="blue"
        )
        console.print(result_panel)
        
        step += 1
        console.print()  # Add spacing
    
    if step > max_steps:
        console.print("[yellow]⚠️ Task reached maximum steps. Agent stopping for safety.[/yellow]")


def generate_agent_command(task: str, session: CLIAgent, conversation_history: list) -> str:
    """Generate the next command for the agent to execute."""
    try:
        # Build system message for agent
        system_message = build_agent_system_message(session, task)
        
        # Get context from session
        context = f"Task: {task}\nCLI: {session.cli_type}\nWorking Directory: {session.working_dir}\n"
        if session.command_history:
            context += f"Previous commands: {', '.join(session.command_history[-3:])}\n"
        if session.last_output:
            context += f"Last output: {session.last_output[:200]}..."
        
        # Build messages for AI
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history
        for msg in conversation_history[-4:]:  # Last 4 messages for context
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current context
        messages.append({"role": "user", "content": context})
        
        # Make API call
        text_api_url = os.getenv('TEXT_API_URL', 'https://text.pollinations.ai')
        url = f"{text_api_url}/openai"
        
        payload = {
            "model": "openai-large",  # Force openai-large for agent mode
            "messages": messages,
            "max_tokens": 200,
            "temperature": 0.3  # Lower temperature for more focused responses
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "XIBE-CHAT-CLI/1.0"
        }
        
        # Add authentication
        token = get_api_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
            sep = '&' if '?' in url else '?'
            url = f"{url}{sep}token={urllib.parse.quote(token)}"
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
        
    except Exception as e:
        return f"ERROR: Failed to generate command - {e}"


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
    """Get the hardcoded API token for premium features."""
    return API_TOKEN


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
        "  [cyan]/image-settings[/cyan] - View image generation settings",
        style="green",
        title="[bold white]💬 Chat Commands[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="green"
    )
    console.print(chat_commands)
    
    # Agent Commands
    agent_commands = Panel(
        "🤖 [bold]Agent Commands:[/bold]\n\n"
        "  [cyan]/demo-agent[/cyan] - Show agent mode demo\n"
        "  [cyan]/sessions[/cyan] - Show active CLI sessions\n"
        "  [cyan]/close-agent[/cyan] - Close all agent sessions\n"
        "  [cyan]agent: open <cli>[/cyan] - Start CLI session\n"
        "  [cyan]agent: <command>[/cyan] - Execute command\n\n"
        "[dim]Natural language tasks auto-detect agent mode[/dim]",
        style="magenta",
        title="[bold white]🤖 Agent Commands[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="magenta"
    )
    console.print(agent_commands)
    
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
        "  [yellow]Normal Text[/yellow] - Just type and press Enter\n"
        "  [yellow]img: prompt[/yellow] - Generate images\n"
        "  [yellow]Multiline[/yellow] - Ctrl+N for new lines\n\n"
        "[dim]Example: img: a beautiful sunset over mountains[/dim]",
        style="yellow",
        title="[bold white]⌨️ Input Methods[/bold white]",
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
        "  • Models change daily - use 'models' for current availability\n"
        "  • Premium features included for enhanced experience\n"
        "  • Conversation history limited to 10 exchanges for memory\n"
        "  • Generated images saved in 'generated_images' folder\n"
        "  • All models available with no additional setup",
        style="magenta",
        title="[bold white]💡 Pro Tips[/bold white]",
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


def show_agent_sessions() -> None:
    """Show active agent sessions."""
    if not agent_sessions:
        sessions_panel = Panel(
            "ℹ️ [yellow]No active CLI sessions[/yellow]\n\n"
            "Start a session with: agent: open\n"
            "Examples:\n"
            "• agent: open powershell\n"
            "• agent: open bash\n"
            "• agent: open cmd",
            style="yellow",
            title="[bold white]🤖 CLI Agent Sessions[/bold white]",
            title_align="center",
            padding=(1, 2),
            border_style="yellow"
        )
        console.print(sessions_panel)
    else:
        sessions_info = ""
        for session_id, session in agent_sessions.items():
            status = "🟢 Active" if session.is_active else "🔴 Inactive"
            active_indicator = "👑" if session_id == active_agent_session else "  "
            sessions_info += f"{active_indicator} 🆔 [bold]{session_id}[/bold]\n"
            sessions_info += f"   🖥️ CLI: {session.cli_type}\n"
            sessions_info += f"   📂 Directory: {session.working_dir}\n"
            sessions_info += f"   📊 Commands: {len(session.command_history)}\n"
            sessions_info += f"   {status}\n\n"
        
        sessions_panel = Panel(
            sessions_info.strip(),
            style="green",
            title="[bold white]🤖 Active CLI Sessions[/bold white]",
            title_align="center",
            padding=(1, 2),
            border_style="green"
        )
        console.print(sessions_panel)


def show_agent_demo() -> None:
    """Show agent mode demo and instructions."""
    demo_panel = Panel(
        "🤖 Agent Mode Demo\n"
        "==================================================\n"
        "Example Agent Mode Commands:\n"
        "  • agent: open powershell - Start PowerShell (background)\n"
        "  • agent: open powershell visible - Start PowerShell (visible window)\n"
        "  • agent: dir - List directory contents\n"
        "  • agent: mkdir test_folder - Create directory\n"
        "  • agent: echo 'Hello from Agent Mode!' - Display message\n"
        "  • /sessions - Show active CLI sessions\n"
        "  • /close-agent - Close all agent sessions\n\n"
        "Natural Language Commands:\n"
        "  • Create a new folder called 'my_project'\n"
        "  • List all files in the current directory\n"
        "  • Show me the current working directory\n"
        "  • Create a Python file with hello world\n\n"
        "✨ Agent Mode is now active! Try the commands above.",
        style="cyan",
        title="[bold white]🤖 Agent Mode Demo[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="cyan"
    )
    console.print(demo_panel)


def handle_agent_command(command: str, token: str, conversation_history: list) -> None:
    """Handle agent mode commands."""
    if not command:
        console.print("[red]Please provide an agent command after 'agent:'[/red]")
        return
    
    # Parse agent command
    parts = command.lower().split()
    
    if parts[0] == "open":
        # Open new CLI session
        if len(parts) > 1:
            cli_type = parts[1]
            visible_window = len(parts) > 2 and parts[2] == "visible"
            session_id = create_agent_session(cli_type, visible_window=visible_window)
            if session_id:
                session = agent_sessions[session_id]
                window_type = "visible window" if visible_window else "background session"
                success_panel = Panel(
                    f"✅ Started {cli_type} session successfully!\n\n"
                    f"🆔 Session ID: {session_id}\n"
                    f"🎯 CLI Type: {session.cli_type}\n"
                    f"📂 Working Directory: {session.working_dir}\n"
                    f"🖥️ Mode: {window_type}\n\n"
                    f"Ready to execute commands. Use 'agent: ' to run commands.",
                    style="green",
                    title="[bold white]🤖 CLI Agent Started[/bold white]",
                    title_align="center",
                    padding=(1, 2),
                    border_style="green"
                )
                console.print(success_panel)
            else:
                console.print(f"[red]Failed to start {cli_type} session[/red]")
        else:
            console.print("[red]Please specify CLI type: agent: open powershell|cmd|bash [visible][/red]")
    
    elif parts[0] == "close":
        # Close current session
        global active_agent_session
        if active_agent_session:
            session = agent_sessions[active_agent_session]
            session.close_session()
            del agent_sessions[active_agent_session]
            active_agent_session = None
            console.print("[green]✅ Agent session closed[/green]")
        else:
            console.print("[yellow]No active session to close[/yellow]")
    
    else:
        # Execute command in active session
        session = get_active_agent_session()
        if session:
            # Direct command execution
            output = session.execute_command(command)
            result_panel = Panel(
                f"📤 [bold]Command:[/bold] {command}\n"
                f"📥 [bold]Output:[/bold]\n{output}",
                style="blue",
                title="[bold white]📋 Command Result[/bold white]",
                title_align="left",
                padding=(1, 2),
                border_style="blue"
            )
            console.print(result_panel)
        else:
            console.print("[red]No active agent session. Start one with 'agent: open <cli_type>'[/red]")


def is_natural_language_task(text: str) -> bool:
    """Check if the text looks like a natural language task for agent mode."""
    task_indicators = [
        "create", "make", "build", "generate", "write", "add", "new",
        "folder", "file", "directory", "script", "project",
        "list", "show", "display", "find", "search",
        "copy", "move", "delete", "remove", "rename",
        "install", "setup", "configure", "run", "execute"
    ]
    
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in task_indicators)


def run_chat_interface() -> None:
    """Run the interactive chat interface."""
    # Get authentication token
    token = get_api_token()
    
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
                
                success_panel = Panel(
                    f"✅ [green]Successfully switched models![/green]\n\n"
                    f"🤖 [bold]Text Model:[/bold] {selected_models['text']}\n"
                    f"🎨 [bold]Image Model:[/bold] {selected_models['image']}\n\n"
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
                new_session_panel = Panel(
                    f"🆕 [green]New chat session started![/green]\n\n"
                    f"🤖 [bold]Text Model:[/bold] {selected_models['text']}\n"
                    f"🎨 [bold]Image Model:[/bold] {selected_models['image']}\n\n"
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
            elif user_input.lower() == '/demo-agent':
                show_agent_demo()
                continue
            elif user_input.lower() == '/sessions':
                show_agent_sessions()
                continue
            elif user_input.lower() == '/close-agent':
                close_all_agent_sessions()
                console.print("[green]✅ All agent sessions closed[/green]")
                continue

            # Check if empty input
            if not user_input:
                continue

            # Handle agent mode commands
            if user_input.startswith('agent:'):
                agent_command = user_input[6:].strip()  # Remove 'agent:' prefix
                handle_agent_command(agent_command, token, conversation_history)
                continue
            # Handle image generation requests
            elif user_input.startswith('img:'):
                image_prompt = user_input[4:].strip()  # Remove 'img:' prefix
                if image_prompt:
                    handle_image_generation(image_prompt, token, selected_models['image'])
                else:
                    console.print("[red]Please provide a prompt after 'img:'[/red]")
            else:
                # Check if this is a natural language task for agent mode
                if is_natural_language_task(user_input) and get_active_agent_session():
                    # Execute as agent task
                    execute_agent_task(user_input, conversation_history)
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
        response = generate_text(prompt, token, conversation_history, model)

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


def handle_image_generation(prompt: str, token: str = "", model: str = None) -> None:
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
        image_path = generate_image(prompt, token, model)

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


def generate_text(prompt: str, token: str = "", conversation_history: list = None, model: str = None) -> str:
    """Generate text response for the given prompt."""
    if conversation_history is None:
        conversation_history = []
    if model is None:
        model = os.getenv('TEXT_MODEL', 'openai')
    
    try:
        # Use text generation endpoint
        text_api_url = os.getenv('TEXT_API_URL', 'https://text.pollinations.ai')
        
        url = f"{text_api_url}/openai"
        # Append token as query parameter if available
        if token:
            sep = '&' if '?' in url else '?'
            url = f"{url}{sep}token={urllib.parse.quote(token)}"
        
        # Build messages array with system context and conversation history
        messages = [{"role": "system", "content": build_system_message(text_model=model)}]
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
        
        # Add authentication if available
        if token:
            headers["Authorization"] = f"Bearer {token}"
            # Also send token as Referer
            headers["Referer"] = f"{text_api_url}/openai?token={urllib.parse.quote(token)}"
        
        # Make request
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result['choices'][0]['message']['content'].strip()

    except (ConnectionError, TimeoutError, ValueError, RuntimeError, requests.RequestException) as e:
        console.print(f"[red]Error generating text: {e}[/red]")
        # Fallback to a simple response if service fails
        return f"I understand you're asking about '{prompt[:50]}...'. However, I'm currently unable to connect to the AI service. Please try again later."


def generate_image(prompt: str, token: str = "", model: str = None) -> str:
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

        # Add premium features
        if token:
            params["nologo"] = "true"
            params["token"] = token

        # Use the image generation endpoint
        image_api_url = os.getenv('IMAGE_API_URL', 'https://image.pollinations.ai')
        url = f"{image_api_url}/prompt/{encoded_prompt}"

        # Make request with increased timeout for image generation
        headers = {"User-Agent": "XIBE-CHAT-CLI/1.0"}
        if token:
            # Also send token via Authorization and Referer
            headers["Authorization"] = f"Bearer {token}"
            headers["Referer"] = f"{image_api_url}/prompt/{encoded_prompt}?token={urllib.parse.quote(token)}"
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
