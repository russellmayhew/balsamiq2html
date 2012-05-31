import os
import re
import sys
import codecs
import urllib
# import xml.dom.minidom
# if not getattr(xml.dom.minidom, 'OrderedDict'):
#     import collections
#     import minidom_mods
#     xml.dom.minidom.OrderedDict = collections.OrderedDict
#     xml.dom.minidom.Element.__init__ = minidom_mods.__init__
#     xml.dom.minidom.Element.writexml = minidom_mods.writexml
from xml.dom.minidom import parseString
from itertools import product
from StringIO import StringIO
from pprint import pformat, pprint
from copy import deepcopy
from uuid import uuid4 as uuid

from elements import BalsamiqElement

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
            try:
                value = float(value)
            except:
                value = value
    return value

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
                for attr in corner_rel_attrs + overlap_attrs:
                    delattr(element, attr)
                big_element.children.append(element)
                big_element.children.sort(key=lambda x: (-(x.width * x.height), x.zOrder))
                elements.remove(element)
                break
            for attr in corner_rel_attrs:
                delattr(element, attr)
    root = BalsamiqElement.new('Root', children=elements)
    return root

def parse_siblings(root):
    root.sort(key=lambda x: x.y)
    import pdb; pdb.set_trace()
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

def re_repl_1(m):
    return '<{0}>{2}</{1}>'.format(m.group(1), m.group(2), m.group(3).strip('\n\t'))
def re_repl_2(m):
    return '{0}{1}'.format(m.group(1), m.group(2).strip('\n\t'))
def re_repl_3(m):
    return '{0}{1}'.format(m.group(1), m.group(2).lstrip('\n\t'))
def re_repl_4(m):
    return m.group(1).rstrip('\n\t')

def remove_extra_white_space(html_string):
    """Remove dumb whitespace for readability.
    
    Maybe something smarter than regex would be better here, but this is a start."""

    temp = re.sub(r'<(([\w]+)[^/]*?)>([^<]+)</\2>', re_repl_1, html_string, re.DOTALL)
    temp = re.sub(r'(</{0,1}(?:a|em|strong|span)[^>]*>)([^<]*)([^<]*)(?=</{0,1}(?:a|em|strong|span)[^>]*>)', re_repl_2, temp, re.DOTALL)
    temp = re.sub(r'(</{0,1}(?:a|em|strong|span)[^>]*>)([^<]*)([^<]*)(?=<)', re_repl_3, temp, re.DOTALL)
    return re.sub(r'([^<]*)(?=</{0,1}(?:a|em|strong|span)[^>]*>)', re_repl_4, temp, re.DOTALL)

def get_html_from_balsamiq_element(element, indent_string="\t"):
    html = parseString(element.html).toprettyxml(indent=indent_string, encoding="utf-8")
    html = remove_extra_white_space(html)
    return element.html

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

    elements = get_elements(balsamiq_xml_string)

    root = nest_elements(elements)
    root = parse_siblings(root)
    html = get_html_from_balsamiq_element(root)

    write_any(html_output, html)
    return html


if __name__ == '__main__':
    main(*sys.argv[1:])
