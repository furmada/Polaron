from pygame import Surface, SRCALPHA
from pygame.draw import rect as draw_rect
from pygame.draw import circle as draw_circle
from pygame.draw import polygon as draw_polygon
from pygame.image import load as load_image
from pygame.transform import smoothscale
from typing import Tuple, List
from ui.actions import EventReceiver, DragReceiver, DragEvent, MouseReceiver,\
    ClickReceiver, KeyboardReceiver, PropertyChangeEvent, MouseScrollReveiver,\
    PropertyChangeReceiver
from ui.components.style import Style, invert_color
from ui.config import CONFIGURATION

"""
This file contains the basic visual building blocks of a Polaron app, Nodes.
"""

class Node(object):
    """
    A Node is the base-level component of GUIs built in Polaron.
    Supported parameters:
    - x: x position relative to parent.
    - y: y position relative to parent.
    - width: width in pixels.
    - height: height in pixels.
    - children: list of Nodes to start with as children.
    - style: a Style object to associate with the Node.
    - receivers: list event receivers to attach to the Node.
    - visible: whether to show the Node or not.
    - focused: whether the Node has keyboard focus. Default False.
    - name: identifies the Node in a human-readable way. Can be used for styling. Default "".
    """
    
    def __init__(self, **data):
        """Initialize the Node."""
        self._children = []
        self._style = Style()
        self.update(**data)
        
    def update(self, **data):
        """Update the Node's properties based on the data provided."""
        self.parent = data.get("parent", None)
        self._x = data.get("x", 0)
        self._y = data.get("y", 0)
        self._width = data.get("width", 0)
        self._height = data.get("height", 0)
        self._name = data.get("name", "")
        self._generate(self._width, self._height)
        self.receivers = {}
        self.style = Style.merge_styles(Style(**CONFIGURATION["STYLE_DEFAULTS"]),
                                        Style(**data.get("style", {})))
        self._visible = data.get("visible", True)
        self._focused = data.get("focused", False)
        for recv in data.get("receivers", []):
            self.attach_receiver(recv)
        self.children = []
        self.add(*data.get("children", []))
                
    def _generate(self, w, h):
        """Generate the Surface for the Node."""
        self.surface = Surface((w, h), SRCALPHA)
        
    @property
    def x(self) -> int:
        return self._x
    
    @x.setter
    def x(self, value):
        self._x = int(value)
        self._on_property_changed("x")
        
    @property
    def y(self) -> int:
        return self._y
    
    @y.setter
    def y(self, value):
        self._y = int(value)
        self._on_property_changed("y")
    
    @property
    def position(self) -> Tuple[int]:
        return (self.x, self.y)
    
    @position.setter
    def position(self, value: Tuple or List):
        if len(value) != 2:
            raise ValueError("Position must be in the form (x, y)")
        self.x, self.y = tuple(value)
        self._on_property_changed("position")
        
    @property
    def absolute_position(self) -> Tuple[int]:
        if self.parent == None:
            return self.position
        parent_abs = self.parent.absolute_position
        return (self.x + parent_abs[0], self.y + parent_abs[1])
    
    @property
    def width(self):
        return self.surface.get_width()
    
    @width.setter
    def width(self, value: int):
        if value != self.width:
            self._width = int(value)
            self._generate(self._width, self.height)
            self._on_property_changed("width")
        
    @property
    def height(self):
        return self.surface.get_height()
    
    @height.setter
    def height(self, value: int):
        if value != self.height:
            self._height = int(value)
            self._generate(self.width, self._height)
            self._on_property_changed("height")
            
    @property
    def size(self):
        return (self.width, self.height)
    
    @size.setter
    def size(self, value: Tuple[int] or List[int]):
        if value != self.size:
            self._generate(value[0], value[1])
    
    @property
    def children(self) -> List["Node"]:
        return self._children
    
    @children.setter
    def children(self, value: Tuple["Node"] or List["Node"]):
        self.clear()
        for node in value:
            self.add_child(node)
        self._on_property_changed("children")
            
    @property
    def style(self):
        return self._style
    
    @style.setter
    def style(self, value):
        s = Style.parse_style(value)
        if s != None:
            self._style = Style.merge_styles(self._style, s)
            Style.apply(self._style, self)
            self._on_property_changed("style")
            
    @property
    def visible(self):
        return self._visible
    
    @visible.setter
    def visible(self, value: bool):
        self._visible = value
        self._on_property_changed("visible")
            
    @property
    def focused(self):
        return self._focused
    
    @focused.setter
    def focused(self, value: bool):
        if value != self._focused:
            self._focused = value
            if self.parent != None:
                if value == True:
                    self.root_node().focused_node = self
                elif value == False and self.root_node().focused_node == self:
                    self.root_node().focused_node = None
            self._on_property_changed("focused")
            
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value: str):
        if value != self._name:
            self._name = value
            self._on_property_changed("name")
            
    def __contains__(self, value):
        return value in self._children
    
    def __iter__(self):
        return iter(self._children)
    
    def __str__(self):
        return str(self.__class__) + " in (" + str(self.parent) + ") at " + str(self.position)
    
    def _on_property_changed(self, prop: str):
        """Call the appropriate event listener when a Node property is changed."""
        if hasattr(self, prop):
            self.receive_event(PropertyChangeEvent(prop, getattr(self, prop)))
    
    def _on_add(self, parent: "Node"):
        """Generate the Surface when added to a Node and register parent node."""
        self.parent = parent
            
    def add(self, *nodes: "Node"):
        """Add Node(s) as a child of this Node."""
        for node in nodes:
            if node in self:
                raise ValueError("The node " + str(node) + " is already a child of " + str(self))
            self._children.append(node)
            node._on_add(self)
        self._on_property_changed("children")
            
    def remove(self, *nodes: "Node"):
        """Remove children from this Node."""
        for child in nodes:
            if child not in self:
                return
            child.parent = None
            self._children.remove(child)
        self._on_property_changed("children")
        
    def clear(self):
        """Remove all child Nodes."""
        for child in self:
            child.parent = None
        self._children = []
        self._on_property_changed("children")
        
    def visible_children(self) -> List["Node"]:
        """Returns a list of child Nodes that are visible within this Node."""
        visible = []
        for child in self:
            if self.intersects(child):
                visible.append(child)
        return visible
    
    def root_node(self) -> "Node":
        """Returns the root (absolute parent) of this Node."""
        if self.parent == None:
            return self
        return self.parent.root_node()
    
    def intersects(self, node: "Node") -> bool:
        """Returns True if the specified Node overlaps this one."""
        cmp_abs = node.absolute_position
        self_abs = self.absolute_position
        #X containment
        if ((cmp_abs[0] >= self_abs[0] and cmp_abs[0] <= self_abs[0] + self.width) or
            (self_abs[0] >= cmp_abs[0] and self_abs[0] <= cmp_abs[0] + node.width)):
            #Y containment
            if ((cmp_abs[1] >= self_abs[1] and cmp_abs[1] <= self_abs[1] + self.height) or
                (self_abs[1] >= cmp_abs[1] and self_abs[1] <= cmp_abs[1] + node.height)):
                return True
        return False
    
    def attach_receiver(self, receiver: EventReceiver):
        """Attach an EventReceiver to this Node."""
        for etype in receiver.event_types:
            if receiver in self.receivers.get(etype, []):
                raise ValueError("The receiver " + str(receiver) + " is already attached.")
            else:
                receiver.nodes.append(self)
                if etype not in self.receivers:
                    self.receivers[etype] = []
                self.receivers[etype].append(receiver)
    
    def detach_receiver(self, receiver):
        """Detach a receiver by value or event type(s)."""
        if isinstance(receiver, EventReceiver):
            for _, value in self.receivers.items():
                if receiver in value:
                    receiver.nodes.remove(self)
                    value.remove(receiver)
            
                
    def get_receivers(self, evt_type) -> EventReceiver or None:
        """Returns the receivers for the specified event type, if it exists."""
        return self.receivers.get(evt_type, None)
    
    def receive_event(self, event) -> bool:
        """Checks self and all children and returns True if an event was received at any level."""
        for child in self:
            if child.receive_event(event) and not event.type in CONFIGURATION["PERMEABLE_EVENT_TYPES"]:
                return True
        if self.get_receivers(event.type) != None:
            received = False
            for receiver in self.get_receivers(event.type):
                if receiver.receive(event):
                    received = True
            if received != True and not event.type in CONFIGURATION["PERMEABLE_EVENT_TYPES"]:
                return received
        return False
    
    def draw(self):
        """Draw the Node's graphics"""
        #background_color
        self.surface.fill(self.style["background_color"])
        #border
        if self.style["border"] > 0:
            draw_rect(self.surface, self.style["border_color"],
                      [0, 0, self.width, self.height],
                      self.style["border"])
    
    def _render(self):
        """Render the node on its parent's Surface."""
        if not self.visible: return
        
        self.draw()
        
        for node in self.visible_children():
            try:
                node._render()
            except:
                self.remove(node)
                print(str(node) + " failed to render and was removed.")
                __import__("traceback").print_exc()
        if self.parent != None:
            self.parent.surface.blit(self.surface, self.position)
            
