import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvLoadData(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvLoadData'
    bl_label = 'LB Load Data'
    sv_icon = 'LB_LOADDATA'
    sv__data_file: StringProperty(
        name='_data_file',
        update=updateNode,
        description='A file path to a CSV, JSON or PKL file from which data collections will be loaded.')
    sv__load: StringProperty(
        name='_load',
        update=updateNode,
        description='Set to "True" to load the data collections from the _data_file.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_data_file')
        input_node.prop_name = 'sv__data_file'
        input_node.tooltip = 'A file path to a CSV, JSON or PKL file from which data collections will be loaded.'
        input_node = self.inputs.new('SvLBSocket', '_load')
        input_node.prop_name = 'sv__load'
        input_node.tooltip = 'Set to "True" to load the data collections from the _data_file.'
        output_node = self.outputs.new('SvLBSocket', 'data')
        output_node.tooltip = 'A list of honeybee objects that have been re-serialized from the input file.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Load Ladybug data collections from a CSV, JSON, or PKL file. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['data']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_data_file', '_load']
        self.sv_input_types = ['string', 'bool']
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

    def process_ladybug(self, _data_file, _load):

        try:
            from ladybug.datautil import collections_from_csv, collections_from_json, \
                collections_from_pkl
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:  # import the core ladybug_tools dependencies
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component) and _load:
            # load the data from the appropriate format
            lower_file = _data_file.lower()
            if lower_file.endswith('.csv'):
                data = collections_from_csv(_data_file)
            elif lower_file.endswith('.json'):
                data = collections_from_json(_data_file)
            elif lower_file.endswith('.pkl'):
                data = collections_from_pkl(_data_file)
            else:
                raise ValueError(
                    'Could not recognize the file extension of: {}'.format(_data_file))
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvLoadData)

def unregister():
    bpy.utils.unregister_class(SvLoadData)
