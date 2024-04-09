import logging

_LOGGER = logging.getLogger("star_ray")
_LOGGER.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s - %(message)s")
handler.setFormatter(formatter)
_LOGGER.addHandler(handler)
