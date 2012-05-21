class BalsamiqElement(object):
    """Base class for all Balsamiq elements."""
    def __init__(self, **kwargs):
        self.tag = kwargs.get('tag', 'div')
        self.controlID = kwargs.get('controlID', uuid())
        self.has_floats = False
        self.flow = True
        self.children = []
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
    def _sort(self, *args, **kwargs):
        self.children.sort(*args, **kwargs)
        for child_element in self.children:
            child_element._sort(*args, **kwargs)
    @staticmethod
    def new(tag="div"):
        return BalsamiqElement._subclass_map.get(tag, BalsamiqElement)(tag=tag)

class Root(BalsamiqElement):
    """Special BalsamiqElement subclass for the root object."""
    title = "TASTAST"
    def __init__(self, children=None):
        super(Root, self).__init__(tag='html')
        if children != None:
            self.children = children
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
    def __init__(self, **kwargs):
        super(Title, self).__init__(**kwargs)
    @property
    def html(self):
        html_str = '<h1 id="{id}">{text}</h1>'.format(
            id=self.controlID,
            text=self.text,
            )
        return html_str

class Canvas(BalsamiqElement):
    """BalsamiqElement subclass for Canvas objects."""
    def __init__(self, **kwargs):
        super(Canvas, self).__init__(**kwargs)
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
        for i, tab_text in enumerate(self.text.split("%2C%20")):
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
        tabs_str = '<ul id="{id}_tabs" class="tab_container {position}">{tabs}<li class="clear"/></ul>'.format(
            id=self.controlID,
            position=self.position,
            tabs=''.join(self.tabs),
            )
        container_str = '<div id="{id}" class="tabbed">{children}</div>'.format(
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
        for i, tab_text in enumerate(self.text.split("%0A")):
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
        container_str = '<div id="{id}_con" class="vert_tabbed {position}">{children}</div>'.format(
            id=self.controlID,
            position=self.position,
            children=self.children_html,
            )
        tabs_str = '<ul id="{id}_tabs" class="vert_tab_container {position}">{tabs}</ul>'.format(
            id=self.controlID,
            position=self.position,
            tabs=''.join(self.tabs),
            )
        html_str = '<div id="{id}">{children}<div class="clear"/></div>'.format(
            id=self.controlID,
            children=container_str + tabs_str,
            )
        return html_str
        

BalsamiqElement._subclass_map = locals()
# for item in vars():
#     SUBCLASS_MAP.update(
#         dict([(item, vars()[item]) for item in vars() if issubclass(vars()[item], BalsamiqElement)])
#         )

import os
import re
import sys
import codecs
import urllib
from xml.dom.minidom import parseString
from itertools import product
from StringIO import StringIO
from pprint import pformat, pprint
from copy import deepcopy
from uuid import uuid4 as uuid


def getattrs(target):
    class_attrs = dir(target.__class__)
    pprint(dict((attr, getattr(target, attr)) for attr in dir(target) if attr not in class_attrs))


def clean_value(value):
    if value.lower() == 'true':
        value = True
    elif value.lower() == 'false':
        value = False
    else:
        try:
            value = int(value)
        except ValueError:
            value = value
    return value

def get_elements(balsamiq_xml_string):
    dom = parseString(balsamiq_xml_string)
    elements = []
    for control in dom.firstChild.getElementsByTagName("control"):
        element_name = str(control.getAttribute('controlTypeID').rsplit('::', 1)[1])
        element = BalsamiqElement.new(element_name)
        control.removeAttribute('controlTypeID')
        for attributeNodeIndex in xrange(control.attributes.length):
            attributeNode = control.attributes.item(attributeNodeIndex)
            name = str(attributeNode.name)
            value = clean_value(attributeNode.value)
            setattr(element, name, value)
        if control.hasChildNodes():
            controlProperties = control.childNodes[1]
            if controlProperties.hasChildNodes():
                for controlProperty in controlProperties.childNodes:
                    if controlProperty.hasChildNodes():
                        name = controlProperty.tagName
                        value = clean_value(controlProperty.firstChild.data)
                        setattr(element, name, value)
        if element.w == -1:
            element.width = element.measuredW
        else:
            element.width = element.w
        if element.h == -1:
            element.height = element.measuredH
        else:
            element.height = element.h
        del element.locked
        del element.isInGroup
        element.x1 = element.x + element.width
        element.y1 = element.y + element.height
        elements.append(element)
    return elements

LOW = -1
MID = 0
HIGH = 1

corner_attrs = ('x', 'x1', 'y', 'y1')
corner_rel_attrs = tuple([x + '_rel' for x in corner_attrs])

def nest_elements(elements):
    """Take flat list of elements and return hierarchical list."""
    elements.sort(key=lambda x: (x.width * x.height))
    elements_copy = elements[:]
    for i, element in enumerate(elements_copy):
        for big_element in elements_copy[i + 1:]:
            for attr in corner_attrs:
                attr_val = getattr(element, attr)
                big_attr_val0 = getattr(big_element, attr[0])
                big_attr_val1 = getattr(big_element, attr[0] + '1')
                if big_attr_val0 <= attr_val <= big_attr_val1:
                    setattr(element, attr + '_rel', MID)
                elif attr_val < big_attr_val0:
                    setattr(element, attr + '_rel', LOW)
                else:
                    setattr(element, attr + '_rel', HIGH)
            element.x_overlaps = sum(getattr(element, attr) == MID for attr in ('x_rel', 'x1_rel'))
            element.y_overlaps = sum(getattr(element, attr) == MID for attr in ('y_rel', 'y1_rel'))
            element.overlaps = element.x_overlaps + element.y_overlaps
            if element.x_overlaps * element.y_overlaps != 0:
                if element.overlaps != 4:
                    # Set position absolute rules
                    element.flow = False
                    element.position_rules.append('position: absolute')
                    if element.x_overlaps == 1 and element.x_rel == MID:
                        element.position_rules.append('right: {0}%'.format(round(100.*(big_element.x1 - element.x1)/big_element.width)))
                    else:
                        element.position_rules.append('left: {0}%'.format(round(100.*(big_element.x - element.x)/big_element.width)))
                    if element.y_overlaps == 1 and element.y_rel == MID:
                        element.position_rules.append('bottom: {0}%'.format(round(100.*(big_element.y1 - element.y1)/big_element.height)))
                    else:
                        element.position_rules.append('top: {0}%'.format(round(100.*(big_element.y - element.y)/big_element.height)))
                big_element.children.append(element)
                big_element.children.sort(key = lambda x: x.zOrder)
                elements.remove(element)
                break
            for attr in corner_rel_attrs:
                delattr(element, attr)
    elements.sort(key=lambda elem: (elem.y, elem.x))
    root = Root(elements)
    return root

def parse_siblings(element):
    element._sort(key=lambda x: x.y)
    return element
#     if element.y_overlaps:
#         if element.x_rel == HIGH:
#             element.position_rules.append('float: left')
#             element.position_rules.append('margin-left: {0}px'.format(element.x - big_element.x1))
#             big_element.position_rules.append('float: left')
#         elif element.x1_rel == LOW:
#             element.position_rules.append('float: right')
#             element.position_rules.append('margin-right: {0}px'.format(big_element.x - element.x1))
#             big_element.position_rules.append('float: right')

#     if [x for x in element.position_rules if x.startswith('float')]:
#         big_element.has_floats = True

def remove_extra_white_space(html_string):
    return re.sub(r'(?=[^/])>\n[\t]*?\b([^<].+?)\n[\t]*?<', r'>\1<', html_string)

def remove_url_escaping(url_string):
    return urllib.unquote(url_string)

def get_html_from_balsamiq_element(element, indent_string="\t"):
    html = parseString(element.html).toprettyxml(indent=indent_string, encoding="utf-8")
    html = remove_extra_white_space(html)
    html = remove_url_escaping(html)
    return html

def encoding_safe_read(file_object):
    if file_object.read(3) != codecs.BOM_UTF8:
        file_object.seek(0)
    return file_object.read()

def read_any(source):
    if hasattr(source, 'read'):
        return encoding_safe_read(source)
    elif os.path.exists(source):
        with open(source, 'rb') as f:
            return encoding_safe_read(f)
    else:
        return source

def write_any(target, text):
    if hasattr(target, 'write'):
        target.write(text)
    else:
        with open(target, 'wb') as f:
            f.write(text)


def main(balsamiq_xml, html_output=sys.stdout):
    balsamiq_xml_string = read_any(balsamiq_xml)
    #
    elements = get_elements(balsamiq_xml_string)
    #
    root = nest_elements(elements)
    #
    root = parse_siblings(root)
    #
    html = get_html_from_balsamiq_element(root)
    #
    write_any(html_output, html)
    return html
    

text = """
<mockup version="1.0" skin="sketch" measuredW="909" measuredH="870" mockupW="801" mockupH="870">
  <controls>
    <control controlID="44" controlTypeID="com.balsamiq.mockups::Title" x="306" y="15" w="435" h="-1" measuredW="286" measuredH="50" zOrder="2" locked="false" isInGroup="-1">
      <controlProperties>
        <align>center</align>
        <text>Kendall%20Mayhew</text>
      </controlProperties>
    </control>
    <control controlID="45" controlTypeID="com.balsamiq.mockups::TabBar" x="171" y="76" w="675" h="744" measuredW="284" measuredH="100" zOrder="1" locked="false" isInGroup="-1">
      <controlProperties>
        <selectedIndex>3</selectedIndex>
        <tabHPosition>center</tabHPosition>
        <text>Home%2C%20Bio%2C%20Photos%2C%20Reel%2C%20Resume</text>
      </controlProperties>
    </control>
    <control controlID="48" controlTypeID="com.balsamiq.mockups::Canvas" x="108" y="0" w="801" h="870" measuredW="100" measuredH="70" zOrder="0" locked="false" isInGroup="-1"/>
    <control controlID="53" controlTypeID="com.balsamiq.mockups::VerticalTabBar" x="251" y="148" w="480" h="600" measuredW="200" measuredH="178" zOrder="3" locked="false" isInGroup="-1">
      <controlProperties>
        <position>left</position>
        <selectedIndex>1</selectedIndex>
        <text>First%20Tab%0ASecond%20Tab%0AThird%20Tab%0AFourth%20Tab</text>
      </controlProperties>
    </control>
    <control controlID="54" controlTypeID="com.balsamiq.mockups::Image" x="357" y="170" w="347" h="447" measuredW="77" measuredH="79" zOrder="4" locked="false" isInGroup="-1">
      <controlProperties>
        <text/>
      </controlProperties>
    </control>
  </controls>
</mockup>
"""

if __name__ == '__main__':
    if len(sys.argv) == 1:
        main(StringIO(text))
    else:
        main(*sys.argv[1:])
