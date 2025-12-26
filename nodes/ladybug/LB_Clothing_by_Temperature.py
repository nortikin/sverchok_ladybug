import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvCloByTemp(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvCloByTemp'
    bl_label = 'LB Clothing by Temperature'
    sv_icon = 'LB_CLOBYTEMP'
    sv__temperature: StringProperty(
        name='_temperature',
        update=updateNode,
        description='A data collection or single number representing the temperature to which the human subject adapts their clothing. This is typically the dry bulb temperature obtained from the "LB Import EPW" component.')
    sv_period_: StringProperty(
        name='period_',
        update=updateNode,
        description='If you have hooked up annual temperatures from the importEPW component, use this input to ')
    sv__max_clo_: StringProperty(
        name='_max_clo_',
        update=updateNode,
        description='A number for the maximum clo value that the human subject wears on the coldest days. (Default: 1 clo, per the original Schiavon clothing function).')
    sv__max_clo_temp_: StringProperty(
        name='_max_clo_temp_',
        update=updateNode,
        description='A number for the temperature below which the _max_clo_ value is applied (in Celsius). (Default: -5 C, per the original Schiavon clothing function with outdoor temperature).')
    sv__min_clo_: StringProperty(
        name='_min_clo_',
        update=updateNode,
        description='A number for the minimum clo value that the human subject wears wears on the hotest days. (Default: 0.46 clo, per the original Schiavon clothing function).')
    sv__min_clo_temp_: StringProperty(
        name='_min_clo_temp_',
        update=updateNode,
        description='A number for the temperature above which the _min_clo_ value is applied (in Celsius). (Default: 26 C, per the original Schiavon clothing function).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_temperature')
        input_node.prop_name = 'sv__temperature'
        input_node.tooltip = 'A data collection or single number representing the temperature to which the human subject adapts their clothing. This is typically the dry bulb temperature obtained from the "LB Import EPW" component.'
        input_node = self.inputs.new('SvLBSocket', 'period_')
        input_node.prop_name = 'sv_period_'
        input_node.tooltip = 'If you have hooked up annual temperatures from the importEPW component, use this input to '
        input_node = self.inputs.new('SvLBSocket', '_max_clo_')
        input_node.prop_name = 'sv__max_clo_'
        input_node.tooltip = 'A number for the maximum clo value that the human subject wears on the coldest days. (Default: 1 clo, per the original Schiavon clothing function).'
        input_node = self.inputs.new('SvLBSocket', '_max_clo_temp_')
        input_node.prop_name = 'sv__max_clo_temp_'
        input_node.tooltip = 'A number for the temperature below which the _max_clo_ value is applied (in Celsius). (Default: -5 C, per the original Schiavon clothing function with outdoor temperature).'
        input_node = self.inputs.new('SvLBSocket', '_min_clo_')
        input_node.prop_name = 'sv__min_clo_'
        input_node.tooltip = 'A number for the minimum clo value that the human subject wears wears on the hotest days. (Default: 0.46 clo, per the original Schiavon clothing function).'
        input_node = self.inputs.new('SvLBSocket', '_min_clo_temp_')
        input_node.prop_name = 'sv__min_clo_temp_'
        input_node.tooltip = 'A number for the temperature above which the _min_clo_ value is applied (in Celsius). (Default: 26 C, per the original Schiavon clothing function).'
        output_node = self.outputs.new('SvLBSocket', 'clo')
        output_node.tooltip = 'A single number or data collection of numbers representing the clothing that would be worn (in clo). Note that, if you have hooked up an hourly continuous data collection, the clothing levels will change on a 12-hour basis to simulate the typical cycle on which a human changes their clothing.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Estimate levels of clothing using a temperature value or data collection of temperatures to which a human subject is adapting (typically the outdoor air temperature). _ This resulting clothing values can be plugged into the _clothing_ input of the "LB PMV Comfort" component or the "LB PET Comfort" component. They can also be used in thermal mapping recipes. _ By default, this function derives clothing levels using a model developed by Schiavon, Stefano based on outdoor air temperature, which is implemented in the CBE comfort tool (https://comfort.cbe.berkeley.edu/). _ The version of the model implemented here allows changing of the maximum and minimum clothing levels, which the Schiavon model sets at 1 and 0.46 respectively, and the temperatures at which these clothing levels occur, which the Schiavon model sets at -5 C and 26 C respectively. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['clo']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_temperature', 'period_', '_max_clo_', '_max_clo_temp_', '_min_clo_', '_min_clo_temp_']
        self.sv_input_types = ['System.Object', 'System.Object', 'double', 'double', 'double', 'double']
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

    def process_ladybug(self, _temperature, period_, _max_clo_, _max_clo_temp_, _min_clo_, _min_clo_temp_):

        try:
            from ladybug.datacollection import BaseCollection, HourlyContinuousCollection
            from ladybug.datatype.rvalue import ClothingInsulation
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_comfort.clo import schiavon_clo
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # set default values
            _max_clo_ = _max_clo_ if _max_clo_ is not None else 1.0
            _max_clo_temp_ = _max_clo_temp_ if _max_clo_temp_ is not None else -5
            _min_clo_ = _min_clo_ if _min_clo_ is not None else 0.46
            _min_clo_temp_ = _min_clo_temp_ if _min_clo_temp_ is not None else 26
        
            # if the temperature is hourly continuous, simplify the values
            if isinstance(_temperature, HourlyContinuousCollection):
                date_times, temps = _temperature.datetimes, _temperature.values
                last_time = date_times[0].sub_hour(18)  # clothing determined at 6 AM
                last_val = temps[0]
                new_vals = []
                for v, dt in zip(temps, date_times):
                    time_diff = dt - last_time
                    if time_diff.days >= 1:
                        last_time, last_val = dt, v
                    new_vals.append(last_val)
                _temperature = _temperature.duplicate()
                _temperature.values = new_vals
        
            # apply the analysis period if requests
            if period_ is not None and isinstance(_temperature, BaseCollection):
                _temperature = _temperature.filter_by_analysis_period(period_)
        
            clo = HourlyContinuousCollection.compute_function_aligned(
                schiavon_clo, [_temperature, _max_clo_, _max_clo_temp_, _min_clo_, _min_clo_temp_],
                ClothingInsulation(), 'clo')
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvCloByTemp)

def unregister():
    bpy.utils.unregister_class(SvCloByTemp)
