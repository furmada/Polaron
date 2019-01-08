from subprocess import Popen as new_process
from subprocess import PIPE
from threading import Thread
from queue import Queue, Empty
from sys import builtin_module_names, stdin

from sys import executable as PYTHON_EXEC
from os import environ as OS_ENV_VARS
from pygame.image import frombuffer
from pygame.event import Event as PygameEvent
from base64 import b64decode, b64encode
from ast import literal_eval

from ui.config import POLARON_ROOT, CONFIGURATION
from ui.components import Node
from ui.actions import EventMonitor, MouseReceiver, EventReceiver,\
    KeyboardReceiver

def is_threaded() -> bool:
    """Returns True if the current process is a subthread."""
    return OS_ENV_VARS.get("POLARON_SUBTHREAD", False) == "YES"

def _enqueue(stream, queue):
    for line in iter(stream.readline, b''):
        queue.put(line)
    stream.close()

def start_app(path, local=POLARON_ROOT[:-3], *args):
    """Runs the specified file as a Polaron app in a subprocess. Specify the local (working) directory and arguments to pass."""
    e = OS_ENV_VARS.copy()
    e["POLARON_SUBTHREAD"] = "YES"
    e["POLARON_ROOT"] = POLARON_ROOT
    proc = new_process([PYTHON_EXEC, path, *args], env=e, cwd=local, stdout=PIPE, stdin=PIPE, bufsize=1, universal_newlines=True,
                       close_fds=("posix" in builtin_module_names))
    queue = Queue()
    Thread(target=_enqueue, args=(proc.stdout, queue), daemon=True, name="Polaron: App").start()
    return proc, queue

class ThreadedEventMonitor(EventMonitor):
    """Monitors for events from stdin."""
    def __init__(self, display):
        EventMonitor.__init__(self, display)
        self.queue = Queue()
        Thread(target=_enqueue, args=(stdin, self.queue), daemon=True, name="Polaron: EventMonitor").start()
    
    def _monitor(self):
        try:
            line = self.queue.get_nowait().rstrip("\n")
            if len(line) > 0 and line[0] == "<" and line[-1] == ">":
                evt = PygameEvent(int(line[1:line.find("|")]), literal_eval(str(b64decode(line[line.find("|") + 1:-1]), encoding="utf-8")))
                self.dispatch(evt)
                if evt.type == CONFIGURATION["EVENT_TYPES"]["quit"]:
                    return False
        except Empty:
            pass
        return True
    
    @staticmethod
    def encode_event(evt):
        """Encode a Pygame event as a base64 string that can be sent over a pipe."""
        return str(evt.type) + "|" + b64encode(bytes(str(evt.__dict__), encoding="utf-8")).decode("ascii")

class ThreadedDisplay(Node):
    """
    A ThreadedDisplay node is used to display the UI of a Subprocess and display it as a Node.
    The Node is automatically resized to match the Display size communicated by the process.
    The queue argument is the Queue object returned by start_app.
    Supported parameters:
    - Node parameters
    """
    
    def __init__(self, proc, queue, **data):
        Node.__init__(self, **data)
        self.process = proc
        self.queue = queue
        self._frame = None
        self.attach_receiver(MouseReceiver(self._mouse_passthrough))
        self.attach_receiver(EventReceiver(CONFIGURATION["EVENT_TYPES"]["quit"], self.passthrough))
        self.attach_receiver(KeyboardReceiver(self, self.passthrough))
        
    def _mouse_passthrough(self, evt, *_):
        evt.pos = (evt.pos[0] - self.absolute_position[0], evt.pos[1] - self.absolute_position[1])
        self.passthrough(evt)
        
    def passthrough(self, evt, *_):
        try:
            self.process.stdin.write("<" + ThreadedEventMonitor.encode_event(evt) + ">\n")
        except:
            self._frame.fill((255, 150, 150))
        
    def draw(self):
        Node.draw(self)
        try:
            line = self.queue.get_nowait().rstrip("\n")
            if len(line) > 0 and line[0] == "<" and line[-1] == ">":
                try:
                    w = int(line[1:line.find(",")])
                    h = int(line[line.find(",") + 1:line.find("|")])
                    self._frame = frombuffer(b64decode(line[line.find("|") + 1:-1]), (w, h), "RGBA")
                    if self.width != w:
                        self.width = w
                    if self.height != h:
                        self.height = h
                    self.root_node().redraw = True
                except Exception as e:
                    print("Malformed frame received!")
                    print(e)
        except Empty:
            pass
        if self._frame != None:
            self.surface.blit(self._frame, (0, 0))
            
            