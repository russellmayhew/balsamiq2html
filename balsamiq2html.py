import sys

from elements import BalsamiqElement
from util import prettify_html, read_any, write_any, getattrs, \
                 parseString, clean_value


bal_dim_attrs = ('w', 'h', 'measuredW', 'measuredH')

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
        for attr in bal_dim_attrs:
            delattr(element, attr)
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
overlap_attrs = ('overlaps', 'x_overlaps', 'y_overlaps')


def nest_elements(elements):
    """Take flat list of elements and return hierarchical list."""
    elements.sort(key=lambda x: x.size)
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
                for attr in corner_rel_attrs + overlap_attrs:
                    delattr(element, attr)
                big_element.children.append(element)
                big_element.children.sort(key=lambda x: (-x.size, x.zOrder))
                elements.remove(element)
                break
            for attr in corner_rel_attrs:
                delattr(element, attr)
    root = BalsamiqElement.new('Root', children=elements)
    return root


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


def balsamiq_to_balsamadom(balsamiq_xml):
    balsamiq_xml_string = read_any(balsamiq_xml)

    elements = get_elements(balsamiq_xml_string)

    root = nest_elements(elements)

    root.sort()

    return root

def balsamiq_to_html(balsamiq_xml, html_output=sys.stdout):
    balsamadom = balsamiq_to_balsamadom(balsamiq_xml)

    html = prettify_html(balsamadom.html)

    write_any(html_output, html)

    return html


if __name__ == '__main__':
    balsamiq_to_html(*sys.argv[1:])
