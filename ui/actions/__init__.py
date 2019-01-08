from pygame.event import get as get_events
from pygame.event import event_name
from pygame import quit as quit_pygame
from pygame import error as pygame_error
from pygame.key import get_mods as get_keyboard_modifiers
from ui.config import CONFIGURATION

class EventMonitor(object):
    def __init__(self, display):
        """The EventMonitor watches for new Pygame events and distributes them to listeners."""
        self._display = display
        
    def _monitor(self):
        """Check for events."""
        evts = []
        try:
            evts = get_events()
        except pygame_error:
            return False
        for event in evts:
            if event != None:
                if event.type == CONFIGURATION["EVENT_TYPES"]["key_up"] or event.type == CONFIGURATION["EVENT_TYPES"]["key_down"]:
                    event.modifiers = get_keyboard_modifiers()
                self.dispatch(event)
        return True
                
    def dispatch(self, event):
        """Find a receiver for the event."""
        self._display.root.receive_event(event)
        
        
class EventReceiver(object):
    def __init__(self, event_types, on_receipt=None, *default, **default_kw):
        """An EventReceiver accepts Events of a certain type.
        Once a matching event is received, the on_receipt method is called,
        with the event as the first parameter and specified defaults following.
        """
        self.event_types = [event_types] if type(event_types) == int else list(event_types)
        self.on_receipt = on_receipt
        self.default_args = list(default)
        self.default_kwargs = default_kw
        self.nodes = []
        self.last_handled = None
                
    def check(self, event) -> bool:
        """Check if an Event can be handled by this receiver."""
        return event.type in self.event_types
    
    def receive(self, event):
        """Receive an Event."""
        if self.check(event):
            if self.on_receipt != None:
                if self.on_receipt(event, *self.default_args, **self.default_kwargs) == False:
                    return False
                self.last_handled = event
                return True
        return False
    
class QuitReceiver(EventReceiver):
    def __init__(self, on_receipt=None, *default, **default_kw):
        """Handles pygame.QUIT events"""
        self._on_receipt = on_receipt
        EventReceiver.__init__(self, CONFIGURATION["EVENT_TYPES"]["quit"], self._handle, *default, **default_kw)
        
    def _handle(self, evt, *args, **kwargs):
        if self._on_receipt != None:
            self._on_receipt(evt, *args, **kwargs)
        quit_pygame()
        
class MouseReceiver(EventReceiver):
    def __init__(self, on_receipt=None, event_types=[CONFIGURATION["EVENT_TYPES"]["mouse_down"],
                                                     CONFIGURATION["EVENT_TYPES"]["mouse_up"],
                                                     CONFIGURATION["EVENT_TYPES"]["mouse_motion"]],
                                                    *default, **default_kw):
        """Handles all mouse events (UP, DOWN, MOTION)
        The receipt method will be given the clicked node in addition to the event."""
        EventReceiver.__init__(self, event_types, on_receipt, *([None] + list(default)), **default_kw)
        
    def check(self, event, buttons=[1, 3]) -> bool:
        if (EventReceiver.check(self, event) and 
            (event.type == CONFIGURATION["EVENT_TYPES"]["mouse_motion"] or event.button in buttons)):
            for node in self.nodes:
                if node.parent == None or node in node.parent.visible_children():
                    abs_pos = node.absolute_position
                    if event.pos[0] >= abs_pos[0] and event.pos[0] <= abs_pos[0] + node.width:
                        if event.pos[1] >= abs_pos[1] and event.pos[1] <= abs_pos[1] + node.height:
                            self.default_args[0] = node
                            return True
        self.default_args[0] = None
        return False
        
class ClickReceiver(MouseReceiver):
    def __init__(self, on_receipt=None, *default, **default_kw):
        """Handles pygame.MOUSEBUTTONUP events"""
        MouseReceiver.__init__(self, on_receipt, CONFIGURATION["EVENT_TYPES"]["mouse_up"], *default, **default_kw)
        
class MouseScrollReveiver(MouseReceiver):
    def __init__(self, on_receipt=None, *default, **default_kw):
        """Handles mouse events representing scroll up (button 4) and down (button 5)."""
        MouseReceiver.__init__(self, on_receipt, [CONFIGURATION["EVENT_TYPES"]["mouse_down"]], *default, **default_kw)
        
    def check(self, event) -> bool:
        return MouseReceiver.check(self, event, buttons=[4, 5])
        
