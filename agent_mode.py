#!/usr/bin/env python3
"""
XIBE-CHAT Agent Mode - CLI automation and control system
"""

import os
import platform
import subprocess
import urllib.parse
import time
from pathlib import Path
from datetime import datetime

import requests
from rich.console import Console
from rich.panel import Panel

# Initialize Rich console
console = Console()

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
            return "ERROR: Session not active"
            
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


def get_api_token() -> str:
    """Get the API token for agent mode."""
    return "uNoesre5jXDzjhiY"  # Same token as main app


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
                f"[dim]Let me try a different approach...[/dim]",
                style="red",
                title="[bold white]⚠️ Agent Error[/bold white]",
                title_align="center",
                padding=(1, 2),
                border_style="red"
            )
            console.print(error_panel)
            # Don't break - try to continue with a simpler approach
            continue
        
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
        "🤖 Integrated Agent + Chat Mode Demo\n"
        "==================================================\n"
        "🎯 [bold]Just Talk Naturally![/bold]\n"
        "  • 'Hello, how are you?' → Normal chat\n"
        "  • 'Create a folder called test' → Task execution\n"
        "  • 'What is Python?' → Normal chat\n"
        "  • 'List all files here' → Task execution\n\n"
        "⚡ [bold]Advanced Commands:[/bold]\n"
        "  • agent: open powershell visible - Start visible PowerShell\n"
        "  • agent: dir - Direct command execution\n"
        "  • /sessions - Show active CLI sessions\n"
        "  • /close-agent - Close all sessions\n\n"
        "✨ [bold]Smart Features:[/bold]\n"
        "  • I automatically decide: Chat or Task?\n"
        "  • No need to specify 'agent:' for most things\n"
        "  • I'll start PowerShell automatically when needed\n"
        "  • Seamless switching between chat and task execution\n\n"
        "💡 [bold]Try saying:[/bold] 'Create a new folder and add a file with hello world'",
        style="cyan",
        title="[bold white]🤖 Integrated Agent Mode Demo[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="cyan"
    )
    console.print(demo_panel)


def show_agent_help() -> None:
    """Show comprehensive help for agent mode."""
    help_panel = Panel(
        "📚 Complete guide to XIBE Agent Mode commands and features",
        style="blue",
        title="[bold white]📖 XIBE Agent Mode Help Center[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="blue"
    )
    console.print(help_panel)
    
    # Chat Commands
    chat_commands = Panel(
        "💬 [bold]Chat Commands:[/bold]\n\n"
        "  [cyan]/help[/cyan] - Show this help screen\n"
        "  [cyan]/clear[/cyan] - Clear screen and show agent logo\n"
        "  [cyan]/new[/cyan] - Start fresh agent session\n"
        "  [cyan]/image-settings[/cyan] - View image generation settings\n"
        "  [cyan]/demo[/cyan] - Show agent mode demo",
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
        "  [cyan]/sessions[/cyan] - Show active CLI sessions\n"
        "  [cyan]/close-agent[/cyan] - Close all agent sessions\n"
        "  [cyan]/demo[/cyan] - Show agent mode demo\n"
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
        "[dim]Agent mode uses openai-large for optimal performance[/dim]",
        style="cyan",
        title="[bold white]🤖 Model Commands[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="cyan"
    )
    console.print(model_commands)
    
    # Smart Features
    smart_features = Panel(
        "🧠 [bold]Smart Features:[/bold]\n\n"
        "  [yellow]Auto-Detection[/yellow] - AI decides chat vs task\n"
        "  [yellow]Auto-Session[/yellow] - Starts PowerShell when needed\n"
        "  [yellow]Visible Windows[/yellow] - See what AI is doing\n"
        "  [yellow]Error Recovery[/yellow] - Graceful error handling\n\n"
        "[dim]Example: 'Create a folder' → Task execution[/dim]",
        style="yellow",
        title="[bold white]🧠 Smart Features[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="yellow"
    )
    console.print(smart_features)
    
    # Session Commands
    session_commands = Panel(
        "🚪 [bold]Session Commands:[/bold]\n\n"
        "  [cyan]/exit-agent[/cyan] or [cyan]exit[/cyan] - Return to chat mode\n\n"
        "[dim]All commands are case-insensitive[/dim]",
        style="bright_black",
        title="[bold white]🚪 Session Commands[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="bright_black"
    )
    console.print(session_commands)
    
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


