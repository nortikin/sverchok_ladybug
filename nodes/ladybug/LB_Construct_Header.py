import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvConstrHeader(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvConstrHeader'
    bl_label = 'LB Construct Header'
    sv_icon = 'LB_CONSTRHEADER'
    sv__data_type: StringProperty(
        name='_data_type',
        update=updateNode,
        description='Text representing the type of data (e.g. Temperature). A full list of acceptable inputs can be seen by checking the all_u output of the "LB Unit Converter" component. This input can also be a custom DataType object that has been created with the "LB Construct Data Type" component.')
    sv__unit_: StringProperty(
        name='_unit_',
        update=updateNode,
        description='Units of the data_type (e.g. C). Default is to use the base unit of the connected_data_type.')
    sv__a_period_: StringProperty(
        name='_a_period_',
        update=updateNode,
        description='Script variable constrData')
    sv_metadata_: StringProperty(
        name='metadata_',
        update=updateNode,
        description='Optional metadata to be associated with the Header. The input should be a list of text strings with a property name and value for the property separated by a colon. For example: _ .    source: TMY .    city: New York .    country: USA')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_data_type')
        input_node.prop_name = 'sv__data_type'
        input_node.tooltip = 'Text representing the type of data (e.g. Temperature). A full list of acceptable inputs can be seen by checking the all_u output of the "LB Unit Converter" component. This input can also be a custom DataType object that has been created with the "LB Construct Data Type" component.'
        input_node = self.inputs.new('SvLBSocket', '_unit_')
        input_node.prop_name = 'sv__unit_'
        input_node.tooltip = 'Units of the data_type (e.g. C). Default is to use the base unit of the connected_data_type.'
        input_node = self.inputs.new('SvLBSocket', '_a_period_')
        input_node.prop_name = 'sv__a_period_'
        input_node.tooltip = 'Script variable constrData'
        input_node = self.inputs.new('SvLBSocket', 'metadata_')
        input_node.prop_name = 'sv_metadata_'
        input_node.tooltip = 'Optional metadata to be associated with the Header. The input should be a list of text strings with a property name and value for the property separated by a colon. For example: _ .    source: TMY .    city: New York .    country: USA'
        output_node = self.outputs.new('SvLBSocket', 'header')
        output_node.tooltip = 'A Ladybug Header object.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Construct a Ladybug Header to be used to create a ladybug DataCollection. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['header']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_data_type', '_unit_', '_a_period_', 'metadata_']
        self.sv_input_types = ['System.Object', 'string', 'System.Object', 'string']
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

    def process_ladybug(self, _data_type, _unit_, _a_period_, metadata_):

        try:
            import ladybug.datatype
            from ladybug.datatype.base import DataTypeBase
            from ladybug.header import Header
            from ladybug.analysisperiod import AnalysisPeriod
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        # error message if the data type is not recognized
        msg = 'The connected _data_type is not recognized.\nMake your own with ' \
            'the "LB Construct Data Type" component or choose from the following:' \
            '\n{}'.format('\n'.join(ladybug.datatype.BASETYPES))
        
        
        if all_required_inputs(ghenv.Component):
            if isinstance(_data_type, DataTypeBase):
                pass
            elif isinstance(_data_type, str):
                _data_type = _data_type.replace(' ', '')
                try:
                    _data_type = ladybug.datatype.TYPESDICT[_data_type]()
                except KeyError:  # check to see if it's a captilaization issue
                    _data_type = _data_type.lower()
                    for key in ladybug.datatype.TYPESDICT:
                        if key.lower() == _data_type:
                            _data_type = ladybug.datatype.TYPESDICT[key]()
                            break
                    else:
                        raise TypeError(msg)
            else:
                raise TypeError(msg)
        
            if _unit_ is None:
                _unit_ = _data_type.units[0]
        
            if _a_period_ is None:
                _a_period_ = AnalysisPeriod()
        
            metadata_dict = {}
            if metadata_ != []:
                for prop in metadata_:
                    key, value = prop.split(':')
                    metadata_dict[key] = value.strip()
        
            header = Header(_data_type, _unit_, _a_period_, metadata_dict)

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvConstrHeader)

def unregister():
    bpy.utils.unregister_class(SvConstrHeader)