class DragEvent(object):
    def __init__(self, start, end):
        """Custom Event for complex drag events."""
        self.type = CONFIGURATION["EVENT_TYPES"]["drag"]
        self.start_pos = start
        self.end_pos = end
        self.pos = end
        
class DragReceiver(MouseReceiver):
    def __init__(self, on_receipt=None, on_update=None, update_args=[], update_kwargs={},
                  *default, **default_kw):
        """Handles complex click, drag and release events.
        This receiver requires focus of DOWN, MOTION, and UP events.
        Optionally, a ClickReceiver can be specified to trigger if no drag
        is detected to send a click event.
        An update method and additional arguments can also be supplied.
        If it exists, the update method will be passed the MOUSEMOTION event
        and a tuple of the form (dx, dy).
        """
        self._on_receipt = on_receipt
        self._drag_state = 0
        self._distance = 0
        self._start_coords = (0, 0)
        self._node_start_coords = (0, 0)
        self.on_update = on_update
        self._update_args = update_args
        self._update_kwargs = update_kwargs
        self.trigger_distance = CONFIGURATION["DRAG_MIN_DISTANCE"]
        MouseReceiver.__init__(self, self._handle, *default, **default_kw)
        
    def check(self, event) -> bool:
        if self._drag_state == 0:
            return MouseReceiver.check(self, event)
        else:
            return event.type in [CONFIGURATION["EVENT_TYPES"]["mouse_motion"], CONFIGURATION["EVENT_TYPES"]["mouse_up"]]
        
    def _handle(self, event, *args, **kwargs):
        if event.type == CONFIGURATION["EVENT_TYPES"]["mouse_down"]:
            if self._drag_state == 0:
                self._drag_state = 1
                self._distance = 0
                self._start_coords = event.pos
                self._node_start_coords = args[0].position
                self._last_coords = event.pos
                return True
            else:
                return False
        if event.type == CONFIGURATION["EVENT_TYPES"]["mouse_motion"] and (self._drag_state == 1 or self._drag_state == 2):
            if ((event.pos[0] - self._start_coords[0])**2 + 
                ((event.pos[1] - self._start_coords[1])**2))**0.5 > self.trigger_distance:
                self._drag_state = 2
            if self.on_update != None:
                self.on_update(event, (event.pos[0] - self._last_coords[0],
                                       event.pos[1] - self._last_coords[1]),
                                       *([self.default_args[0]] + list(self._update_args)), **self._update_kwargs)
            self._last_coords = event.pos
            return True
        if event.type == CONFIGURATION["EVENT_TYPES"]["mouse_up"]:
            if self._drag_state == 2:
                if self._on_receipt != None:
                    self._on_receipt(DragEvent(self._start_coords, event.pos), *args, **kwargs)
                self._drag_state = 0
                return True
            if self._drag_state == 1:
                args[0].position = self._node_start_coords
            self._drag_state = 0
            return False

class KeyboardReceiver(EventReceiver):
    def __init__(self, node, on_receipt=None, *default, **default_kw):
        """Handles KEYDOWN and KEYUP events."""
        EventReceiver.__init__(self, [CONFIGURATION["EVENT_TYPES"]["key_down"], CONFIGURATION["EVENT_TYPES"]["key_up"]],
                               on_receipt, *default, **default_kw)
        self.node = node
        
    def check(self, event) -> bool:
        return (EventReceiver.check(self, event) and self.node.focused)
    
class PropertyChangeEvent(object):   
    def __init__(self, prop, value):
        """Custom event type for handling Node property changes."""
        self.type = CONFIGURATION["EVENT_TYPES"]["property_change"]
        self.prop = prop
        self.value = value
    
class PropertyChangeReceiver(EventReceiver):
    def __init__(self, prop, on_receipt=None, *default, **default_kw):
        """Handles Node property value change events. Specify the property/properties to monitor."""
        self.properties = [prop] if type(prop) != list else prop
        EventReceiver.__init__(self, CONFIGURATION["EVENT_TYPES"]["property_change"], on_receipt, *default, **default_kw)
        
    def check(self, event) -> bool:
        return event.prop in self.properties