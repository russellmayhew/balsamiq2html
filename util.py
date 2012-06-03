import os
import re
import codecs
from pprint import pprint

from cgi import escape
from urllib import unquote

from xml.dom.minidom import parseString


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

def REst_repl(m):
    match1, match2, match3 = m.group(1, 2, 3)
    if match1:
        return '<em>{0}</em>'.format(match1)
    elif match2:
        return '<a href="#">{0}</a>'.format(match2)
    elif match3:
        return '<strong>{0}</strong>'.format(match3)
    else:
        return m.group(0)

def REst_filter(string):
    return re.sub(r'_(.+?)_|\[(.+?)\]|\s{0,1}\*(.+?)\*', REst_repl, string)

def unquote_all(text):
    def unicode_unquoter(match):
        return unichr(int(match.group(1),16))

    text = re.sub('(%)(?=\d{2})', '%u00', text)
    text = unquote(re.sub(r'%u([0-9a-fA-F]{4})',unicode_unquoter,text))

    return escape(text).encode('ascii', 'xmlcharrefreplace')

def getattrs(target):
    class_attrs = dir(target.__class__)
    pprint(dict((attr, getattr(target, attr)) for attr in dir(target) if attr not in class_attrs))

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

def remove_extra_white_space(html_string):
    """Remove dumb whitespace for readability.
    
    Maybe something smarter than regex would be better here, but this is a start."""

    temp = re.sub(
        r'<(([\w]+)[^/]*?)>([^<]+)</\2>',
        lambda m: '<{0}>{2}</{1}>'.format(m.group(1), m.group(2), m.group(3).strip('\n\t')),
        html_string,
        re.DOTALL)
    temp = re.sub(
        r'(</{0,1}(?:a|em|strong|span)[^>]*>)([^<]*)([^<]*)(?=</{0,1}(?:a|em|strong|span)[^>]*>)',
        lambda m: '{0}{1}'.format(m.group(1), m.group(2).strip('\n\t')),
        temp,
        re.DOTALL)
    temp = re.sub(
        r'(</{0,1}(?:a|em|strong|span)[^>]*>)([^<]*)([^<]*)(?=<)',
        lambda m: '{0}{1}'.format(m.group(1), m.group(2).lstrip('\n\t')),
        temp,
        re.DOTALL)
    temp = re.sub(
        r'([^<]*)(?=</{0,1}(?:a|em|strong|span)[^>]*>)',
        lambda m: m.group(1).rstrip('\n\t'),
        temp,
        re.DOTALL)

    return temp

def prettify_html(html, indent_string="\t"):
    html = parseString(html).toprettyxml(indent=indent_string, encoding="utf-8")
    html = remove_extra_white_space(html)
    return html
