import bpy
import enum
from typing import Any, Callable, IO, List, Optional
import dataclasses

message_to_str_count = 0
"""
Logging Style Guide:
    - Put the name of object or source of error first, leave a trail to follow quickly
    - Include how to correct a problem instead of simply complaining about it, if possible
    - Simple English benefits all, no programmer speak, mentions of the API, or complex grammar
    - Be clear when you're talking about Blender concepts and X-Plane concepts
    - Be terse, avoid more than a sentence including data filled in strings - avoid word wrapping
    - Speak calmly and positively. Avoid "you failed" statements and exclamation marks
    - One error per problem, not one error per newline
    - Find errors whenever possible during the collection phase instead of writing the writing phase
    - Test errors are emitted as part of unit testing

Spending 20mins on a good error message is better than 2hrs troubleshooting an author's
non-existant bug
"""


class MessageTypes(enum.Enum):
    """
    Types of messages that a logger might choose to care about.
    All MessageCodes should start with one of these values
    """

    INFO = "I"
    WARNING = "W"
    ERROR = "E"
    SUCCESS = "S"


class MessageCodes(enum.Enum):
    """
    The unit test uses these error codes to test that specific errors/warnings/etc occured.
    Renumbering these will probably break tests. The naming convention is important, In case a message isn't given, the code's
    fallback message is the enum value
    """

    # 0-99 - general exporter things
    # 100-999 - global file problems
    #
    # TODO: Pick a scheme and start using that,
    # QUICK!
    I000 = "Not writing file due to dry run"
    E000 = "Unknown error"
    E001 = "Bad layer number name"
    E002 = "Couldn't find texture file"
    E003 = "GROUP percentages do not add up to 100"
    E004 = "Tree wrapper does not have vertical quad"
    E011 = "Could not find any forests to export"
    S000 = ".for exported successfully"


class _Singleton(type):
    _instances: Optional["_Singleton"] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ForestLogger(metaclass=_Singleton):
    @dataclasses.dataclass
    class Message:
        msg_code: MessageCodes
        msg_content: str
        # TODO: Implement select datablock on problem
        problem_datablock: Optional[bpy.types.ID]
        # This is a free variable used to customize how this message is logged.
        # It should be used sparingly
        msg_context: Any

        def __str__(self) -> str:
            return f"{self.msg_code.name}: {self.msg_content or self.msg_code.value}"

        @property
        def msg_type(self):
            return {t.name[0]: t.value for t in MessageTypes}[self.msg_code.name[0]]

    class ConsoleTransport:
        def __init__(self):
            self.count = 0

        def __call__(self, msg: "ForestLogger.Message") -> None:
            if self.count == 1:
                print()
            print(str(msg))
            self.count += 1

    class FileTransport:
        def __init__(self, filehandle: IO):
            self.filehandle = filehandle

        def __call__(self, msg: "ForestLogger.Message") -> None:
            try:
                self.filehandle.write(str(msg) + "\n")
            except IOError as ioe:
                assert False, "File transport failed:\n" + ioe

    class InternalTextTransport:
        def __init__(self, name="ForestLogger.log") -> None:
            if bpy.data.texts.find(name) == -1:
                self.log_txt_block = bpy.data.texts.new(name)
            else:
                self.log_txt_block = bpy.data.texts[name]

            self.log_txt_block.clear()

        def __call__(self, msg: "ForestLogger.Message") -> None:
            self.log_txt_block.write(f"{msg}\n")

    def __init__(
        self, transports: Optional = None, msg_types: List[MessageTypes] = None
    ):
        self.transports = transports or [ForestLogger.ConsoleTransport()]
        self._messages: List["ForestLogger.Message"] = []
        self.msg_types = msg_types or list(MessageTypes)

    def reset(self, transports: Optional = None, msg_types: List[MessageTypes] = None):
        self.transports = transports or [ForestLogger.ConsoleTransport()]
        self._messages.clear()
        self.msg_types = msg_types or list(MessageTypes)

    def log(
        self,
        msg_code: MessageCodes,
        msg_content: str,
        problem_datablock=None,
        msg_context=None,
    ):
        # TODO: add filtering by type
        if msg_code.name in self.msg_types or True:
            msg = ForestLogger.Message(
                msg_code=msg_code,
                msg_content=msg_content,
                problem_datablock=problem_datablock,
                msg_context=msg_context,
            )
            self._messages.append(msg)
            for transport in self.transports:
                transport(msg)
        else:
            pass

    def error(
        self,
        code: MessageCodes,
        message: str,
        problem_datablock: Optional[bpy.types.Object],
        context=None,
    ):
        self.log(code, message, problem_datablock, context)

    def warn(
        self,
        code: MessageCodes,
        message: str,
        problem_datablock: Optional[bpy.types.Object],
        context=None,
    ):
        self.log(code, message, problem_datablock, context)

    def info(
        self,
        code: MessageCodes,
        message: str,
        problem_datablock: Optional[bpy.types.Object],
        context=None,
    ):
        self.log(code, message, problem_datablock, context)

    def success(
        self,
        code: MessageCodes,
        message: str,
        problem_datablock: Optional[bpy.types.Object],
        context=None,
    ):
        self.log(code, message, problem_datablock, context)

    @property
    def messages(self):
        return self._messages.copy()

    @property
    def infos(self):
        return [m for m in self.messages if m.msg_type == MessageTypes.INFO]

    @property
    def warnings(self):
        return [m for m in self.messages if m.msg_type == MessageTypes.SUCCESS]

    @property
    def errors(self):
        return [m for m in self.messages if m.msg_type == MessageTypes.ERROR]

    @property
    def successes(self):
        return [m for m in self.messages if m.msg_type == MessageTypes.SUCCESS]


logger = ForestLogger()
