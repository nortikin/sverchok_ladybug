import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvXMatrix(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvXMatrix'
    bl_label = 'LB Deconstruct Matrix'
    sv_icon = 'LB_XMATRIX'
    sv__matrix: StringProperty(
        name='_matrix',
        update=updateNode,
        description='A Ladybug Matrix object such as the intersection matrices output from any of the ray-tracing components (eg. "LB Direct Sun Hours").')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_matrix')
        input_node.prop_name = 'sv__matrix'
        input_node.tooltip = 'A Ladybug Matrix object such as the intersection matrices output from any of the ray-tracing components (eg. "LB Direct Sun Hours").'
        output_node = self.outputs.new('SvLBSocket', 'values')
        output_node.tooltip = 'The numerical values of the matrix as a Grasshopper Data Tree.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Deconstruct a Ladybug Matrix object into a Grasshopper Data Tree of values. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['values']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_matrix']
        self.sv_input_types = ['System.Object']
        self.sv_input_defaults = [None]
        self.sv_input_access = ['list']
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

    def process_ladybug(self, _matrix):

        try:
            from ladybug_tools.sverchok import all_required_inputs, de_objectify_output, \
                list_to_data_tree, merge_data_tree
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            values = []
            for i, mtx in enumerate(_matrix):
                values.append(list_to_data_tree(de_objectify_output(mtx), root_count=i))
            values = merge_data_tree(values)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvXMatrix)

def unregister():
    bpy.utils.unregister_class(SvXMatrix)