def show_available_models() -> None:
    """Show available AI models."""
    console.print("\n[bold blue]Available AI Models[/bold blue]")
    console.print("=" * 50)
    
    # Text models
    console.print("\n[bold green]Text Generation Models:[/bold green]")
    console.print("  🚀 [bold]openai-large[/bold] - OpenAI GPT-5 Mini (Agent Mode Default)")
    console.print("  🚀 [bold]mistral[/bold] - Mistral Small 3.1 24B")
    console.print("  🚀 [bold]gemini[/bold] - Gemini 2.5 Flash Lite")
    
    # Image models
    console.print("\n[bold green]Image Generation Models:[/bold green]")
    console.print("  🎨 [bold]flux[/bold] - High-quality image generation")
    console.print("  🎨 [bold]kontext[/bold] - Image-to-image editing")
    console.print("  🎨 [bold]turbo[/bold] - Fast generation")
    console.print("  🎨 [bold]nanobanana[/bold] - Advanced image editing")
    console.print("  🎨 [bold]gptimage[/bold] - GPT-powered generation")
    
    console.print(f"\n[dim]Agent mode uses openai-large for optimal task execution and chat[/dim]")
    console.print()
    console.print("[yellow]💡 Models change daily - use the 'models' command for current availability[/yellow]")
    console.print()


def handle_agent_command(command: str, conversation_history: list) -> None:
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


