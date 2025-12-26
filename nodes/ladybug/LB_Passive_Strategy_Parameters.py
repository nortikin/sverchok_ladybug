import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvStrategyPar(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvStrategyPar'
    bl_label = 'LB Passive Strategy Parameters'
    sv_icon = 'LB_STRATEGYPAR'
    sv__day_above_comf_: StringProperty(
        name='_day_above_comf_',
        update=updateNode,
        description='A number in degrees Celsius representing the maximum daily temperature above the comfort range which can still be counted in the "Mass + Night Vent" polygon. (Default: 12 C).')
    sv__night_below_comf_: StringProperty(
        name='_night_below_comf_',
        update=updateNode,
        description='A number in degrees Celsius representing the minimum temperature below the maximum comfort polygon temperature that the outdoor temperature must drop at night in order to count towards the "Mass + Night Vent" polygon. (Default: 3C).')
    sv__fan_air_speed_: StringProperty(
        name='_fan_air_speed_',
        update=updateNode,
        description='The air speed around the occupants that the fans create in m/s. This is used to create the "Occupant Use of Fans" polygon. Note that values above 1 m/s tend to blow papers off desks. (Default: 1.0 m/3)')
    sv__balance_temp_: StringProperty(
        name='_balance_temp_',
        update=updateNode,
        description='The balance temperature of the building in Celsius when accounting for all internal heat. This is used to create the "Capture Internal Heat" polygon. This value must be greater or equal to 5 C (balance temperatures below 10 C are exceedingly rare) and it should be less than the coldest temperature of the merged comfort polygon in order to be meaningful. (Default: 12.8 C)')
    sv__solar_heat_cap_: StringProperty(
        name='_solar_heat_cap_',
        update=updateNode,
        description='A number representing the amount of outdoor solar flux (W/m2) that is needed to raise the temperature of the theoretical building by 1 degree Celsius. The lower this number, the more efficiently the space is able to absorb passive solar heat. The default assumes a relatively small passively solar heated zone without much mass. A higher number will be required the larger the space is and the more mass that it has. (Default: 50 W/m2)')
    sv__time_constant_: StringProperty(
        name='_time_constant_',
        update=updateNode,
        description='A number that represents the amount of time in hours that a therortical building can passively maintain its temperature. This is used to determine how many hours a space can maintain a cool temperature after night flushing for the "Mass + Night Vent" polygon. It is also used to determine how many hours a space can store solar radiation for the "Passive Solar Heating" polygon. The default assumes a relatively well-isulated building with a thermal mass typical of most contemporary buildings. Higher mass buildings will be able to support a longer time constant. (Default: 8 hours).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_day_above_comf_')
        input_node.prop_name = 'sv__day_above_comf_'
        input_node.tooltip = 'A number in degrees Celsius representing the maximum daily temperature above the comfort range which can still be counted in the "Mass + Night Vent" polygon. (Default: 12 C).'
        input_node = self.inputs.new('SvLBSocket', '_night_below_comf_')
        input_node.prop_name = 'sv__night_below_comf_'
        input_node.tooltip = 'A number in degrees Celsius representing the minimum temperature below the maximum comfort polygon temperature that the outdoor temperature must drop at night in order to count towards the "Mass + Night Vent" polygon. (Default: 3C).'
        input_node = self.inputs.new('SvLBSocket', '_fan_air_speed_')
        input_node.prop_name = 'sv__fan_air_speed_'
        input_node.tooltip = 'The air speed around the occupants that the fans create in m/s. This is used to create the "Occupant Use of Fans" polygon. Note that values above 1 m/s tend to blow papers off desks. (Default: 1.0 m/3)'
        input_node = self.inputs.new('SvLBSocket', '_balance_temp_')
        input_node.prop_name = 'sv__balance_temp_'
        input_node.tooltip = 'The balance temperature of the building in Celsius when accounting for all internal heat. This is used to create the "Capture Internal Heat" polygon. This value must be greater or equal to 5 C (balance temperatures below 10 C are exceedingly rare) and it should be less than the coldest temperature of the merged comfort polygon in order to be meaningful. (Default: 12.8 C)'
        input_node = self.inputs.new('SvLBSocket', '_solar_heat_cap_')
        input_node.prop_name = 'sv__solar_heat_cap_'
        input_node.tooltip = 'A number representing the amount of outdoor solar flux (W/m2) that is needed to raise the temperature of the theoretical building by 1 degree Celsius. The lower this number, the more efficiently the space is able to absorb passive solar heat. The default assumes a relatively small passively solar heated zone without much mass. A higher number will be required the larger the space is and the more mass that it has. (Default: 50 W/m2)'
        input_node = self.inputs.new('SvLBSocket', '_time_constant_')
        input_node.prop_name = 'sv__time_constant_'
        input_node.tooltip = 'A number that represents the amount of time in hours that a therortical building can passively maintain its temperature. This is used to determine how many hours a space can maintain a cool temperature after night flushing for the "Mass + Night Vent" polygon. It is also used to determine how many hours a space can store solar radiation for the "Passive Solar Heating" polygon. The default assumes a relatively well-isulated building with a thermal mass typical of most contemporary buildings. Higher mass buildings will be able to support a longer time constant. (Default: 8 hours).'
        output_node = self.outputs.new('SvLBSocket', 'strategy_par')
        output_node.tooltip = 'Passive strategy parameters that can be plugged into the "LB PMV Polygon" to adjust the assumptions of the passive strategy polygons.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Adjust the assumptions of the passive strategies that can be overalid on the Psychrometric Chart using the "LB PMV Polygon" component. The default assumptions of each of the strategies are as follows:  _ Thermal Mass + Night Vent - The polygon represents the conditions under which shaded, night-flushed thermal mass can keep occupants cool. By default, this polygon assumes that temperatures can get as high as 12 C above the max temperature of the comfort polygon as long temperatures 8 hours before the hot hour are 3.0 C lower than the max temperture of the comfort polygon. This parameter component can be used to adjust these two temperature values and the number of hours that the building keeps its "coolth". _ Occupant Use of Fans - This polygon is made by assuming that an air speed of 1.0 m/s is the maximum speed tolerable before papers start blowing around and conditions become annoying to occupants. The polygon is determined by running a PMV model with this fan air speed and the PMV inputs of the warmest comfort conditions. This parameter component can be used to adjust this maximum acceptable air speed. _ Capture Internal Heat - The polygon is made by assuming a minimum building balance point of 12.8 C and any conditions that are warmer than that will keep occupants comfortable (up to the comfort polygon). It is assumed that, above this building balance temperature, the building is free-running and occupants are able to open windows as they wish to keep conditions from overshooting the comfort polygon. Note that the default balance temperature of 12.8 C is fairly low and assumes a significant amount of internal heat from people, equipment. etc. Or the building  as a well-insulated envelope to ensure what internal heat there is can leave the building slowly. This parameter component can be used to adjust the balance temperature. _ Passive Solar Heating - The polygon represents the conditions under which sun-exposed thermal mass can keep occupants warm in winter. By default, this polygon assumes that temperatures can get as high as 12 C above the max temperature of the comfort polygon as long temperatures 8 hours before the hot hour are 3.0 C lower than the max temperture of the comfort polygon. This parameter component can be used to adjust these two temperature values and the number of hours that the building keeps its "coolth". -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['strategy_par']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_day_above_comf_', '_night_below_comf_', '_fan_air_speed_', '_balance_temp_', '_solar_heat_cap_', '_time_constant_']
        self.sv_input_types = ['double', 'double', 'double', 'double', 'double', 'int']
        self.sv_input_defaults = [None, None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _day_above_comf_, _night_below_comf_, _fan_air_speed_, _balance_temp_, _solar_heat_cap_, _time_constant_):

        try:
            from ladybug_tools.sverchok import give_warning, objectify_output, turn_off_old_tag
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        turn_off_old_tag(ghenv.Component)
        
        
        def check_strategy(value, name, default, max, min):
            """Check a strategy parameter to ensure it is correct."""
            if value is None:
                strategy_par.append(default)
            elif value <= max and value >= min:
                strategy_par.append(value)
            else:
                strategy_par.append(default)
                msg = '"{}" must be between {} and {}. Got {}.\nReverting to default ' \
                    'value of {}'.format(name, min, max, value, default)
                print(msg)
                give_warning(ghenv.Component, msg)
        
        
        #check and add each of the strategies
        strategy_par = []
        check_strategy(_day_above_comf_, '_day_above_comf_', 12.0, 30.0, 0.0)
        check_strategy(_night_below_comf_, '_night_below_comf_', 3.0, 15.0, 0.0)
        check_strategy(_fan_air_speed_, '_fan_air_speed_', 1.0, 10.0, 0.1)
        check_strategy(_balance_temp_, '_balance_temp_', 12.8, 20.0, 5.0)
        check_strategy(_solar_heat_cap_, '_solar_heat_cap_', 50.0, 1000.0, 1.0)
        check_strategy(_time_constant_, '_time_constant_', 8, 48, 1)
        strategy_par = objectify_output('Passive Strategy Parameters', strategy_par)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvStrategyPar)

def unregister():
    bpy.utils.unregister_class(SvStrategyPar)
