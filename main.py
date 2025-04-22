#!/usr/bin/env python3
import os
import uuid
import traceback
from langchain_core.messages import HumanMessage, AIMessage

from main_graph import get_agent_graph
from config import LLM_MODEL

def colorize(text, color_code):
    """Add color to terminal output."""
    return f"\033[{color_code}m{text}\033[0m"

def format_message(message):
    """Format message with colors based on type."""
    if hasattr(message, 'type') and message.type == 'human':
        return colorize(f"You: {message.content}", "36;1")  # Cyan
    else:
        return colorize(f"Assistant: {message.content}", "32;1")  # Green

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_header():
    """Display the application header."""
    header = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║            VA EXPENSES - Personal Finance Assistant               ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(colorize(header, "34;1"))  # Blue
    print(colorize(f"  Using {LLM_MODEL} for financial assistance", "33"))  # Yellow
    print(colorize("  Type 'exit' to quit. Type 'help' for available commands.\n", "33"))  # Yellow

def display_help():
    """Display help information."""
    help_text = """
    Available Commands:
    ------------------
    help        - Show this help message
    clear       - Clear the screen
    exit/quit   - Exit the application
    debug       - Run diagnostics on the agent setup
    
    Example Queries:
    --------------
    "I spent $45 on groceries yesterday"
    "What did I spend on food this month?"
    "Create a budget for me"
    "How can I reduce my expenses?"
    "Analyze my spending trends"
    """
    print(colorize(help_text, "37;1"))  # White

def run_diagnostics():
    """Run diagnostics to check the agent setup."""
    try:
        from tools.utils import tools
        print(colorize(f"\nFound {len(tools)} tools:", "33"))
        for tool in tools:
            print(colorize(f"  - {tool.name}: {tool.__doc__.strip() if tool.__doc__ else 'No description'}", "37"))
        
        # Test ExpenseRetriever
        from agents.retriever import ExpenseRetriever
        retriever = ExpenseRetriever()
        print(colorize("\nTesting ExpenseRetriever...", "33"))
        data = retriever.get_expense_data(period="month")
        print(colorize(f"  Retrieved {data['count']} expenses, total: ${data['total']:.2f}", "37"))
        
        # Test IntentAnalyzer
        from agents.analyzer import IntentAnalyzer
        analyzer = IntentAnalyzer()
        print(colorize("\nTesting IntentAnalyzer...", "33"))
        test_intent = analyzer.analyze("Show me my expenses for this month")
        print(colorize(f"  Detected intent: {test_intent.get('intent', 'Unknown')}", "37"))
        
        print(colorize("\nDiagnostics completed successfully.", "32"))
        return True
    except Exception as e:
        print(colorize(f"\nDiagnostics error: {str(e)}", "31"))
        traceback.print_exc()
        return False

def main():
    """Main function for the console interface."""
    clear_screen()
    display_header()
    
    # Get the agent graph
    try:
        agent = get_agent_graph()
        print(colorize("Agent loaded successfully!", "32"))
    except Exception as e:
        print(colorize(f"Error loading agent: {str(e)}", "31"))
        traceback.print_exc()
        return
    
    session_id = str(uuid.uuid4())
    
    while True:
        try:
            user_input = input(colorize("\nYou: ", "36;1"))
            
            if user_input.lower() in ("exit", "quit"):
                print(colorize("\nThank you for using VA Expenses. Goodbye!", "33;1"))
                break
                
            if user_input.lower() == "help":
                display_help()
                continue
                
            if user_input.lower() == "clear":
                clear_screen()
                display_header()
                continue
            
            if user_input.lower() == "debug":
                run_diagnostics()
                continue
            
            if not user_input.strip():
                continue
            
            # Set up the conversation configuration with the session ID
            config = {"configurable": {"thread_id": session_id}}
            
            # Create initial state with the user message
            state = {"messages": [HumanMessage(content=user_input)]}
            
            print(colorize("Processing your request...", "33"))
            
            # Get the response from the agent
            try:
                result = agent.invoke(state, config)
                
                # Print the assistant's response, skipping system messages
                for msg in result["messages"]:
                    if hasattr(msg, 'type') and msg.type in ('ai', 'human'):
                        print(format_message(msg))
            except Exception as e:
                print(colorize(f"\nAgent error: {str(e)}", "31"))
                print(colorize("Error details:", "31"))
                traceback.print_exc()
        
        except KeyboardInterrupt:
            print(colorize("\n\nInterrupted by user. Exiting...", "31;1"))  # Red
            break
        except Exception as e:
            print(colorize(f"\nAn error occurred: {str(e)}", "31;1"))  # Red
            traceback.print_exc()
    
if __name__ == "__main__":
    main() 