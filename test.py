from ui import Application, Display
from ui.components import Text

app = Application(Display(640, 480))

txt = Text(**{
    "text": "Hello World\n\nWelcome to Polaron!",
    "x": 20,
    "y": 20,
    "width": 400,
    "height": 300,
    "style": { "color": (255, 255, 255) }
    })

app.display.root.style["background_color"] = (50, 50, 50)
app.display.root.add(txt)

app.launch()
