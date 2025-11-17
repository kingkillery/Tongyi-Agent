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

# Import orchestrators - try Claude SDK first, fallback to Tongyi
# Use absolute imports to avoid path issues
try:
    from claude_agent_orchestrator import ClaudeAgentOrchestrator
    CLAUDE_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    CLAUDE_ORCHESTRATOR_AVAILABLE = False
    CLAUDE_ORCHESTRATOR_ERROR = "Claude Agent SDK not installed"

try:
    from tongyi_orchestrator import TongyiOrchestrator
    TONGYI_ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    TONGYI_ORCHESTRATOR_AVAILABLE = False
    TONGYI_ORCHESTRATOR_ERROR = str(e)

# Import model manager for model switching
try:
    from model_manager import model_manager
    MODEL_MANAGER_AVAILABLE = True
except ImportError as e:
    MODEL_MANAGER_AVAILABLE = False
    MODEL_MANAGER_ERROR = str(e)

# Determine which orchestrator to use
ORCHESTRATOR_AVAILABLE = CLAUDE_ORCHESTRATOR_AVAILABLE or TONGYI_ORCHESTRATOR_AVAILABLE
ORCHESTRATOR_ERROR = (CLAUDE_ORCHESTRATOR_ERROR if not CLAUDE_ORCHESTRATOR_AVAILABLE
                     else TONGYI_ORCHESTRATOR_ERROR if not TONGYI_ORCHESTRATOR_AVAILABLE
                     else "No orchestrator available")

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
        help_table.add_row("models", "Model management (see 'models help')")
        help_table.add_row("exit/quit", "Exit the agent")

        console.print(help_table)
        console.print("\n[dim]Type 'models help' for model management commands.[/dim]")
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
        tools_table.add_row("models", "Model management")
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
  - models: Model management
  - exit: Exit the application

Note: This is the standalone CLI version.
        """)

def show_models_help():
    """Display model management help."""
    if RICH_AVAILABLE:
        models_table = Table(title="Model Management Commands")
        models_table.add_column("Command", style="cyan", no_wrap=True)
        models_table.add_column("Description", style="white")

        models_table.add_row("models", "Show current model")
        models_table.add_row("models list", "List all available models")
        models_table.add_row("models recommended", "Show recommended models")
        models_table.add_row("models set <model>", "Switch to a specific model")
        models_table.add_row("models search <query>", "Search models by name/capability")
        models_table.add_row("models info <model>", "Get detailed model information")
        models_table.add_row("models capability <cap>", "List models with capability")
        models_table.add_row("models suggest <usecase>", "Get model suggestion for use case")

        console.print(models_table)
        console.print("\n[dim]Example: models set anthropic/claude-3.5-sonnet[/dim]")
    else:
        print("""
Model Management Commands:
  models                    - Show current model
  models list               - List all available models
  models recommended        - Show recommended models
  models set <model>        - Switch to a specific model
  models search <query>     - Search models by name/capability
  models info <model>       - Get detailed model information
  models capability <cap>   - List models with capability
  models suggest <usecase>  - Get model suggestion for use case

