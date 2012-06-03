import re
from cStringIO import StringIO
from inspect import isclass
from uuid import uuid4 as uuid
from functools import total_ordering

from util import REst_repl, REst_filter, unquote_all

@total_ordering
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

    # Comparers
    def __eq__(self, other):
        return False

    def __lt__(self, other):
        if self.y1 < other.y:
            return True
        elif self.size > other.size:
            return True
        return False

    @property
    def size(self):
        return self.width * self.height

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
        return ''.join([elem if isinstance(elem, basestring) else elem.html for elem in self.children])

    @property
    @staticmethod
    def default_css():
        """This property should be overridden by subclasses and return a (non-pretty) string """
        return None

    @property
    def unescaped_text(self):
        text = getattr(self, 'text', '')
        return unquote_all(text) if isinstance(text, basestring) else text

    @property
    def REst_repl_text(self):
        return re.sub('_(.+?)_|\[(.+?)\]|(?<=\s)\*(.+?)\*', REst_repl, self.unescaped_text)

    def sort(self, *args, **kwargs):
        self.children.sort(*args, **kwargs)
        for child_element in self.children:
            child_element.sort(*args, **kwargs)

    @staticmethod
    def new(tag="div", **kwargs):
        return BalsamiqElement._subclass_map.get(tag, BalsamiqElement)(tag=tag, **kwargs)


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
<link rel="stylesheet" type="text/css" href="style/custom.css"/>
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
            text=self.unescaped_text,
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
        for i, tab_text in enumerate(re.split(r'(?<=[^\\]),', self.unescaped_text)):
            if i == self.selectedIndex:
                class_str = "tab selected"
            else:
                class_str = "tab"
            tabs.append('<li class="{class_str}">{tab_text}</li>'.format(
                class_str=class_str,
                tab_text=REst_filter(tab_text.strip())
                ))
        return tabs
    @property
    def html(self):
        tabs_str = '<ul class="tab_container {position}">{tabs}</ul>'.format(
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
                tab_text=REst_filter(tab_text.strip())
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
            text=self.unescaped_text,
            )
        return html_str

class CheckBox(BalsamiqElement):
    def __init__(self, **kwargs):
        super(CheckBox, self).__init__(**kwargs)
        self.state = ""

    @property
    def html(self):
        html_str = '<div id="{id}"><label><input type="checkbox" name="{name}" value="{value}"{checked}{disabled}/> {display_val}</label></div>'.format(
            id=self.controlID,
            name=self.name if hasattr(self, 'name') else self.controlID,
            display_val=self.display_val if hasattr(self, 'display_val') else self.REst_repl_text,
            value=self.unescaped_text,
            checked=' checked=""' if 'selected' in self.state.lower() else '',
            disabled=' disabled=""' if 'disabled' in self.state.lower() else '',
            )
        return html_str

class RadioButton(BalsamiqElement):
    def __init__(self, **kwargs):
        super(RadioButton, self).__init__(**kwargs)
        self.state = ""

    @property
    def html(self):
        html_str = '<div id="{id}"><label><input type="radio" name="{name}" value="{value}"{checked}{disabled}/> {display_val}</label></div>'.format(
            id=self.controlID,
            name=self.name if hasattr(self, 'name') else self.controlID,
            display_val=self.display_val if hasattr(self, 'display_val') else self.REst_repl_text,
            value=self.unescaped_text,
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
                name=REst_filter(option_name),
                selected=' selected=""' if i == 0 else '',
                ))
        return options

    @property
    def html(self):
        html_str = '<div id="{id}"><label><select name="{id}"{disabled}>{children}</select></label></div>'.format(
            id=self.controlID,
            disabled=' disabled=""' if 'disabled' in getattr(self, 'state', '').lower() else '',
            children=''.join(self.options),
            )
        return html_str

