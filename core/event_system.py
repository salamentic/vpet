"""
Event system for DigiPet application.
Provides a centralized event dispatcher for communication between components.
"""
from typing import Dict, List, Callable, Any
import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Standard event types in the application."""
    # System events
    STARTUP = auto()
    SHUTDOWN = auto()
    CONFIG_CHANGED = auto()
    
    # User interaction events
    MOUSE_CLICK = auto()
    MOUSE_DRAG = auto()
    MOUSE_RELEASE = auto()
    MOUSE_DOUBLE_CLICK = auto()
    
    # Entity state events
    STATE_CHANGED = auto()
    ANIMATION_FRAME = auto()
    
    # Behavior events
    BEHAVIOR_CHANGED = auto()
    START_WALK = auto()
    START_IDLE = auto()
    START_TALK = auto()
    START_SLEEP = auto()
    
    # Speech events
    SPEAK = auto()
    STOP_SPEAKING = auto()
    
    # Plugin events
    PLUGIN_LOADED = auto()
    PLUGIN_UNLOADED = auto()
    
    # LLM integration events
    LLM_RESPONSE = auto()

class Event:
    """
    Event class that carries information about an event.
    
    Attributes:
        event_type (EventType): The type of event
        source (object): The object that generated the event
        data (dict): Additional data about the event
    """
    def __init__(self, event_type: EventType, source: Any = None, data: Dict = None):
        """
        Initialize a new event.
        
        Args:
            event_type (EventType): The type of event
            source (object, optional): The object that generated the event
            data (dict, optional): Additional data about the event
        """
        self.event_type = event_type
        self.source = source
        self.data = data or {}
    
    def __str__(self):
        return f"Event({self.event_type.name}, source={self.source.__class__.__name__ if self.source else None}, data={self.data})"

class EventDispatcher:
    """
    Centralized event dispatcher.
    Allows components to register for events and dispatch events.
    """
    def __init__(self):
        """Initialize an empty event dispatcher."""
        self._listeners: Dict[EventType, List[Callable[[Event], None]]] = {}
        logger.debug("EventDispatcher initialized")
    
    def register_listener(self, event_type: EventType, listener: Callable[[Event], None]):
        """
        Register a listener for a specific event type.
        
        Args:
            event_type (EventType): The event type to listen for
            listener (callable): The function to call when the event occurs
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)
        logger.debug(f"Registered listener for {event_type.name}")
    
    def unregister_listener(self, event_type: EventType, listener: Callable[[Event], None]):
        """
        Unregister a listener for a specific event type.
        
        Args:
            event_type (EventType): The event type to stop listening for
            listener (callable): The function to unregister
        """
        if event_type in self._listeners and listener in self._listeners[event_type]:
            self._listeners[event_type].remove(listener)
            logger.debug(f"Unregistered listener for {event_type.name}")
    
    def dispatch_event(self, event: Event):
        """
        Dispatch an event to all registered listeners.
        
        Args:
            event (Event): The event to dispatch
        """
        logger.debug(f"Dispatching {event}")
        if event.event_type in self._listeners:
            for listener in self._listeners[event.event_type]:
                try:
                    listener(event)
                except Exception as e:
                    logger.error(f"Error in event listener: {e}", exc_info=True)