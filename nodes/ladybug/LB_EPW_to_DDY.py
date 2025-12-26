import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvEPWtoDDY(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvEPWtoDDY'
    bl_label = 'LB EPW to DDY'
    sv_icon = 'LB_EPWTODDY'
    sv__weather_file: StringProperty(
        name='_weather_file',
        update=updateNode,
        description='The path to an .epw file or .stat file on your system, from which a .ddy will be generated.')
    sv__percentile_: StringProperty(
        name='_percentile_',
        update=updateNode,
        description='A number between 0 and 50 for the percentile difference from the most extreme conditions within the EPW or STAT to be used for the design day. Typical values are 0.4 and 1.0. (Default: 0.4).')
    sv_monthly_cool_: StringProperty(
        name='monthly_cool_',
        update=updateNode,
        description='A boolean to note whether the resulting .ddy file should contain twelve cooling design days for each of the months of the year. This type of DDY file is useful when the peak cooling might not be driven by warm outdoor temperatures but instead by the highest-intensity solar condition, which may not conincide with the highest temperature. Monthly conditions will be for the 2.0% hottest conditions in each month, which generally aligns with the annual 0.4% cooling design conditions.')
    sv__folder_: StringProperty(
        name='_folder_',
        update=updateNode,
        description='An optional file path to a directory into which the DDY file will be written.  If None, the DDY file will be written to the ladybug default weather data folder and placed in a sub-folder called "ddy".')
    sv__write: StringProperty(
        name='_write',
        update=updateNode,
        description='Set to "True" to write the .ddy file.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_weather_file')
        input_node.prop_name = 'sv__weather_file'
        input_node.tooltip = 'The path to an .epw file or .stat file on your system, from which a .ddy will be generated.'
        input_node = self.inputs.new('SvLBSocket', '_percentile_')
        input_node.prop_name = 'sv__percentile_'
        input_node.tooltip = 'A number between 0 and 50 for the percentile difference from the most extreme conditions within the EPW or STAT to be used for the design day. Typical values are 0.4 and 1.0. (Default: 0.4).'
        input_node = self.inputs.new('SvLBSocket', 'monthly_cool_')
        input_node.prop_name = 'sv_monthly_cool_'
        input_node.tooltip = 'A boolean to note whether the resulting .ddy file should contain twelve cooling design days for each of the months of the year. This type of DDY file is useful when the peak cooling might not be driven by warm outdoor temperatures but instead by the highest-intensity solar condition, which may not conincide with the highest temperature. Monthly conditions will be for the 2.0% hottest conditions in each month, which generally aligns with the annual 0.4% cooling design conditions.'
        input_node = self.inputs.new('SvLBSocket', '_folder_')
        input_node.prop_name = 'sv__folder_'
        input_node.tooltip = 'An optional file path to a directory into which the DDY file will be written.  If None, the DDY file will be written to the ladybug default weather data folder and placed in a sub-folder called "ddy".'
        input_node = self.inputs.new('SvLBSocket', '_write')
        input_node.prop_name = 'sv__write'
        input_node.tooltip = 'Set to "True" to write the .ddy file.'
        output_node = self.outputs.new('SvLBSocket', 'ddy_file')
        output_node.tooltip = 'A .ddy file path that has been written to your system.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Produce a DDY file from the data contained within an EPW or STAT file. _ For EPW files, this method will first check if there is any heating or cooling design day information contained within the EPW itself. If None is found, the heating and cooling design days will be derived from analysis of the annual data within the EPW. This process of analyzing the annual TMY data is less representative of the climate since only one year of data is used to derive the DDY (instead of the usual multi-year analysis). However, if the EPW is the best available representation of the climate for a given site, it can often be preferable to using a DDY constructed with more years of data but from further away. Information on the uncertainty introduced by using only one year of data to create design days can be found in AHSRAE HOF 2013, Chapter 14.14. _ For STAT files, the DDY file will only be produced if the design day information is found within the file. If no information on the relevant design days are found, and error will be raised and the component will fail to run. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['ddy_file']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_weather_file', '_percentile_', 'monthly_cool_', '_folder_', '_write']
        self.sv_input_types = ['string', 'double', 'bool', 'string', 'bool']
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

    def process_ladybug(self, _weather_file, _percentile_, monthly_cool_, _folder_, _write):

        import os
        
        try:
            from ladybug.epw import EPW
            from ladybug.stat import STAT
            from ladybug.config import folders
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component) and _write:
            # set default values
            _percentile_ = 0.4 if _percentile_ is None else _percentile_
            _folder_ = os.path.join(folders.default_epw_folder, 'ddy') if _folder_ \
                is None else _folder_
            if _weather_file.lower().endswith('.epw'):
                f_name = os.path.basename(_weather_file.lower()).replace('.epw', '.ddy')
                epw_data = True
            elif _weather_file.lower().endswith('.stat'):
                f_name = os.path.basename(_weather_file.lower()).replace('.stat', '.ddy')
                epw_data = False
            else:
                raise ValueError('Failed to recognize the file type of "{}".\n'
                                 'Must end in .epw or .stat.'.format(_weather_file))
            f_path = os.path.join(_folder_, f_name)
        
            # create the DDY file
            if epw_data:
                epw = EPW(_weather_file)
                ddy_file = epw.to_ddy_monthly_cooling(f_path, _percentile_, 2) \
                    if monthly_cool_ else epw.to_ddy(f_path, _percentile_)
            else:
                stat = STAT(_weather_file)
                ddy_file = stat.to_ddy_monthly_cooling(f_path, _percentile_, 2) \
                    if monthly_cool_ else stat.to_ddy(f_path, _percentile_)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvEPWtoDDY)

def unregister():
    bpy.utils.unregister_class(SvEPWtoDDY)