class RadioButtonGroup(BalsamiqElement):
    def __init__(self, **kwargs):
        super(RadioButtonGroup, self).__init__(**kwargs)
        self.text_parsed = False

    def parse_text(self):
        for row in self.unescaped_text.split('\n'):
            state = StringIO()
            if row[0] == row[-1] == '-':
                radio = True
                state.write('disabled')
                row = row[1:-1]
            if '(o)' in row[0:3]:
                radio = True
                state.write('selected')
                row = row[3:]
            elif '(' and ')' in row[0:3]:
                radio = True
                row = row.replace('(', '', 1).replace(')', '', 1)
            else:
                radio = False
            if radio:
                element = RadioButton()
                element.state = state.getvalue()
                element.name = self.controlID
            else:
                element = Label()
                element.for_ = self.controlID
            element.text = REst_filter(row).strip()
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
    def __init__(self, **kwargs):
        super(CheckBoxGroup, self).__init__(**kwargs)
        self.text_parsed = False

    def parse_text(self):
        for row in self.unescaped_text.split('\n'):
            state = StringIO()
            if row[0] == row[-1] == '-':
                checkbox = True
                state.write('disabled')
                row = row[1:-1]
            if '[x]' in row[0:3]:
                checkbox = True
                state.write('selected')
                row = row[3:]
            elif '[' and ']' in row[0:3]:
                checkbox = True
                row = row.replace('[', '', 1).replace(']', '', 1)
            else:
                checkbox = False
            if checkbox:
                element = CheckBox()
                element.state = state.getvalue()
                element.name = self.controlID
            else:
                element = Label()
                element.for_ = self.controlID
            element.text = REst_filter(row).strip()
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

class TextInput(BalsamiqElement):
    @property
    def html(self):
        html_str = '<input type="text" id="{id}" name="{id}" placeholder="{text}"{disabled} />'.format(
            id=self.controlID,
            disabled=' disabled=""' if 'disabled' in getattr(self, 'state', '').lower() else '',
            text=self.unescaped_text,
            )

        return html_str

class TextArea(BalsamiqElement):
    @property
    def html(self):
        html_str = '<textarea id="{id}" name="{id}" placeholder="{text}"{disabled}>\r</textarea>'.format(
            id=self.controlID,
            disabled=' disabled=""' if 'disabled' in getattr(self, 'state', '').lower() else '',
            text=self.unescaped_text,
            )

        return html_str

class Link(BalsamiqElement):
    @property
    def html(self):
        html_str = '<a id="{id}" href="{href}">{text}</a>'.format(
            id=self.controlID,
            href=getattr(self, 'href', '#'),
            text=self.REst_repl_text,
            )

        return html_str

class Label(BalsamiqElement):
    @property
    def html(self):
        html_str = '<label id="{id}"{for_}>{text}</label>'.format(
            id=self.controlID,
            for_= ' for="{0}"'.format(self.for_) if hasattr(self, 'for_') else '',
            text=self.REst_repl_text,
            )

        return html_str

class Paragraph(BalsamiqElement):
    @property
    def html(self):
        html_str = '<p id="{id}">{text}</p>'.format(
            id=self.controlID,
            # Do some _asdf_ *dalsfj* replacement here
            text=self.REst_repl_text,
            )

        return html_str



class DateChooser(BalsamiqElement):
    @property
    def html(self):
        html_str = '<input type="date" id="{id}" name="{id}" placeholder="{text}"{disabled} />'.format(
            id=self.controlID,
            disabled=' disabled=""' if 'disabled' in getattr(self, 'state', '').lower() else '',
            text=self.unescaped_text,
            )

        return html_str

class HRule(BalsamiqElement):
    @property
    def html(self):
        return '<hr/>'

class NumericStepper(BalsamiqElement):
    @property
    def html(self):
        html_str = '<input type="number" id="{id}" name="{id}" placeholder="{text}"{disabled} />'.format(
            id=self.controlID,
            disabled=' disabled=""' if 'disabled' in getattr(self, 'state', '').lower() else '',
            text=self.unescaped_text,
            )

        return html_str

class NavElement(BalsamiqElement):
    def __init__(self, **kwargs):
        super(NavElement, self).__init__(**kwargs)
        self.text_parsed = False

    def parse_text(self, sep):
        for i, elem_text in enumerate(re.split(r'(?<=[^\\]),', self.unescaped_text)):
            elem_text = elem_text.strip()
            if i != 0:
                self.children.append(sep)

            if i == getattr(self, 'selectedIndex', -1):
                self.children.append('<div>{0}</div>'.format(elem_text))
            else:
                self.children.append('<a href="#"><div>{0}</div></a>'.format(elem_text))

    @property
    def html(self):
        if not self.text_parsed:
            self.parse_text()

        html_str = '<div id="{id}" class="nav_element">{children}</div>'.format(
            id=self.controlID,
            children=self.children_html
            )
        return html_str

class BreadCrumbs(NavElement):
    @property
    def html(self):
        if not self.text_parsed:
            self.selectedIndex = len(re.split(r'(?<=[^\\]),', self.unescaped_text)) - 1
            self.parse_text('&gt;')

        html_str = '<div id="{id}" class="breadcrumbs">{children}</div>'.format(
            id=self.controlID,
            children=self.children_html
            )
        return html_str

