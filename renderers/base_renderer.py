"""
Base renderer module for DigiPet application.
Provides an abstract base class for all rendering implementations.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any, Optional
import logging
from core.event_system import EventDispatcher, Event, EventType

logger = logging.getLogger(__name__)

class BaseRenderer(ABC):
    """
    Abstract base class for all renderers.
    
    Attributes:
        width (int): Width of the rendering area
        height (int): Height of the rendering area
        event_dispatcher (EventDispatcher): The event dispatcher
        bg_color (str): Background color
        transparent_color (str): Color to make transparent
    """
    
    def __init__(self, width: int, height: int, event_dispatcher: EventDispatcher,
                 bg_color: str = "white", transparent_color: Optional[str] = None):
        """
        Initialize the base renderer.
        
        Args:
            width (int): Width of the rendering area
            height (int): Height of the rendering area
            event_dispatcher (EventDispatcher): The event dispatcher
            bg_color (str, optional): Background color
            transparent_color (str, optional): Color to make transparent
        """
        self.width = width
        self.height = height
        self.event_dispatcher = event_dispatcher
        self.bg_color = bg_color
        self.transparent_color = transparent_color
        self.entities = []
        
        # Register for relevant events
        self._register_event_handlers()
        
        logger.debug(f"Renderer initialized with size ({width}x{height})")
    
    def _register_event_handlers(self):
        """Register for events this renderer is interested in."""
        self.event_dispatcher.register_listener(EventType.SPEAK, self.handle_speak_event)
        self.event_dispatcher.register_listener(EventType.STOP_SPEAKING, self.handle_stop_speaking_event)
        self.event_dispatcher.register_listener(EventType.CONFIG_CHANGED, self.handle_config_changed)
    
    def add_entity(self, entity):
        """
        Add an entity to be rendered.
        
        Args:
            entity: The entity to add
        """
        self.entities.append(entity)
        logger.debug(f"Added entity '{entity.name}' to renderer")
    
    def remove_entity(self, entity):
        """
        Remove an entity from rendering.
        
        Args:
            entity: The entity to remove
        """
        if entity in self.entities:
            self.entities.remove(entity)
            logger.debug(f"Removed entity '{entity.name}' from renderer")
    
    def handle_speak_event(self, event: Event):
        """
        Handle speak events to display speech bubbles.
        
        Args:
            event (Event): The speak event
        """
        # Each renderer implementation should handle this
        # to display speech bubbles in their own way
        pass
    
    def handle_stop_speaking_event(self, event: Event):
        """
        Handle stop speaking events to remove speech bubbles.
        
        Args:
            event (Event): The stop speaking event
        """
        # Each renderer implementation should handle this
        pass
    
    def handle_config_changed(self, event: Event):
        """
        Handle configuration change events.
        
        Args:
            event (Event): The configuration changed event
        """
        # Update background and transparency if in the config
        if 'bg_color' in event.data:
            self.bg_color = event.data['bg_color']
        
        if 'transparent_color' in event.data:
            self.transparent_color = event.data['transparent_color']
        
        # Update size if needed
        if 'width' in event.data and 'height' in event.data:
            self.width = event.data['width']
            self.height = event.data['height']
        
        logger.debug(f"Renderer updated from config change")
    
    @abstractmethod
    def initialize(self):
        """Initialize the renderer and create necessary resources."""
        pass
    
    @abstractmethod
    def render(self):
        """Render the current state of all entities."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up resources when shutting down."""
        pass
    
    @abstractmethod
    def convert_input_event(self, event_data: Dict[str, Any]) -> Optional[Event]:
        """
        Convert platform-specific input events to system events.
        
        Args:
            event_data (dict): Platform-specific event data
        
        Returns:
            Optional[Event]: Converted system event, or None if not relevant
        """
        pass