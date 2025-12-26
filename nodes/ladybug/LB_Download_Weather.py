import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvDownloadEPW(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvDownloadEPW'
    bl_label = 'LB Download Weather'
    sv_icon = 'LB_DOWNLOADEPW'
    sv__weather_URL: StringProperty(
        name='_weather_URL',
        update=updateNode,
        description='Text representing the URL at which the climate data resides.  To open the a map interface for all publicly availabe climate data, use the "LB EPWmap" component.')
    sv__folder_: StringProperty(
        name='_folder_',
        update=updateNode,
        description='An optional file path to a directory into which the weather file will be downloaded and unziped.  If None, the weather files will be downloaded to the ladybug default weather data folder and placed in a sub-folder with the name of the weather file location.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_weather_URL')
        input_node.prop_name = 'sv__weather_URL'
        input_node.tooltip = 'Text representing the URL at which the climate data resides.  To open the a map interface for all publicly availabe climate data, use the "LB EPWmap" component.'
        input_node = self.inputs.new('SvLBSocket', '_folder_')
        input_node.prop_name = 'sv__folder_'
        input_node.tooltip = 'An optional file path to a directory into which the weather file will be downloaded and unziped.  If None, the weather files will be downloaded to the ladybug default weather data folder and placed in a sub-folder with the name of the weather file location.'
        output_node = self.outputs.new('SvLBSocket', 'epw_file')
        output_node.tooltip = 'The file path of the downloaded epw file.'
        output_node = self.outputs.new('SvLBSocket', 'stat_file')
        output_node.tooltip = 'The file path of the downloaded stat file.'
        output_node = self.outputs.new('SvLBSocket', 'ddy_file')
        output_node.tooltip = 'The file path of the downloaded ddy file.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Automatically download a .zip file from a URL where climate data resides, unzip the file, and open .epw, .stat, and ddy weather files. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['epw_file', 'stat_file', 'ddy_file']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_weather_URL', '_folder_']
        self.sv_input_types = ['string', 'string']
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

    def process_ladybug(self, _weather_URL, _folder_):

        import os
        
        try:
            from ladybug.futil import unzip_file
            from ladybug.config import folders
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.download import download_file
            from ladybug_tools.sverchok import all_required_inputs, give_warning
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # process the URL and check if it is outdated
            _weather_URL = _weather_URL.strip()
            if _weather_URL.lower().endswith('.zip'):  # onebuilding URL type
                _folder_name = _weather_URL.split('/')[-1][:-4]
            else: # dept of energy URL type
                _folder_name = _weather_URL.split('/')[-2]
                if _weather_URL.endswith('/all'):
                    repl_section = '{0}/all'.format(_folder_name)
                    new_section = '{0}/{0}.zip'.format(_folder_name)
                    _weather_URL = _weather_URL.replace(repl_section, new_section)
                    _weather_URL = _weather_URL.replace(
                        'www.energyplus.net/weather-download',
                        'energyplus-weather.s3.amazonaws.com')
                    _weather_URL = _weather_URL.replace(
                        'energyplus.net/weather-download',
                        'energyplus-weather.s3.amazonaws.com')
                    _weather_URL = _weather_URL[:8] + _weather_URL[8:].replace('//', '/')
                    msg = 'The weather file URL is out of date.\nThis component ' \
                        'is automatically updating it to the newer version:'
                    print(msg)
                    print(_weather_URL)
                    give_warning(ghenv.Component, msg)
                    give_warning(ghenv.Component, _weather_URL)
        
            # create default working_dir
            if _folder_ is None:
                _folder_ = folders.default_epw_folder
            print(('Files will be downloaded to: {}'.format(_folder_)))
        
            # default file names
            epw = os.path.join(_folder_, _folder_name, _folder_name + '.epw')
            stat = os.path.join(_folder_, _folder_name, _folder_name + '.stat')
            ddy = os.path.join(_folder_, _folder_name, _folder_name + '.ddy')
        
            # download and unzip the files if they do not exist
            if not os.path.isfile(epw) or not os.path.isfile(stat) or not os.path.isfile(ddy):
                zip_file_path = os.path.join(_folder_, _folder_name, _folder_name + '.zip')
                download_file(_weather_URL, zip_file_path, True)
                unzip_file(zip_file_path)
        
            # set output
            epw_file, stat_file, ddy_file = epw, stat, ddy

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvDownloadEPW)

def unregister():
    bpy.utils.unregister_class(SvDownloadEPW)
