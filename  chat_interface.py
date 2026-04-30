# FILE: chat_interface.py

import requests
import uuid
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

# Initialize Rich Console for beautiful UI
console = Console()

# Configuration
API_URL = "http://localhost:8000/chat/query"

def main():
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]WisIQ Enterprise Hardware AI[/bold cyan]\n"
        "Type [bold red]'quit'[/bold red] to exit.\n"
        "Session Memory is [bold green]ACTIVE[/bold green].",
        title="Terminal Interface",
        border_style="cyan"
    ))
    
    # Generate a unique session ID for this conversation loop
    session_id = uuid.uuid4().hex[:8]
    console.print(f"[dim]Session ID: {session_id}[/dim]\n")

    while True:
        try:
            # 1. Get User Input
            user_input = Prompt.ask("\n[bold yellow]You[/bold yellow]")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print("\n[dim]Closing session...[/dim]")
                break
            if not user_input.strip():
                continue

            # 2. Show a loading spinner while waiting for the backend
            with console.status("[bold green]Agent is reasoning (Extracting intent, querying Postgres, searching Qdrant)...[/bold green]"):
                
                payload = {
                    "session_id": session_id,
                    "message": user_input
                }
                
                response = requests.post(API_URL, json=payload)
                
            # 3. Handle the Response
            if response.status_code == 200:
                data = response.json()
                
                # Display Agent Metadata (Intent & Hardware recognized)
                meta_str = (
                    f"[dim]Intent:[/dim] [cyan]{data.get('intent_detected')}[/cyan] | "
                    f"[dim]Hardware:[/dim] [magenta]{', '.join(data.get('hardware_detected', [])) or 'None'}[/magenta]"
                )
                console.print(meta_str)
                
                # Display the Markdown Response
                console.print(Panel(
                    Markdown(data.get("reply", "")),
                    title="WisIQ Agent",
                    title_align="left",
                    border_style="green"
                ))
            else:
                console.print(f"[bold red]Error {response.status_code}:[/bold red] {response.text}")

        except requests.exceptions.ConnectionError:
            console.print("[bold red]Connection Error:[/bold red] Make sure the FastAPI server is running on port 8000.")
            sys.exit(1)
        except KeyboardInterrupt:
            console.print("\n[dim]Closing session...[/dim]")
            break

if __name__ == "__main__":
    main()