import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvStatement(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvStatement'
    bl_label = 'LB Apply Conditional Statement'
    sv_icon = 'LB_STATEMENT'
    sv__data: StringProperty(
        name='_data',
        update=updateNode,
        description='A list of aligned Data Collections to be evaluated against the _statement.')
    sv__statement: StringProperty(
        name='_statement',
        update=updateNode,
        description='A conditional statement as a string (e.g. a > 25). _ The variable of the first data collection should always be named \'a\' (without quotations), the variable of the second list should be named \'b\', and so on. _ For example, if three data collections are connected to _data and the following statement is applied: \'18 < a < 26 and b < 80 and c > 2\' The resulting collections will only include values where the first data collection is between 18 and 26, the second collection is less than 80 and the third collection is greater than 2.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_data')
        input_node.prop_name = 'sv__data'
        input_node.tooltip = 'A list of aligned Data Collections to be evaluated against the _statement.'
        input_node = self.inputs.new('SvLBSocket', '_statement')
        input_node.prop_name = 'sv__statement'
        input_node.tooltip = 'A conditional statement as a string (e.g. a > 25). _ The variable of the first data collection should always be named \'a\' (without quotations), the variable of the second list should be named \'b\', and so on. _ For example, if three data collections are connected to _data and the following statement is applied: \'18 < a < 26 and b < 80 and c > 2\' The resulting collections will only include values where the first data collection is between 18 and 26, the second collection is less than 80 and the third collection is greater than 2.'
        output_node = self.outputs.new('SvLBSocket', 'data')
        output_node.tooltip = 'A list of Data Collections that have been filtered by the statement_.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Apply a conditional statement to a data collection. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['data']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_data', '_statement']
        self.sv_input_types = ['System.Object', 'string']
        self.sv_input_defaults = [None, None]
        self.sv_input_access = ['list', 'item']
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

    def process_ladybug(self, _data, _statement):

        try:
            from ladybug.datacollection import BaseCollection
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            for dat in _data:
                assert isinstance(dat, BaseCollection), '_data must be a data' \
                    ' collection. Got {}.'.format(type(dat))
        
            data = BaseCollection.filter_collections_by_statement(
                _data, _statement)

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvStatement)

def unregister():
    bpy.utils.unregister_class(SvStatement)
