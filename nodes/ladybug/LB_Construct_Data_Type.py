import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvConstrType(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvConstrType'
    bl_label = 'LB Construct Data Type'
    sv_icon = 'LB_CONSTRTYPE'
    sv__name: StringProperty(
        name='_name',
        update=updateNode,
        description='A name for the data type as a string.')
    sv__unit: StringProperty(
        name='_unit',
        update=updateNode,
        description='A unit for the data type as a string.')
    sv_cumulative_: StringProperty(
        name='cumulative_',
        update=updateNode,
        description='Boolean to tell whether the data type can be cumulative when it is represented over time (True) or it can only be averaged over time to be meaningful (False).')
    sv_categories_: StringProperty(
        name='categories_',
        update=updateNode,
        description='An optional list of text for categories to be associated with the data type. These categories will show up in the legend whenever data with this data type is visualized. The input should be text strings with a category number (integer) and name separated by a colon. For example: _ .    -1: Cold .     0: Neutral .     1: Hot')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_name')
        input_node.prop_name = 'sv__name'
        input_node.tooltip = 'A name for the data type as a string.'
        input_node = self.inputs.new('SvLBSocket', '_unit')
        input_node.prop_name = 'sv__unit'
        input_node.tooltip = 'A unit for the data type as a string.'
        input_node = self.inputs.new('SvLBSocket', 'cumulative_')
        input_node.prop_name = 'sv_cumulative_'
        input_node.tooltip = 'Boolean to tell whether the data type can be cumulative when it is represented over time (True) or it can only be averaged over time to be meaningful (False).'
        input_node = self.inputs.new('SvLBSocket', 'categories_')
        input_node.prop_name = 'sv_categories_'
        input_node.tooltip = 'An optional list of text for categories to be associated with the data type. These categories will show up in the legend whenever data with this data type is visualized. The input should be text strings with a category number (integer) and name separated by a colon. For example: _ .    -1: Cold .     0: Neutral .     1: Hot'
        output_node = self.outputs.new('SvLBSocket', 'type')
        output_node.tooltip = 'A Ladybug DataType object that can be assigned to the header of a Ladybug DataCollection.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Construct a Ladybug DataType to be used in the header of a ladybug DataCollection. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['type']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_name', '_unit', 'cumulative_', 'categories_']
        self.sv_input_types = ['string', 'string', 'bool', 'string']
        self.sv_input_defaults = [None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'list']
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

    def process_ladybug(self, _name, _unit, cumulative_, categories_):

        try:
            from ladybug.datatype.generic import GenericType
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # process the categories_ if they are supplied
            unit_descr = None
            if categories_ != []:
                unit_descr = {}
                for prop in categories_:
                    key, value = prop.split(':')
                    unit_descr[int(key)] = value.strip()
        
            if cumulative_:
                type = GenericType(_name, _unit, unit_descr=unit_descr,
                                   point_in_time=False, cumulative=True)
            else:
                type = GenericType(_name, _unit, unit_descr=unit_descr)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvConstrType)

def unregister():
    bpy.utils.unregister_class(SvConstrType)
