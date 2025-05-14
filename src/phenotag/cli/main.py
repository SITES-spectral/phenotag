#!/usr/bin/env python3
import argparse
import sys
import subprocess
import os
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="PhenoTag - Phenotype Annotation Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command: start the Streamlit UI
    run_parser = subparsers.add_parser("run", help="Start the PhenoTag web application")
    
    # Add option to use memory-optimized version
    run_parser.add_argument(
        "--memory-optimized", "-m",
        action="store_true",
        help="Use memory-optimized version of the application"
    )
    run_parser.add_argument(
        "--port", "-p",
        type=int,
        default=8501,
        help="Port to run the Streamlit UI on"
    )
    run_parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to run the Streamlit UI on"
    )
    run_parser.add_argument(
        "--browser",
        action="store_true",
        help="Open the UI in the default browser"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # Handle commands
    if args.command == "run":
        # Always use the main app path - memory optimization is handled within the app
        app_path = Path(__file__).parent.parent / "ui" / "main.py"
        
        # Print memory optimization status
        if args.memory_optimized:
            print("Using memory-optimized mode")
        
        # Print the path for debugging
        print(f"Starting Streamlit with app path: {app_path}")
        
        # Check if the file exists
        if not app_path.exists():
            print(f"Error: UI file not found at {app_path}")
            sys.exit(1)
        
        # Build the Streamlit command
        # Use the executable from the Python environment
        streamlit_path = os.path.join(os.path.dirname(sys.executable), "streamlit")
        
        # If streamlit is not found next to the Python executable, try from PATH
        if not os.path.exists(streamlit_path):
            streamlit_path = "streamlit"
            
        print(f"Using Streamlit executable: {streamlit_path}")
        
        cmd = [
            streamlit_path, "run",
            str(app_path),
            "--server.port", str(args.port),
            "--server.address", args.host
        ]
        
        # Pass memory optimization as a command-line argument to the Python app
        # (Streamlit doesn't recognize custom flags)
        if args.memory_optimized:
            cmd.append("--")  # Delimiter for passing arguments to the target script
            cmd.append("--memory-optimized")
        
        if args.browser:
            cmd.append("--server.headless")
            cmd.append("false")
        
        # Run the Streamlit UI
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\nShutting down PhenoTag...")
            sys.exit(0)

if __name__ == "__main__":
    main() 