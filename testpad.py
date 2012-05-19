import re

text = """
<mockup version="1.0" skin="sketch" measuredW="909" measuredH="870" mockupW="801" mockupH="870">
  <controls>
    <control controlID="44" controltagID="com.balsamiq.mockups::Title" x="306" y="15" w="435" h="-1" measuredW="286" measuredH="50" zOrder="2" locked="false" isInGroup="-1">
      <controlProperties>
        <align>center</align>
        <text>Kendall%20Mayhew</text>
      </controlProperties>
    </control>
    <control controlID="45" controltagID="com.balsamiq.mockups::TabBar" x="171" y="76" w="675" h="744" measuredW="284" measuredH="100" zOrder="1" locked="false" isInGroup="-1">
      <controlProperties>
        <selectedIndex>3</selectedIndex>
        <tabHPosition>center</tabHPosition>
        <text>Home%2C%20Bio%2C%20Photos%2C%20Reel%2C%20Resume</text>
      </controlProperties>
    </control>
    <control controlID="48" controltagID="com.balsamiq.mockups::Canvas" x="108" y="0" w="801" h="870" measuredW="100" measuredH="70" zOrder="0" locked="false" isInGroup="-1"/>
    <control controlID="53" controltagID="com.balsamiq.mockups::VerticalTabBar" x="251" y="148" w="480" h="600" measuredW="200" measuredH="178" zOrder="3" locked="false" isInGroup="-1">
      <controlProperties>
        <position>left</position>
        <selectedIndex>1</selectedIndex>
        <text>First%20Tab%0ASecond%20Tab%0AThird%20Tab%0AFourth%20Tab</text>
      </controlProperties>
    </control>
    <control controlID="54" controltagID="com.balsamiq.mockups::Image" x="357" y="170" w="347" h="447" measuredW="77" measuredH="79" zOrder="4" locked="false" isInGroup="-1">
      <controlProperties>
        <text/>
      </controlProperties>
    </control>
  </controls>
</mockup>
"""

# blah = re.split('\n    (?=<[^/])', text)
# beginning = blah.pop(0)
# blah.sort(key=lambda x: int(re.findall(r'zOrder="([\d]*?)"', x)[0]))
# blah.insert(0, beginning)
# blah = '\n    '.join(blah)

from xml.dom.minidom import parse
from itertools import product
from StringIO import StringIO
from pprint import pformat
from copy import deepcopy


class Element(object):
    def __init__(self, tag=None):
        if tag != None:
            self.tag = tag
        self.has_floats = False
        self.flow = True
        self.children = []
        self.position_rules = []
    def __repr__(self):
        return '<Element instace with attrs:\n{0}>'.format(pformat(dict([(attr, getattr(self, attr) if attr != 'children' else [len(getattr(self, attr))]) for attr in dir(self) if not attr.startswith('_')])))
    def _write(self, f):
        f.write('<{0}>'.format(self.tag))
        for child_element in self.children:
            child_element._write(f)
        f.write('</{0}>'.format(self.tag))
    def _sort(self, *args, **kwargs):
        self.children.sort(*args, **kwargs)
        for child_element in self.children:
            child_element._sort(*args, **kwargs)

class Title(Element):
    """Element subclass for Title balsamiq TypeID objects."""
    def __init__(self):
        super(Title, self).__init__(tag='h1')
        


def get_elements(file):
    dom = parse(file)
    elements = []
    for control in dom.firstChild.getElementsByTagName("control"):
        element = Element()
        for attributeNodeIndex in xrange(control.attributes.length):
            attributeNode = control.attributes.item(attributeNodeIndex)
            if attributeNode.name == 'controltagID':
                name = 'tag'
                value = str(attributeNode.value.rsplit('::', 1)[1])
            else:
                name = str(attributeNode.name)
                if attributeNode.value.lower() == 'true':
                    value = True
                elif attributeNode.value.lower() == 'false':
                    value = False
                else:
                    try:
                        value = int(attributeNode.value)
                    except ValueError:
                        value = attributeNode.value
            setattr(element, name, value)
        if control.hasChildNodes():
            controlProperties = control.childNodes[1]
            if controlProperties.hasChildNodes():
                for controlProperty in controlProperties.childNodes:
                    if controlProperty.hasChildNodes():
                        setattr(element, controlProperty.tagName, controlProperty.firstChild.data)
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
            #pdb.set_trace()
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
    root = Element('html')
    root.children = elements
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


blah = StringIO()
blah.write(text)
blah.seek(0)

elements = get_elements(blah)
root = nest_elements(elements)
root = parse_siblings(root)

temp = StringIO()
root._write(temp)

temp.seek(0)
html = parse(temp)
print html.toprettyxml()
