import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvImportDesignDay(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvImportDesignDay'
    bl_label = 'LB Import Design Day'
    sv_icon = 'LB_IMPORTDESIGNDAY'
    sv__design_day: StringProperty(
        name='_design_day',
        update=updateNode,
        description='A DesignDay object to import.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_design_day')
        input_node.prop_name = 'sv__design_day'
        input_node.tooltip = 'A DesignDay object to import.'
        output_node = self.outputs.new('SvLBSocket', 'location')
        output_node.tooltip = 'A Ladybug Location object describing the location of the design day.'
        output_node = self.outputs.new('SvLBSocket', 'dry_bulb_temperature')
        output_node.tooltip = 'The houlry dry bulb temperature over the design day, in C.'
        output_node = self.outputs.new('SvLBSocket', 'dew_point_temperature')
        output_node.tooltip = 'The hourly dew point temperature over the design day, in C.'
        output_node = self.outputs.new('SvLBSocket', 'relative_humidity')
        output_node.tooltip = 'The hourly Relative Humidity over the design day in percent.'
        output_node = self.outputs.new('SvLBSocket', 'wind_speed')
        output_node.tooltip = 'The hourly wind speed over the design day in m/sec.'
        output_node = self.outputs.new('SvLBSocket', 'wind_direction')
        output_node.tooltip = 'The hourly wind direction over the design day in degrees. The convention is that North=0.0, East=90.0, South=180.0, West=270.0.'
        output_node = self.outputs.new('SvLBSocket', 'direct_normal_rad')
        output_node.tooltip = 'The hourly Direct Normal Radiation over the design day in Wh/m2.'
        output_node = self.outputs.new('SvLBSocket', 'diffuse_horizontal_rad')
        output_node.tooltip = 'The hourly Diffuse Horizontal Radiation over the design day in Wh/m2.'
        output_node = self.outputs.new('SvLBSocket', 'global_horizontal_rad')
        output_node.tooltip = 'The hourly Global Horizontal Radiation over the design day in Wh/m2.'
        output_node = self.outputs.new('SvLBSocket', 'horizontal_infrared_rad')
        output_node.tooltip = 'The Horizontal Infrared Radiation Intensity over the design day in Wh/m2.'
        output_node = self.outputs.new('SvLBSocket', 'total_sky_cover')
        output_node.tooltip = 'The fraction for total sky cover over the design day in tenths of coverage.'
        output_node = self.outputs.new('SvLBSocket', 'barometric_pressure')
        output_node.tooltip = 'The hourly weather station pressure over the design day in Pa.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Import hourly climate data from a Ladybug DesignDay object. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['location', 'dry_bulb_temperature', 'dew_point_temperature', 'relative_humidity', 'wind_speed', 'wind_direction', 'direct_normal_rad', 'diffuse_horizontal_rad', 'global_horizontal_rad', 'horizontal_infrared_rad', 'total_sky_cover', 'barometric_pressure']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_design_day']
        self.sv_input_types = ['System.Object']
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

    def process_ladybug(self, _design_day):

        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            dry_bulb_temperature = _design_day.hourly_dry_bulb
            dew_point_temperature = _design_day.hourly_dew_point
            relative_humidity = _design_day.hourly_relative_humidity
            wind_speed = _design_day.hourly_wind_speed
            wind_direction = _design_day.hourly_wind_direction
            direct_normal_rad, diffuse_horizontal_rad, global_horizontal_rad = \
                _design_day.hourly_solar_radiation
            horizontal_infrared_rad = _design_day.hourly_horizontal_infrared
            total_sky_cover = _design_day.hourly_sky_cover
            barometric_pressure = _design_day.hourly_barometric_pressure
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvImportDesignDay)

def unregister():
    bpy.utils.unregister_class(SvImportDesignDay)