class RootNode(Node):
    """
    The Root Node is the top of the Node hierarchy. It should only be instantiated once per application.
    The focused_node property is the node with keyboard focus.
    Supported parameters:
    - Node parameters.
    """
    
    def __init__(self, **data):
        Node.__init__(self, **data)
        self._focused_node = None
        
    @property
    def focused_node(self):
        return self._focused_node
    
    @focused_node.setter
    def focused_node(self, value: "Node"):
        if self._focused_node != None:
            self._focused_node.focused = False
        self._focused_node = value
        self._on_property_changed("focused_node")
            
class Text(Node):
    """
    A Node that displays text.
    Supported parameters:
    - Node parameters.
    - text: the text to display.
    - font: the Freetype font object to display the text in. Default "regular".
    - font_size: the size of the text. Default 12.
    - line_spacing: amount of spacing between lines. Default 2.
    - restrict_width: if True, text will be wrapped to fit in the Node's width. Default False.
    - restrict_height: if True, the Node will not be resized vertically to fit the text. Default False.
    """
        
    def update(self, **data):
        Node.update(self, **data)
        self._text = data.get("text", "")
        self._font = data.get("font", CONFIGURATION["DEFAULT_FONTS"]["regular"])
        self._font_size = data.get("font_size", 12)
        self._line_spacing = data.get("line_spacing", 2)
        self._restrict_width = data.get("restrict_width", False)
        self._restrict_height = data.get("restrict_height", False)
        self._fit_text()
        
    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, value):
        self._text = str(value).replace("\r\n", "\n")
        self._fit_text()
        self._on_property_changed("text")
        
    @property
    def font(self):
        return self._font
    
    @font.setter
    def font(self, value):
        self._font = value
        self._fit_text()
        self._on_property_changed("font")
        
    @property
    def font_size(self):
        return self._font_size
    
    @font_size.setter
    def font_size(self, value: int):
        self._font_size = int(value)
        self._fit_text()
        self._on_property_changed("font_size")
        
    @property
    def line_spacing(self):
        return self._line_spacing
    
    @line_spacing.setter
    def line_spacing(self, value: int):
        self._line_spacing = int(value)
        self._calculate()
        self._on_property_changed("line_spacing")
        
    @property
    def restrict_width(self):
        return self._restrict_width
    
    @restrict_width.setter
    def restrict_width(self, value):
        self._restrict_width = value
        self._fit_text()
        self._on_property_changed("restrict_width")
        
    @property
    def restrict_height(self):
        return self._restrict_height
    
    @restrict_height.setter
    def restrict_height(self, value):
        self._restrict_height = value
        self._fit_text()
        self._on_property_changed("restrict_height")
        
    def _fit_text(self):
        lines = self._text.split("\n")
        new_lines = []
        l = 0
        for line in lines:
            words = line.split(" ")
            total_width = 0
            w = 0
            new_line = ""
            for word in words:
                word_width = self.font.get_rect(word + " ", size=self.font_size).width
                total_width += word_width
                if self.restrict_width:
                    if word_width > self.width:
                        self.text = ""
                        raise ValueError("A word does not fit in the bounds provided.")
                    if total_width > self.width:
                        new_txt = ""
                        for wrd in words[w:]:
                            new_txt += wrd + " "
                        if l == len(lines) - 1:
                            lines.append(new_txt[:-1])
                        else:
                            lines[l + 1] = new_txt + " " + lines[l + 1]
                        break
                elif w == len(words) - 1:
                    self.width = total_width
                new_line += word + " "
                w += 1
            new_lines.append(new_line[:-1])
            l += 1
        
        total_height = 0
        self._text_lines = []
        for line in new_lines:
            self._text_lines.append((line, total_height))
            total_height += self.font.get_rect(line, size=self.font_size).height + self.line_spacing
            
        if not self.restrict_height:
            self.height = total_height
        
    def draw(self):
        Node.draw(self)
        for line in self._text_lines:
            self.font.render_to(self.surface, (0, line[1]), line[0], self.style["color"], size=self.font_size)
        
    def at_position(self, position: Tuple[int] or List[int]) -> Tuple[int] or None:
        """Returns the position (row, column) of the character in the text at the specified position (x, y) in local coordinates."""
        row = 0
        for line in self._text_lines:
            if position[1] > line[1] and (row == len(self._text_lines) - 1 or position[1] < self._text_lines[row + 1][1]):
                w = 0
                txt = ""
                for column in range(len(line[0])):
                    txt += line[0][column]
                    n_w = self.font.get_rect(txt, size=self.font_size).width
                    if position[0] > w and position[0] < n_w:
                        return (row, column)
                    w = n_w
            row += 1
        return None
    
    def char_at(self, position: Tuple[int] or List[int]) -> str:
        """Returns the character at the (row, column) position"""
        return self._text_lines[position[0]][0][position[1]]
    
