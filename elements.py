import urllib
from StringIO import StringIO
from inspect import isclass
from uuid import uuid4 as uuid

class BalsamiqElement(object):
    """Base class for all Balsamiq elements."""
    _subclass_map = {}

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
        self.tag = kwargs.get('tag', self.__class__.__name__)
        self.controlID = kwargs.get('controlID', uuid())
        self.has_floats = False
        self.flow = True
        self.children = kwargs.get('children', [])
        self.position_rules = []

    def __repr__(self):
        return '<BalsamiqElement instace of type "{tag}" with {children} children.>'.format(
                                                                            tag=self.tag,
                                                                            children=len(self.children)
                                                                            )

    @property
    def html(self):
        html_str = '<{tag} id="{id}">{children}</{tag}>'.format(
            tag=self.tag,
            id=self.controlID,
            children=self.children_html,
            )
        return html_str

    @property
    def children_html(self):
        return ''.join([elem.html for elem in self.children])

    @property
    def unescaped_text(self):
        return urllib.unquote(self.text)

    def sort(self, *args, **kwargs):
        self.children.sort(*args, **kwargs)
        for child_element in self.children:
            child_element.sort(*args, **kwargs)
    @staticmethod
    def new(tag="div"):
        return BalsamiqElement._subclass_map.get(tag, BalsamiqElement)(tag=tag)


class Root(BalsamiqElement):
    """Special BalsamiqElement subclass for the root object."""
    title = "TASTAST"

    @property
    def html(self):
        html_str = """
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
<meta name="generator" content="Balsamatron 0.1.0"/>
<meta name="author" content="Russell Mayhew"/>
<title>{title}</title>
<link rel="stylesheet" type="text/css" href="style/default.css"/>
</head>
<body>
<div id="main">
{children}
</div>
</body>
</html>
""".replace('\n', '').format(
            title=self.title,
            children=self.children_html
            )
        return html_str


class Title(BalsamiqElement):
    """BalsamiqElement subclass for Title objects."""
    @property
    def html(self):
        html_str = '<h1 id="{id}">{text}</h1>'.format(
            id=self.controlID,
            text=self.text,
            )
        return html_str

class Canvas(BalsamiqElement):
    """BalsamiqElement subclass for Canvas objects."""
    @property
    def html(self):
        html_str = '<{tag} id="{id}">{children}</{tag}>'.format(
            tag='div',
            id=self.controlID,
            children=self.children_html,
            )
        return html_str

class Image(BalsamiqElement):
    """BalsamiqElement subclass for Image objects."""
    def __init__(self, **kwargs):
        super(Image, self).__init__(**kwargs)
        self.src = "image/image_not_found.png"
    @property
    def html(self):
        html_str = '<{tag} id="{id}" width="{width}" height="{height}" src="{src}">{children}</{tag}>'.format(
            tag='img',
            id=self.controlID,
            width=self.width,
            height=self.height,
            src=self.src,
            children=self.children_html,
            )
        return html_str

class TabBar(BalsamiqElement):
    """BalsamiqElement subclass for TabBar objects."""
    def __init__(self, **kwargs):
        super(TabBar, self).__init__(**kwargs)
        self.position = "top"
    @property
    def tabs(self):
        tabs = []
        for i, tab_text in enumerate(self.unescaped_text.split(", ")):
            if i == self.selectedIndex:
                class_str = "tab selected"
            else:
                class_str = "tab"
            tabs.append('<li class="{class_str}">{tab_text}</li>'.format(
                class_str=class_str,
                tab_text=tab_text
                ))
        return tabs
    @property
    def html(self):
        tabs_str = '<ul class="tab_container {position}">{tabs}<li class="tab clear"/></ul>'.format(
            id=self.controlID,
            position=self.position,
            tabs=''.join(self.tabs),
            )
        container_str = '<div class="tabbed">{children}</div>'.format(
            id=self.controlID,
            children=self.children_html,
            )
        tabs_and_container = tabs_str + container_str if self.position == "top" else container_str + tabs_str
        html_str = '<div id="{id}">{children}</div>'.format(
            id=self.controlID,
            children=tabs_and_container,
            )
        return html_str

