import logging


class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Set a fixed length for levelname
        max_len = 8  # Maximum length for standard level names like WARNING, ERROR, etc.
        record.levelname = record.levelname.ljust(max_len)
        return super().format(record)


_LOGGER = logging.getLogger("star_ray.plugin.xml")
_LOGGER.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = CustomFormatter("%(levelname)s - %(message)s")
handler.setFormatter(formatter)
_LOGGER.propagate = False
_LOGGER.addHandler(handler)
