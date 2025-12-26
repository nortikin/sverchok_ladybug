import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvMassArithOp(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvMassArithOp'
    bl_label = 'LB Mass Arithmetic Operation'
    sv_icon = 'LB_MASSARITHOP'
    sv__data: StringProperty(
        name='_data',
        update=updateNode,
        description='A list of Data Collections to be used in the arithmetic operation.')
    sv__operator_: StringProperty(
        name='_operator_',
        update=updateNode,
        description='Text for the operator to use between the Data Collections. Valid examples include (+, -, *, /). By default this is + for addition.')
    sv_type_: StringProperty(
        name='type_',
        update=updateNode,
        description='Optional text for a new "type" key in the Data Collection\'s metadata. This will usually show up in most Ladybug visualiztions and it should usually change for most types of operations.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_data')
        input_node.prop_name = 'sv__data'
        input_node.tooltip = 'A list of Data Collections to be used in the arithmetic operation.'
        input_node = self.inputs.new('SvLBSocket', '_operator_')
        input_node.prop_name = 'sv__operator_'
        input_node.tooltip = 'Text for the operator to use between the Data Collections. Valid examples include (+, -, *, /). By default this is + for addition.'
        input_node = self.inputs.new('SvLBSocket', 'type_')
        input_node.prop_name = 'sv_type_'
        input_node.tooltip = 'Optional text for a new "type" key in the Data Collection\'s metadata. This will usually show up in most Ladybug visualiztions and it should usually change for most types of operations.'
        output_node = self.outputs.new('SvLBSocket', 'data')
        output_node.tooltip = 'A Ladybug data collection object derived from the operation between the two data inputs.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Perform a "mass" arithmetic operation between Data Collections. For example, adding a list of Data Collections into one Data Collection. - Note that Data Collections must be aligned in order for this component to run successfully. - Using this component will often be much faster and more elegant compared to deconstructing the data collection, performing the operation with native Grasshopper components, and rebuilding the collection. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['data']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_data', '_operator_', 'type_']
        self.sv_input_types = ['System.Object', 'string', 'string']
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

    def process_ladybug(self, _data, _operator_, type_):

        try:
            import ladybug.datatype
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # build the arithmetic statement
            operator = '+' if _operator_ is None else _operator_
            statement = 'data {} data_i'.format(operator)
        
            # perform the arithmetic operation
            data = _data[0]
            for data_i in _data[1:]:
                data = eval(statement, {'data': data, 'data_i': data_i})  # I love Python!
        
            # try to replace the data collection type
            try:
                data = data.duplicate()
                if type_:
                    data.header.metadata['type'] = type_
                elif 'type' in data.header.metadata:
                    d_unit = data.header.unit
                    for key in ladybug.datatype.UNITS:
                        if d_unit in ladybug.datatype.UNITS[key]:
                            base_type = ladybug.datatype.TYPESDICT[key]()
                            data.header.metadata['type'] = str(base_type)
                            break
                    else:
                        data.header.metadata['type'] = 'Unknown Data Type'
                if 'System' in data.header.metadata:
                    data.header.metadata.pop('System')
                if 'Zone' in data.header.metadata:
                    data.header.metadata.pop('Zone')
            except AttributeError:
                pass  # data was not a data collection; just return it anyway

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvMassArithOp)

def unregister():
    bpy.utils.unregister_class(SvMassArithOp)
