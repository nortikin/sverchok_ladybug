import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvTimeOp(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvTimeOp'
    bl_label = 'LB Time Interval Operation'
    sv_icon = 'LB_TIMEOP'
    sv__data: StringProperty(
        name='_data',
        update=updateNode,
        description='A Ladybug data collection object.')
    sv__operation_: StringProperty(
        name='_operation_',
        update=updateNode,
        description='Text indicating the operation that should be performed on the input hourly data. _ Such text must be one of the following: - average - total - [a number between 0 and 100] _ In the case of the last option, the number will be interpreted as a percentile of the data over the time period. For example, inputting 75 will return the 75th percentile value of each day/month/hour, inputting 0 will give the minimum value of each day/month/hour and inputting 100 will give the max value of each day/month/hour. _ Default is \'average\' if the input data type is not cumulative and \'total\' if the data type is cumulative.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_data')
        input_node.prop_name = 'sv__data'
        input_node.tooltip = 'A Ladybug data collection object.'
        input_node = self.inputs.new('SvLBSocket', '_operation_')
        input_node.prop_name = 'sv__operation_'
        input_node.tooltip = 'Text indicating the operation that should be performed on the input hourly data. _ Such text must be one of the following: - average - total - [a number between 0 and 100] _ In the case of the last option, the number will be interpreted as a percentile of the data over the time period. For example, inputting 75 will return the 75th percentile value of each day/month/hour, inputting 0 will give the minimum value of each day/month/hour and inputting 100 will give the max value of each day/month/hour. _ Default is \'average\' if the input data type is not cumulative and \'total\' if the data type is cumulative.'
        output_node = self.outputs.new('SvLBSocket', 'daily')
        output_node.tooltip = 'Daily data collection derived from the input _data and _operation_.'
        output_node = self.outputs.new('SvLBSocket', 'monthly')
        output_node.tooltip = 'Monthly data collection derived from the input _data and _operation_.'
        output_node = self.outputs.new('SvLBSocket', 'mon_per_hr')
        output_node.tooltip = 'Monthly Per Hour data collection derived from the input _data and _operation_.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Perform time interval operations on an hourly data collection. _ This includes operations like: - Average - Total - Percentile _ These actions can be performed over the following time intervals: - Daily - Monthly - Monthly per Hour -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['daily', 'monthly', 'mon_per_hr']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_data', '_operation_']
        self.sv_input_types = ['System.Object', 'string']
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

    def process_ladybug(self, _data, _operation_):

        try:
            from ladybug.datacollection import HourlyDiscontinuousCollection
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            assert isinstance(_data, HourlyDiscontinuousCollection), \
                '_data must be an Hourly Data Collection.' \
                ' Got {}.'.format(type(_data))
            if _operation_ is None:
                _operation_ = 'total' if _data.header.data_type.cumulative else 'average'
        
            if _operation_.lower() == 'average':
                daily = _data.average_daily()
                monthly = _data.average_monthly()
                mon_per_hr = _data.average_monthly_per_hour()
            elif _operation_.lower() == 'total':
                daily = _data.total_daily()
                monthly = _data.total_monthly()
                mon_per_hr = _data.total_monthly_per_hour()
            else:
                try:
                    percentile = float(_operation_)
                except ValueError as e:
                    raise TypeError(" Input '{}' for _operation_ is not valid. \n"
                                    "operation_ must be one of the following:\n"
                                    " average\n total\n [a number between 0 and "
                                    "100]".format(_operation_))
                else:
                    daily = _data.percentile_daily(percentile)
                    monthly = _data.percentile_monthly(percentile)
                    mon_per_hr = _data.percentile_monthly_per_hour(percentile)

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvTimeOp)

def unregister():
    bpy.utils.unregister_class(SvTimeOp)
