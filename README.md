# Polaron
A Python 3 cross platform API for building event-driven Pygame apps.

### Overview
Change the Python coding paradigm with Polaron, the newest way to create event-driven user interfaces in Python and Pygame. Pygame is a powerful and useful graphics library, but on its own is not well suited to building user interfaces. Polaron bridges this gap and provides utilities for creating apps based on a node hierarchy and event inputs.

### Get Started
Try out Polaron with a simple demo! Download the library and then run the `test.py` file. Note that Polaron requires Python 3 and Pygame.


## Documentation
A quick overview of the features and components of Polaron.

### Polaron Modules
The base Polaron library contains several modules. Each can be used individually or together with the others.

* `ui`: Used to create and display graphical interfaces for Polaron apps. It is further subdivided into the following:
  * `ui.actions`: The event binding framework.
  * `ui.components`: Graphical building blocks (buttons, text nodes, and more).
    * `ui.components.style`: Tools for manipulating the appearance of Nodes.
  * `ui.threaded`: Tools for running Polaron apps in parallel processes.
  * `ui.config`: Default values and constants used by the rest of the UI.
  * The `ui/resources` folder, which holds non-code resources used by the UI (such as fonts).
  
* `app`: Keeps track of, installs, removes, and provides information about Polaron applications.
  * Subfolders of `app` are the actual installed apps themselves.
  
### The Event System
Polaron uses a sophisticated system for tracking and dispatching events different from the one provided by Pygame.

---

*Example*: Say you want to track when a button is clicked. Let's say that you want to call the method `display_info` when it is clicked.
First, set up your Button:
```python
from ui.components import Button
...
btn = Button(**{
                "x": 20,
                "y": 50,
                "text": "Display Information"
                })
```
Assuming you have already initialized an `Application` object and called it `app` (as done in the `test.py` file), you can now add the button to the screen.
```python
app.display.root.add(btn)
```
Finally, to trigger an action on click, use a `ClickReceiver`.
```python
from ui.actions import ClickReceiver
...
btn.attach_receiver(ClickReceiver(display_info))
```
When the button is clicked, `display_info` will be called with two arguments `(evt, node)`, respectively the Pygame Event and the node (in this case, `btn`) that was clicked by the user. This is useful, as the same `Receiver` can optionally be used to monitor several different Nodes.

---

The Polaron event system also extends upon the Pygame event specification by providing ways to handle user mouse drag events and node attribute changes using `DragReceiver` and `PropertyChangeReceiver` objects.


### Multi-Modal Applications
Polaron apps work in two distinct settings. A Python program using Polaron can be run stand-alone, or it can be invoked from inside an already-running Polaron app. There is no difference in code required to adapt to this change.

An example of running a Polaron app nesting is found in the `test_wm.py` file, which runs the `test.py` application inside a draggable window.

The `ui.threading` module provides tools for nesting apps. Most notably, the `start_app` method is used to run the nested app in a subprocess, and the `ThreadedDisplay` node is used to display the nested app's UI as a Node within the parent app while appropriately forwarding events. An app can check whether it is being run as a nested app by invoking the `is_threaded` method.