class SelectableText(Text):
    """
    A Node that displays text that can be selected by the user. May not work well with drag events.
    Supported parameters:
    - Text parameters.
    """
    
    def __init__(self, **data):
        Text.__init__(self, **data)
        self.clear_selection()
        
        select_receiver = DragReceiver(self._handle, self._handle)
        select_receiver.trigger_distance = 0
        self.attach_receiver(select_receiver)
        self.attach_receiver(ClickReceiver(self.clear_selection))
                
    def _handle(self, evt, *_):
        loc = self.at_position((evt.pos[0] - self.absolute_position[0], evt.pos[1] - self.absolute_position[1]))
        if loc != None:
            if not self._select_active:
                self.selection_start = loc
                self._select_active = True
            else:
                self.selection_end = loc
                if isinstance(evt, DragEvent):
                    self._select_active = False
    
    def clear_selection(self, evt=None, *_):
        if evt != None:
            if evt.button == 3:
                return
        for drag_recv in self.get_receivers(CONFIGURATION["EVENT_TYPES"]["mouse_up"]) or []:
            if isinstance(drag_recv, DragReceiver) and drag_recv.last_handled == evt:
                return
        self.selection_start = [0, 0]
        self.selection_end = [0, 0]
        self._select_active = False
        
    def selected_lines(self) -> List[str]:
        """Get the lines of the selection."""
        if self.selection_start == [0, 0] and self.selection_end == [0, 0]:
            return []
        lines = []
        start_row = min(self.selection_start[0], self.selection_end[0])
        end_row = max(self.selection_start[0], self.selection_end[0])
        start_col = self.selection_start[1] if self.selection_start[0] <= self.selection_end[0] else self.selection_end[1]
        end_col = self.selection_end[1] if self.selection_start[0] <= self.selection_end[0] else self.selection_start[1]
        row = start_row
        for row_text in [l[0] for l in self._text_lines][start_row:end_row + 1]:
            if row == start_row:
                if row == end_row:
                    lines.append(row_text[min(start_col, end_col):max(start_col, end_col) + 1])
                else:
                    lines.append(row_text[start_col:])
            elif row == end_row:
                lines.append(row_text[:end_col + 1])
            else:
                lines.append(row_text)
            row += 1
        return lines
            
            
    def get_selection(self) -> str:
        """Returns the selected text, with newlines as necessary."""
        text = ""
        for line in self.selected_lines():
            text += line + "\n"
        return text.rstrip("\n")
    
    def draw(self):
        Text.draw(self)
        if self.selection_start != [0, 0] or self.selection_end != [0, 0]:
            start_row = min(self.selection_start[0], self.selection_end[0])
            end_row = max(self.selection_start[0], self.selection_end[0])
            start_col = self.selection_start[1] if self.selection_start[0] <= self.selection_end[0] else self.selection_end[1]
            end_col = self.selection_end[1] if self.selection_start[0] <= self.selection_end[0] else self.selection_start[1]
            row = start_row
            for row_data in self._text_lines[start_row:end_row + 1]:
                rect = [0, row_data[1] + self.font.get_rect(row_data[0], size=self.font_size).height - self.line_spacing - 1,
                        0, self.line_spacing + 1]
                if row == start_row:
                    if row == end_row:
                        rect[0] = self.font.get_rect(row_data[0][:min(start_col, end_col)], size=self.font_size).width
                        rect[2] = self.font.get_rect(row_data[0][min(start_col, end_col):max(start_col, end_col) + 1], size=self.font_size).width
                    else:
                        rect[0] = self.font.get_rect(row_data[0][:start_col], size=self.font_size).width
                        rect[2] = self.font.get_rect(row_data[0][start_col:], size=self.font_size).width
                elif row == end_row:
                    rect[2] = self.font.get_rect(row_data[0][:end_col + 1], size=self.font_size).width
                else:
                    rect[2] = self.font.get_rect(row_data[0], size=self.font_size).width
                draw_rect(self.surface, self.style["selection_color"], rect)
                row += 1
                
