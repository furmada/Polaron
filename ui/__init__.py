from pygame import init, RESIZABLE, FULLSCREEN, VIDEORESIZE, Surface, surface
from pygame.display import set_mode as set_display_mode
from pygame.display import set_caption, flip, Info
from pygame.time import Clock
from pygame import error as pygame_error
from pygame.image import tostring as surface_to_str
from base64 import b64encode
from sys import stdout

from ui.components import RootNode
from ui.actions import QuitReceiver, EventMonitor, EventReceiver
from ui.threaded import is_threaded, ThreadedEventMonitor

from typing import Tuple, List

class Display(object):
    def __init__(self, width: int, height: int, title="Polaron App", resizable=True, fullscreen=False):
        """Create a new Display."""
        self.threaded = is_threaded()
        init()
        if not self.threaded:
            set_caption(title)
        else:
            self._last_frame = None
        self.title = title
        self.resizable = resizable
        self.fullscreen = fullscreen
        self._flags = RESIZABLE if resizable else 0 | FULLSCREEN if fullscreen else 0
        self.root = RootNode(**{
            "x": 0,
            "y": 0,
            "width": width,
            "height": height
            })
        self._generate(width, height)
        self.root.attach_receiver(QuitReceiver())
        self.root.attach_receiver(EventReceiver(VIDEORESIZE, self._handle_resize))
        
    def _generate(self, w, h):
        """Generate the Pygame surface given a width and height."""
        if not self.threaded:
            self.surface = set_display_mode((w, h), self._flags)
        else:
            self.surface = Surface((w, h))
        self.root.size = self.size
        
    def _handle_resize(self, evt):
        """Handles VideoResize events."""
        self.size = evt.size
            
    @property
    def width(self) -> int:
        return self.surface.get_width()
    
    @width.setter
    def width(self, value: int):
        if value != self.width:
            self._generate(value, self.height)
        
    @property
    def height(self) -> int:
        return self.surface.get_height()
    
    @height.setter
    def height(self, value: int):
        if value != self.height:
            self._generate(self.width, value)
        
    @property
    def size(self):
        return (self.width, self.height)
    
    @size.setter
    def size(self, value: Tuple[int] or List[int]):
        if value != self.size:
            self._generate(value[0], value[1])
            
    def render(self):
        """Render the display to the screen."""
        self.root._render()
        self.surface.blit(self.root.surface, (0, 0))
        if not self.threaded:
            flip()
        else:
            f = surface_to_str(self.surface, "RGBA")
            if f != self._last_frame:
                try:
                    stdout.write("<" + str(self.width) + "," + str(self.height) + "|" + b64encode(f).decode("ascii") + ">\n")
                except:
                    pass
                self._last_frame = f
        
    @staticmethod
    def get_system_display_size():
        info = Info()
        return (info.current_w, info.current_h)
            
class Application(object):
    def __init__(self, display, fps=30):
        """The Application is the outermost control object."""
        self.display = display
        self.target_fps = fps
        self.event_monitor = EventMonitor(self.display) if not self.display.threaded else ThreadedEventMonitor(self.display)
        
    def launch(self):
        """Run the application."""
        clock = Clock()
        while self.event_monitor._monitor():
            clock.tick(self.target_fps)
            try:
                self.display.render()
            except pygame_error:
                return
            
class MultiScreenApplication(Application):
    def __init__(self, display, fps=30, **screens):
        """
        An Application that has distinct Screens that display individually.
        Each screen entry should have a unique string name and Node value.
        """
        Application.__init__(self, display, fps=fps)
        self.screens = screens
        
    def add_screen(self, name: str, screen):
        self.screens[name] = screen
        
    def switch_to(self, name: str):
        self.display.root.clear()
        if name in self.screens:
            self.display.root.add(self.screens[name])
        