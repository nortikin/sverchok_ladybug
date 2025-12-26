import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvHumidityR(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvHumidityR'
    bl_label = 'LB Humidity Metrics'
    sv_icon = 'LB_HUMIDITYR'
    sv__dry_bulb: StringProperty(
        name='_dry_bulb',
        update=updateNode,
        description='A value or data collection representing  dry bulb temperature [C]')
    sv__rel_humid: StringProperty(
        name='_rel_humid',
        update=updateNode,
        description='A value or data collection representing relative humidity [%]')
    sv__pressure_: StringProperty(
        name='_pressure_',
        update=updateNode,
        description='A value or data collection representing atmospheric pressure [Pa] Default is to use air pressure at sea level (101,325 Pa).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_dry_bulb')
        input_node.prop_name = 'sv__dry_bulb'
        input_node.tooltip = 'A value or data collection representing  dry bulb temperature [C]'
        input_node = self.inputs.new('SvLBSocket', '_rel_humid')
        input_node.prop_name = 'sv__rel_humid'
        input_node.tooltip = 'A value or data collection representing relative humidity [%]'
        input_node = self.inputs.new('SvLBSocket', '_pressure_')
        input_node.prop_name = 'sv__pressure_'
        input_node.tooltip = 'A value or data collection representing atmospheric pressure [Pa] Default is to use air pressure at sea level (101,325 Pa).'
        output_node = self.outputs.new('SvLBSocket', 'humid_ratio')
        output_node.tooltip = 'A data collection or value for humidity ratio (aka. absolute humidity). Units are fractional (kg water / kg air).'
        output_node = self.outputs.new('SvLBSocket', 'enthalpy')
        output_node.tooltip = 'A data collection or value for enthalpy (kJ / Kg).'
        output_node = self.outputs.new('SvLBSocket', 'wet_bulb')
        output_node.tooltip = 'A data collection or value for wet bulb temperature (C).'
        output_node = self.outputs.new('SvLBSocket', 'dew_point')
        output_node.tooltip = 'A data collection or value for dew point temperature (C).'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate humidity metrics from relative humidity, dry bulb temperature and (if present) atmospheric pressure. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['humid_ratio', 'enthalpy', 'wet_bulb', 'dew_point']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_dry_bulb', '_rel_humid', '_pressure_']
        self.sv_input_types = ['System.Object', 'System.Object', 'System.Object']
        self.sv_input_defaults = [None, None, None]
        self.sv_input_access = ['item', 'item', 'item']
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

    def process_ladybug(self, _dry_bulb, _rel_humid, _pressure_):

        try:
            from ladybug.psychrometrics import humid_ratio_from_db_rh, enthalpy_from_db_hr, \
                wet_bulb_from_db_rh, dew_point_from_db_rh
            from ladybug.datacollection import HourlyContinuousCollection
            from ladybug.datatype.fraction import HumidityRatio
            from ladybug.datatype.specificenergy import Enthalpy
            from ladybug.datatype.temperature import WetBulbTemperature, DewPointTemperature
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            if _pressure_ is None:
                _pressure_ = 101325
        
            humid_ratio = HourlyContinuousCollection.compute_function_aligned(
                humid_ratio_from_db_rh, [_dry_bulb, _rel_humid, _pressure_],
                HumidityRatio(), 'fraction')
            
            enthalpy = HourlyContinuousCollection.compute_function_aligned(
                enthalpy_from_db_hr, [_dry_bulb, humid_ratio], Enthalpy(), 'kJ/kg')
        
            wet_bulb = HourlyContinuousCollection.compute_function_aligned(
                wet_bulb_from_db_rh, [_dry_bulb, _rel_humid, _pressure_],
                WetBulbTemperature(), 'C')
        
            dew_point = HourlyContinuousCollection.compute_function_aligned(
                dew_point_from_db_rh, [_dry_bulb, _rel_humid],
                DewPointTemperature(), 'C')

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvHumidityR)

def unregister():
    bpy.utils.unregister_class(SvHumidityR)
