"""
Main application module for DigiPet application.
Coordinates all components and provides the main entry point.
"""
import os
import tkinter as tk
import json
import logging
import random
from typing import Dict, List, Any, Optional
import threading
import time

from core.event_system import EventDispatcher, Event, EventType
from core.plugin_manager import PluginManager
from entities.digimon import Digimon
from sprites.sprite_manager import SpriteManager
from renderers.tkinter_renderer import TkinterRenderer

logger = logging.getLogger(__name__)

class DigiPetApplication:
    """
    Main application class that coordinates all components.
    
    Attributes:
        config_manager (ConfigManager): Configuration manager
        event_dispatcher (EventDispatcher): Event dispatcher
        plugin_manager (PluginManager): Plugin manager
        renderer: The active renderer
        entities (list): List of active entities
        running (bool): Whether the application is running
    """
    
    def __init__(self, config_path: str = "resources/config/default_config.json"):
        """
        Initialize the application.
        
        Args:
            config_path (str, optional): Path to the configuration file
        """
        # Set up logging
        self._configure_logging()
        
        logger.info("Initializing DigiPet application")
        
        # Create core components
        self.event_dispatcher = EventDispatcher()
        self.plugin_manager = PluginManager(self.event_dispatcher)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize state
        self.renderer = None
        self.entities = []
        self.running = False
        self.update_thread = None
        
        logger.info("DigiPet application initialized")
    
    def _configure_logging(self):
        """Configure the logger."""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('digipet.log', mode='w')
            ]
        )
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load the configuration from a JSON file.
        
        Args:
            config_path (str): Path to the configuration file
        
        Returns:
            dict: The configuration data
        """
        # Create default configuration
        default_config = {
            "window": {
                "width": 300,  # Increased window size for better visibility
                "height": 200, # Increased window height
                "title": "DigiPet",
                "bg_color": "lightblue",
                "transparent_color": "lightblue"
            },
            "animation": {
                "speed": 150,  # ms between frames
                "behavior_interval": 3000  # ms between behaviors
            },
            "sprites": {
                "folder": "resources/spritesheets",
                "default": "pet_sprites.png",
                "width": 32,
                "height": 32
            },
            "digimon": {
                "default_type": "Rookie",
                "default_name": "Agumon",
                "behavior": {
                    "walk_probability": 40,
                    "talk_probability": 10,
                    "sleep_probability": 5
                },
                "messages": [
                    "Hello there!",
                    "Need any help?",
                    "I'm your desktop buddy!",
                    "Don't forget to take breaks!",
                    "What are you working on?",
                    "Remember to stay hydrated!",
                    "You're doing great!",
                    "*yawns*"
                ]
            },
            "plugins": {
                "enabled": ["llm_integration"]
            }
        }
        
        # Try to load from file
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                
                # Merge with default config (keeping loaded values)
                self._merge_configs(default_config, loaded_config)
                logger.info(f"Configuration loaded from {config_path}")
            else:
                logger.warning(f"Configuration file {config_path} not found, using defaults")
                
                # Create the config directory if it doesn't exist
                config_dir = os.path.dirname(config_path)
                if not os.path.exists(config_dir):
                    os.makedirs(config_dir, exist_ok=True)
                
                # Save default config
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                
                logger.info(f"Default configuration saved to {config_path}")
        
        except Exception as e:
            logger.error(f"Error loading configuration: {e}", exc_info=True)
        
        return default_config
    
    def _merge_configs(self, base_config: Dict, overlay_config: Dict):
        """
        Recursively merge overlay_config into base_config.
        
        Args:
            base_config (dict): The base configuration to merge into
            overlay_config (dict): The configuration to overlay
        """
        for key, value in overlay_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_configs(base_config[key], value)
            else:
                base_config[key] = value
    
    def _on_config_changed(self, new_config: Dict[str, Any]):
        """
        Handle configuration changes.
        
        Args:
            new_config (dict): The new configuration
        """
        self.config = new_config
        
        # Dispatch config changed event

        self.event_dispatcher.dispatch_event(
            Event(EventType.CONFIG_CHANGED, self, {
                'config': new_config,
                'width': new_config['window']['width'],
                'height': new_config['window']['height'],
                'bg_color': new_config['window']['bg_color'],
                'transparent_color': new_config['window']['transparent_color'],
                'animation_speed': new_config['animation']['speed']
            })
        )
        
        logger.info("Configuration updated")
    
    def initialize(self):
        """Initialize the application components."""
        logger.info("Initializing application components")
        
        # Initialize the renderer
        self.renderer = TkinterRenderer(
            self.config['window']['width'],
            self.config['window']['height'],
            self.event_dispatcher,
            self.config['window']['bg_color'],
            self.config['window']['transparent_color'],
            self.config['window']['title']
        )
        self.renderer.width
        
        # Initialize the renderer window
        self.renderer.initialize()
        
        # Load plugins
        enabled_plugins = self.config['plugins']['enabled']
        self.plugin_manager.load_plugins(enabled_plugins)
        
        # Create and add a Digimon entity
        self._create_digimon()
        
        # Register for events
        self.event_dispatcher.register_listener(EventType.SHUTDOWN, self._handle_shutdown)
        
        logger.info("Application components initialized")
    
    def _create_digimon(self):
        """Create and add a Digimon entity."""
        digimon_config = self.config['digimon']
        sprite_config = self.config['sprites']
        
        # Determine sprite path
        digimon_type = digimon_config['default_type']
        sprite_path = os.path.join(
            sprite_config['folder'],
            digimon_type.lower(),
            sprite_config['default']
        )
        
        # If sprite doesn't exist, use the default
        if not os.path.exists(sprite_path):
            sprite_path = os.path.join(
                sprite_config['folder'],
                sprite_config['default']
            )
            
            # If still doesn't exist, use src directory for backward compatibility
            if not os.path.exists(sprite_path):
                sprite_path = os.path.join("src", sprite_config['default'])
                
                # If still doesn't exist, log error
                if not os.path.exists(sprite_path):
                    logger.error(f"Sprite file not found: {sprite_path}")
                    sprite_path = None
        
        # Create sprite manager
        sprite_manager = SpriteManager(
            sprite_path,
            (sprite_config['width'], sprite_config['height']),
            (self.config['window']['width'], self.config['window']['height']),
            self.config['window']['transparent_color'],
            self._create_sprite_mapping()
        )
        
        # Create Digimon properties
        digimon_props = {
            'evolution_level': digimon_type,
            'messages': digimon_config['messages'],
            'behavior_interval': self.config['animation']['behavior_interval'] / 1000.0,
            'walk_probability': digimon_config['behavior']['walk_probability'],
            'talk_probability': digimon_config['behavior']['talk_probability'],
            'sleep_probability': digimon_config['behavior']['sleep_probability']
        }
        
        # Create Digimon entity
        digimon = Digimon(
            digimon_config['default_name'],
            digimon_type,
            self.event_dispatcher,
            sprite_manager,
            (50, 50),  # Initial position
            (self.config['window']['width'], self.config['window']['height']),
            digimon_props
        )
        
        # Add to entities list
        self.entities.append(digimon)
        
        # Add to renderer
        self.renderer.add_entity(digimon)
        
        logger.info(f"Created Digimon entity: {digimon_config['default_name']} ({digimon_type})")
    
    def _create_sprite_mapping(self) -> Dict[str, List[tuple]]:
        """
        Create a sprite mapping based on configuration.
        
        Returns:
            dict: Mapping of animation states to frame coordinates
        """
        # This would normally be loaded from configuration
        # For now, return a default mapping compatible with existing sprites
        return {
            "idle": [(0, 0), (0, 1), (0, 2), (0, 3)],
            "walk": [(0, 4), (0, 5), (0, 6), (0, 7)],
            "talk": [(0, 0), (0, 1), (0, 2), (0, 3)],
            "sleep": [(0, 4), (0, 5), (0, 6), (0, 7)]
        }
    
    def _handle_shutdown(self, event: Event):
        """
        Handle shutdown events.
        
        Args:
            event (Event): The shutdown event
        """
        logger.info("Shutdown event received")
        self.stop()
    
    def run(self):
        """Run the application."""
        if self.running:
            logger.warning("Application is already running")
            return
        
        logger.info("Starting application")
        
        # Initialize components
        self.initialize()
        
        # Mark as running
        self.running = True
        
        # Dispatch startup event
        self.event_dispatcher.dispatch_event(
            Event(EventType.STARTUP, self)
        )
        
        # Start update thread
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        logger.info("Application started")
        
        # Run the renderer (this will block until window is closed)
        self.renderer.run()
    
    def _update_loop(self):
        """Update loop for background processing."""
        last_time = time.time()
        
        while self.running:
            # Calculate delta time
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time
            
            # Update plugins
            self.plugin_manager.update(delta_time)
            
            # Sleep to reduce CPU usage
            time.sleep(0.01)
    
    def stop(self):
        """Stop the application."""
        if not self.running:
            return
        
        logger.info("Stopping application")
        
        # Mark as not running
        self.running = False
        
        # Clean up renderer
        if self.renderer:
            self.renderer.cleanup()
        
        # Unload plugins
        self.plugin_manager.unload_all_plugins()
        
        logger.info("Application stopped")
