import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvDecnstrDesignDay(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvDecnstrDesignDay'
    bl_label = 'LB Deconstruct Design Day'
    sv_icon = 'LB_DECNSTRDESIGNDAY'
    sv__design_day: StringProperty(
        name='_design_day',
        update=updateNode,
        description='A DesignDay object to deconstruct.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_design_day')
        input_node.prop_name = 'sv__design_day'
        input_node.tooltip = 'A DesignDay object to deconstruct.'
        output_node = self.outputs.new('SvLBSocket', 'name')
        output_node.tooltip = 'The name of the DesignDay object.'
        output_node = self.outputs.new('SvLBSocket', 'day_type')
        output_node.tooltip = 'Text indicating the type of design day (ie. \'SummerDesignDay\', \'WinterDesignDay\' or other EnergyPlus days).'
        output_node = self.outputs.new('SvLBSocket', 'location')
        output_node.tooltip = 'A Ladybug Location object describing the location of the design day.'
        output_node = self.outputs.new('SvLBSocket', 'date')
        output_node.tooltip = 'Date for the day of the year the design day'
        output_node = self.outputs.new('SvLBSocket', 'dry_bulb_max')
        output_node.tooltip = 'Maximum dry bulb temperature over the design day (in C).'
        output_node = self.outputs.new('SvLBSocket', 'dry_bulb_range')
        output_node.tooltip = 'Dry bulb range over the design day (in C).'
        output_node = self.outputs.new('SvLBSocket', 'humidity_type')
        output_node.tooltip = 'Type of humidity to use. Will be one of the following: * Wetbulb * Dewpoint * HumidityRatio * Enthalpy'
        output_node = self.outputs.new('SvLBSocket', 'humidity_value')
        output_node.tooltip = 'The value of the humidity condition above.'
        output_node = self.outputs.new('SvLBSocket', 'barometric_p')
        output_node.tooltip = 'Barometric pressure in Pa.'
        output_node = self.outputs.new('SvLBSocket', 'wind_speed')
        output_node.tooltip = 'Wind speed over the design day in m/s.'
        output_node = self.outputs.new('SvLBSocket', 'wind_dir')
        output_node.tooltip = 'Wind direction over the design day in degrees.'
        output_node = self.outputs.new('SvLBSocket', 'sky_type')
        output_node.tooltip = 'Script output sky_type.'
        output_node = self.outputs.new('SvLBSocket', 'sky_properties')
        output_node.tooltip = 'A list of properties describing the sky above. For ASHRAEClearSky this is a single value for clearness. For ASHRAETau, this is the tau_beam and tau_diffuse.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Deconstruct design day into parameters. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['name', 'day_type', 'location', 'date', 'dry_bulb_max', 'dry_bulb_range', 'humidity_type', 'humidity_value', 'barometric_p', 'wind_speed', 'wind_dir', 'sky_type', 'sky_properties']
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
            from ladybug.designday import ASHRAEClearSky, ASHRAETau
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # extract typical design day properties
            name = _design_day.name
            day_type = _design_day.day_type
            location  = _design_day.location
            date = _design_day.sky_condition.date
            dry_bulb_max = _design_day.dry_bulb_condition.dry_bulb_max
            dry_bulb_range = _design_day.dry_bulb_condition.dry_bulb_range
            humidity_type = _design_day.humidity_condition.humidity_type
            humidity_value = _design_day.humidity_condition.humidity_value
            barometric_p = _design_day.humidity_condition.barometric_pressure
            wind_speed = _design_day.wind_condition.wind_speed
            wind_dir = _design_day.wind_condition.wind_direction
            
            # extract properties of the sky condition
            if isinstance(_design_day.sky_condition, ASHRAETau):
                sky_type = 'ASHRAETau'
                sky_properties = [_design_day.sky_condition.tau_b,
                                  _design_day.sky_condition.tau_d]
            elif isinstance(_design_day.sky_condition, ASHRAEClearSky):
                sky_type = 'ASHRAEClearSky'
                sky_properties = _design_day.sky_condition.clearness

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvDecnstrDesignDay)

def unregister():
    bpy.utils.unregister_class(SvDecnstrDesignDay)