class EditableText(SelectableText):
    """
    A Node that allows text to be edited.
    Note: A width must be provided. restrict_width is automatically set to True.
    Supported parameters:
    - SelectableText parameters.
    """
    #TODO: Work on this!
    
    def update(self, **data):
        data["restrict_width"] = True
        SelectableText.update(self, **data)
        self.attach_receiver(ClickReceiver(self._on_click))
        self.attach_receiver(KeyboardReceiver(self, self._on_key))
        self._blink = 0
        
    def _pos_to_index(self, pos):
        i = 0
        for l in range(pos[0]):
            i += len(self._text_lines[l][0])
        i += pos[1]
        return i
    
    def _index_to_pos(self, index):
        pos = [0, 0]
        i = 0
        for line in [l[0] for l in self._text_lines]:
            if i + len(line) + 1 < index:
                pos[0] += 1
                i += len(line) + 1
            else:
                pos[1] = index - i
                break
        return pos
        
    def _on_click(self, evt, *_):
        if self.focused:
            clicked = self.at_position([evt.pos[0] - self.absolute_position[0], evt.pos[1] - self.absolute_position[1]])
            if clicked != None:
                self._caret = self._pos_to_index(clicked)
        else:
            self.focused = True
            self._caret = len(self.text)
            
    def _on_key(self, evt, *_):
        if evt.type == CONFIGURATION["EVENT_TYPES"]["key_down"]:    
            if evt.key == 127:
                if self._caret < len(self.text):
                    self.text = self.text[:self._caret] + self.text[self._caret + 1:]
                return
            elif evt.key == 8:
                if self._caret > 0:
                    self.text = self.text[:self._caret - 1] + self.text[self._caret:]
                    self._caret -= 1
                return
            elif evt.key == 276:
                if evt.modifiers & (CONFIGURATION["KEY_MODIFIERS"]["left_shift"] | CONFIGURATION["KEY_MODIFIERS"]["right_shift"]):
                    if self.get_selection() == "":
                        self.selection_start = self._index_to_pos(self._caret)
                        self.selection_end = self.selection_start
                    if self.selection_end[1] > 0:
                        self.selection_end[1] -= 1
                    elif self.selection_end[0] > 0:
                        self.selection_end[0] -= 1
                        self.selection_end[1] = len(self._text_lines[self.selection_end[0]][0]) - 1
                elif self._caret > 0:
                    self._caret -= 1
            elif evt.key == 275:
                if evt.modifiers & (CONFIGURATION["KEY_MODIFIERS"]["left_shift"] | CONFIGURATION["KEY_MODIFIERS"]["right_shift"]):
                    if self.get_selection() == "":
                        self.selection_start = self._index_to_pos(self._caret)
                        self.selection_end = self.selection_start
                    if self.selection_end[1] < len(self._text_lines[self.selection_end[0]][0]) - 1:
                        self.selection_end[1] += 1
                    elif self.selection_end[0] < len(self._text_lines):
                        self.selection_end[0] += 1
                        self.selection_end[1] = 0
                elif self._caret < len(self.text):
                    self._caret += 1
            elif evt.key == 27:
                self.focused = False
            
            elif (evt.key >= 32 and evt.key <= 122) or evt.key == 13:        
                c = chr(evt.key)    
                if evt.key == 13:
                    c = "\n"       
                if evt.modifiers & CONFIGURATION["KEY_MODIFIERS"]["capitalize"]:
                    c = c.upper()
                    if (evt.key >= 48 and evt.key <= 57):
                        caps = [")", "!", "@", "#", "$", "%", "^", "&", "*", "("]
                        c = caps[evt.key - 48]
                    elif evt.key == 96:
                        c = "~"
                    elif evt.key == 45:
                        c = "_"
                    elif evt.key == 61:
                        c = "+"
                    elif evt.key == 91:
                        c = "{"
                    elif evt.key == 93:
                        c = "}"
                    elif evt.key == 92:
                        c = "|"
                    elif evt.key == 59:
                        c = ":"
                    elif evt.key == 39:
                        c = "\""
                    elif evt.key == 44:
                        c = "<"
                    elif evt.key == 46:
                        c = ">"
                    elif evt.key == 47:
                        c = "?"
                self.text = self.text[:self._caret] + c + self.text[self._caret:]
                self._caret += 1
        
    def draw(self):
        SelectableText.draw(self)
        if self.focused:
            self._blink -= 1
            if self._blink >= 0:
                pos = self._index_to_pos(self._caret)
                draw_rect(self.surface, self.style["color"],
                           [self.font.get_rect(self._text_lines[pos[0]][0][:pos[1]], size=self.font_size).width,
                            self._text_lines[pos[0]][1], 2, self.font_size])
            if self._blink == -10:
                self._blink = 10
    
