#!/usr/bin/env python3
"""
Main entry point for DigiPet application.
"""
import os
import sys
import argparse
import logging
from core.application import DigiPetApplication

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='DigiPet - Desktop Digimon Pet')
    
    parser.add_argument(
        '--config',
        type=str,
        default=os.path.join('resources', 'config', 'default_config.json'),
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--digimon',
        type=str,
        help='Specify Digimon type (e.g., Rookie, Champion)'
    )
    
    return parser.parse_args()

def setup_logging(debug=False):
    """
    Set up logging configuration.
    
    Args:
        debug (bool): Whether to enable debug logging
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Set up logging
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join('logs', 'digipet.log'), mode='w')
        ]
    )

def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging
    setup_logging(args.debug)
    
    # Create the application
    app = DigiPetApplication(args.config)
    
    # Apply command line overrides
    if args.digimon:
        app.config['digimon']['default_type'] = args.digimon
    
    # Create required directories
    os.makedirs('resources/config', exist_ok=True)
    os.makedirs('resources/spritesheets', exist_ok=True)
    
    # Run the application
    app.run()

if __name__ == "__main__":
    # Add the current directory to the Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    main()
