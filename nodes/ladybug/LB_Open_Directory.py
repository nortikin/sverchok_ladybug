import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvOpenDir(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvOpenDir'
    bl_label = 'LB Open Directory'
    sv_icon = 'LB_OPENDIR'
    sv__file_path: StringProperty(
        name='_file_path',
        update=updateNode,
        description='Full path to a file or directory to be opened in Explorer/Finder.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_file_path')
        input_node.prop_name = 'sv__file_path'
        input_node.tooltip = 'Full path to a file or directory to be opened in Explorer/Finder.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Open a file\'s directory in Windows Explorer or Mac Finder. This is useful for understanding weather data or simulation files. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = []
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_file_path']
        self.sv_input_types = ['string']
        self.sv_input_defaults = [None]
        self.sv_input_access = ['item']
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

    def process_ladybug(self, _file_path):

        import os
        import subprocess
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # check that the file exists
            assert os.path.exists(_file_path), \
                'No file or directory was found at: {}'.format(_file_path)
            folder = _file_path if os.path.isdir(_file_path) else os.path.dirname(_file_path)
        
            # open the file in explorer or finder
            if os.name == 'nt':  # we are on Windows
                folder = folder.replace('/', '\\')
                subprocess.Popen('explorer.exe ' + folder)
            else:  # assume we are on Mac
                subprocess.call(['open', '-R', _file_path])
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvOpenDir)

def unregister():
    bpy.utils.unregister_class(SvOpenDir)
