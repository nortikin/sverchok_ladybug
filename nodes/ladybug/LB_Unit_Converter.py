import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvUnits(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvUnits'
    bl_label = 'LB Unit Converter'
    sv_icon = 'LB_UNITS'
    sv__values: StringProperty(
        name='_values',
        update=updateNode,
        description='Values to be converted from one unit type to another.')
    sv__from_u: StringProperty(
        name='_from_u',
        update=updateNode,
        description='Text indicating the units of the input _values (eg. \'C\')')
    sv__to_u: StringProperty(
        name='_to_u',
        update=updateNode,
        description='Text indicating the units of the output values (eg. \'K\')')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_values')
        input_node.prop_name = 'sv__values'
        input_node.tooltip = 'Values to be converted from one unit type to another.'
        input_node = self.inputs.new('SvLBSocket', '_from_u')
        input_node.prop_name = 'sv__from_u'
        input_node.tooltip = 'Text indicating the units of the input _values (eg. \'C\')'
        input_node = self.inputs.new('SvLBSocket', '_to_u')
        input_node.prop_name = 'sv__to_u'
        input_node.tooltip = 'Text indicating the units of the output values (eg. \'K\')'
        output_node = self.outputs.new('SvLBSocket', 'all_u')
        output_node.tooltip = 'A text string indicating all possible units that can be plugged into _from_u and _to_u.'
        output_node = self.outputs.new('SvLBSocket', 'values')
        output_node.tooltip = 'The converted numerical values.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Convert a value or list of values from one unit to another. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['all_u', 'values']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_values', '_from_u', '_to_u']
        self.sv_input_types = ['double', 'string', 'string']
        self.sv_input_defaults = [None, None, None]
        self.sv_input_access = ['list', 'item', 'item']
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

    def process_ladybug(self, _values, _from_u, _to_u):

        try:
            import ladybug.datatype
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        all_u = [': '.join([key, ', '.join(val)]) for key, val in list(ladybug.datatype.UNITS.items())]
        
        if all_required_inputs(ghenv.Component):
            base_type = None
            for key in ladybug.datatype.UNITS:
                if _from_u in ladybug.datatype.UNITS[key]:
                    base_type = ladybug.datatype.TYPESDICT[key]()
                    break
            else:
                msg = 'Input _from_u "{}" is not recgonized as a valid unit.\n Check all_u ' \
                '(with nothing connected to the component) to see the acceptable units.'.format(_from_u)
                raise ValueError(msg)
        
            values = base_type.to_unit(_values, _to_u, _from_u)

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvUnits)

def unregister():
    bpy.utils.unregister_class(SvUnits)
