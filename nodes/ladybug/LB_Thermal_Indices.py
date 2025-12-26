import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvThermalIndices(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvThermalIndices'
    bl_label = 'LB Thermal Indices'
    sv_icon = 'LB_THERMALINDICES'
    sv__air_temp: StringProperty(
        name='_air_temp',
        update=updateNode,
        description='Data Collection or individual value for air temperature in C. This input is used by all three metrics.')
    sv__mrt_: StringProperty(
        name='_mrt_',
        update=updateNode,
        description='Data Collection or individual value for mean radiant temperature (MRT) in C. Default is the same as the air_temp. This input only affects the WBGT.')
    sv__rel_humid: StringProperty(
        name='_rel_humid',
        update=updateNode,
        description='Data Collection or individual value for relative humidity in %. Note that percent values are between 0 and 100. This input affects WBGT as well as HI.')
    sv__wind_vel: StringProperty(
        name='_wind_vel',
        update=updateNode,
        description='Data Collection or individual value for meteoroligical wind velocity at 10 m above ground level in m/s. This is used by both WBGT and WCT.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_air_temp')
        input_node.prop_name = 'sv__air_temp'
        input_node.tooltip = 'Data Collection or individual value for air temperature in C. This input is used by all three metrics.'
        input_node = self.inputs.new('SvLBSocket', '_mrt_')
        input_node.prop_name = 'sv__mrt_'
        input_node.tooltip = 'Data Collection or individual value for mean radiant temperature (MRT) in C. Default is the same as the air_temp. This input only affects the WBGT.'
        input_node = self.inputs.new('SvLBSocket', '_rel_humid')
        input_node.prop_name = 'sv__rel_humid'
        input_node.tooltip = 'Data Collection or individual value for relative humidity in %. Note that percent values are between 0 and 100. This input affects WBGT as well as HI.'
        input_node = self.inputs.new('SvLBSocket', '_wind_vel')
        input_node.prop_name = 'sv__wind_vel'
        input_node.tooltip = 'Data Collection or individual value for meteoroligical wind velocity at 10 m above ground level in m/s. This is used by both WBGT and WCT.'
        output_node = self.outputs.new('SvLBSocket', 'wbgt')
        output_node.tooltip = 'A data collection or value for Wet Bulb Globe Temperature (WBGT) [C]. WBGT is a type of feels-like temperature that is widely used as a heat stress index (ISO 7243). It is incorporates the effect of temperature, humidity, wind speed, and mean radiant temperature (optionally including the effect of sun).'
        output_node = self.outputs.new('SvLBSocket', 'heat_index')
        output_node.tooltip = 'A data collection or value for Heat Index (HI) temperature [C]. Heat index is derived from original work carried out by Robert G. Steadman, which defined heat index through large tables of empirical data. The formula here approximates the heat index to within +/- 0.7C and is the result of a multivariate fit. Heat index was adopted by the US\'s National Weather Service (NWS) in 1979.'
        output_node = self.outputs.new('SvLBSocket', 'wind_chill')
        output_node.tooltip = 'A data collection or value for Wind Cill Temperature (WCT) [C]. Wind Chill Index is derived from original work carried out by Gregorczuk. It qualifies thermal sensations of a person in wintertime. It is especially useful at low and very low air temperature and at high wind speed.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate thermal indices that have historically been used by meteorologists. All of them are "feels like" temperatures that attempt to account for factors beyond sir temperature. These include the following: _ * Wet Bulb Globe Temperature (WBGT) * Heat Index (HI) * Wind Chill Temperature (WCT) _ Most of these indices have fallen out of use in favor of Universal Thermal Climate Index (UTCI). However, they are still used in some regions and are a part of older codes and standards. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['wbgt', 'heat_index', 'wind_chill']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_air_temp', '_mrt_', '_rel_humid', '_wind_vel']
        self.sv_input_types = ['System.Object', 'System.Object', 'System.Object', 'System.Object']
        self.sv_input_defaults = [None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item']
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

    def process_ladybug(self, _air_temp, _mrt_, _rel_humid, _wind_vel):

        try:
            from ladybug_comfort.wbgt import wet_bulb_globe_temperature
            from ladybug_comfort.hi import heat_index as heat_index_temperature
            from ladybug_comfort.wc import windchill_temp
            from ladybug.datacollection import HourlyContinuousCollection
            from ladybug.datatype.temperature import WetBulbGlobeTemperature, \
                HeatIndexTemperature, WindChillTemperature
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            if _mrt_ is None:
                _mrt_ = _air_temp
        
            wbgt = HourlyContinuousCollection.compute_function_aligned(
                wet_bulb_globe_temperature, [_air_temp, _mrt_, _wind_vel, _rel_humid],
                WetBulbGlobeTemperature(), 'C')
        
            heat_index = HourlyContinuousCollection.compute_function_aligned(
                heat_index_temperature, [_air_temp, _rel_humid],
                HeatIndexTemperature(), 'C')
        
            wind_chill = HourlyContinuousCollection.compute_function_aligned(
                windchill_temp, [_air_temp, _wind_vel],
                WindChillTemperature(), 'C')

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvThermalIndices)

def unregister():
    bpy.utils.unregister_class(SvThermalIndices)