class VerticalTabBar(BalsamiqElement):
    """BalsamiqElement subclass for VerticalTabBar objects."""
    def __init__(self, **kwargs):
        super(VerticalTabBar, self).__init__(**kwargs)
        self.position = "left"
    @property
    def tabs(self):
        tabs = []
        for i, tab_text in enumerate(self.unescaped_text.split("\n")):
            if i == self.selectedIndex:
                class_str = "tab selected"
            else:
                class_str = "tab"
            tabs.append('<li class="{class_str}">{tab_text}</li>'.format(
                class_str=class_str,
                tab_text=tab_text.strip()
                ))
        return tabs
    @property
    def html(self):
        container_str = '<div class="vert_tabbed {position}">{children}</div>'.format(
            id=self.controlID,
            position=self.position,
            children=self.children_html,
            )
        tabs_str = '<ul class="vert_tab_container {position}">{tabs}</ul>'.format(
            id=self.controlID,
            position=self.position,
            tabs=''.join(self.tabs),
            )
        html_str = '<div id="{id}">{children}<div class="clear"/></div>'.format(
            id=self.controlID,
            children=container_str + tabs_str,
            )
        return html_str

class Button(BalsamiqElement):
    @property
    def html(self):
        html_str = '<div id="{id}"><input name="{text}" type="button" value="{text}"/></div>'.format(
            id=self.controlID,
            text=self.text,
            )
        return html_str

class CheckBox(BalsamiqElement):
    @property
    def html(self):
        html_str = '<div id="{id}"><label><input type="checkbox" name="{name}" value="{value}"{checked}{disabled}/> {value}</label></div>'.format(
            id=self.controlID,
            name=self.name if hasattr(self, 'name') else self.controlID,
            value=self.text,
            checked=' checked=""' if 'selected' in self.state.lower() else '',
            disabled=' disabled=""' if 'disabled' in self.state.lower() else '',
            )
        return html_str

class RadioButton(BalsamiqElement):
    @property
    def html(self):
        html_str = '<div id="{id}"><label><input type="radio" name="{name}" value="{value}"{checked}{disabled}/> {value}</label></div>'.format(
            id=self.controlID,
            name=self.name if hasattr(self, 'name') else self.controlID,
            value=self.text,
            checked=' checked=""' if 'selected' in self.state.lower() else '',
            disabled=' disabled=""' if 'disabled' in self.state.lower() else '',
            )
        return html_str

class ComboBox(BalsamiqElement):
    @property
    def options(self):
        options = []
        for i, option_name in enumerate(self.unescaped_text.split('\n')):
            options.append('<option name="{name}"{selected}></option>'.format(
                name=option_name,
                selected=' selected=""' if i == 0 else '',
                ))
        return options

    @property
    def html(self):
        html_str = '<div id="{id}"><label><select name="{id}"{disabled}>{children}</select></label></div>'.format(
            id=self.controlID,
            text=self.text,
            disabled=' disabled=""' if 'disabled' in self.state.lower() else '',
            children=''.join(self.options),
            )
        return html_str

class RadioButtonGroup(BalsamiqElement):
    def __init__(self, **kwargs):
        super(RadioButtonGroup, self).__init__(**kwargs)
        self.text_parsed = False

    def parse_text(self):
        state = StringIO()
        for row in self.unescaped_text.split('\n'):
            if row[0] == row[-1] == '-':
                radio = True
                state.write('disabled')
                row = row[1:-1]
            if '(o)' in row[0:3]:
                radio = True
                state.write('selected')
                row = row[3:]
            elif '()' in row[0:2]:
                radio = True
                row = row[2:]
            else:
                radio = False
            if radio:
                element = RadioButton()
                element.state = state.getvalue()
                element.name = self.controlID
            else:
                element = Label()
                element.for_ = self.controlID
            element.text = row.strip()
            self.children.append(element)

        self.text_parsed = True

    @property
    def html(self):
        if not self.text_parsed:
            self.parse_text()

        html_str = '<div id="{id}">{children}</div>'.format(
            id=self.controlID,
            children=self.children_html,
            )

        return html_str

class CheckBoxGroup(BalsamiqElement):
    pass

class TextInput(BalsamiqElement):
    pass

class TextArea(BalsamiqElement):
    pass

class Link(BalsamiqElement):
    pass

class Label(BalsamiqElement):
    pass

class Paragraph(BalsamiqElement):
    pass


for key, value in locals().copy().iteritems():
    if isclass(value) and issubclass(value, BalsamiqElement):
        BalsamiqElement._subclass_map[key] = value
