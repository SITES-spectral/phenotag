#!/usr/bin/env python3
import argparse
import sys
import subprocess
import os
import json
import yaml
from pathlib import Path


def get_default_roi_for_image(image_path, roi_name="ROI_00", color=[0, 255, 0], thickness=7):
    """
    Calculate default ROI for a given image using the same algorithm as the app.
    
    Args:
        image_path (str): Path to the image file
        roi_name (str): Name for the ROI
        color (list): RGB color as [R, G, B]
        thickness (int): Line thickness
        
    Returns:
        dict: ROI data in stations.yaml format
    """
    try:
        import cv2
        import numpy as np
        import gc
    except ImportError as e:
        print(f"Error: Required dependencies not available: {e}")
        print("Please ensure opencv-python and numpy are installed")
        sys.exit(1)
    
    # Validate image path
    if not os.path.exists(image_path):
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    # Load image
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"Error: Could not load image: {image_path}")
            sys.exit(1)
    except Exception as e:
        print(f"Error loading image: {e}")
        sys.exit(1)
    
    height, width = image.shape[:2]
    
    # Try to detect and exclude sky (same algorithm as in the app)
    try:
        # Convert to HSV for better color segmentation
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Process in smaller chunks to reduce memory usage
        chunk_height = min(500, height)  # Process 500 rows at a time
        top_third_height = height // 3
        sky_line = top_third_height  # Default if no sky found
        
        # First pass: quick check of top area for sky
        for start_y in range(0, top_third_height, chunk_height):
            end_y = min(start_y + chunk_height, top_third_height)
            hsv_chunk = hsv[start_y:end_y, :]
            
            # Blue sky: high hue, moderate-high saturation, high value
            sky_mask_blue = cv2.inRange(
                hsv_chunk, 
                np.array([90, 50, 150]), 
                np.array([140, 255, 255])
            )
            
            # White/cloudy sky: low saturation, high value
            sky_mask_white = cv2.inRange(
                hsv_chunk, 
                np.array([0, 0, 180]), 
                np.array([180, 50, 255])
            )
            
            # Combine masks
            sky_mask_chunk = cv2.bitwise_or(sky_mask_blue, sky_mask_white)
            
            # Check each row in the chunk
            for y_offset in range(0, end_y - start_y, 5):  # Check every 5 rows
                y = start_y + y_offset
                row_sum = np.sum(sky_mask_chunk[y_offset, :]) / 255
                if row_sum > width * 0.3:  # If >30% of row is detected as sky
                    sky_line = y
            
            # Release chunk memory
            del hsv_chunk, sky_mask_blue, sky_mask_white, sky_mask_chunk
            gc.collect()
        
        # Add a buffer of 10% to avoid cutting off important features
        sky_line = int(min(sky_line * 1.1, height))
        
        # Create a rectangle that excludes the detected sky
        points = [[0, sky_line], [width-1, sky_line], [width-1, height-1], [0, height-1]]
        
    except Exception as e:
        print(f"Sky detection failed: {e}. Using full frame as default ROI.")
        # Fallback: use the entire image
        points = [[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]]
    
    # Clean up
    del image, hsv
    gc.collect()
    
    # Create ROI data in stations.yaml format
    roi_data = {
        roi_name: {
            'points': points,
            'color': color,
            'thickness': thickness
        }
    }
    
    return roi_data


def handle_images_command(args):
    """Handle the images subcommand."""
    if args.images_subcommand == "default-roi":
        # Parse color argument
        try:
            color = [int(c.strip()) for c in args.color.split(',')]
            if len(color) != 3:
                raise ValueError("Color must have exactly 3 values (R,G,B)")
            if not all(0 <= c <= 255 for c in color):
                raise ValueError("Color values must be between 0 and 255")
        except Exception as e:
            print(f"Error parsing color '{args.color}': {e}")
            sys.exit(1)
        
        # Get default ROI
        roi_data = get_default_roi_for_image(
            args.image_path,
            roi_name=args.roi_name,
            color=color,
            thickness=args.thickness
        )
        
        # Output in requested format
        if args.format == "json":
            print(json.dumps(roi_data, indent=2))
        else:  # yaml
            print(yaml.dump(roi_data, default_flow_style=False))
    else:
        print(f"Unknown images subcommand: {args.images_subcommand}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="PhenoTag - Phenotype Annotation Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command: start the Streamlit UI
    run_parser = subparsers.add_parser("run", help="Start the PhenoTag web application")
    
    # Images command: utilities for working with images
    images_parser = subparsers.add_parser("images", help="Image utility commands")
    images_subparsers = images_parser.add_subparsers(dest="images_subcommand", help="Available image utilities")
    
    # Default ROI subcommand
    default_roi_parser = images_subparsers.add_parser("default-roi", help="Get default ROI for a JPEG file")
    default_roi_parser.add_argument(
        "image_path",
        type=str,
        help="Path to the JPEG image file"
    )
    default_roi_parser.add_argument(
        "--format", "-f",
        choices=["json", "yaml"],
        default="yaml",
        help="Output format (default: yaml)"
    )
    default_roi_parser.add_argument(
        "--roi-name",
        type=str,
        default="ROI_00",
        help="Name for the ROI (default: ROI_00)"
    )
    default_roi_parser.add_argument(
        "--color",
        type=str,
        default="0,255,0",
        help="RGB color for the ROI as comma-separated values (default: 0,255,0 for green)"
    )
    default_roi_parser.add_argument(
        "--thickness",
        type=int,
        default=7,
        help="Line thickness for the ROI (default: 7)"
    )
    
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
    if args.command == "images":
        handle_images_command(args)
    elif args.command == "run":
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