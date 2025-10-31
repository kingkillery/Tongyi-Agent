"""CLI entry point for Tongyi Agent."""
import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tongyi_orchestrator import TongyiOrchestrator


def main():
    """Entry point for tongyi-agent CLI."""
    parser = argparse.ArgumentParser(description="Run Tongyi Agent research assistant")
    parser.add_argument("question", nargs="*", help="Question to process")
    parser.add_argument("--root", default=".", help="Root directory to analyze")
    parser.add_argument("--tools", action="store_true", help="Show available tools and exit")
    args = parser.parse_args()
    
    if args.tools:
        try:
            orch = TongyiOrchestrator(root=args.root)
            summary = orch.get_tool_usage_summary()
            print(f"Tongyi Agent Tools ({summary['total_tools']} available):")
            for name in summary["tool_names"]:
                print(f"  - {name}")
            print(f"\nModel: {summary['model']}")
            print(f"Root: {summary['root_directory']}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        return
    
    question = " ".join(args.question) if args.question else input("Question: ")
    
    try:
        orch = TongyiOrchestrator(root=args.root)
        answer = orch.run(question)
        print(answer)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
