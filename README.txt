README
======

Suggestions
-----------

Attributes are output in alphabetical order.  To stop that nonsense, I suggest you make the following simple modification as suggested at http://stackoverflow.com/questions/662624/preserve-order-of-attributes-when-modifying-with-minidom#answer-8345268:

To keep the attribute order I made this slight modification in minidom:

    from collections import OrderedDict

In the Element class :

    __init__(...)
        self._attrs = OrderedDict()
        #self._attrs = {}
    writexml(...)
        #a_names.sort()

Now this will only work with Python 2.7+ And I'm not sure if it actually works => Use at your own risks...

And please note that you should not rely on attribute order:

Note that the order of attribute specifications in a start-tag or empty-element tag is not significant.
