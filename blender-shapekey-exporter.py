import bpy
from bpy.props import *
from bpy.types import Scene
from bpy_extras.io_utils import ExportHelper, ImportHelper
from mathutils import Vector
import json
import operator


bl_info = {
    "name" : "Shapekey Exporter",
    "author" : "Blender Newbie",
    'category': 'Import-Export',
    'location': 'View 3D > Tool Shelf > Shapekey Exporter',
    'description': 'Experimental shapekey export/import tool based on https://github.com/Narazaka/blender-shapekey-exporter/issues by Narazaka',
    "version" : (0, 3, 0),
    "blender" : (2, 79, 0),
    'tracker_url': 'https://github.com/BlenderNewbie2020/blender-shapekey-exporter/issues',
}


class ShapekeyExporter_PT_Main(bpy.types.Panel):
    bl_idname = "shapekey_exporter.main"
    bl_label = "Shapekey Exporter"
    bl_category = "ShapekeyExporter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_context = "objectmode"

    def draw(self, context):
        self.layout.operator(ShapekeyExporter_OT_Export.bl_idname)
        self.layout.operator(ShapekeyExporter_OT_Import.bl_idname)
        return None


class ShapekeyExporter_OT_Export(bpy.types.Operator, ExportHelper):
    ''' Create a json file of shapekeys for the active mesh object '''
    bl_idname = "shapekey_exporter.export"
    bl_label = "Export"
    bl_options = {'REGISTER'}

    filename_ext = ".skx.json"
    filter_glob = StringProperty(
            default="*.skx.json",
            options={'HIDDEN'},
            )

    def execute(self, context):
        if self.filepath == "":
            return {'FINISHED'}

        obj = bpy.context.object
        if obj.type != 'MESH' or not obj.data.shape_keys:
            raise RuntimeError("No active mesh with shape keys")

        shapekeys = obj.data.shape_keys
        basis_name = shapekeys.reference_key.name
        shapekey_names = [s for i, s in enumerate(shapekeys.key_blocks.keys())]

        # create a dictionary of [ vector values ] for each shapekey
        shapekey_vectors = {k.name: [item.co for item in k.data.values()] for k in shapekeys.key_blocks}

        # create a dictionary of [ deltas for all vectors ] for each shapekey
        shapekey_deltas = {k: [tuple(a - b) for a, b in zip(shapekey_vectors[k], shapekey_vectors[basis_name])] for k in shapekey_names if k != basis_name}

        with open(self.filepath, mode='w', encoding="utf8") as f:
            json.dump(shapekey_deltas, f, sort_keys=True, indent='', ensure_ascii=False)

        return {'FINISHED'}


class ShapekeyExporter_OT_Import(bpy.types.Operator, ImportHelper):
    ''' Import shape keys from a json file for the active mesh object '''
    bl_idname = "shapekey_exporter.import"
    bl_label = "Import"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".skx.json"

    filter_glob = StringProperty(
            default="*.skx.json",
            options={'HIDDEN'},
            )

    def execute(self, context):
        obj = bpy.context.object
        if obj.type != 'MESH':
            raise RuntimeError("Object is not a mesh")

        # deltas is a dictionary of shapekey tuples
        with open(self.filepath, mode='r', encoding="utf8") as f:
            deltas = json.load(f)

        # ensure basis key
        if not obj.data.shape_keys:
            obj.shape_key_add(name = 'basis')

        shapekeys = obj.data.shape_keys
        shapekey_blocks = shapekeys.key_blocks

        basis_block = shapekeys.reference_key
        basis_name = shapekeys.reference_key.name
        basis_vectors = [item.co for item in basis_block.data.values()]

        delta_names = [s for i, s in enumerate(deltas)]

        for shapekey in delta_names:
            if not shapekey_blocks.get(shapekey):
               key = obj.shape_key_add(name=shapekey, from_mix=False)

            if len(deltas[shapekey]) != len(basis_vectors):
                raise RuntimeError("mesh vertex count is different: " + shapekey)

            ''' use one of
            # first, convert [ lists to vectors ]
            key_vectors = [Vector(vec) for vec in deltas[shapekey]]
            timeit.timeit(lambda: '[a + b for a, b in zip(key_vectors, basis_vectors)]', number=1000)
            key_values = [a + b for a, b in zip(key_vectors, basis_vectors)]

            # or, map an operator
            timeit.timeit(lambda: '[Vector(map(operator.add, a, b)) for a, b in zip(deltas[shapekey], basis_vectors)]', number=1000)
            key_values = [Vector(map(operator.add, a, b)) for a, b in zip(deltas[shapekey], basis_vectors)]

            # or, just map
            timeit.timeit(lambda: '[Vector(map(float.__add__, a, b)) for a, b in zip(deltas[shapekey], basis_vectors)]', number=1000)
            key_values = [Vector(map(float.__add__, a, b)) for a, b in zip(deltas[shapekey], basis_vectors)]
            '''

            key_values = [Vector(map(float.__add__, a, b)) for a, b in zip(deltas[shapekey], basis_vectors)]
            for i in range(len(key_values)):
                shapekey_blocks[shapekey].data[i].co = key_values[i]

        return {'FINISHED'}


classes = (
    ShapekeyExporter_PT_Main,
    ShapekeyExporter_OT_Export,
    ShapekeyExporter_OT_Import,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
