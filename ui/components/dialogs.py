from ui.components import Node, DraggableContainer, Button, Text
from ui.actions import ClickReceiver
from ui.config import CONFIGURATION

class Dialog(Node):
    """
    A Dialog is a Node that displays content as well as a sequence of buttons for the user to select.
    When the user makes a choice, the on_select property is called and passed the chosen option.
    The Dialog node should be added to the area of the screen it is to be centered in.
    If the x and y coordinates of the content node are not zero, padding is created around the node.
    Supported parameters:
    - Node parameters.
    - cancelable: Whether the user can tap outside of the Node to close it. Default True.
    - options: The buttons to display. Default ["OK"].
    - content: The content to show.
    - button_height: The size of the buttons to show. Default 40.
    - on_select: The method to call when a selection is made. Default None.
    
    In addition, the following styling parameters are supported:
    - header_color: The color for the draggable area of the dialog. Default (200, 200, 200).
    - dialog_color: The color of the background pane of the dialog. Default (255, 255, 255).
    - button_color: The background color of the buttons. Default (50, 50, 50).
    - button_text_color: The font color of the buttons. Default (255, 255, 255).
    """
    
    def update(self, **data):
        Node.update(self, **data)
        self.cancelable = data.get("cancelable", True)
        self._options = data.get("options", ["OK"])
        if "content" not in data:
            raise ValueError("The 'content' parameter is required.")
        self._content = data.get("content")
        self.button_height = data.get("button_height", 40)
        self.on_select = data.get("on_select", None)
        
    @property
    def options(self):
        return self._options
    
    @options.setter
    def options(self, value):
        if value != self._options:
            self._options = value
            self._on_property_changed("options")
            
    @property
    def content(self):
        return self._content
    
    @content.setter
    def content(self, value):
        if value != self._content:
            self._content = value
            self._on_property_changed("content")
            
    def _handle_cancel(self, e, *_):
        if self.cancelable and not self._dialog.get_receivers(CONFIGURATION["EVENT_TYPES"]["mouse_up"])[0].check(e):
            self.hide()
            
    def _handle_select(self, _, btn):
        self.hide()
        if self.on_select != None:
            self.on_select(btn.text.text)
            
    def show(self):
        """Show the dialog."""
        if self.parent == None:
            print("Add the dialog to a Node before showing it.")
            return
        self._dialog_root = Node(**{
            "x": 0,
            "y": 0,
            "width": self.parent.width,
            "height": self.parent.height
            })
        self._dialog_root.attach_receiver(ClickReceiver(self._handle_cancel))
        pane = Node(**{
            "x": 0,
            "y": 0,
            "width": self._content.width + (2 * self._content.x),
            "height": self._content.height + (2 * self._content.y) + self.button_height,
            "style": {
                "background_color": self.style.get("dialog_color", (255, 255, 255))
                }
            })
        pane.add(self._content)
        pane.add(*[Button(**{
            "x": int(i * (pane.width / len(self.options))),
            "y": self._content.height + (2 * self.content.y),
            "width": int(pane.width / len(self.options)),
            "restrict_width": True,
            "height": self.button_height,
            "restrict_height": True,
            "text": self.options[i],
            "receivers": [ClickReceiver(self._handle_select)],
            "style": {
                "background_color": self.style.get("button_color", (50, 50, 50)),
                "color": self.style.get("button_text_color", (255, 255, 255)),
                "border": 1,
                "border_color": self.style.get("button_text_color", (255, 255, 255))
                }
            }) for i in range(len(self.options))])
        self._dialog = DraggableContainer(**{
            "target": pane,
            "orientation": "vertical",
            "style": {
                "color": self.style.get("header_color", (200, 200, 200))
                }
            })
        self._dialog.position = (int((self.parent.width / 2) - (self._dialog.width / 2)),
                           int((self.parent.height / 2) - (self._dialog.height / 2)))
        self.parent.add(self._dialog_root, self._dialog)
        
    def hide(self):
        """Hide the dialog."""
        if hasattr(self, "_dialog_root"):
            self.parent.remove(self._dialog_root, self._dialog)
            
class TextDialog(Dialog):
    """
    A TextDialog is a dialog that displays text as well as a list of clickable buttons.
    Supported parameters:
    - Dialog parameters (Note that "content" is ignored if provided).
    - text: The string to display. Default ""
    - text_width: The width of the text area. Default parent.width / 4.
    
    Style options:
    - text_color: The color of the text to display. Default (0, 0, 0).
    """ 
            
    def update(self, **data):
        data["content"] = None
        Dialog.update(self, **data)
        self._text = data.get("text", "")
        self._text_width = data.get("text_width", 0)
        
    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, value):
        if value != self._text:
            self._text = value
            self._on_property_changed("text")
            
    def show(self):
        if self.parent == None:
            print("Add the dialog to a Node before showing it.")
            return
        self._content = Text(**{
            "x": 20,
            "y": 20,
            "width": self._text_width if self._text_width != 0 else int(self.parent.width / 4),
            "restrict_width": True,
            "text": self.text,
            "style": {
                "color": self.style.get("text_color", (0, 0, 0))
                }
            })
        Dialog.show(self)