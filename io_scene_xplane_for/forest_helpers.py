import os
import itertools
from typing import Iterable, List, Optional, Tuple, Union

import bpy
import mathutils

from .forest_constants import *

"""
Given the difficulty in keeping all these words straight, these
types have been created. Use these to keep yourself from
running in circles
"""

"""Something with an XPlaneLayer property"""
PotentialRoot = Union[bpy.types.Collection]

"""
Something with an XPlaneLayer property that also meets all other requirements.
It does not garuntee an error or warning free export, however
"""
ExportableRoot = Union[bpy.types.Collection]

"""
Something that has a .children property. A collection and object's
children are not compatible
"""
BlenderParentType = Union[bpy.types.Collection, bpy.types.Object]

def floatToStr(n:float)->str:
    """
    Makes a rounded float with as 0's
    and decimal place removed if possible
    """
    #THIS IS A HOT PATH, DO NOT CHANGE WITHOUT PROFILING

    # 'g' can do the rstrip and '.' removal for us, except for rare cases when we need to fallback
    # to the less fast 'f', rstrip, ternary approach
    s = f"{n:.{PRECISION_OBJ_FLOAT}g}"
    if "e" in s:
        s = f"{n:.{PRECISION_OBJ_FLOAT}f}".rstrip('0')
        return s if s[-1] != "." else s[:-1]
    return s

def get_collections_in_scene(scene:bpy.types.Scene)->List[bpy.types.Collection]:
    """
    First entry in list is always the scene's 'Master Collection'
    """
    def recurse_child_collections(col:bpy.types.Collection):
        yield col
        for c in col.children:
            yield from recurse_child_collections(c)

    return list(recurse_child_collections(scene.collection))

def get_layer_collections_in_view_layer(view_layer:bpy.types.ViewLayer)->List[bpy.types.Collection]:
    """
    First entry in list is always the scene's 'Master Collection'
    """
    def recurse_child_collections(layer_col:bpy.types.LayerCollection):
        yield layer_col
        for c in layer_col.children:
            yield from recurse_child_collections(c)

    return list(recurse_child_collections(view_layer.layer_collection))

def get_exportable_roots_in_scene(scene: bpy.types.Scene, view_layer:bpy.types.ViewLayer)->List[ExportableRoot]:
    return [root for root in filter(lambda o: is_exportable_root(o, view_layer), get_collections_in_scene(scene))]

def get_plugin_resources_folder()->str:
    return os.path.join(os.path.dirname(__file__),"resources")

def is_visible_in_viewport(datablock: bpy.types.Collection, view_layer:bpy.types.ViewLayer)->Optional[ExportableRoot]:
    all_layer_collections = {c.name: c for c in get_layer_collections_in_view_layer(view_layer)}
    return all_layer_collections[datablock.name].is_visible

def is_exportable_root(potential_root: PotentialRoot, view_layer:bpy.types.ViewLayer)->bool:
    """
    Since datablocks don't keep track of which view layers they're a part of,
    we have to provide it
    """
    return (
        potential_root.xplane_for.is_exportable_collection
        and is_visible_in_viewport(potential_root, view_layer)
    )

def round_vec(v:mathutils.Vector, ndigits:int)->mathutils.Vector:
    return mathutils.Vector(round(comp, ndigits) for comp in v)

def vec_b_to_x(v)->mathutils.Vector:
    return mathutils.Vector((v[0], v[2], -v[1]))


def vec_x_to_b(v)->mathutils.Vector:
    return mathutils.Vector((v[0], -v[2], v[1]))

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
class Logger():
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

    def addTransport(self, transport, messageTypes = ['error', 'warning', 'info', 'success']):
        self.transports.append({
            'fn': transport,
            'types': messageTypes
        })

    def clear(self):
        self.transports.clear()
        self.messages.clear()

    def messagesToString(self, messages = None):
        if messages == None:
            messages = self.messages

        out = ''

        for message in messages:
            out += Logger.messageToString(message['type'], message['message'], message['context']) + '\n'

        return out

    def log(self, messageType, message, context = None):
        self.messages.append({
            'type': messageType,
            'message': message,
            'context': context
        })

        for transport in self.transports:
            if messageType in transport['types']:
                transport['fn'](messageType, message, context)

    def error(self, message, context = None):
        self.log('error', message, context)

    def warn(self, message, context = None):
        self.log('warning', message, context)

    def info(self, message, context = None):
        self.log('info', message, context)

    def success(self, message, context = None):
        self.log('success', message, context)

    @staticmethod
    def messageToString(messageType, message, context = None):
        #message_to_str_count += 1
        return '%s: %s' % (messageType.upper(), message)

    @staticmethod
    def InternalTextTransport(name = 'XPlaneForExporter.log'):
        if bpy.data.texts.find(name) == -1:
            log = bpy.data.texts.new(name)
        else:
            log = bpy.data.texts[name]

        log.clear()

        def transport(messageType, message, context = None):
            log.write(Logger.messageToString(messageType, message, context) + '\n')

        return transport

    @staticmethod
    def ConsoleTransport():
        def transport(messageType, message, context = None):
            #if io_xplane2blender.xplane_helpers.message_to_str_count == 1:
                #print('\n')
            print(Logger.messageToString(messageType, message, context))

        return transport

    @staticmethod
    def FileTransport(filehandle):
        def transport(messageType, message, context = None):
            filehandle.write(Logger.messageToString(messageType, message, context) + '\n')

        return transport


logger = Logger()
