"""Interactive CLI entry point for Tongyi Agent."""
import argparse
import sys
import os
import json
import readline
import atexit
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.markdown import Markdown
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback to basic print
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
        def rule(self, title):
            print(f"--- {title} ---")
        def panel(self, content, title=""):
            print(f"[{title}]")
            print(content)
            print(f"[/{title}]")

# Import TongyiOrchestrator
try:
    from tongyi_orchestrator import TongyiOrchestrator
    ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    ORCHESTRATOR_AVAILABLE = False
    ORCHESTRATOR_ERROR = str(e)

# Initialize console
console = Console()

# Session management
class Session:
    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or Path.home() / ".tongyi_agent_history.json"
        self.conversation_history: List[Dict] = []
        self.session_start = datetime.now()
        self.load_history()
    
    def load_history(self):
        """Load conversation history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.conversation_history = data.get('history', [])
            except (json.JSONDecodeError, IOError):
                self.conversation_history = []
    
    def save_history(self):
        """Save conversation history to file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump({
                    'history': self.conversation_history[-50:],  # Keep last 50 conversations
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except IOError:
            pass  # Silently fail if can't save
    
    def add_exchange(self, question: str, answer: str, tool_calls: List[Dict] = None):
        """Add a question-answer exchange to history."""
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'answer': answer,
            'tool_calls': tool_calls or []
        })
    
    def get_recent_context(self, limit: int = 5) -> str:
        """Get recent conversation context as string."""
        if not self.conversation_history:
            return ""
        
        recent = self.conversation_history[-limit:]
        context = "Recent conversation context:\n"
        for i, exchange in enumerate(recent, 1):
            context += f"{i}. Q: {exchange['question']}\n   A: {exchange['answer'][:200]}...\n\n"
        return context

# Global session
session = Session()

# Register cleanup
atexit.register(session.save_history)

def show_banner():
    """Display welcome banner."""
    if RICH_AVAILABLE:
        banner = Panel(
            "[bold blue]Tongyi CLI Interactive[/bold blue]\n"
            "[dim]Modern Terminal Interface for Tongyi Agent[/dim]\n\n"
            "Type 'help' for commands • Ctrl+C to exit • Ctrl+D to clear",
            title="[Tongyi] Welcome",
            border_style="blue"
        )
        console.print(banner)
    else:
        print("""
╔═══════════════════════════════════════╗
║     Tongyi CLI Interactive          ║
║   Modern Terminal Interface        ║
╚═══════════════════════════════════════╝

Type 'help' for commands • Ctrl+C to exit
        """)

def show_help():
    """Display help information."""
    if RICH_AVAILABLE:
        help_table = Table(title="Available Commands")
        help_table.add_column("Command", style="cyan", no_wrap=True)
        help_table.add_column("Description", style="white")
        
        help_table.add_row("help", "Show this help message")
        help_table.add_row("tools", "List available tools")
        help_table.add_row("history", "Show conversation history")
        help_table.add_row("clear", "Clear conversation history")
        help_table.add_row("context", "Show recent conversation context")
        help_table.add_row("status", "Show session status")
        help_table.add_row("exit/quit", "Exit the agent")
        
        console.print(help_table)
    else:
        print("""
Available Commands:
  help     - Show this help message
  tools    - List available tools
  history  - Show conversation history
  clear    - Clear conversation history
  context  - Show recent conversation context
  status   - Show session status
  exit/quit- Exit the agent
        """)

def show_history():
    """Display conversation history."""
    if not session.conversation_history:
        console.print("[dim]No conversation history yet.[/dim]")
        return
    
    console.print(f"[bold]Conversation History ({len(session.conversation_history)} exchanges):[/bold]")
    for i, exchange in enumerate(session.conversation_history[-10:], 1):  # Show last 10
        timestamp = datetime.fromisoformat(exchange['timestamp']).strftime("%H:%M:%S")
        console.print(f"\n[cyan]{i}. [{timestamp}][/cyan]")
        console.print(f"[bold]Q:[/bold] {exchange['question']}")
        console.print(f"[dim]A:[/dim] {exchange['answer'][:150]}...")

def show_status():
    """Display session status."""
    session_duration = datetime.now() - session.session_start
    
    if RICH_AVAILABLE:
        status_table = Table(title="Session Status")
        status_table.add_column("Property", style="cyan")
        status_table.add_column("Value", style="white")
        
        status_table.add_row("Session Duration", str(session_duration).split('.')[0])
        status_table.add_row("Total Exchanges", str(len(session.conversation_history)))
        status_table.add_row("History File", str(session.history_file))
        status_table.add_row("Rich UI", "Enabled" if RICH_AVAILABLE else "Disabled")
        
        console.print(status_table)
    else:
        print(f"""
Session Status:
  Duration: {str(session_duration).split('.')[0]}
  Exchanges: {len(session.conversation_history)}
  History File: {session.history_file}
  Rich UI: {'Enabled' if RICH_AVAILABLE else 'Disabled'}
        """)

