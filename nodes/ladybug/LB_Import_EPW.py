import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvImportEPW(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvImportEPW'
    bl_label = 'LB Import EPW'
    sv_icon = 'LB_IMPORTEPW'
    sv__epw_file: StringProperty(
        name='_epw_file',
        update=updateNode,
        description='An .epw file path on your system as a string.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_epw_file')
        input_node.prop_name = 'sv__epw_file'
        input_node.tooltip = 'An .epw file path on your system as a string.'
        output_node = self.outputs.new('SvLBSocket', 'location')
        output_node.tooltip = 'A Ladybug Location object describing the location data in the weather file.'
        output_node = self.outputs.new('SvLBSocket', 'dry_bulb_temperature')
        output_node.tooltip = 'The houlry dry bulb temperature, in C. Note that this is a full numeric field (i.e. 23.6) and not an integer representation with tenths. Valid values range from 70 C to 70 C. Missing value for this field is 99.9.'
        output_node = self.outputs.new('SvLBSocket', 'dew_point_temperature')
        output_node.tooltip = 'The hourly dew point temperature, in C. Note that this is a full numeric field (i.e. 23.6) and not an integer representation with tenths. Valid values range from 70 C to 70 C. Missing value for this field is 99.9.'
        output_node = self.outputs.new('SvLBSocket', 'relative_humidity')
        output_node.tooltip = 'The hourly Relative Humidity in percent. Valid values range from 0% to 110%. Missing value for this field is 999.'
        output_node = self.outputs.new('SvLBSocket', 'wind_speed')
        output_node.tooltip = 'The hourly wind speed in m/sec. Values can range from 0 to 40. Missing value is 999.'
        output_node = self.outputs.new('SvLBSocket', 'wind_direction')
        output_node.tooltip = 'The hourly wind direction in degrees. The convention is North=0.0, East=90.0, South=180.0, West=270.0. If wind is calm for the given hour, the direction equals zero. Values can range from 0 to 360. Missing value is 999.'
        output_node = self.outputs.new('SvLBSocket', 'direct_normal_rad')
        output_node.tooltip = 'The hourly Direct Normal Radiation in Wh/m2. Direc Normal Radiation is the amount of solar radiation in Wh/m2 received directly from the solar disk on a surface perpendicular to the sun\'s rays. Missing values are (9999).'
        output_node = self.outputs.new('SvLBSocket', 'diffuse_horizontal_rad')
        output_node.tooltip = 'The hourly Diffuse Horizontal Radiation in Wh/m2. Diffuse Horizontal Radiation is the amount of solar radiation in Wh/m2 received from the sky (excluding the solar disk) on a horizontal surface. Missing values are (9999).'
        output_node = self.outputs.new('SvLBSocket', 'global_horizontal_rad')
        output_node.tooltip = 'The hourly Global Horizontal Radiation in Wh/m2. Global Horizontal Radiation is the total amount of direct and diffuse solar radiation in Wh/m2 received on a horizontal surface. It is not currently used inbEnergyPlus calculations. It should have a minimum value of 0; missing value for this field is 9999.'
        output_node = self.outputs.new('SvLBSocket', 'horizontal_infrared_rad')
        output_node.tooltip = 'The Horizontal Infrared Radiation Intensity in Wh/m2. If it is missing, EnergyPlus calculates it from the Opaque Sky Cover field. It should have a minimum value of 0; missing value is 9999.'
        output_node = self.outputs.new('SvLBSocket', 'direct_normal_ill')
        output_node.tooltip = 'The hourly Direct Normal Illuminance in lux. Direct Normal Illuminance is the average amount of illuminance in lux received directly from the solar disk on a surface perpendicular to the sun\'s rays. It is not currently used in EnergyPlus calculations. It should have a minimum value of 0; missing value is 999999.'
        output_node = self.outputs.new('SvLBSocket', 'diffuse_horizontal_ill')
        output_node.tooltip = 'The hourly Diffuse Horizontal Illuminance in lux. Diffuse Horizontal Illuminance is the average amount of illuminance in lux received from the sky (excluding the solar disk) on a horizontal surface. It is not currently used in EnergyPlus calculations. It should have a minimum value of 0; missing value is 999999.'
        output_node = self.outputs.new('SvLBSocket', 'global_horizontal_ill')
        output_node.tooltip = 'The hourly Global Horizontal Illuminance in lux. Global Horizontal Illuminance is the average total amount of direct and diffuse illuminance in lux received on a horizontal surface. It is not currently used in EnergyPlus calculations. It should have a minimum value of 0; missing value is 999999.'
        output_node = self.outputs.new('SvLBSocket', 'total_sky_cover')
        output_node.tooltip = 'The fraction for Total Sky Cover  in tenths of coverage. (eg. 1 is 1/10 covered. 10 is total coverage). Total Sky Cover is the amount of the sky dome covered by clouds or obscuring phenomena. Minium value is 0; maximum value is 10; missing value is 99.'
        output_node = self.outputs.new('SvLBSocket', 'barometric_pressure')
        output_node.tooltip = 'The hourly weather station pressure in Pa. Valid values range from 31,000 to 120,000. Missing value is 999999.'
        output_node = self.outputs.new('SvLBSocket', 'model_year')
        output_node.tooltip = 'The year from which the hourly data has been extracted. EPW files are synthesized from real recorded data from different years in a given climate. This is done to ensure that, for each month, the selected data is statistically representative of the average monthly conditions over the 18+ years of recording the data. Different EPW files will be synthesized from different years depeding on whether they are TMY (Typical Meteorological Year), TMY2, TMY3, AMY (Actual Meteorological Year) or other.'
        output_node = self.outputs.new('SvLBSocket', 'ground_temperature')
        output_node.tooltip = 'Monthly ground temperature data if it exists within the EPW file. Typically, each data collection in this list represents monthly temperatures at three different depths. - 0.5 meters - 2.0 meters - 4.0 meters'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Import climate data from a standard .epw file. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['location', 'dry_bulb_temperature', 'dew_point_temperature', 'relative_humidity', 'wind_speed', 'wind_direction', 'direct_normal_rad', 'diffuse_horizontal_rad', 'global_horizontal_rad', 'horizontal_infrared_rad', 'direct_normal_ill', 'diffuse_horizontal_ill', 'global_horizontal_ill', 'total_sky_cover', 'barometric_pressure', 'model_year', 'ground_temperature']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_epw_file']
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

    def process_ladybug(self, _epw_file):

        try:
            import ladybug.epw as epw
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            epw_data = epw.EPW(_epw_file)
            location = epw_data.location
            dry_bulb_temperature = epw_data.dry_bulb_temperature
            dew_point_temperature = epw_data.dew_point_temperature
            relative_humidity = epw_data.relative_humidity
            wind_speed = epw_data.wind_speed
            wind_direction = epw_data.wind_direction
            direct_normal_rad = epw_data.direct_normal_radiation
            diffuse_horizontal_rad = epw_data.diffuse_horizontal_radiation
            global_horizontal_rad = epw_data.global_horizontal_radiation
            horizontal_infrared_rad = epw_data.horizontal_infrared_radiation_intensity
            direct_normal_ill = epw_data.direct_normal_illuminance
            diffuse_horizontal_ill = epw_data.diffuse_horizontal_illuminance
            global_horizontal_ill = epw_data.global_horizontal_illuminance
            total_sky_cover = epw_data.total_sky_cover
            barometric_pressure = epw_data.atmospheric_station_pressure
            model_year = epw_data.years
            g_temp = epw_data.monthly_ground_temperature
            ground_temperature = [g_temp[key] for key in sorted(g_temp.keys())]
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvImportEPW)

def unregister():
    bpy.utils.unregister_class(SvImportEPW)
