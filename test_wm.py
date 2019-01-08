from ui import Application, Display
from ui.threaded import ThreadedDisplay, start_app
from ui.components import DraggableContainer

app = Application(Display(800, 600))

td = ThreadedDisplay(*start_app("test.py"))

td.focused = True

win = DraggableContainer(**{
    "target": td,
    "orientation": "vertical",
    "x": 50,
    "y": 50,
    "style": { "color": (200, 200, 200) }
    })

app.display.root.style["background_color"] = (255, 255, 255)
app.display.root.add(win)

app.launch()