def show_tools():
    """Display available tools."""
    if RICH_AVAILABLE:
        tools_table = Table(title="Available Tools")
        tools_table.add_column("Tool Name", style="cyan")
        tools_table.add_column("Description", style="white")
        
        tools_table.add_row("help", "Show available commands")
        tools_table.add_row("tools", "List available tools")
        tools_table.add_row("history", "View conversation history")
        tools_table.add_row("status", "Show session information")
        tools_table.add_row("clear", "Clear conversation history")
        tools_table.add_row("context", "Show recent context")
        tools_table.add_row("exit", "Exit the application")
        
        console.print(tools_table)
        console.print(f"\n[dim]Note: This is the standalone CLI version.[/dim]")
    else:
        print("""
Available Tools:
  - help: Show available commands
  - tools: List available tools
  - history: View conversation history
  - status: Show session information
  - clear: Clear conversation history
  - context: Show recent context
  - exit: Exit the application

Note: This is the standalone CLI version.
        """)

def process_command(command: str) -> bool:
    """Process special commands. Returns True if command was handled."""
    cmd = command.strip().lower()
    
    if cmd in ['help', '?']:
        show_help()
        return True
    elif cmd == 'tools':
        show_tools()
        return True
    elif cmd == 'history':
        show_history()
        return True
    elif cmd == 'clear':
        session.conversation_history.clear()
        console.print("[green]Conversation history cleared.[/green]")
        return True
    elif cmd == 'context':
        context = session.get_recent_context()
        if context:
            console.print("[bold]Recent Context:[/bold]")
            console.print(context)
        else:
            console.print("[dim]No recent context available.[/dim]")
        return True
    elif cmd == 'status':
        show_status()
        return True
    elif cmd in ['exit', 'quit', 'q']:
        console.print("[yellow]Goodbye! 👋[/yellow]")
        return True
    
    return False

def interactive_mode(root: str = "."):
    """Run the interactive CLI loop."""
    show_banner()
    
    # Initialize orchestrator
    orchestrator = None
    if ORCHESTRATOR_AVAILABLE:
        try:
            orchestrator = TongyiOrchestrator(root=root)
            console.print("[green]✓ Tongyi Agent initialized successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to initialize Tongyi Agent: {e}[/red]")
            console.print("[yellow]Running in limited mode with stub responses.[/yellow]")
    else:
        console.print(f"[red]✗ TongyiOrchestrator not available: {ORCHESTRATOR_ERROR}[/red]")
        console.print("[yellow]Running in limited mode with stub responses.[/yellow]")
    
    while True:
        try:
            if RICH_AVAILABLE:
                question = Prompt.ask("\n[bold cyan]Question[/bold cyan]")
            else:
                question = input("\nQuestion: ").strip()
            
            if not question:
                continue
            
            # Check for special commands
            if process_command(question):
                if question.lower() in ['exit', 'quit', 'q']:
                    break
                continue
            
            # Process with orchestrator or stub
            if orchestrator:
                try:
                    if RICH_AVAILABLE:
                        with Live(Spinner("dots", text="[cyan]Thinking...[/cyan]"), console=console):
                            response = orchestrator.run(question)
                    else:
                        print("Thinking...")
                        response = orchestrator.run(question)
                    
                    console.print(f"\n[bold green]Answer:[/bold green]")
                    if RICH_AVAILABLE:
                        console.print(Markdown(response))
                    else:
                        console.print(response)
                    
                    # Add to history
                    session.add_exchange(question, response)
                    
                except Exception as e:
                    console.print(f"[red]Error processing question: {e}[/red]")
                    import traceback
                    console.print(f"[dim]{traceback.format_exc()}[/dim]")
            else:
                # Stub response
                response = f"I received your question: '{question}'. TongyiOrchestrator is not available. Please check your environment setup."
                console.print(f"\n[bold yellow]Stub Response:[/bold yellow] {response}")
                session.add_exchange(question, response)
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' or 'quit' to close the application.[/yellow]")
        except EOFError:
            console.print("\n[yellow]Use 'exit' or 'quit' to close the application.[/yellow]")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive Tongyi CLI - Modern Terminal Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tongyi-cli                              # Start interactive mode
  tongyi-cli "What is this project?"     # Ask a question directly
  tongyi-cli --root /path/to/project     # Specify project root
  tongyi-cli --tools                      # List available tools
        """
    )
    
    parser.add_argument(
        "question", 
        nargs="*", 
        help="Question to process (runs in non-interactive mode)"
    )
    
    parser.add_argument(
        "--root",
        default=".",
        help="Project root directory (default: current directory)"
    )
    
    parser.add_argument(
        "--tools", 
        action="store_true",
        help="Show available tools and exit"
    )
    
    parser.add_argument(
        "--no-interactive", 
        action="store_true",
        help="Disable interactive mode"
    )
    
    args = parser.parse_args()
    
    # Handle --tools flag
    if args.tools:
        show_tools()
        return
    
    # Handle non-interactive mode
    if args.question or args.no_interactive:
        question = " ".join(args.question) if args.question else "No question provided"
        
        if ORCHESTRATOR_AVAILABLE:
            try:
                orchestrator = TongyiOrchestrator(root=args.root)
                print("Processing your question...")
                response = orchestrator.run(question)
                print(f"\nAnswer:\n{response}")
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"TongyiOrchestrator not available: {ORCHESTRATOR_ERROR}")
            print(f"Received question: '{question}'")
        return
    
    # Default to interactive mode
    interactive_mode(root=args.root)

if __name__ == "__main__":
    main()
