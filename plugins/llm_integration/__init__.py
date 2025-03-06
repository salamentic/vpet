"""
LLM Integration plugin for DigiPet application.
Allows pets to generate dynamic responses using LLMs.
"""
import logging
import json
import random
from typing import Dict, List, Any, Optional
import threading
import time

from core.event_system import EventDispatcher, Event, EventType
from core.plugin_manager import PluginInterface
from plugins.llm_integration.llm_connector import LLMConnector

logger = logging.getLogger(__name__)

class LLMIntegrationPlugin(PluginInterface):
    """
    Plugin for integrating LLMs with DigiPet.
    
    Attributes:
        event_dispatcher (EventDispatcher): The event dispatcher
        llm_connector (LLMConnector): Connector to the LLM service
        config (dict): Plugin configuration
        interaction_history (list): History of interactions for context
        entities (dict): Dictionary of known entities
        prompt_templates (dict): Templates for different types of prompts
    """
    
    def __init__(self):
        """Initialize the LLM integration plugin."""
        self.event_dispatcher = None
        self.llm_connector = None
        self.config = None
        self.interaction_history = []
        self.entities = {}
        self.prompt_templates = {}
        self.api_ready = False
        
        # Default prompt templates
        self._load_default_templates()
    
    def initialize(self, event_dispatcher: EventDispatcher, config: Dict[str, Any] = None) -> bool:
        """
        Initialize the plugin.
        
        Args:
            event_dispatcher (EventDispatcher): The event dispatcher
            config (dict, optional): Plugin-specific configuration
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        self.event_dispatcher = event_dispatcher
        self.config = config or {}
        
        # Register for events
        self._register_events()
        
        # Initialize LLM connector
        api_key = self.config.get('api_key', None)
        model = self.config.get('model', 'gpt-3.5-turbo')
        
        # Use mock connector if no API key provided
        if not api_key:
            logger.warning("No API key provided, using mock LLM connector")
            self.llm_connector = MockLLMConnector()
        else:
            self.llm_connector = LLMConnector(api_key, model)
        
        # Check if API is ready
        self.api_ready = self.llm_connector.check_availability()
        
        # Load custom prompt templates if provided
        if 'prompt_templates' in self.config:
            self.prompt_templates.update(self.config['prompt_templates'])
        
        logger.info(f"LLM Integration plugin initialized (API ready: {self.api_ready})")
        return True
    
    def shutdown(self) -> bool:
        """
        Clean up resources when the plugin is unloaded.
        
        Returns:
            bool: True if shutdown was successful, False otherwise
        """
        # Unregister event handlers
        if self.event_dispatcher:
            self.event_dispatcher.unregister_listener(EventType.MOUSE_DOUBLE_CLICK, self.handle_double_click)
            self.event_dispatcher.unregister_listener(EventType.STATE_CHANGED, self.handle_state_changed)
        
        logger.info("LLM Integration plugin shut down")
        return True
    
    def update(self, delta_time: float) -> None:
        """
        Update the plugin state.
        
        Args:
            delta_time (float): Time elapsed since last update (in seconds)
        """
        # Nothing to do in update for this plugin
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the plugin.
        
        Returns:
            dict: Plugin information
        """
        return {
            'name': 'LLM Integration',
            'version': '1.0.0',
            'description': 'Integrates LLMs for dynamic pet responses',
            'author': 'DigiPet Team',
            'api_ready': self.api_ready
        }
    
    def _register_events(self):
        """Register for events this plugin is interested in."""
        self.event_dispatcher.register_listener(EventType.MOUSE_DOUBLE_CLICK, self.handle_double_click)
        self.event_dispatcher.register_listener(EventType.STATE_CHANGED, self.handle_state_changed)
    
    def _load_default_templates(self):
        """Load default prompt templates."""
        self.prompt_templates = {
            'greeting': (
                "You are a Digimon named {name} of type {type}. "
                "You are a digital pet living on the user's desktop. "
                "Generate a short, friendly greeting (max 1-2 sentences) for your human partner. "
                "Be cute and friendly. Make sure your response reflects your Digimon personality."
            ),
            'chat': (
                "You are a Digimon named {name} of type {type}. "
                "You are a digital pet living on the user's desktop. "
                "The user has just interacted with you. "
                "Generate a short response (max 1-2 sentences) that a friendly digital pet would say. "
                "Be cute and engage with the user. Your response must be suitable for all ages. "
                "Previous interactions: {history}"
            ),
            'state_change': (
                "You are a Digimon named {name} of type {type}. "
                "Your state just changed from {old_state} to {new_state}. "
                "Generate a very short response (max 1 sentence) about this change. "
                "For example, if you're going to sleep, say something sleepy. "
                "If you're waking up, say something energetic."
            )
        }
    
    def handle_double_click(self, event: Event):
        """
        Handle double-click events to generate LLM responses.
        
        Args:
            event (Event): The double-click event
        """
        # Only handle events with an entity
        if 'entity' not in event.data:
            return
        
        entity = event.data['entity']
        
        # Store entity if not already known
        if entity.name not in self.entities:
            self.entities[entity.name] = {
                'type': getattr(entity, 'digimon_type', 'Unknown'),
                'last_interaction_time': time.time()
            }
        
        # Create a thread to avoid blocking the UI
        threading.Thread(
            target=self._generate_response,
            args=(entity, 'chat'),
            daemon=True
        ).start()
    
    def handle_state_changed(self, event: Event):
        """
        Handle state change events to generate contextual responses.
        
        Args:
            event (Event): The state change event
        """
        entity = event.source
        old_state = event.data.get('old_state')
        new_state = event.data.get('new_state')
        
        # Only respond to certain state changes (not every change should trigger a response)
        interesting_changes = [
            ('idle', 'sleep'),
            ('sleep', 'idle'),
            ('idle', 'talk'),
            ('walk', 'idle')
        ]
        
        if (old_state, new_state) in interesting_changes:
            # Create a thread to avoid blocking the UI
            threading.Thread(
                target=self._generate_response,
                args=(entity, 'state_change'),
                kwargs={'old_state': old_state, 'new_state': new_state},
                daemon=True
            ).start()
    
    def _generate_response(self, entity, prompt_type: str, **kwargs):
        """
        Generate a response using the LLM.
        
        Args:
            entity: The entity to generate a response for
            prompt_type (str): The type of prompt to use
            **kwargs: Additional context for the prompt
        """
        if not self.api_ready:
            # If API is not available, use a fallback response
            self._send_fallback_response(entity, prompt_type)
            return
        
        try:
            # Get entity info
            entity_info = self.entities.get(entity.name, {
                'type': getattr(entity, 'digimon_type', 'Unknown'),
                'last_interaction_time': time.time()
            })
            
            # Update last interaction time
            entity_info['last_interaction_time'] = time.time()
            
            # Format the prompt template
            prompt_template = self.prompt_templates.get(prompt_type, self.prompt_templates['chat'])
            
            # Create context for template formatting
            context = {
                'name': entity.name,
                'type': entity_info['type'],
                'history': self._format_history(),
                **kwargs
            }
            
            # Format the prompt
            prompt = prompt_template.format(**context)
            
            # Generate response from LLM
            response = self.llm_connector.generate_response(prompt)
            
            if response:
                # Store in interaction history
                self.interaction_history.append({
                    'timestamp': time.time(),
                    'entity': entity.name,
                    'response': response
                })
                
                # Trim history if it gets too long
                if len(self.interaction_history) > 10:
                    self.interaction_history = self.interaction_history[-10:]
                
                # Parse for actions (if any)
                actions = self._parse_actions(response)
                
                # Dispatch LLM response event
                self.event_dispatcher.dispatch_event(
                    Event(EventType.LLM_RESPONSE, self, {
                        'target': entity.name,
                        'message': response,
                        'prompt_type': prompt_type,
                        'actions': actions
                    })
                )
            else:
                # If no response, fall back to predefined responses
                self._send_fallback_response(entity, prompt_type)
        
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}", exc_info=True)
            self._send_fallback_response(entity, prompt_type)
    
    def _format_history(self) -> str:
        """
        Format the interaction history for inclusion in prompts.
        
        Returns:
            str: Formatted interaction history
        """
        if not self.interaction_history:
            return "No previous interactions."
        
        # Format the last few interactions
        history_items = []
        for item in self.interaction_history[-3:]:  # Last 3 interactions
            timestamp = time.strftime('%H:%M:%S', time.localtime(item['timestamp']))
            history_items.append(f"[{timestamp}] {item['entity']}: {item['response']}")
        
        return "\n".join(history_items)
    
    def _parse_actions(self, response: str) -> List[str]:
        """
        Parse the response for any special actions.
        
        Args:
            response (str): The LLM response
        
        Returns:
            list: List of action identifiers
        """
        actions = []
        
        # Simple keyword matching for actions
        if any(word in response.lower() for word in ['hungry', 'feed', 'food']):
            actions.append('feed')
        
        if any(word in response.lower() for word in ['play', 'fun', 'game']):
            actions.append('play')
        
        if any(word in response.lower() for word in ['sleep', 'tired', 'rest']):
            actions.append('sleep')
        
        return actions
    
    def _send_fallback_response(self, entity, prompt_type: str):
        """
        Send a fallback response when LLM is unavailable.
        
        Args:
            entity: The entity to send a response for
            prompt_type (str): The type of prompt that was requested
        """
        # Fallback responses for different prompt types
        fallbacks = {
            'greeting': [
                "Hello there!",
                "Hi! Nice to see you!",
                "Hey! How are you today?"
            ],
            'chat': [
                "What's up?",
                "How can I help you?",
                "It's nice to chat with you!",
                "I'm your digital buddy!",
                "Need something?"
            ],
            'state_change': {
                'sleep': ["Yawn... getting sleepy...", "Time for a nap..."],
                'idle': ["I'm back!", "That was refreshing!"],
                'walk': ["Let's explore!", "Walking is fun!"],
                'talk': ["Did someone say something?", "I love chatting!"]
            }
        }
        
        # Select appropriate fallback
        if prompt_type == 'state_change':
            new_state = getattr(entity, 'current_state', 'idle')
            responses = fallbacks['state_change'].get(new_state, fallbacks['chat'])
        else:
            responses = fallbacks.get(prompt_type, fallbacks['chat'])
        
        # Pick a random response
        response = random.choice(responses)
        
        # Dispatch LLM response event with fallback
        self.event_dispatcher.dispatch_event(
            Event(EventType.LLM_RESPONSE, self, {
                'target': entity.name,
                'message': response,
                'prompt_type': prompt_type,
                'actions': [],
                'fallback': True
            })
        )


class MockLLMConnector:
    """
    Mock LLM connector for testing or when API is unavailable.
    """
    
    def __init__(self):
        """Initialize the mock connector."""
        self.responses = [
            "Hi there! How can I help you today?",
            "I'm your digital pet! Let's have fun together!",
            "Did you know Digimon stands for Digital Monsters?",
            "I'm feeling energetic today! Want to play?",
            "The digital world is full of adventures!",
            "I'm hungry! Got any digital food?",
            "It's nice spending time with you!",
            "I wonder what other Digimon are doing right now?",
            "Your desktop is my favorite place to be!",
            "Let me know if you need anything!"
        ]
    
    def check_availability(self) -> bool:
        """
        Check if the API is available.
        
        Returns:
            bool: Always returns True for the mock connector
        """
        return True
    
    def generate_response(self, prompt: str) -> str:
        """
        Generate a mock response.
        
        Args:
            prompt (str): The prompt (ignored in mock)
        
        Returns:
            str: A random predefined response
        """
        # Simulate network delay
        time.sleep(0.5)
        
        # Return random response
        return random.choice(self.responses)