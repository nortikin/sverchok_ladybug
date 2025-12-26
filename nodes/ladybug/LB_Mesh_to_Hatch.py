import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvHatch(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvHatch'
    bl_label = 'LB Mesh to Hatch'
    sv_icon = 'LB_HATCH'
    sv__mesh: StringProperty(
        name='_mesh',
        update=updateNode,
        description='A colored mesh (or list of colored meshes) to be baked into the Rhino scene as groups of colored hatches.')
    sv_layer_: StringProperty(
        name='layer_',
        update=updateNode,
        description='Text for the layer name on which the hatch will be added. If unspecified, it will be baked onto the currently active layer.')
    sv__run: StringProperty(
        name='_run',
        update=updateNode,
        description='Set to \'True\' to bake the mesh into the scene as hatches.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_mesh')
        input_node.prop_name = 'sv__mesh'
        input_node.tooltip = 'A colored mesh (or list of colored meshes) to be baked into the Rhino scene as groups of colored hatches.'
        input_node = self.inputs.new('SvLBSocket', 'layer_')
        input_node.prop_name = 'sv_layer_'
        input_node.tooltip = 'Text for the layer name on which the hatch will be added. If unspecified, it will be baked onto the currently active layer.'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to \'True\' to bake the mesh into the scene as hatches.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Bake a clored mesh into the Rhino scene as a group of colored hatches. _ This is useful when exporting ladybug graphics from Rhino to vector-based programs like Inkscape or Illustrator since hatches are exported from Rhino as colored-filled polygons. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = []
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_mesh', 'layer_', '_run']
        self.sv_input_types = ['Mesh', 'string', 'bool']
        self.sv_input_defaults = [None, None, None]
        self.sv_input_access = ['item', 'item', 'item']
        sv_inputs_nested = []
        for name in self.sv_input_names:
            sv_inputs_nested.append(self.inputs[name].sv_get())
        for sv_input_nested in zip_long_repeat(*sv_inputs_nested):
            for sv_input in zip_long_repeat(*sv_input_nested):
                sv_input = list(sv_input)
                for i, value in enumerate(sv_input):
                    if self.sv_input_access[i] == 'list':
                        if isinstance(value, (list, tuple)):
                            values = value
                        else:
                            values = [value]
                        value = [self.sv_cast(v, self.sv_input_types[i], self.sv_input_defaults[i]) for v in values]
                        if value == [None]:
                            value = []
                        sv_input[i] = value
                    else:
                        sv_input[i] = self.sv_cast(value, self.sv_input_types[i], self.sv_input_defaults[i])
                self.process_ladybug(*sv_input)
        for name in self.sv_output_names:
            value = getattr(self, '{}_out'.format(name))
            # Not sure if this hack is correct, will find out when more nodes are generated
            #if len(value) == 0 or not isinstance(value[0], (list, tuple)):
            #    value = [value]
            self.outputs[name].sv_set(value)

    def sv_cast(self, value, data_type, default):
        result = default if isinstance(value, str) and value == '' else value
        if result is None and data_type == 'bool':
            return False
        elif result is not None and data_type == 'bool':
            if result == 'True' or result == '1':
                return True
            elif result == 'False' or result == '0':
                return False
            return bool(result)
        elif result is not None and data_type == 'int':
            return int(result)
        elif result is not None and data_type == 'double':
            return float(result)
        return result

    def process_ladybug(self, _mesh, layer_, _run):

        
        try:
            from ladybug_tools.togeometry import to_mesh3d
            from ladybug_tools.bakegeometry import bake_mesh3d_as_hatch
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component) and _run:
            lb_mesh = to_mesh3d(_mesh, color_by_face=False)
            bake_mesh3d_as_hatch(lb_mesh, layer_)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvHatch)

def unregister():
    bpy.utils.unregister_class(SvHatch)
