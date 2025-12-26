import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvNormalize(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvNormalize'
    bl_label = 'LB Area Normalize'
    sv_icon = 'LB_NORMALIZE'
    sv__data: StringProperty(
        name='_data',
        update=updateNode,
        description='A Data Collection to be normalized by the input _area.')
    sv__area: StringProperty(
        name='_area',
        update=updateNode,
        description='A number representing area by which all of the data is normalized.')
    sv__unit_: StringProperty(
        name='_unit_',
        update=updateNode,
        description='Text for the units that the area value is in. Acceptable inputs include \'m2\', \'ft2\' and any other unit that is supported. (Default: m2).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_data')
        input_node.prop_name = 'sv__data'
        input_node.tooltip = 'A Data Collection to be normalized by the input _area.'
        input_node = self.inputs.new('SvLBSocket', '_area')
        input_node.prop_name = 'sv__area'
        input_node.tooltip = 'A number representing area by which all of the data is normalized.'
        input_node = self.inputs.new('SvLBSocket', '_unit_')
        input_node.prop_name = 'sv__unit_'
        input_node.tooltip = 'Text for the units that the area value is in. Acceptable inputs include \'m2\', \'ft2\' and any other unit that is supported. (Default: m2).'
        output_node = self.outputs.new('SvLBSocket', 'data')
        output_node.tooltip = 'A Ladybug data collection object derived that is normalized by the input area.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Get a Data Collection that is normalized by an area value. _ Note that this component will raise a ValueError if the data type in the header of the data collection is not normalizable to yeild a useful type. Also note that a ZeroDivisionError will be raised if the input area is equal to 0. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['data']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_data', '_area', '_unit_']
        self.sv_input_types = ['System.Object', 'double', 'string']
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

    def process_ladybug(self, _data, _area, _unit_):

        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            unit = _unit_ if _unit_ is not None else 'm2'
            data = _data.normalize_by_area(_area, unit)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvNormalize)

def unregister():
    bpy.utils.unregister_class(SvNormalize)