Example: models set anthropic/claude-3.5-sonnet
        """)

def handle_models_command(args: list) -> bool:
    """Handle model management commands."""
    if not MODEL_MANAGER_AVAILABLE:
        console.print(f"[red]Model manager not available: {MODEL_MANAGER_ERROR}[/red]")
        return True

    if not args or args[0].lower() == 'help':
        show_models_help()
        return True

    command = args[0].lower()

    if command == 'current':
        current_model = model_manager.get_current_model()
        model_info = model_manager.get_model_info(current_model)
        if model_info:
            if RICH_AVAILABLE:
                info_table = Table(title="Current Model")
                info_table.add_column("Property", style="cyan")
                info_table.add_column("Value", style="white")
                info_table.add_row("Name", model_info.name)
                info_table.add_row("Display Name", model_info.display_name)
                info_table.add_row("Provider", model_info.provider)
                info_table.add_row("Context Length", str(model_info.context_length))
                info_table.add_row("Capabilities", ", ".join(model_info.capabilities))
                if model_info.pricing_per_mtok:
                    info_table.add_row("Pricing", f"${model_info.pricing_per_mtok}/Mtok")
                console.print(info_table)
            else:
                print(f"Current Model: {model_info.display_name} ({model_info.name})")
                print(f"Provider: {model_info.provider}")
                print(f"Context Length: {model_info.context_length}")
                print(f"Capabilities: {', '.join(model_info.capabilities)}")
        else:
            console.print(f"[red]Current model '{current_model}' not found in registry[/red]")

    elif command == 'list':
        models = model_manager.list_available_models()
        if RICH_AVAILABLE:
            models_table = Table(title="Available Models")
            models_table.add_column("Model", style="cyan")
            models_table.add_column("Display Name", style="white")
            models_table.add_column("Provider", style="green")
            models_table.add_column("Capabilities", style="yellow")

            for name, model in models.items():
                cap_str = ", ".join(model.capabilities[:2])  # Show first 2 capabilities
                if len(model.capabilities) > 2:
                    cap_str += "..."
                current_marker = " * " if name == model_manager.get_current_model() else "   "
                models_table.add_row(f"{current_marker}{name}", model.display_name, model.provider, cap_str)

            console.print(models_table)
            console.print("\n[dim]Use 'models info <model>' for detailed information[/dim]")
        else:
            print("Available Models:")
            for name, model in models.items():
                current = " (CURRENT)" if name == model_manager.get_current_model() else ""
                print(f"  {name} - {model.display_name}{current}")

    elif command == 'recommended':
        recommended = model_manager.list_recommended_models()
        if RICH_AVAILABLE:
            rec_table = Table(title="Recommended Models")
            rec_table.add_column("Model", style="cyan")
            rec_table.add_column("Display Name", style="white")
            rec_table.add_column("Best For", style="green")

            for model in recommended:
                best_for = "Overall" if "sonnet" in model.name.lower() else "Speed/Cost"
                rec_table.add_row(model.name, model.display_name, best_for)

            console.print(rec_table)
        else:
            print("Recommended Models:")
            for model in recommended:
                print(f"  {model.name} - {model.display_name}")

    elif command == 'set':
        if len(args) < 2:
            console.print("[red]Usage: models set <model_name>[/red]")
            console.print("[dim]Use 'models list' to see available models[/dim]")
        else:
            model_name = args[1]
            if model_manager.set_model(model_name):
                console.print(f"[green]✓ Switched to model: {model_name}[/green]")
                console.print("[dim]Note: Restart the application to apply the change[/dim]")
            else:
                console.print(f"[red]✗ Invalid model: {model_name}[/red]")
                console.print("[dim]Use 'models list' to see available models[/dim]")

    elif command == 'search':
        if len(args) < 2:
            console.print("[red]Usage: models search <query>[/red]")
        else:
            query = " ".join(args[1:])
            results = model_manager.search_models(query)
            if RICH_AVAILABLE and results:
                search_table = Table(title=f"Search Results for '{query}'")
                search_table.add_column("Model", style="cyan")
                search_table.add_column("Display Name", style="white")
                search_table.add_column("Provider", style="green")

                for name, model in results.items():
                    search_table.add_row(name, model.display_name, model.provider)

                console.print(search_table)
            elif results:
                print(f"Search Results for '{query}':")
                for name, model in results.items():
                    print(f"  {name} - {model.display_name} ({model.provider})")
            else:
                console.print(f"[yellow]No models found for '{query}'[/yellow]")

    elif command == 'info':
        if len(args) < 2:
            console.print("[red]Usage: models info <model_name>[/red]")
        else:
            model_name = args[1]
            model_info = model_manager.get_model_info(model_name)
            if model_info:
                if RICH_AVAILABLE:
                    info_table = Table(title=f"Model Information: {model_info.display_name}")
                    info_table.add_column("Property", style="cyan")
                    info_table.add_column("Value", style="white")
                    info_table.add_row("Name", model_info.name)
                    info_table.add_row("Display Name", model_info.display_name)
                    info_table.add_row("Provider", model_info.provider)
                    info_table.add_row("Context Length", f"{model_info.context_length:,}")
                    info_table.add_row("Capabilities", ", ".join(model_info.capabilities))
                    if model_info.pricing_per_mtok:
                        info_table.add_row("Pricing", f"${model_info.pricing_per_mtok}/Mtok")
                    console.print(info_table)
                else:
                    print(f"Model: {model_info.display_name}")
                    print(f"  Name: {model_info.name}")
                    print(f"  Provider: {model_info.provider}")
                    print(f"  Context Length: {model_info.context_length:,}")
                    print(f"  Capabilities: {', '.join(model_info.capabilities)}")
                    if model_info.pricing_per_mtok:
                        print(f"  Pricing: ${model_info.pricing_per_mtok}/Mtok")
            else:
                console.print(f"[red]Model '{model_name}' not found[/red]")

    elif command == 'capability':
        if len(args) < 2:
            console.print("[red]Usage: models capability <capability>[/red]")
            console.print("[dim]Examples: coding, reasoning, fast, multilingual[/dim]")
        else:
            capability = args[1]
            models = model_manager.get_models_by_capability(capability)
            if RICH_AVAILABLE and models:
                cap_table = Table(title=f"Models with '{capability}' capability")
                cap_table.add_column("Model", style="cyan")
                cap_table.add_column("Display Name", style="white")
                cap_table.add_column("Provider", style="green")

                for name, model in models.items():
                    cap_table.add_row(name, model.display_name, model.provider)

                console.print(cap_table)
            elif models:
                print(f"Models with '{capability}' capability:")
                for name, model in models.items():
                    print(f"  {name} - {model.display_name} ({model.provider})")
            else:
                console.print(f"[yellow]No models found with '{capability}' capability[/yellow]")

    elif command == 'suggest':
        if len(args) < 2:
            console.print("[red]Usage: models suggest <use_case>[/red]")
            console.print("[dim]Examples: coding, fast, reasoning, cheap, analysis[/dim]")
        else:
            use_case = " ".join(args[1:])
            suggestion = model_manager.get_model_suggestion(use_case)
            if suggestion:
                if RICH_AVAILABLE:
                    console.print(f"[green]Suggested model for '{use_case}':[/green]")
                    info_table = Table()
                    info_table.add_column("Property", style="cyan")
                    info_table.add_column("Value", style="white")
                    info_table.add_row("Model", suggestion.name)
                    info_table.add_row("Display Name", suggestion.display_name)
                    info_table.add_row("Provider", suggestion.provider)
                    info_table.add_row("Why", ", ".join(suggestion.capabilities[:3]))
                    console.print(info_table)
                else:
                    print(f"Suggested model for '{use_case}':")
                    print(f"  {suggestion.display_name} ({suggestion.name})")
                    print(f"  Provider: {suggestion.provider}")
                    print(f"  Capabilities: {', '.join(suggestion.capabilities[:3])}")
            else:
                console.print(f"[red]No suggestion available for '{use_case}'[/red]")

    else:
        console.print(f"[red]Unknown models command: {command}[/red]")
        console.print("[dim]Type 'models help' for available commands[/dim]")

    return True

def process_command(command: str) -> bool:
    """Process special commands. Returns True if command was handled."""
    cmd_parts = command.strip().split()
    cmd = cmd_parts[0].lower() if cmd_parts else ""

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
    elif cmd == 'models':
        # Handle models command with arguments
        return handle_models_command(cmd_parts[1:] if len(cmd_parts) > 1 else [])
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

    # Initialize orchestrator - prioritize Claude SDK
    orchestrator = None
    orchestrator_type = None

    if CLAUDE_ORCHESTRATOR_AVAILABLE:
        try:
            orchestrator = ClaudeAgentOrchestrator(root=root)
            orchestrator_type = "Claude Agent SDK"
            console.print("[green]✓ Tongyi Agent (Claude SDK) initialized successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to initialize Claude Agent SDK: {e}[/red]")
            console.print("[yellow]Falling back to Tongyi orchestrator...[/yellow]")

    if orchestrator is None and TONGYI_ORCHESTRATOR_AVAILABLE:
        try:
            orchestrator = TongyiOrchestrator(root=root)
            orchestrator_type = "Tongyi"
            console.print("[green]✓ Tongyi Agent (Tongyi SDK) initialized successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to initialize Tongyi Agent: {e}[/red]")

    if orchestrator is None:
        console.print(f"[red]✗ No orchestrator available: {ORCHESTRATOR_ERROR}[/red]")
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
                            if orchestrator_type == "Claude Agent SDK":
                                try:
                                    import asyncio
                                    response = asyncio.run(orchestrator.process_query(question))
                                except RuntimeError as e:
                                    if "event loop is already running" in str(e):
                                        # Handle nested event loop (common in some environments)
                                        import nest_asyncio
                                        nest_asyncio.apply()
                                        response = asyncio.run(orchestrator.process_query(question))
                                    else:
                                        raise
                            else:
                                response = orchestrator.run(question)
                    else:
                        print("Thinking...")
                        if orchestrator_type == "Claude Agent SDK":
                            try:
                                import asyncio
                                response = asyncio.run(orchestrator.process_query(question))
                            except RuntimeError as e:
                                if "event loop is already running" in str(e):
                                    # Handle nested event loop (common in some environments)
                                    import nest_asyncio
                                    nest_asyncio.apply()
                                    response = asyncio.run(orchestrator.process_query(question))
                                else:
                                    raise
                        else:
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
                response = f"I received your question: '{question}'. No orchestrator is available. Please check your environment setup."
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

    parser.add_argument(
        "--model",
        help="Specify OpenRouter model to use (e.g., anthropic/claude-3.5-sonnet)"
    )

    parser.add_argument(
        "--models-info",
        action="store_true",
        help="Show available models and current selection"
    )

    args = parser.parse_args()
    
    # Handle --tools flag
    if args.tools:
        show_tools()
        return

    # Handle --models-info flag
    if args.models_info:
        if MODEL_MANAGER_AVAILABLE:
            handle_models_command([])
        else:
            print(f"Model manager not available: {MODEL_MANAGER_ERROR}")
        return

    # Handle model selection
    if args.model and MODEL_MANAGER_AVAILABLE:
        if model_manager.set_model(args.model):
            print(f"Model set to: {args.model}")
        else:
            print(f"Invalid model: {args.model}")
            print("Use --models-info to see available models")
            return

    # Handle non-interactive mode
    if args.question or args.no_interactive:
        question = " ".join(args.question) if args.question else "No question provided"
        
        # Handle model override for orchestrators
        if args.model:
            import os
            os.environ["MODEL_OVERRIDE"] = args.model
            print(f"Using model override: {args.model}")

        # Try to initialize an orchestrator for non-interactive mode
        orchestrator = None
        orchestrator_type = None

        if CLAUDE_ORCHESTRATOR_AVAILABLE:
            try:
                orchestrator = ClaudeAgentOrchestrator(root=args.root)
                orchestrator_type = "Claude Agent SDK"
            except Exception as e:
                print(f"Failed to initialize Claude Agent SDK: {e}")

        if orchestrator is None and TONGYI_ORCHESTRATOR_AVAILABLE:
            try:
                orchestrator = TongyiOrchestrator(root=args.root)
                orchestrator_type = "Tongyi"
            except Exception as e:
                print(f"Failed to initialize Tongyi Agent: {e}")

        if orchestrator:
            try:
                print("Processing your question...")
                if orchestrator_type == "Claude Agent SDK":
                    try:
                        import asyncio
                        response = asyncio.run(orchestrator.process_query(question))
                    except RuntimeError as e:
                        if "event loop is already running" in str(e):
                            # Handle nested event loop (common in some environments)
                            import nest_asyncio
                            nest_asyncio.apply()
                            response = asyncio.run(orchestrator.process_query(question))
                        else:
                            raise
                    except Exception as e:
                        print(f"Claude Agent SDK failed: {e}")
                        # Try to fall back to Tongyi orchestrator
                        if TONGYI_ORCHESTRATOR_AVAILABLE:
                            print("Falling back to Tongyi Agent...")
                            try:
                                tongyi_orchestrator = TongyiOrchestrator(root=args.root)
                                response = tongyi_orchestrator.run(question)
                                print(f"\nAnswer (using Tongyi Agent):\n{response}")
                                return
                            except Exception as fallback_error:
                                print(f"Tongyi fallback also failed: {fallback_error}")
                        return
                    finally:
                        # Clean up environment variable
                        if args.model and "MODEL_OVERRIDE" in os.environ:
                            del os.environ["MODEL_OVERRIDE"]
                else:
                    response = orchestrator.run(question)
                print(f"\nAnswer:\n{response}")
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"No orchestrator available: {ORCHESTRATOR_ERROR}")
            print(f"Received question: '{question}'")
        return
    
    # Default to interactive mode
    interactive_mode(root=args.root)

if __name__ == "__main__":
    main()