class Button(Node):
    """
    A Node that displays text in a background.
    Supported parameters:
    - Node parameters.
    - text: the text to display. If this is a Text node, it overrides the font and font_size settings.
    - font: the Freetype font object to display the text in. Default "regular".
    - font_size: the size of the text. Default 12.
    - restrict_width: if True, text will be wrapped to fit in the Node's width. Default False.
    - restrict_height: if True, the Node will not be resized vertically to fit the text. Default False.
    - margin: the tuple (left, right, top, bottom) of spacing around the text node. Default (5, 5, 5, 5).
    - animate_click: whether to invert colors when clicked. Default True.
    """
    
    def __init__(self, **data):
        Node.__init__(self, **data)
        self.attach_receiver(MouseReceiver(self._invert_on_click,
                                           [CONFIGURATION["EVENT_TYPES"]["mouse_down"], CONFIGURATION["EVENT_TYPES"]["mouse_up"]]))
    
    def update(self, **data):
        Node.update(self, **data)
        self._restrict_width = data.get("restrict_width", False)
        self._restrict_height = data.get("restrict_height", False)
        self._margin = data.get("margin", (5, 5, 5, 5))
        self.animate_click = data.get("animate_click", True)
        if self.height - (self._margin[2] + self._margin[3]) < 0:
            print("Warning: Button Y margins exceed height.")
            self._margin = (self._margin[0], self._margin[1], 0, 0)
        if self.width - (self._margin[0] + self._margin[1]) < 0:
            print("Warning: Button X margins exceed width.")
            self._margin = (0, 0, self._margin[2], self._margin[3])
        if type(data.get("text", "")) == str:
            self.text = Text(**{
                "text": data.get("text", ""),
                "font": data.get("font", CONFIGURATION["DEFAULT_FONTS"]["regular"]),
                "font_size": data.get("font_size", 12),
                "style": {"color": self.style["color"]}
                })
        else:
            self.text = data.get("text")
                
    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, value):
        if type(value) == str:
            value = Text(**{
                "text": value,
                "font": self.font,
                "font_size": self.font_size
                })
        if len(self.children) > 0:
            self.clear()
        self.add(value)
        self._text = value
        self._position_text()
        self._on_property_changed("text")
        
    @property
    def margin(self):
        return self._margin
    
    @margin.setter
    def margin(self, value):
        self._margin = value
        self._position_text()
        self._on_property_changed("margin")
        
    @property
    def font(self):
        return self.text.font
    
    @font.setter
    def font(self, value):
        self.text.font = value
        self._position_text()
        self._on_property_changed("font")
        
    @property
    def font_size(self):
        return self.text.font_size
    
    @font_size.setter
    def font_size(self, value: int):
        self.text.font_size = int(value)
        self._position_text()
        self._on_property_changed("font_size")
        
    @property
    def restrict_width(self):
        return self._restrict_width
    
    @restrict_width.setter
    def restrict_width(self, value):
        self._restrict_width = value
        self._position_text()
        self._on_property_changed("restrict_width")
        
    @property
    def restrict_height(self):
        return self._restrict_height
    
    @restrict_height.setter
    def restrict_height(self, value):
        self._restrict_height = value
        self._position_text()
        self._on_property_changed("restrict_height")
                         
    def _position_text(self):
        """Position the text node within the button."""
        if self._restrict_width:
            if self.text.width > self.width - (self.margin[0] + self.margin[1]):
                self.text.restrict_width = True
                self.text.width = self.width - (self.margin[0] + self.margin[1])
            self.text.x = self.margin[0] + int(((self.width - (self.margin[0] + self.margin[1])) / 2) - (self.text.width / 2))
        else:
            self.width = self.text.width + (self.margin[0] + self.margin[1])
            self.text.x = self.margin[0]
        if self._restrict_height:
            if self.text.height > self.height - (self.margin[2] + self.margin[3]):
                self.text.restrict_width = True
                self.text.height = self.height - (self.margin[2] + self.margin[3])
            self.text.y = self.margin[2] + int(((self.height - (self.margin[2] + self.margin[3])) / 2) - (self.text.height / 2))
        else:
            self.height = self.text.height + (self.margin[2] + self.margin[3])
            self.text.y = self.margin[2]
        
    def _invert_on_click(self, *_):
        """Invert the button colors on click."""
        self.style["background_color"] = invert_color(self.style["background_color"])
        self.text.style["color"] = invert_color(self.text.style["color"])
        