class LinkBar(NavElement):
    @property
    def html(self):
        if not self.text_parsed:
            self.parse_text('|')

        html_str = '<div id="{id}" class="link_bar">{children}</div>'.format(
            id=self.controlID,
            children=self.children_html
            )
        return html_str

class ButtonBar(NavElement):
    @property
    def html(self):
        if not self.text_parsed:
            self.parse_text('')

        html_str = '<div id="{id}" class="button_bar">{children}</div>'.format(
            id=self.controlID,
            children=self.children_html
            )
        return html_str

class DataGrid(BalsamiqElement):
    def __init__(self, **kwargs):
        super(DataGrid, self).__init__(**kwargs)
        self.text_parsed = False

    @property
    def children_html(self):
        return ''.join(self.raw_children)

    def parse_text(self):
        header_names = []
        self.raw_children = []
        rows = self.unescaped_text.split('\n')
        for row_index, row in enumerate(rows):
            if row_index == len(rows) - 1 and row.startswith('{') and row.endswith('}'):
                continue
            self.raw_children.append('<tr>')
            split_row = re.split(r'(?<=[^\\]),', row)
            for cell_index, cell in enumerate(split_row):
                cell = cell.strip()

                split_cell = cell.split(' ')

                if row_index == 0:
                    cell_tag = 'th'
                    if len(split_cell) > 1 and split_cell[-1].strip('^v') == '':
                        del split_cell[-1]
                        sortable = True
                    else:
                        sortable = False
                    header_names.append(split_cell[0])
                else:
                    cell_tag = 'td'

                    if cell in ('[]', '[ ]', '[x]'):
                        elem = CheckBox()
                        elem.name = header_names[cell_index]
                        elem.text = split_row[0].split(r'\r ')[0]
                        elem.display_val = ''
                        if cell == '[x]':
                            elem.state = "selected"
                        self.raw_children.extend(['<td>', elem.html, '</td>'])
                        continue
                    elif cell in ('()', '( )', '(o)'):
                        elem = RadioButton()
                        elem.name = header_names[cell_index]
                        elem.text = split_row[0].split(r'\r ')[0]
                        elem.display_val = ''
                        if cell == '(o)':
                            elem.state = "selected"
                        self.raw_children.append(['<td>', elem.html, '</td>'])
                        continue


                cell = ' '.join([x.strip() for x in split_cell if x])

                self.raw_children.append('<{0}>'.format(cell_tag))

                cell_lines = REst_filter(cell).split(r'\r')
                if len(cell_lines) > 1:
                    for cell_line in cell_lines:
                        self.raw_children.append('<span>{text}</span>'.format(text=cell_line))
                else:
                    self.raw_children.append(cell_lines[0])
                
                self.raw_children.append('</{0}>'.format(cell_tag))
            self.raw_children.append('</tr>')
        self.text_parsed = True

    @property
    def html(self):
        if not self.text_parsed:
            self.parse_text()

        html_str = '<table id="{id}">{children}</table>'.format(
            id=self.controlID,
            children=self.children_html
            )
        return html_str

class SearchBox(TextInput):
    def __init__(self, **kwargs):
        super(SearchBox, self).__init__(**kwargs)
        self.text = "search"
    @property
    def html(self):
        html_str = '<input type="search" id="{id}" name="{id}" placeholder="{text}"{disabled} />'.format(
            id=self.controlID,
            disabled=' disabled=""' if 'disabled' in getattr(self, 'state', '').lower() else '',
            text=self.unescaped_text,
            )

        return html_str

class MultilineButton(BalsamiqElement):
    @property
    def html(self):
        html_str = '<a href="#"><div class="MultilineButton">{children}</div></a>'.format(
            children=''.join('<span>{0}</span>'.format(x) for x in self.REst_repl_text.split('\n'))
            )
        return html_str

class ProgressBar(BalsamiqElement):
    def __init__(self, **kwargs):
        super(ProgressBar, self).__init__(**kwargs)
        self.scrollBarValue = 50
    @property
    def html(self):
        html_str = '<progress value="{value}" max="100">{value}%</progress>'.format(
            value=self.scrollBarValue,
            )
        return html_str



for key, value in locals().copy().iteritems():
    if isclass(value) and issubclass(value, BalsamiqElement):
        BalsamiqElement._subclass_map[key] = value
