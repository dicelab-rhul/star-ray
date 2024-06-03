import time
import re
from lxml import etree
from ast import literal_eval


class _TrackingElement(etree.ElementBase):

    @property
    def positional_xpath(self):
        return True

    @staticmethod
    def _literal_eval(v):
        try:
            return literal_eval(v)
        except:
            return v

    def notify(self, **kwargs):
        # this could be an @abstractmethod, but I am not sure how lxml will handle this,
        # better to just have a simple error (this is an internal class anyway).
        raise NotImplementedError(
            f"`notify(self, **kwargs)` was not implemented for class deriving {_TrackingElement}."
        )

    def set(self, key, value):
        super().set(key, value)
        # notify the tracker of the change
        xpath, element_id = self._get_element_xpath()
        # _TrackingElement._tracker.notify(
        self.notify(
            timestamp=time.time(),
            element_id=element_id,
            xpath=xpath,
            # value will always be a string, here, we prefer it to be a python type (int, float, etc) downstream
            attributes={key: _TrackingElement._literal_eval(value)},
        )

    def replace(self, old_element, new_element):
        # replace a child element
        xpath, element_id = old_element._get_element_xpath()
        value = etree.tostring(new_element)
        # the ordering matters here! this must be called after old_element._get_element_xpath()
        super().replace(old_element, new_element)
        # TODO some more information may be needed here?
        self.notify(
            timestamp=time.time(), element_id=element_id, xpath=xpath, attributes=value
        )

    @property
    def text(self):
        return super().text

    @text.setter
    def text(self, value):
        xpath, element_id = self._get_element_xpath() + "/text()"
        # _TrackingElement._tracker.notify(
        self.notify(
            timestamp=time.time(), element_id=element_id, xpath=xpath, attributes=value
        )
        super(_TrackingElement, self.__class__).text.__set__(self, value)

    def _get_element_xpath(self):
        # TODO note that the element xpath is defined as relative, but it is always relative to the root of the xml tree!
        # TODO document this somewhere
        id = self.get("id", None)
        if id:
            # there is a unique id, use this as the unique identifier for this change
            prefix = _TrackingElement._get_namespace_prefix(self)
            tag = etree.QName(self.tag).localname
            return f".//{prefix}:{tag}[@id='{id}']", id
        elif self.positional_xpath:
            # positional paths start with a /* indicating the root node, make this relative to the root
            return f"./{self.getroottree().getpath(self)[2:]}", None
        else:
            # fall back to getting the unique path to the element, this includes the namespace URIs which usually need to be resolve to their prefix.
            return f"./{self._get_prefixed_element_path()}", None

    def _get_prefixed_element_path(self):
        path = self.getroottree().getelementpath(self)
        path_split = _TrackingElement._split_element_path(path)
        node = self
        result = []
        for part in reversed(path_split):
            if part[0] == "{":
                prefix = _TrackingElement._get_namespace_prefix(node)
                result.append(f"{prefix}:{part.split('}')[1]}")
            else:
                result.append(part)
            node = node.getparent()
        return "/".join(reversed(result))

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
        raise ValueError(f"Failed to find namespace prefix for element: {element}")

    @staticmethod
    def _split_element_path(path):
        # Regular expression to match '/' outside curly brackets
        pattern = r"/(?![^{]*})"  # TODO revise this? its a bit nebulous
        return re.split(pattern, path)
