import re

text = """<mockup version="1.0" skin="sketch" measuredW="909" measuredH="872" mockupW="801" mockupH="870">
  <controls>
    <control controlID="44" controlTypeID="com.balsamiq.mockups::Title" x="365" y="26" w="-1" h="-1" measuredW="286" measuredH="50" zOrder="4" locked="false" isInGroup="-1">
      <controlProperties>
        <text>Kendall%20Mayhew</text>
      </controlProperties>
    </control>
    <control controlID="45" controlTypeID="com.balsamiq.mockups::TabBar" x="179" y="76" w="675" h="744" measuredW="259" measuredH="100" zOrder="1" locked="false" isInGroup="-1">
      <controlProperties>
        <selectedIndex>3</selectedIndex>
        <tabHPosition>center</tabHPosition>
        <text>Home%2C%20Bio%2C%20Photos%2C%20Reel%2C%20Res</text>
      </controlProperties>
    </control>
    <control controlID="46" controlTypeID="com.balsamiq.mockups::VerticalTabBar" x="237" y="169" w="480" h="600" measuredW="200" measuredH="178" zOrder="2" locked="false" isInGroup="-1">
      <controlProperties>
        <selectedIndex>1</selectedIndex>
        <text>First%20Tab%0ASecond%20Tab%0AThird%20Tab%0AFourth%20Tab</text>
      </controlProperties>
    </control>
    <control controlID="47" controlTypeID="com.balsamiq.mockups::Image" x="315" y="169" w="402" h="600" measuredW="332" measuredH="500" zOrder="3" locked="false" isInGroup="-1">
      <controlProperties>
        <src>http%3A//farm4.staticflickr.com/3569/3524015958_4a4128f171.jpg</src>
        <text/>
      </controlProperties>
    </control>
    <control controlID="48" controlTypeID="com.balsamiq.mockups::Canvas" x="108" y="2" w="801" h="870" measuredW="100" measuredH="70" zOrder="0" locked="false" isInGroup="-1"/>
  </controls>
</mockup>"""

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
    has_floats = False
    flow = True
    children = []
    position_rules = []
    def __repr__(self):
        return '<Element instace with attrs:\n{0}>'.format(pformat(dict([(attr, getattr(self, attr) if attr != 'children' else [len(getattr(self, attr))]) for attr in dir(self) if not attr.startswith('_')])))

def get_element_list(file):
    dom = parse(file)
    elements = []
    for control in dom.firstChild.getElementsByTagName("control"):
        element = Element()
        for attributeNodeIndex in xrange(control.attributes.length):
            attributeNode = control.attributes.item(attributeNodeIndex)
            if attributeNode.name == 'controlTypeID':
                name = 'type'
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
            for controlProperty in control.firstChild.childNodes:
                setattr(element, controlProperty.tagName, controlProperty.firstChild.data)
        element.width_is_measured = element.height_is_measured = False
        if element.w == -1:
            element.width_is_measured = True
            element.width = element.measuredW
        else:
            element.width = element.w
        if element.h == -1:
            element.height_is_measured = True
            element.height = element.measuredH
        else:
            element.height = element.h
        del element.locked
        del element.isInGroup
        element.x1 = element.x + element.width
        element.y1 = element.y + element.height

        elements.append(element)
    return elements

blah = StringIO()
blah.write(text)
blah.seek(0)
element_list = get_element_list(blah)

# with open(sys.argv[1], 'rb') as f:
#     element_list = get_element_list(f)

element_list.sort(key=lambda x: (x.width * x.height))

LOW = -1
MID = 0
HIGH = 1

corner_attrs = ('x', 'x1', 'y', 'y1')
corner_rel_attrs = tuple([x + '_rel' for x in corner_attrs])

def nest_elements(element_list):
    """Take flat list of elements and return hierarchical list."""
    for i, element in enumerate(element_list[:]):
        for big_element in element_list[i + 1:]:
            for attr in corner_attrs:
                attr_val = getattr(element, attr)
                big_attr_val0 = getattr(big_element, attr[0])
                big_attr_val1 = getattr(big_element, attr[0] + '1')
                if big_attr_val0 <= attr_val <= big_attr_val1:
                    setattr(element, attr + '_rel', LOW)
                elif attr_val < big_attr_val0:
                    setattr(element, attr + '_rel', MID)
                else:
                    setattr(element, attr + '_rel', HIGH)
            element.x_overlaps = sum(getattr(element, attr) == MID for attr in ('x_rel', 'x1_rel'))
            element.y_overlaps = sum(getattr(element, attr) == MID for attr in ('y_rel', 'y1_rel'))
            element.overlaps = element.x_overlaps + element.y_overlaps
            if element.overlaps == 4:
                big_element.children.append(element)
                big_element.children.sort(key = lambda x: x.zOrder)
                if [x for x in element.position_rules if x.startswith('float')]:
                    big_element.has_floats = True
                element_list.remove(element)
                break
            elif element.y_overlaps:
                if element.x_rel == HIGH:
                    element.position_rules.append('float: left')
                    element.position_rules.append('margin-left: {0}px'.format(element.x - big_element.x1))
                    big_element.position_rules.append('float: left')
                elif element.x1_rel == LOW:
                    element.position_rules.append('float: right')
                    element.position_rules.append('margin-right: {0}px'.format(big_element.x - element.x1))
                    big_element.position_rules.append('float: right')
            elif element.overlaps != 0:
                element.position_rules.append('position: absolute')
                element.position_rules.append('')
            for attr in corner_rel_attrs:
                delattr(element, attr)
    element_list.sort(key=lambda elem: (elem.y, elem.x))
    return element_list


temp = StringIO()

root_element
