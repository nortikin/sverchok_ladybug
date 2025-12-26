import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvHDD_CDD(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvHDD_CDD'
    bl_label = 'LB Degree Days'
    sv_icon = 'LB_HDD_CDD'
    sv__dry_bulb: StringProperty(
        name='_dry_bulb',
        update=updateNode,
        description='A data collection representing outdoor dry bulb temperature [C]')
    sv__heat_base_: StringProperty(
        name='_heat_base_',
        update=updateNode,
        description='A number for the base temperature below which a given hour is considered to be in heating mode. Default is 18 Celcius, which is a common balance point for buildings.')
    sv__cool_base_: StringProperty(
        name='_cool_base_',
        update=updateNode,
        description='A number for the base temperature above which a given hour is considered to be in cooling mode. Default is 23 Celcius, which is a common balance point for buildings.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_dry_bulb')
        input_node.prop_name = 'sv__dry_bulb'
        input_node.tooltip = 'A data collection representing outdoor dry bulb temperature [C]'
        input_node = self.inputs.new('SvLBSocket', '_heat_base_')
        input_node.prop_name = 'sv__heat_base_'
        input_node.tooltip = 'A number for the base temperature below which a given hour is considered to be in heating mode. Default is 18 Celcius, which is a common balance point for buildings.'
        input_node = self.inputs.new('SvLBSocket', '_cool_base_')
        input_node.prop_name = 'sv__cool_base_'
        input_node.tooltip = 'A number for the base temperature above which a given hour is considered to be in cooling mode. Default is 23 Celcius, which is a common balance point for buildings.'
        output_node = self.outputs.new('SvLBSocket', 'hourly_heat')
        output_node.tooltip = 'A data collection of heating degree-days. Plug this into the \'Time Interval Operation\' component to get the number of degree-days at different time intervals.'
        output_node = self.outputs.new('SvLBSocket', 'hourly_cool')
        output_node.tooltip = 'A data collection of cooling degree-days. Plug this into the \'Time Interval Operation\' component to get the number of degree-days at different time intervals.'
        output_node = self.outputs.new('SvLBSocket', 'heat_deg_days')
        output_node.tooltip = 'A value indicating the total number of heating degree-days over the entire input _dry_bulb collection.'
        output_node = self.outputs.new('SvLBSocket', 'cool_deg_days')
        output_node.tooltip = 'A value indicating the total number of cooling degree-days over the entire input _dry_bulb collection.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate heating and cooling degree-days from outdoor dry bulb temperature. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['hourly_heat', 'hourly_cool', 'heat_deg_days', 'cool_deg_days']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_dry_bulb', '_heat_base_', '_cool_base_']
        self.sv_input_types = ['System.Object', 'double', 'double']
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

    def process_ladybug(self, _dry_bulb, _heat_base_, _cool_base_):

        try:
            from ladybug_comfort.degreetime import heating_degree_time, cooling_degree_time
            from ladybug.datacollection import HourlyContinuousCollection
            from ladybug.datatype.temperaturetime import HeatingDegreeTime, CoolingDegreeTime
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            if _heat_base_ is None:
                _heat_base_ = 18
            if _cool_base_ is None:
                _cool_base_ = 23
        
            hourly_heat = HourlyContinuousCollection.compute_function_aligned(
                heating_degree_time, [_dry_bulb, _heat_base_],
                HeatingDegreeTime(), 'degC-hours')
            hourly_heat.convert_to_unit('degC-days')
        
            hourly_cool = HourlyContinuousCollection.compute_function_aligned(
                cooling_degree_time, [_dry_bulb, _cool_base_],
                CoolingDegreeTime(), 'degC-hours')
            hourly_cool.convert_to_unit('degC-days')
        
            heat_deg_days = hourly_heat.total
            cool_deg_days = hourly_cool.total

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvHDD_CDD)

def unregister():
    bpy.utils.unregister_class(SvHDD_CDD)
