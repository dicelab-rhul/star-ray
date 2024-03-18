""" TODO """

import time
import re
from lxml import etree


def _split_element_path(path):
    # Regular expression to match '/' outside curly brackets
    pattern = r"/(?![^{]*})"

    # Split the path based on the pattern
    return re.split(pattern, path)


class XMLChangeTracker:
    def __init__(self):
        self._changes = []

    def notify(self, **kwargs):
        self._changes.append(kwargs)

    @staticmethod
    def new(parser, tracker=None, positional_xpath=False):
        if tracker is None:
            tracker = XMLChangeTracker()

        class TrackingElement(etree.ElementBase):

            _tracker = tracker

            def set(self, key, value):
                # print("SET", key, value)
                super().set(key, value)
                # notify the tracker of the change
                xpath = self._get_element_xpath()
                TrackingElement._tracker.notify(
                    timestamp=time.time(), xpath=xpath, attributes={key: value}
                )

            # function used to replace fully qualified namespaces

            def _get_element_xpath(self):
                # TODO note that the element xpath is defined as relative, but it is always relative to the root of the xml tree!
                # TODO document this somewhere
                id = self.get("id", None)
                if id:
                    # there is a unique id, use this as the unique identifier for this change
                    prefix = TrackingElement._get_namespace_prefix(self)
                    tag = etree.QName(self.tag).localname
                    return f".//{prefix}:{tag}[@id='{id}']"
                elif positional_xpath:
                    # positional paths start with a /* indicating the root node, make this relative to the root
                    return f"./{self.getroottree().getpath(self)[2:]}"
                else:
                    # fall back to getting the unique path to the element, this includes the namespace URIs which usually need to be resolve to their prefix.
                    return f"./{self._get_prefixed_element_path()}"

            @staticmethod
            def _get_namespace_prefix(element):
                # Get the namespace URI of the element
                qname = etree.QName(element.tag)
                namespace_uri = qname.namespace

                # Iterate over the ancestor elements' namespace mappings
                for prefix, uri in element.nsmap.items():
                    if uri == namespace_uri:
                        if prefix is None:
                            # use the last bit of the uri as the prefix... this seems to be the default behaviour elsewhere
                            return namespace_uri.split("/")[-1]
                        return prefix
                raise ValueError(
                    f"Failed to find namespace prefix for element: {element}"
                )

            def _get_prefixed_element_path(self):
                path = self.getroottree().getelementpath(self)
                path_split = _split_element_path(path)
                node = self
                result = []
                for part in reversed(path_split):
                    if part[0] == "{":
                        prefix = TrackingElement._get_namespace_prefix(node)
                        result.append(f"{prefix}:{part.split('}')[1]}")
                    else:
                        result.append(part)
                    node = node.getparent()
                return "/".join(reversed(result))

            def replace(self, old_element, new_element):
                # replace a child element
                xpath = old_element._get_element_xpath()
                value = etree.tostring(new_element)
                # the ordering matters here! this must be called after old_element._get_element_xpath()
                super().replace(old_element, new_element)
                TrackingElement._tracker.notify(
                    timestamp=time.time(), xpath=xpath, attributes=value
                )

            @property
            def text(self):
                return super().text

            @text.setter
            def text(self, value):
                xpath = self._get_element_xpath() + "/text()"
                # key=None means "replace the element" with value
                TrackingElement._tracker.notify(
                    timestamp=time.time(), xpath=xpath, attributes=value
                )
                super(TrackingElement, self.__class__).text.__set__(self, value)

        parser_lookup = etree.ElementDefaultClassLookup(element=TrackingElement)
        parser.set_element_class_lookup(parser_lookup)
        return tracker


if __name__ == "__main__":
    parser = etree.XMLParser()
    tracker = XMLChangeTracker.new(parser)

    # Use the parser with fromstring to parse an XML string
    xml_string = '<root><child attr1="value1"> <rect width="100"/> <rect width="200"/> some text </child> </root>'
    root = etree.fromstring(xml_string, parser=parser)

    # Example of setting an attribute on an element to trigger change tracking
    child = root.xpath(".//child")[0]
    child.set("attr2", "value2")
    child.text = "new text"
    print(child.text)

    child = root.xpath(".//rect")[0]
    child.set("width", "200")

    child = root.xpath(".//child/text()")[0]
    print(type(child))

    for child in root.xpath(".//rect"):
        child.getparent().replace(child, etree.fromstring('<rect width="200"/>'))

    # Demonstrate that the change was tracked
    print("Recorded changes:", tracker._changes)

    NAMESPACES = {"svg": "http://www.w3.org/2000/svg"}

    XML = """
    <svg width="200" height="200">
        <g>
            <!-- Circle 1 -->
            <circle cx="50" cy="50" r="30" fill="red" />
            <!-- Circle 2 -->
            <circle cx="150" cy="50" r="30" fill="green" />
        </g>
            <!-- Rectangle 1 -->
            <rect x="130" y="20" width="50" height="30" fill="orange" />
    </svg>
    """

    parser = etree.XMLParser()
    tracker = XMLChangeTracker.new(parser)

    root = etree.fromstring(XML, parser=parser)

    children = root.xpath("//circle")
    for child in children:
        child.set("cx", "10")
        child.set("cy", "10")

    print("Recorded changes:", tracker._changes)
