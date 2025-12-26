import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvDumpVisSet(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvDumpVisSet'
    bl_label = 'LB Dump VisualizationSet'
    sv_icon = 'LB_DUMPVISSET'
    sv__vis_set: StringProperty(
        name='_vis_set',
        update=updateNode,
        description='A VisualizationSet object to be written to a file. This can also be VisualizationSet arguments from any Ladybug Tools component with a vis_set output.')
    sv__format_: StringProperty(
        name='_format_',
        update=updateNode,
        description='Text or an integer to set the format of the output file. Choose from the options below. (Default: JSON). * 0 = JSON - Cross-language and handles any types of collections * 1 = PKL - Compressed format only readable with Python')
    sv__name_: StringProperty(
        name='_name_',
        update=updateNode,
        description='A name for the file to which the VisualizationSet will be written. The default is derived from the identifier of the visualization set.')
    sv__folder_: StringProperty(
        name='_folder_',
        update=updateNode,
        description='An optional directory into which the VisualizationSet will be written.  The default is set to a user-specific simulation folder.')
    sv__dump: StringProperty(
        name='_dump',
        update=updateNode,
        description='Set to "True" to save the VisualizationSet to a file.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_vis_set')
        input_node.prop_name = 'sv__vis_set'
        input_node.tooltip = 'A VisualizationSet object to be written to a file. This can also be VisualizationSet arguments from any Ladybug Tools component with a vis_set output.'
        input_node = self.inputs.new('SvLBSocket', '_format_')
        input_node.prop_name = 'sv__format_'
        input_node.tooltip = 'Text or an integer to set the format of the output file. Choose from the options below. (Default: JSON). * 0 = JSON - Cross-language and handles any types of collections * 1 = PKL - Compressed format only readable with Python'
        input_node = self.inputs.new('SvLBSocket', '_name_')
        input_node.prop_name = 'sv__name_'
        input_node.tooltip = 'A name for the file to which the VisualizationSet will be written. The default is derived from the identifier of the visualization set.'
        input_node = self.inputs.new('SvLBSocket', '_folder_')
        input_node.prop_name = 'sv__folder_'
        input_node.tooltip = 'An optional directory into which the VisualizationSet will be written.  The default is set to a user-specific simulation folder.'
        input_node = self.inputs.new('SvLBSocket', '_dump')
        input_node.prop_name = 'sv__dump'
        input_node.tooltip = 'Set to "True" to save the VisualizationSet to a file.'
        output_node = self.outputs.new('SvLBSocket', 'vs_file')
        output_node.tooltip = 'The path of the file where the VisualisationSet is saved. The "LB Preview VisualizationSet" component can be used to visualize the content from the file back into Grasshopper.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Dump a Ladybug VisualiztionSet into a file. _ The "LB Preview VisualizationSet" component can be used to visualize the content from the file back into Grasshopper. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['vs_file']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_vis_set', '_format_', '_name_', '_folder_', '_dump']
        self.sv_input_types = ['System.Object', 'string', 'string', 'string', 'bool']
        self.sv_input_defaults = [None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _vis_set, _format_, _name_, _folder_, _dump):

        import os
        
        try:
            from ladybug.config import folders
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:  # import the core ladybug_tools dependencies
            from ladybug_tools.visset import process_vis_set
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        FORMAT_MAP = {
            '0': 'json',
            '1': 'pkl',
            'json': 'json',
            'pkl': 'pkl'
        }
        
        
        if all_required_inputs(ghenv.Component) and _dump:
            # extract the VisualizationSet object
            _vs = process_vis_set(_vis_set)
        
            # set the component defaults
            name = _name_ if _name_ is not None else _vs.identifier
            home_folder = os.getenv('HOME') or os.path.expanduser('~')
            folder = _folder_ if _folder_ is not None else \
                os.path.join(home_folder, 'simulation')
            file_format = 'json' if _format_ is None else FORMAT_MAP[_format_.lower()]
        
            # write the data into the appropriate format
            if file_format == 'json':
                vs_file = _vs.to_json(name, folder)
            elif file_format == 'pkl':
                vs_file = _vs.to_pkl(name, folder)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvDumpVisSet)

def unregister():
    bpy.utils.unregister_class(SvDumpVisSet)