class Image(Node):
    """
    A Node that displays an image.
    Supported parameters:
    - Node parameters.
    - image: the image path or Surface to display.
    - restrict_width: if True, the Node will not resize to match image width. Default True.
    - restrict_height: if True, the Node will not resize to match image height. Default True.
    - maintain_ratio: whether to maintain the aspect ratio of the original image. Default True.
    """
    
    def update(self, **data):
        Node.update(self, **data)
        self._restrict_width = data.get("restict_width", True)
        self._restrict_height = data.get("restict_height", True)
        self._maintain_ratio = data.get("maintain_ratio", True)
        self.image = data.get("image", None)
        
    @property
    def image(self):
        return self._image
    
    @image.setter
    def image(self, value):
        if type(value) == str:
            try:
                self._image = load_image(value)
            except:
                print("Warning: The image", value, "could not be loaded!")
        elif isinstance(value, Surface):
            self._image = value
        else:
            self._image = Surface((self.width, self.height), SRCALPHA)
        self._process_image()
        self._on_property_changed("image")
        
    @property
    def restrict_width(self):
        return self._restrict_width
    
    @restrict_width.setter
    def restrict_width(self, value):
        self._restrict_width = value
        self._process_image()
        self._on_property_changed("restrict_width")
        
    @property
    def restrict_height(self):
        return self._restrict_height
    
    @restrict_height.setter
    def restrict_height(self, value):
        self._restrict_height = value
        self._process_image()
        self._on_property_changed("restrict_height")
        
    @property
    def maintain_ratio(self):
        return self._maintain_ratio
    
    @maintain_ratio.setter
    def maintain_ratio(self, value):
        self._maintain_ratio = value
        self._process_image()
        self._on_property_changed("maintain_ratio")
        
    def _process_image(self):
        """Scale the image based on Node properties."""
        w = self._image.get_width()
        h = self._image.get_height()
        if self.restrict_width:
            if w > self.width:
                if self.maintain_ratio:
                    h = int(h * (self.width / w))
                w = self.width
        else:
            self.width = w
        if self.restrict_height:
            if h > self.height:
                if self.maintain_ratio:
                    w = int(w * (self.height / h))
                h = self.height
        else:
            self.height = h
        self._image = smoothscale(self._image, (w, h))
        
    def draw(self):
        Node.draw(self)
        self.surface.blit(self._image, (0, 0))
        
class Checkbox(Node):
    """
    A Node that displays a clickable square next to text.
    Supported parameters:
    - Node parameters.
    - text: the text to display. If this is a Text node, it overrides the font and font_size settings.
    - font: the Freetype font object to display the text in. Default "regular".
    - font_size: the size of the text. Default 12.
    - spacing: the distance between the box and text. Default 5.
    - checked: whether the box is checked. Default False.
    """
    
    def __init__(self, **data):
        Node.__init__(self, **data)
        self.attach_receiver(ClickReceiver(self.flip))
    
    def update(self, **data):
        Node.update(self, **data)
        self.spacing = data.get("spacing", 5)
        self.checked = data.get("checked", False)
        if type(data.get("text", "")) == str:
            self.text = Text(**{
                "text": data.get("text", ""),
                "font": data.get("font", CONFIGURATION["DEFAULT_FONTS"]["regular"]),
                "font_size": data.get("font_size", 12),
                "style": {"color": self.style["color"]}
                })
        else:
            self.text = data.get("text")
            
    def flip(self, *_):
        """Flip the check state."""
        self.checked = not self.checked
        self._on_property_changed("checked")
        
    @property
    def font(self):
        return self.text.font
    
    @font.setter
    def font(self, value):
        self.text.font = value
        self._on_property_changed("font")
        
    @property
    def font_size(self):
        return self.text.font_size
    
    @font_size.setter
    def font_size(self, value: int):
        self.text.font_size = int(value)
        self._on_property_changed("font_size")
        
    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, value):
        if type(value) == str:
            value = Text(**{
                "text": value,
                "font": self.font,
                "font_size": self.font_size
                })
        if len(self.children) > 0:
            self.clear()
        self.add(value)
        self._text = value
        self.width = self.text.width + self.font_size + self.spacing
        self.height = self.font_size
        self.text.x = self.font_size + self.spacing
        self.text.y = int((self.height / 2) - (self.text.height / 2)) + 1
        self._on_property_changed("text")
        
    def draw(self):
        Node.draw(self)
        draw_rect(self.surface, self.style["color"], [0, 0, self.font_size, self.font_size])
        if self.checked:
            draw_rect(self.surface, invert_color(self.style["color"]),
                      [int(self.font_size / 4), int(self.font_size / 4), int(self.font_size / 2), int(self.font_size / 2)])
            
            
