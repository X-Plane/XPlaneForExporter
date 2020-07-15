import bpy

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


class Logger:
    def __init__(self):
        self.transports = []
        self.messages = []

    @property
    def errors(self):
        return [m["message"] for m in self.messages if m["type"] == "error"]

    @property
    def infos(self):
        return [m["message"] for m in self.messages if m["type"] == "info"]

    @property
    def successes(self):
        return [m["message"] for m in self.messages if m["type"] == "success"]

    @property
    def warnings(self):
        return [m["message"] for m in self.messages if m["type"] == "warning"]

    def addTransport(
        self, transport, messageTypes=["error", "warning", "info", "success"]
    ):
        self.transports.append({"fn": transport, "types": messageTypes})

    def clear(self):
        self.transports.clear()
        self.messages.clear()

    def log(self, messageType, message, context=None):
        self.messages.append(
            {"type": messageType, "message": message, "context": context}
        )

        for transport in self.transports:
            if messageType in transport["types"]:
                transport["fn"](messageType, message, context)

    def error(self, message, context=None):
        self.log("error", message, context)

    def warn(self, message, context=None):
        self.log("warning", message, context)

    def info(self, message, context=None):
        self.log("info", message, context)

    def success(self, message, context=None):
        self.log("success", message, context)

    @staticmethod
    def messageToString(messageType, message, context=None):
        # message_to_str_count += 1
        return "%s: %s" % (messageType.upper(), message)

    @staticmethod
    def InternalTextTransport(name="XPlaneForExporter.log"):
        if bpy.data.texts.find(name) == -1:
            log = bpy.data.texts.new(name)
        else:
            log = bpy.data.texts[name]

        log.clear()

        def transport(messageType, message, context=None):
            log.write(Logger.messageToString(messageType, message, context) + "\n")

        return transport

    @staticmethod
    def ConsoleTransport():
        def transport(messageType, message, context=None):
            # if io_xplane2blender.xplane_helpers.message_to_str_count == 1:
            # print('\n')
            print(Logger.messageToString(messageType, message, context))

        return transport

    @staticmethod
    def FileTransport(filehandle):
        def transport(messageType, message, context=None):
            filehandle.write(
                Logger.messageToString(messageType, message, context) + "\n"
            )

        return transport


logger = Logger()
