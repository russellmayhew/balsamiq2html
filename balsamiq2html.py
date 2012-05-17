import sys
from StringIO import StringIO
from xml.dom.minidom import parse
from xml.parsers.expat import ParserCreate
from elementtree.SimpleXMLWriter import XMLWriter
from functools import partial

def create_title(xml_writer, **kwargs):
	xml_writer.element('h1', kwargs['text'])

def create_tab_bar(xml_writer, **kwargs):
	if "tabHPosition" in kwargs:
		class_string = "tab_container " + kwargs["tabHPosition"]
	else:
		class_string = "tab_container"

	xml_writer.start('ul', {'class': class_string})

	for i, tab_text in enumerate(kwargs['text'].split("%2C%20")):
		if i == int(kwargs["selectedIndex"]):
			class_string = "tab selected"
		else:
			class_string = "tab"
		xml_writer.element('li', tab_text, {'class': class_string})
	xml_writer.end('ul')

def create_vert_tab_bar(xml_writer, **kwargs):
	if "tabVPosition" in kwargs:
		class_string = "vert_tab_container " + kwargs["tabVPosition"]
	else:
		class_string = "vert_tab_container"

	xml_writer.start('ul', {'class': class_string})

	for i, tab_text in enumerate(kwargs['text'].split("%0A")):
		if i == int(kwargs["selectedIndex"]):
			class_string = "vert_tab selected"
		else:
			class_string = "vert_tab"
		xml_writer.element('li', tab_text, {'class': class_string})
	xml_writer.end('ul')

def create_image(xml_writer, **kwargs):
	attrs = {
		'src': kwargs['src'],
		'width': kwargs['width'],
		'height': kwargs['height'],
		'alt': kwargs.get('text', ''),
		}
	xml_writer.element('img', '', attrs)



temp = StringIO()

w = XMLWriter(temp)
html = w.start('html')


outer_src_tags = set(["mockup", "controls", "control"])

control_map = {
	'Title': partial(create_title, w),
	'TabBar': partial(create_tab_bar, w),
	'VerticalTabBar': partial(create_vert_tab_bar, w),
	'Image': partial(create_image, w),
	}

this_control = { "attrs": {} }
this_src_tag = ""
pending_method = None

# 3 handler functions
def start_element(name, attrs):
	if name not in outer_src_tags:
		globals()['this_src_tag'] = name

	if name == "control":
		globals()['this_control']["method"] = control_map[attrs.get('controlTypeID').rsplit("::", 1)[1]]
		globals()['this_control']["attrs"].update({
			'width': attrs['w'],
			'height': attrs['h'],
			})

def end_element(name):
	if name == "control":
		globals()['this_control']["method"](**globals()['this_control']["attrs"])
		globals()['this_control'] = { "attrs": {} }

def char_data(data):
	data = data.strip()
	if data:
		globals()['this_control']["attrs"][globals()['this_src_tag']] = data


p = ParserCreate()

p.StartElementHandler = start_element
p.EndElementHandler = end_element
p.CharacterDataHandler = char_data

with open(sys.argv[1], 'rb') as f:
	p.ParseFile(f)


w.close(html)





temp.seek(0)
xmltree = parse(temp)

with open(sys.argv[2], 'wb') as f:
	f.write(xmltree.toprettyxml())

	