class CircularCheckbox(Checkbox):
    """
    A Node that displays a clickable circle next to text. Analogous to RadioButton.
    Supported parameters:
    - Checkbox parameters.
    """
    
    def draw(self):
        Node.draw(self)
        draw_circle(self.surface, self.style["color"], (int(self.font_size / 2), int(self.font_size / 2)), int(self.font_size / 2))
        if self.checked:
            draw_circle(self.surface, invert_color(self.style["color"]),
                      (int(self.font_size / 2), int(self.font_size / 2)), int(self.font_size / 4))
            

class ScrollBar(Node):
    """
    A ScrollBar is used in a ScrollableContainer to indicate and control vertical and horizontal scroll.
    Supported parameters:
    - Node parameters.
    - container: the ScrollableContainer the ScrollBar is an indicator for.
    """
    
    def update(self, **data):
        Node.update(self, **data)
        self.container = data.get("container", None)
        
        self.attach_receiver(ClickReceiver(self._scroll_on_click))
    
    def draw(self):
        Node.draw(self)
        
        if self.width > self.height:
            scale = (self.container.width / self.container.content_width)
            draw_rect(self.surface, self.style["color"],
                       [int(scale * -self.container.offsets[0]), 0, int(scale * self.container.width), self.height])
        else:
            scale = (self.container.height / self.container.content_height)
            draw_rect(self.surface, self.style["color"],
                       [0, int(scale * -self.container.offsets[1]), self.width, int(scale * self.container.height)])
            
    def _scroll_on_click(self, evt, _):
        if self.width > self.height:
            dx = 0
            if evt.pos[0] > (self.width // 2) + 20:
                dx = 20
            if evt.pos[0] < (self.width // 2) - 20:
                dx = -20
            self.container.scroll(dx)
        else:
            dy = 0
            if evt.pos[1] > (self.height // 2) + 20:
                dy = 20
            if evt.pos[1] < (self.height // 2) - 20:
                dy = -20
            self.container.scroll(0, dy)

class ScrollableContainer(Node):
    """
    A ScrollableContainer is used to hold other Nodes with the ability to scroll the contents.
    Supported parameters:
    - Node parameters.
    - scrollX: one of (None (default) - No horizontal scrolling, "show" - show scrollbar, "hide" - scroll only with gesture).
    - scrollY: one of (None - No vertical scrolling, "show" - show scrollbar (default), "hide" - scroll only with gesture).
    """
    
    def update(self, **data):
        self.scrollX = data.get("scrollX", None)
        self.scrollY = data.get("scrollY", "show")
        self.offsets = [0, 0]
        
        self._scrollBarX = None
        self._scrollBarY = None
        if self.scrollX == "show":
            self._scrollBarX = ScrollBar(**{                
                "container": self
                })
        if self.scrollY == "show":
            self._scrollBarY = ScrollBar(**{
                "container": self
                })
            
        Node.update(self, **data)
        self.content_width = self.width
        self.content_height = self.height
        
        drag_receiver = DragReceiver(None, self._gesture_scroll)
        drag_receiver.trigger_distance = 0
        self.attach_receiver(drag_receiver)
        self.attach_receiver(MouseScrollReveiver(self._mouse_scroll))
        
        if self.scrollX == "show":
            self.add(self._scrollBarX)
        if self.scrollY == "show":
            self.add(self._scrollBarY)
            
    def _generate(self, w, h):
        Node._generate(self, w, h)
        if self.scrollX == "show":
            self._scrollBarX.x = 0
            self._scrollBarX.y = self.height - 10
            self._scrollBarX.width = self.width - 10
            self._scrollBarX.height = 10
        if self.scrollY == "show":
            self._scrollBarY.x = self.width - 10
            self._scrollBarY.y = 0
            self._scrollBarY.width = 10
            self._scrollBarY.height = self.height
            
    def add(self, *nodes: "Node"):
        Node.add(self, *nodes)
        
        cw = self.width
        for child in self.children:
            if child.x + child.width > cw:
                cw = child.x + child.width
        self.content_width = cw
        
        ch = self.height
        for child in self.children:
            if child.y + child.height > ch:
                ch = child.y + child.height
        self.content_height = ch
            
    def scroll(self, dx=0, dy=0):
        """Scroll the contents by the specified amount."""
        if self.offsets[0] + dx < -(self.content_width - self.width) or self.offsets[0] + dx > 0:
            dx = 0
        if self.offsets[1] + dy < -(self.content_height - self.height + 20) or self.offsets[1] + dy > 20:
            dy = 0
        self.offsets[0] += dx
        self.offsets[1] += dy
        for child in self.children:
            if child == self._scrollBarX or child == self._scrollBarY:
                continue
            if self.scrollX != None:
                child.x += dx
            if self.scrollY != None:
                child.y += dy
                
        if dy != 0 or dy != 0:
            self._on_property_changed("offsets")
                
    def _gesture_scroll(self, _, drag, __):
        self.scroll(*drag)
        
    def _mouse_scroll(self, evt, *_):
        if evt.button == 4:
            self.scroll(0, 7)
        else:
            self.scroll(0, -7)
            
class DraggableContainer(Node):
    """
    A DraggableContainer is used to let a user drag a Node around the screen.
    The "bar" property is the Node the user can drag.
    Supported parameters:
    - Node parameters.
    - target: The node to drag.
    - orientation: If "horizontal" (default), the bar is shown above the target, if "vertical" it is on the left.
    - size: The size of the bar. Default 20.
    """
    
    def update(self, **data):
        Node.update(self, **data)
        self.clear()
        if "target" not in data:
            raise AttributeError("DraggableContainer requires a target parameter.")
        self.target = data.get("target")
        self.orientation = data.get("orientation", "horizontal")
        self.bar = Node(**{
            "x": 0,
            "y": 0,
            "width": self.target.width if self.orientation == "horizontal" else data.get("size", 20),
            "height": data.get("size", 20) if self.orientation == "horizontal" else self.target.height,
            "style": { "background_color": self.style["color"] }
            })
        self.target.attach_receiver(PropertyChangeReceiver("width", self._update_size))
        self.target.attach_receiver(PropertyChangeReceiver("height", self._update_size))
        if self.orientation == "horizontal":
            self.target.position = (0, data.get("size", 20))
            self.width = self.target.width
            self.height = self.target.height + self.bar.height
        else:
            self.target.position = (data.get("size", 20), 0)
            self.width = self.target.width + self.bar.width
            self.height = self.target.height
        self.add(self.target, self.bar)
        self.attach_receiver(DragReceiver(None, self._handle_drag))
        
    def _update_size(self, *_):
        if self.orientation == "horizontal":
            self.width = self.target.width
            self.bar.width = self.width
            self.height = self.target.height + self.bar.height
        else:
            self.width = self.target.width + self.bar.width
            self.bar.height = self.width
            self.height = self.target.height
            
    def _handle_drag(self, evt, motion, *_):
        self.x += motion[0]
        self.y += motion[1]
        
class Selector(Node):
    """
    A Selector allows the user to pick items from a drop-down list.
    Supported parameters:
    - Node parameters.
    - items: A list of strings representing the selectable items.
    - value: The currently-selected item. Default "None".
    - margin: The tuple (left & right, top & bottom) of spacing around items in the list. Default (5, 5).
    - font: the Freetype font object to display the text in. Default "regular".
    - font_size: the size of the text. Default 12.
    """
    
    def update(self, **data):
        Node.update(self, **data)
        self.items = [str(i) for i in data.get("items", [])]
        self.value = data.get("value", "None")
        self.margin = data.get("margin", (5, 5))
        self._text = Text(**{
            "text": self.value,
            "font": data.get("font", CONFIGURATION["DEFAULT_FONTS"]["regular"]),
            "font_size": data.get("font_size", 12),
            "style": {
                "color": self.style["color"]
                }
            })
        self.clear()
        self.add(self._text)
        self._position_text()
        self.attach_receiver(ClickReceiver(self._generate_popup))
    
    @property
    def font(self):
        return self._text.font
    
    @font.setter
    def font(self, value):
        self._text.font = value
        self._on_property_changed("font")
        self._position_text()
        
    @property
    def font_size(self):
        return self._text.font_size
    
    @font_size.setter
    def font_size(self, value: int):
        self._text.font_size = value
        self._on_property_changed("font_size")
        self._position_text()
        
    def _on_select(self, _, n):
        self.value = n.text
        self._text.text = self.value
        self._on_property_changed("value")
        self._close_popup()
            
    def _position_text(self):
        self._text.position = (self.margin[0], int((self.height / 2) - (self._text.height / 2)))
        
    def _close_popup(self, *_):
        if self.parent != None:
            self.root_node().remove(self._bg)
        
    def _generate_popup(self, *_):
        below = self.root_node().height - self.absolute_position[1] >= self.absolute_position[1] + self.height
        ch = (self.font_size + (2 * self.margin[1])) * (len(self.items) if len(self.items) > 0 else 1)
        ht = min(ch, self.root_node().height - self.absolute_position[1]) if below else min(ch, self.absolute_position[1] + self.height)
        popup = ScrollableContainer(**{
            "x": self.absolute_position[0],
            "y": self.absolute_position[1] if below else (self.absolute_position[1] + self.height) - ht,
            "width": self.width,
            "height": ht,
            "style": {
                "background_color": (255, 255, 255),
                "border": 1,
                "border_color": (50, 50, 50)
                }
            })
        for i in range(len(self.items)):
            popup.add(Text(**{
                "text": self.items[i],
                "font": self.font,
                "font_size": self.font_size,
                "x": self.margin[0],
                "y": (i * (self.font_size + (2 * self.margin[1]))) + self.margin[1],
                "width": self.width - (2 * self.margin[0]),
                "restrict_width": True,
                "receivers": [ClickReceiver(self._on_select)]
                }))
        self._bg = Node(**{
            "x": 0,
            "y": 0,
            "width": self.root_node().width,
            "height": self.root_node().height,
            "receivers": [ClickReceiver(self._close_popup)]
            })
        if self.parent != None:
            self._bg.add(popup)
            self.root_node().add(self._bg)
            
    def draw(self):
        Node.draw(self)
        draw_polygon(self.surface, self.style["color"],
                      [(self.width - self.font_size - 10, int((self.height / 2) - (0.433 * self.font_size))),
                       (int(self.width - (self.font_size / 2) - 10), int((self.height / 2) + (0.433 * self.font_size))),
                       (self.width - 10, int((self.height / 2) - (0.433 * self.font_size)))])
        
