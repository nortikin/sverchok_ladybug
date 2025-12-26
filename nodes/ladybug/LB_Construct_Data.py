import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvPlusData(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvPlusData'
    bl_label = 'LB Construct Data'
    sv_icon = 'LB_PLUSDATA'
    sv__header: StringProperty(
        name='_header',
        update=updateNode,
        description='A Ladybug header object describing the metadata of the data collection.')
    sv__values: StringProperty(
        name='_values',
        update=updateNode,
        description='A list of numerical values for the data collection.')
    sv__interval_: StringProperty(
        name='_interval_',
        update=updateNode,
        description='Text to indicate the time interval of the data collection, which determines the type of collection that is output. (Default: hourly). _ Choose from the following: - hourly - daily - monthly - monthly-per-hour _ Note that the "hourly" input is also used to represent sub-hourly intervals (in this case, the timestep of the analysis period must not be 1).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_header')
        input_node.prop_name = 'sv__header'
        input_node.tooltip = 'A Ladybug header object describing the metadata of the data collection.'
        input_node = self.inputs.new('SvLBSocket', '_values')
        input_node.prop_name = 'sv__values'
        input_node.tooltip = 'A list of numerical values for the data collection.'
        input_node = self.inputs.new('SvLBSocket', '_interval_')
        input_node.prop_name = 'sv__interval_'
        input_node.tooltip = 'Text to indicate the time interval of the data collection, which determines the type of collection that is output. (Default: hourly). _ Choose from the following: - hourly - daily - monthly - monthly-per-hour _ Note that the "hourly" input is also used to represent sub-hourly intervals (in this case, the timestep of the analysis period must not be 1).'
        output_node = self.outputs.new('SvLBSocket', 'data')
        output_node.tooltip = 'A Ladybug data collection object.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Construct a Ladybug data collection from header and values. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['data']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_header', '_values', '_interval_']
        self.sv_input_types = ['System.Object', 'double', 'string']
        self.sv_input_defaults = [None, None, None]
        self.sv_input_access = ['item', 'list', 'item']
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

    def process_ladybug(self, _header, _values, _interval_):

        try:
            from ladybug.datacollection import HourlyContinuousCollection, DailyCollection, \
                MonthlyCollection, MonthlyPerHourCollection, HourlyDiscontinuousCollection
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            inter = _interval_.lower() if _interval_ is not None else 'hourly'
            if inter == 'hourly':
                aper = _header.analysis_period
                if aper.st_hour == 0 and aper.end_hour == 23:
                    data = HourlyContinuousCollection(_header, _values)
                else:
                    data = HourlyDiscontinuousCollection(_header, _values, aper.datetimes)
            elif inter == 'monthly':
                data = MonthlyCollection(
                    _header, _values, _header.analysis_period.months_int)
            elif inter == 'daily':
                data = DailyCollection(
                    _header, _values, _header.analysis_period.doys_int)
            elif inter == 'monthly-per-hour':
                data = MonthlyPerHourCollection(
                    _header, _values, _header.analysis_period.months_per_hour)
            else:
                raise ValueError('{} is not a recongized interval.'.format(_interval_))
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvPlusData)

def unregister():
    bpy.utils.unregister_class(SvPlusData)
