[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# XPlaneForExporter
Our .for exporter addon for Blender

# How To Use
As a general rule - things that are not visible are never exported, including forests, layers, and individual trees. WYSIWYG.
Hopefully all properties are self explanatory of what they're for.

## Root Collections
Root collections are where the exporter starts collecting datablocks for making a .for. A single .blend file can make multiple .for files in a single Scene. Any top level collection counts as a root collection automatically. Important properties for changing the .for's header or other options are found in the Scene Properties.

## Layers
The layers are child collections of a root collection. They must have a special name `<int-convertable >= 0>` followed optionally by a space anything else that may one day be used as a comment or simply for your convince. You may not have duplicate layer numbers. Trees in this collection use this layer number. It is possible to make two sub collections with names like `3 - shrubs part 1` and `3 - shrubs (just testing this)` and have the trees in both collections receive 3 as their layer.

If PERLIN_ directives are used, GROUPs will use that layer number. Further sub-collections have no special meaning.

## Tree Wrappers
Empties with no parents inside a layer collection are called "Tree Wrappers". They contain the various billboards and meshes to create the true content of a .for. Empties in other places (like under the root object or inside another empty) are not tree wrappers. The Empty Properties tab contains options related to trees, such as the maximum height of the billboard and relative importances to other trees in the layer (controls frequency of tree of all trees in that layer). 

### Billboards
A tree wrapper **must** have
1. One perfectly vertical, UV unwrapped, quad
It may also have
1. One perfectly horizontal, UV unwrapped, quad, whose origin matches the vertical quad (for defining a Y_QUAD)
2. One copy of the vertical, rotated at 90 degrees about the Z-Axis and sharing the origin of the other vertical quad.

These quads are WYSIWYG and define the offsets, min height, width, rotation, etc of the billboard system.

The location of the tree wrapper has no meaning.

### 3D Meshes
It may also have 3D trees. A 3D mesh is a mesh with more than 1 face. Its Object Properties tab contains the Near and Far LOD settings. By default, vertex weight is 0 (perfectly static trees). Vertex groups may be used to set different weights per vertex, however, if a vertex is in multiple groups only the 1st group's weight will be used.

Multiple 3D meshes may be used and given different LOD ranges.

## Materials
2 materials may be used, 1 for the 2D shader options and another optional for the 3D shader. The use of EEVEE or Cycles is completely optional and all material properties are found under the XPlaneForExporter panel, not in Blender's settings.

# Missing Features
1. SKIP_SURFACE isn't in
2. There aren't a lot of validations
3. Don't be in edit mode and hit export
4. There is an inconsistent use of the logger to give errors vs exceptions just showing up