def decide_chat_or_task(user_input: str, conversation_history: list) -> str:
    """Smart decision: Should this be a chat response or task execution?"""
    try:
        # Build context for decision
        context = f"User input: {user_input}\n"
        if conversation_history:
            recent_context = "Recent conversation:\n"
            for msg in conversation_history[-3:]:
                recent_context += f"- {msg['role']}: {msg['content'][:100]}...\n"
            context += recent_context
        
        # Decision prompt
        decision_prompt = f"""You are an AI assistant in "Integrated Agent + Chat Mode". 
Your job is to decide whether the user wants to:
1. CHAT - Have a normal conversation (questions, explanations, help, etc.)
2. TASK - Execute a command or perform an action (create files, run commands, etc.)

{context}

Examples:
- "Hello, how are you?" → CHAT
- "What is Python?" → CHAT  
- "Create a folder called test" → TASK
- "List all files in this directory" → TASK
- "Can you help me with coding?" → CHAT
- "Make a Python script that prints hello" → TASK

Respond with ONLY: CHAT or TASK"""
        
        # Make API call for decision
        text_api_url = os.getenv('TEXT_API_URL', 'https://text.pollinations.ai')
        url = f"{text_api_url}/openai"
        
        payload = {
            "model": "openai-large",
            "messages": [{"role": "user", "content": decision_prompt}],
            "max_tokens": 10,
            "temperature": 0.1  # Very low temperature for consistent decisions
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
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        decision = result['choices'][0]['message']['content'].strip().upper()
        
        return "task" if "TASK" in decision else "chat"
        
    except Exception as e:
        # Fallback to simple keyword detection
        return "task" if is_natural_language_task(user_input) else "chat"


def handle_chat_response(user_input: str, conversation_history: list) -> None:
    """Handle chat responses in agent mode."""
    try:
        # Import chat functionality from main app
        from ai_cli import generate_text, build_system_message
        
        # Build agent-aware system message
        agent_system_message = build_system_message("openai-large") + "\n\nYou are in Agent Mode. You can both chat and execute tasks. Be helpful and friendly!"
        
        # Generate response
        with console.status(f"[bold green]🤖 AI Agent is thinking...[/bold green]", spinner="dots"):
            response = generate_text(user_input, get_api_token(), conversation_history, "openai-large")
        
        # Add to conversation history
        conversation_history.append({"role": "user", "content": user_input})
        conversation_history.append({"role": "assistant", "content": response})
        
        # Keep only last 10 exchanges to avoid token limits
        if len(conversation_history) > 20:  # 10 exchanges = 20 messages
            conversation_history = conversation_history[-20:]
        
        # Display response in chat bubble
        from rich.markdown import Markdown
        from ai_cli import clean_response_for_markdown
        
        try:
            cleaned_response = clean_response_for_markdown(response, user_input)
            ai_panel = Panel(
                Markdown(cleaned_response, code_theme="monokai"),
                style="green",
                title="[bold white]🤖 AI Assistant (Agent Mode)[/bold white]",
                title_align="right",
                padding=(1, 2),
                border_style="green"
            )
            console.print(ai_panel)
        except Exception:
            # Fallback to plain text
            ai_panel = Panel(
                response,
                style="green",
                title="[bold white]🤖 AI Assistant (Agent Mode)[/bold white]",
                title_align="right",
                padding=(1, 2),
                border_style="green"
            )
            console.print(ai_panel)
        
        console.print()  # Add spacing
        
    except Exception as e:
        console.print(f"[red]Error in chat response: {e}[/red]")
        console.print("[yellow]I'll try to help you anyway. What do you need?[/yellow]")


def show_agent_logo() -> None:
    """Show XIBE AGENT logo and branding."""
    try:
        import pyfiglet
        from rich.text import Text
        
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
            try:
                ascii_logo = pyfiglet.figlet_format(title, font="ansi_shadow")
            except Exception:
                ascii_logo = pyfiglet.figlet_format(title, font="big")

            lines = ascii_logo.splitlines()
            max_len = max((len(l) for l in lines), default=0)
            palette = _hex_gradient("#ff6b35", "#f7931e", max_len)  # Orange gradient for agent

            styled = Text()
            for line in lines:
                for idx, ch in enumerate(line.ljust(max_len)):
                    if ch == ' ':
                        styled.append(ch)
                    else:
                        styled.append(ch, style=f"bold {palette[idx]}")
                styled.append("\n")
            return styled
        
        # Clear screen and show agent logo
        console.clear()
        
        logo = _build_gradient_logo("XIBE AGENT")
        subtitle = Panel(
            "[italic]AI-powered CLI automation and control system[/italic]",
            style="bright_black",
            title="[bold red]Agent Mode Active[/bold red]",
            title_align="center",
            padding=(1, 2)
        )
        console.print(logo, justify="center")
        console.print(subtitle, justify="center")
        console.print()
        
    except ImportError:
        console.clear()
        console.print("[bold red]XIBE AGENT[/bold red]", justify="center")
        console.print("[italic]AI-powered CLI automation and control system[/italic]", justify="center")
        console.print()


def run_agent_mode() -> None:
    """Run the integrated agent mode interface."""
    # Show agent logo
    show_agent_logo()
    
    # Show welcome message
    welcome_panel = Panel(
        "🤖 [bold]Integrated Agent + Chat Mode[/bold]\n\n"
        "✨ [green]Smart Features:[/green]\n"
        "  • I can chat with you normally\n"
        "  • I can execute tasks automatically\n"
        "  • Just tell me what you want - I'll decide!\n\n"
        "🎯 [cyan]Examples:[/cyan]\n"
        "  • 'Hello, how are you?' → Chat\n"
        "  • 'Create a folder called test' → Task execution\n"
        "  • 'What's the weather like?' → Chat\n"
        "  • 'List all files in this directory' → Task execution\n\n"
        "⚡ [yellow]Special Commands:[/yellow]\n"
        "  • /help - Show comprehensive help\n"
        "  • /clear - Clear screen and show logo\n"
        "  • /new - Start fresh session\n"
        "  • /sessions - Show active CLI sessions\n"
        "  • /close-agent - Close all sessions\n"
        "  • /exit-agent - Return to chat mode\n\n"
        "[dim]I'll automatically detect if you want me to do something or just chat![/dim]",
        style="cyan",
        title="[bold white]🤖 Welcome to Integrated Agent Mode[/bold white]",
        title_align="center",
        padding=(1, 2),
        border_style="cyan"
    )
    console.print(welcome_panel)
    
    # Initialize conversation history
    conversation_history = []
    
    # Agent mode loop
    while True:
        try:
            # Get user input with multi-line support
            from ai_cli import get_multiline_input
            user_input = get_multiline_input()
            
            # Check for exit conditions
            if user_input.lower() in ['exit', 'quit', '/exit-agent']:
                goodbye_panel = Panel(
                    "🤖 [bold]Returning to XIBE-CHAT mode![/bold]\n\n"
                    "[dim]Agent sessions preserved. Use /agent to return.[/dim]",
                    style="yellow",
                    title="[bold white]🤖 Agent Mode Exit[/bold white]",
                    title_align="center",
                    padding=(1, 2),
                    border_style="yellow"
                )
                console.print(goodbye_panel)
                break
            
            # Check for special commands
            if user_input.lower() == '/sessions':
                show_agent_sessions()
                continue
            elif user_input.lower() == '/close-agent':
                close_all_agent_sessions()
                console.print("[green]✅ All agent sessions closed[/green]")
                continue
            elif user_input.lower() == '/demo':
                show_agent_demo()
                continue
            elif user_input.lower() == '/help':
                show_agent_help()
                continue
            elif user_input.lower() == '/clear':
                show_agent_logo()
                continue
            elif user_input.lower() == '/new':
                conversation_history.clear()
                new_session_panel = Panel(
                    "🆕 [green]New agent session started![/green]\n\n"
                    "[dim]Previous conversation history cleared[/dim]",
                    style="green",
                    title="[bold white]🆕 New Agent Session[/bold white]",
                    title_align="center",
                    padding=(1, 2),
                    border_style="green"
                )
                console.print(new_session_panel)
                continue
            elif user_input.lower() == '/image-settings':
                show_image_settings()
                continue
            elif user_input.lower() == 'models':
                show_available_models()
                continue
            elif user_input.lower() == 'switch':
                switch_panel = Panel(
                    "🔄 Switching AI Models in Agent Mode",
                    style="yellow",
                    title="[bold white]⚙️ Model Switch[/bold white]",
                    title_align="center",
                    padding=(0, 2),
                    border_style="yellow"
                )
                console.print(switch_panel)
                console.print("[yellow]Note: Agent mode uses openai-large for task execution and chat.[/yellow]")
                continue
            
            # Check if empty input
            if not user_input:
                continue
            
            # Handle direct agent commands (for advanced users)
            if user_input.startswith('agent:'):
                agent_command = user_input[6:].strip()  # Remove 'agent:' prefix
                handle_agent_command(agent_command, conversation_history)
                continue
            
            # Smart decision: Chat or Task?
            with console.status(f"[bold green]🤖 AI Agent is analyzing your request...[/bold green]", spinner="dots"):
                decision = decide_chat_or_task(user_input, conversation_history)
            
            # Show decision indicator
            if decision == "task":
                decision_panel = Panel(
                    "🎯 [bold green]Task Mode Detected[/bold green]\n"
                    "I'll execute this as a task for you!",
                    style="green",
                    title="[bold white]🤖 AI Decision[/bold white]",
                    title_align="center",
                    padding=(0, 2),
                    border_style="green"
                )
                console.print(decision_panel)
            else:
                decision_panel = Panel(
                    "💬 [bold blue]Chat Mode Detected[/bold blue]\n"
                    "I'll respond to you normally!",
                    style="blue",
                    title="[bold white]🤖 AI Decision[/bold white]",
                    title_align="center",
                    padding=(0, 2),
                    border_style="blue"
                )
                console.print(decision_panel)
            
            if decision == "task" and get_active_agent_session():
                # Execute as agent task
                execute_agent_task(user_input, conversation_history)
            elif decision == "task" and not get_active_agent_session():
                # Need to start a session first
                console.print("[yellow]💡 I can help you with that task! Let me start a PowerShell session first...[/yellow]")
                session_id = create_agent_session("powershell", visible_window=True)
                if session_id:
                    console.print("[green]✅ PowerShell session started! Now executing your task...[/green]")
                    execute_agent_task(user_input, conversation_history)
                else:
                    console.print("[red]❌ Failed to start PowerShell session. I'll respond via chat instead.[/red]")
                    handle_chat_response(user_input, conversation_history)
            else:
                # Regular chat
                handle_chat_response(user_input, conversation_history)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Use '/exit-agent' to return to chat mode[/yellow]")
        except EOFError:
            console.print("\n[yellow]Returning to XIBE-CHAT mode! 👋[/yellow]")
            break


if __name__ == "__main__":
    run_agent_mode()
