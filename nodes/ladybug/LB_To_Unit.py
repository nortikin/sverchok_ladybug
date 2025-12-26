import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvToUnit(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvToUnit'
    bl_label = 'LB To Unit'
    sv_icon = 'LB_TOUNIT'
    sv__data: StringProperty(
        name='_data',
        update=updateNode,
        description='A DataCollection to be converted to different units.')
    sv_to_unit_: StringProperty(
        name='to_unit_',
        update=updateNode,
        description='Text representing the unit to convert the DataCollection to (eg. m2). Connect the _data and see the all_unit output for a list of all currently-supported units for a given collection. The default won\'t perform any unit conversion on the output data.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_data')
        input_node.prop_name = 'sv__data'
        input_node.tooltip = 'A DataCollection to be converted to different units.'
        input_node = self.inputs.new('SvLBSocket', 'to_unit_')
        input_node.prop_name = 'sv_to_unit_'
        input_node.tooltip = 'Text representing the unit to convert the DataCollection to (eg. m2). Connect the _data and see the all_unit output for a list of all currently-supported units for a given collection. The default won\'t perform any unit conversion on the output data.'
        output_node = self.outputs.new('SvLBSocket', 'all_unit')
        output_node.tooltip = 'A list of all possible units that the input _data can be converted to.'
        output_node = self.outputs.new('SvLBSocket', 'data')
        output_node.tooltip = 'The converted DataCollection.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Convert a DataCollection to the input _to_unit. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['all_unit', 'data']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_data', 'to_unit_']
        self.sv_input_types = ['System.Object', 'string']
        self.sv_input_defaults = [None, None]
        self.sv_input_access = ['item', 'item']
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

    def process_ladybug(self, _data, to_unit_):

        try:
            from ladybug.datacollection import BaseCollection
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            assert isinstance(_data, BaseCollection), \
                '_data must be a Data Collection. Got {}.'.format(type(_data))
            all_unit = _data.header.data_type.units
            data = _data.to_unit(to_unit_) if to_unit_ else _data

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvToUnit)

def unregister():
    bpy.utils.unregister_class(SvToUnit)
