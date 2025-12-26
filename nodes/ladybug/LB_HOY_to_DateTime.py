import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvDateTime(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvDateTime'
    bl_label = 'LB HOY to DateTime'
    sv_icon = 'LB_DATETIME'
    sv__hoy: StringProperty(
        name='_hoy',
        update=updateNode,
        description='A number between 0 and 8759 for an hour of the year.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_hoy')
        input_node.prop_name = 'sv__hoy'
        input_node.tooltip = 'A number between 0 and 8759 for an hour of the year.'
        output_node = self.outputs.new('SvLBSocket', 'month')
        output_node.tooltip = 'The month of the year on which the input hoy falls.'
        output_node = self.outputs.new('SvLBSocket', 'day')
        output_node.tooltip = 'The day of the month on which the input hoy falls.'
        output_node = self.outputs.new('SvLBSocket', 'hour')
        output_node.tooltip = 'The hour of the day on which the input hoy falls.'
        output_node = self.outputs.new('SvLBSocket', 'minute')
        output_node.tooltip = 'The minute of the hour on which the input hoy falls.'
        output_node = self.outputs.new('SvLBSocket', 'date')
        output_node.tooltip = 'The input information as a human-readable date time.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate date information from an hour of the year. _ Date information includes the month of the year, day of the month and the hour + minute of the day. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['month', 'day', 'hour', 'minute', 'date']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_hoy']
        self.sv_input_types = ['double']
        self.sv_input_defaults = [None]
        self.sv_input_access = ['list']
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

    def process_ladybug(self, _hoy):

        try:
            from ladybug.dt import DateTime
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            month = []
            day = []
            hour = []
            minute = []
            date = []
        
            for hoy in _hoy:
                datetime = DateTime.from_hoy(hoy)
                month.append(datetime.month)
                day.append(datetime.day)
                hour.append(datetime.hour)
                minute.append(datetime.minute)
                date.append(datetime)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvDateTime)

def unregister():
    bpy.utils.unregister_class(SvDateTime)
