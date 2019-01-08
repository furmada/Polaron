from ui.config import CONFIGURATION
from inspect import isclass

def invert_color(color, max_value=255):
    """Invert a RGB(a) color."""
    color = list(color)
    for b in range(3):
        color[b] = max_value - color[b]
    return tuple(color)

class Style(object):
    def __init__(self, **data):
        """Styling data for a Node."""
        self.data = data
        
    def get(self, attribute: str, default=None):
        """Get the value of a styling attribute."""
        return self.data.get(attribute, default)
    
    def set(self, attribute: str, value):
        """Set the value of a styling attribute."""
        self.data[attribute] = value
        
    def __getitem__(self, attr):
        return self.get(attr)
    
    def __setitem__(self, attr, value):
        self.set(attr, value)
        
    def __str__(self):
        return "Stylesheet: " + str(self.data)
    
    def __iter__(self):
        return iter(self.data.keys())
        
    @staticmethod
    def parse_style(value) -> "Style" or None:
        """Convert dicts to Style objects."""
        if isinstance(value, Style):
            return value
        if type(value) == dict:
            return Style(**value)
        return None
    
    @staticmethod
    def merge_styles(original: "Style", modifications: "Style") -> "Style":
        """Merge the modified stylesheet onto the old one."""
        for prop, value in modifications.data.items():
            original[prop] = value
        return original
    
    @staticmethod
    def apply(style: "Style", node):
        """Apply the styling values to a Node."""
        getval = lambda prop: style.data.get(prop, CONFIGURATION["STYLE_DEFAULTS"].get(prop, None))
        for prop in style:
            value = getval(prop)
            if value != None:
                node.style[prop] = value
        
class StyleSheet(object):
    def __init__(self, **rules):
        """
        A StyleSheet is used to programatically ascribe properties to Nodes.
        It contains entries of the format filter: { attributes }.
        Rules can be entries matching tuples of names, Classes, or custom lambdas.
        Lambdas will be passed the components and the rule will be applied if they return True.
        Attributes from the dict will be applied directly to the Node if the Node has the property,
        otherwise they will be added to the Node's Style.
        """
        self.rules = rules
        
    def add_rule(self, rule, attrs):
        self.rules[rule] = attrs
        
    def remove_rule(self, rule):
        if rule in self.rules:
            del self.rules[rule]
            
    def get_attributes(self, rule, default={}):
        return self.rules.get(rule, default)
    
    def __setitem__(self, key, value):
        self.add_rule(key, value)
        
    def __getitem__(self, key):
        return self.get_attributes(key)
    
    def apply(self, node):
        """Apply the stylesheet to the Node and its children."""
        for rule, attrs in self.rules.items():
            apply = False
            if type(rule) != list:
                try:
                    if type(rule) != str:
                        rule = list(rule)
                    else:
                        rule = [rule]
                except TypeError:
                    rule = [rule]
            for entry in rule:
                if entry == node.name:
                    apply = True
                    break
                if isclass(entry) and isinstance(node, entry):
                    apply = True
                    break
                if callable(entry) and entry(node) == True:
                    apply = True
                    break
            if apply:
                for attr, value in attrs.items():
                    if hasattr(node, attr):
                        setattr(node, attr, value)
                    else:
                        node.style[attr] = value
        for child in node.children:
            self.apply(child)
                
        