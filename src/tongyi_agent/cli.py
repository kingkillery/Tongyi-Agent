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
sys.path.insert(0, str(Path(__file__).parent.parent))

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

from tongyi_orchestrator import TongyiOrchestrator

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
            "[bold blue]Tongyi Agent[/bold blue]\n"
            "[dim]Interactive Research Assistant[/dim]\n\n"
            "Type 'help' for commands • Ctrl+C to exit • Ctrl+D to clear",
            title="[Tongyi] Welcome",
            border_style="blue"
        )
        console.print(banner)
    else:
        print("""
╔═══════════════════════════════════════╗
║         Tongyi Agent                  ║
║      Interactive Research Assistant  ║
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

def process_command(command: str, orchestrator: TongyiOrchestrator) -> bool:
    """Process special commands. Returns True if command was handled."""
    cmd = command.strip().lower()
    
    if cmd in ['help', '?']:
        show_help()
        return True
    elif cmd == 'tools':
        try:
            summary = orchestrator.get_tool_usage_summary()
            if RICH_AVAILABLE:
                tools_table = Table(title=f"Available Tools ({summary['total_tools']})")
                tools_table.add_column("Tool Name", style="cyan")
                for name in summary["tool_names"]:
                    tools_table.add_row(name)
                console.print(tools_table)
                console.print(f"\n[dim]Model: {summary['model']}[/dim]")
                console.print(f"[dim]Root: {summary['root_directory']}[/dim]")
            else:
                print(f"Available Tools ({summary['total_tools']}):")
                for name in summary["tool_names"]:
                    print(f"  - {name}")
                print(f"\nModel: {summary['model']}")
                print(f"Root: {summary['root_directory']}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
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
            console.print(Panel(context, title="Recent Context"))
        else:
            console.print("[dim]No recent context.[/dim]")
        return True
    elif cmd == 'status':
        show_status()
        return True
    elif cmd in ['exit', 'quit', 'q']:
        console.print("[yellow]Goodbye![/yellow]")
        return False
    
    return False

def interactive_mode(orchestrator: TongyiOrchestrator):
    """Run the interactive CLI mode."""
    show_banner()
    
    while True:
        try:
            # Get user input
            if RICH_AVAILABLE:
                question = Prompt.ask("\n[bold blue][Tongyi][/bold blue]", console=console)
            else:
                question = input("\n[Tongyi]> ").strip()
            
            if not question:
                continue
            
            # Check for special commands
            should_continue = process_command(question, orchestrator)
            if not should_continue:
                break
            if should_continue is True:  # Command was handled
                continue
            
            # Process the question with orchestrator
            console.print("[dim]Thinking...[/dim]")
            
            try:
                answer = orchestrator.run(question)
                
                # Display answer
                if RICH_AVAILABLE:
                    console.print("\n[bold green][Response]:[/bold green]")
                    # Try to render as markdown if it looks like markdown
                    if any(c in answer for c in ['**', '##', '###', '* ', '- ', '1.', '```']):
                        try:
                            md = Markdown(answer)
                            console.print(md)
                        except:
                            console.print(answer)
                    else:
                        console.print(answer)
                else:
                    print("\n[Response]:")
                    print(answer)
                
                # Add to session history
                session.add_exchange(question, answer)
                
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' or 'quit' to close the agent.[/yellow]")
            continue
        except EOFError:
            console.print("\n[yellow]Goodbye![/yellow]")
            break


def main():
    """Entry point for tongyi-agent CLI."""
    parser = argparse.ArgumentParser(description="Interactive Tongyi Agent research assistant")
    parser.add_argument("question", nargs="*", help="Question to process (runs in non-interactive mode)")
    parser.add_argument("--root", default=".", help="Root directory to analyze")
    parser.add_argument("--tools", action="store_true", help="Show available tools and exit")
    parser.add_argument("--no-interactive", action="store_true", help="Disable interactive mode")
    args = parser.parse_args()
    
    try:
        orch = TongyiOrchestrator(root=args.root)
    except Exception as e:
        console.print(f"[red]Error initializing orchestrator: {e}[/red]")
        sys.exit(1)
    
    if args.tools:
        try:
            summary = orch.get_tool_usage_summary()
            if RICH_AVAILABLE:
                tools_table = Table(title=f"Tongyi Agent Tools ({summary['total_tools']} available)")
                tools_table.add_column("Tool Name", style="cyan")
                for name in summary["tool_names"]:
                    tools_table.add_row(name)
                console.print(tools_table)
                console.print(f"\n[dim]Model: {summary['model']}[/dim]")
                console.print(f"[dim]Root: {summary['root_directory']}[/dim]")
            else:
                print(f"Tongyi Agent Tools ({summary['total_tools']} available):")
                for name in summary["tool_names"]:
                    print(f"  - {name}")
                print(f"\nModel: {summary['model']}")
                print(f"Root: {summary['root_directory']}")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
        return
    
    # Non-interactive mode (backward compatibility)
    if args.question or args.no_interactive:
        question = " ".join(args.question) if args.question else input("Question: ")
        
        try:
            answer = orch.run(question)
            if RICH_AVAILABLE:
                console.print("\n[bold green][Response]:[/bold green]")
                if any(c in answer for c in ['**', '##', '###', '* ', '- ', '1.', '```']):
                    try:
                        md = Markdown(answer)
                        console.print(md)
                    except:
                        console.print(answer)
                else:
                    console.print(answer)
            else:
                print(answer)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    else:
        # Interactive mode
        interactive_mode(orch)


if __name__ == "__main__":
    main()
