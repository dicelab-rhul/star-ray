# import pathlib
# from datetime import datetime
# import logging as _logging  # this is the python logging package...
# from svgrenderengine.event import Event

# from dataclasses import dataclass, asdict


# @dataclass
# class LogEvent:
#     event: Event
#     message: str
#     exception: str
#     stack_trace: str


# class LogMessageFormatter(_logging.Formatter):
#     """This Formatter is used to log messages as if they were events."""

#     def format(self, record):
#         # For error and exception, include exception info and stack trace
#         exception = self.formatException(record.exc_info) if record.exc_info else None
#         stack_trace = self.formatStack(record.stack_info) if record.stack_info else None
#         event = LogEvent(
#             Event.create_event(), record.getMessage(), exception, stack_trace
#         )
#         return str(event)  # TODO format this properly...


# class EventLogger:
#     def __init__(self, path, file=None):
#         super().__init__()
#         if file is None:
#             dt = datetime.now().strftime("%Y%m%d%H%M%S")
#             file = pathlib.Path(path, f"event-log-{dt}.log")
#         else:
#             file = pathlib.Path(path, file)
#         self.handler = _logging.FileHandler(file)
#         # self.handler.setFormatter(EventFormatter())
#         self.logger = _logging.getLogger()
#         self.logger.setLevel(_logging.DEBUG)
#         self.logger.addHandler(self.handler)

#     def log_event(self, event):
#         self.handler.stream.write(f"{self.event_to_string(event)}\n")
#         self.handler.flush()

#     def event_to_string(self, event):
#         data = asdict(event)
#         id = data.pop("id")
#         timestamp = data.pop("timestamp")
#         return f"{id}, {timestamp:.7f}, '{type(event).__name__}', {data}"


# # # this is a logger for events that are triggered via the event system.
# # LOGGER = EventLogger("./logs")

# # # aliases for the logger above
# # debug = LOGGER.logger.debug
# # info = LOGGER.logger.info
# # warning = LOGGER.logger.warning
# # error = LOGGER.logger.error
# # exception = LOGGER.logger.exception
