"""
Plugin manager for DigiPet application.
Handles loading, initializing, and managing plugins.
"""
import os
import sys
import importlib
import inspect
import logging
from typing import Dict, List, Any, Callable, Optional

from core.event_system import EventDispatcher, Event, EventType

logger = logging.getLogger(__name__)

class PluginInterface:
    """
    Interface that all plugins must implement.
    """
    
    def initialize(self, event_dispatcher: EventDispatcher, config: Dict[str, Any] = None) -> bool:
        """
        Initialize the plugin.
        
        Args:
            event_dispatcher (EventDispatcher): The event dispatcher
            config (dict, optional): Plugin-specific configuration
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        raise NotImplementedError("Plugins must implement initialize()")
    
    def shutdown(self) -> bool:
        """
        Clean up resources when the plugin is unloaded.
        
        Returns:
            bool: True if shutdown was successful, False otherwise
        """
        raise NotImplementedError("Plugins must implement shutdown()")
    
    def update(self, delta_time: float) -> None:
        """
        Update the plugin state.
        
        Args:
            delta_time (float): Time elapsed since last update (in seconds)
        """
        raise NotImplementedError("Plugins must implement update()")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the plugin.
        
        Returns:
            dict: Plugin information (name, version, description)
        """
        raise NotImplementedError("Plugins must implement get_info()")


class PluginManager:
    """
    Manages plugin loading, unloading, and lifecycle.
    
    Attributes:
        event_dispatcher (EventDispatcher): The event dispatcher
        plugins (dict): Dictionary of loaded plugins
        plugin_dir (str): Directory where plugins are located
    """
    
    def __init__(self, event_dispatcher: EventDispatcher, plugin_dir: str = "plugins"):
        """
        Initialize the plugin manager.
        
        Args:
            event_dispatcher (EventDispatcher): The event dispatcher
            plugin_dir (str, optional): Directory where plugins are located
        """
        self.event_dispatcher = event_dispatcher
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_dir = plugin_dir
        
        # Make sure the plugin directory is in the Python path
        if plugin_dir not in sys.path:
            sys.path.append(os.path.abspath(plugin_dir))
        
        logger.debug(f"Plugin manager initialized with plugin directory: {plugin_dir}")
    
    def load_plugin(self, plugin_name: str, config: Dict[str, Any] = None) -> bool:
        """
        Load a single plugin by name.
        
        Args:
            plugin_name (str): Name of the plugin (directory name)
            config (dict, optional): Plugin-specific configuration
        
        Returns:
            bool: True if the plugin was loaded successfully, False otherwise
        """
        # Skip if already loaded
        if plugin_name in self.plugins:
            logger.warning(f"Plugin {plugin_name} is already loaded")
            return True
        
        try:
            # Try to import the plugin module
            if not os.path.exists(os.path.join(self.plugin_dir, plugin_name)):
                logger.error(f"Plugin directory not found: {plugin_name}")
                return False
            
            # Import the plugin module
            plugin_module = importlib.import_module(f"{plugin_name}")
            
            # Find the plugin class
            plugin_class = None
            for _, obj in inspect.getmembers(plugin_module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginInterface) and 
                    obj != PluginInterface):
                    plugin_class = obj
                    break
            
            if not plugin_class:
                logger.error(f"No plugin class found in {plugin_name}")
                return False
            
            # Create an instance of the plugin
            plugin = plugin_class()
            
            # Initialize the plugin
            success = plugin.initialize(self.event_dispatcher, config)
            if not success:
                logger.error(f"Failed to initialize plugin {plugin_name}")
                return False
            
            # Store the plugin
            self.plugins[plugin_name] = plugin
            
            # Get plugin info
            info = plugin.get_info()
            logger.info(f"Loaded plugin: {info.get('name', plugin_name)} v{info.get('version', '?')}")
            
            # Dispatch plugin loaded event
            self.event_dispatcher.dispatch_event(
                Event(EventType.PLUGIN_LOADED, self, {
                    'plugin_name': plugin_name,
                    'plugin_info': info
                })
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}", exc_info=True)
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin by name.
        
        Args:
            plugin_name (str): Name of the plugin to unload
        
        Returns:
            bool: True if the plugin was unloaded successfully, False otherwise
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin {plugin_name} is not loaded")
            return False
        
        try:
            # Get the plugin
            plugin = self.plugins[plugin_name]
            
            # Shut down the plugin
            success = plugin.shutdown()
            
            if success:
                # Remove from plugins dict
                del self.plugins[plugin_name]
                
                # Dispatch plugin unloaded event
                self.event_dispatcher.dispatch_event(
                    Event(EventType.PLUGIN_UNLOADED, self, {
                        'plugin_name': plugin_name
                    })
                )
                
                logger.info(f"Unloaded plugin: {plugin_name}")
            else:
                logger.error(f"Failed to shutdown plugin {plugin_name}")
            
            return success
        
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}", exc_info=True)
            return False
    
    def load_plugins(self, plugin_names: List[str], config: Dict[str, Dict[str, Any]] = None) -> Dict[str, bool]:
        """
        Load multiple plugins by name.
        
        Args:
            plugin_names (list): List of plugin names to load
            config (dict, optional): Dictionary of plugin-specific configurations
        
        Returns:
            dict: Dictionary of plugin names and load success status
        """
        results = {}
        
        for plugin_name in plugin_names:
            plugin_config = None
            if config and plugin_name in config:
                plugin_config = config[plugin_name]
                
            success = self.load_plugin(plugin_name, plugin_config)
            results[plugin_name] = success
        
        return results
    
    def unload_all_plugins(self) -> Dict[str, bool]:
        """
        Unload all loaded plugins.
        
        Returns:
            dict: Dictionary of plugin names and unload success status
        """
        results = {}
        
        # Create a copy of keys to avoid modification during iteration
        plugin_names = list(self.plugins.keys())
        
        for plugin_name in plugin_names:
            success = self.unload_plugin(plugin_name)
            results[plugin_name] = success
        
        return results
    
    def update(self, delta_time: float) -> None:
        """
        Update all loaded plugins.
        
        Args:
            delta_time (float): Time elapsed since last update (in seconds)
        """
        for plugin_name, plugin in self.plugins.items():
            try:
                plugin.update(delta_time)
            except Exception as e:
                logger.error(f"Error updating plugin {plugin_name}: {e}", exc_info=True)
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """
        Get a plugin by name.
        
        Args:
            plugin_name (str): Name of the plugin
        
        Returns:
            Optional[PluginInterface]: The plugin instance, or None if not found
        """
        return self.plugins.get(plugin_name, None)