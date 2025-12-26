import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvRate(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvRate'
    bl_label = 'LB Time Rate of Change'
    sv_icon = 'LB_RATE'
    sv__data: StringProperty(
        name='_data',
        update=updateNode,
        description='A houry, sub-hourly or daily data collection that can converted to a time rate of change metric. (eg. a data collection of Energy values in kWh).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_data')
        input_node.prop_name = 'sv__data'
        input_node.tooltip = 'A houry, sub-hourly or daily data collection that can converted to a time rate of change metric. (eg. a data collection of Energy values in kWh).'
        output_node = self.outputs.new('SvLBSocket', 'data_rate')
        output_node.tooltip = 'The data collection converted to time rate of changevalues. (eg. a data collection of Energy values in kWh).'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Convert a DataCollection of time-aggregated values to time rate of change units. _ For example, if the collection has an Energy data type in kWh, this method will return a collection with an Power data type in W. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['data_rate']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_data']
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

    def process_ladybug(self, _data):

        try:
            from ladybug.datacollection import HourlyDiscontinuousCollection, DailyCollection
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            accept = (HourlyDiscontinuousCollection, DailyCollection)
            assert isinstance(_data, accept), '_data must be a an hourly ot daily data ' \
                'collection. Got {}.'.format(type(_data))
            data_rate = _data.to_time_rate_of_change()
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvRate)

def unregister():
    bpy.utils.unregister_class(SvRate)
