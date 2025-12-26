import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvHOY(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvHOY'
    bl_label = 'LB Calculate HOY'
    sv_icon = 'LB_HOY'
    sv__month_: StringProperty(
        name='_month_',
        update=updateNode,
        description='Integer for month (1-12).')
    sv__day_: StringProperty(
        name='_day_',
        update=updateNode,
        description='Integer for day (1-31).')
    sv__hour_: StringProperty(
        name='_hour_',
        update=updateNode,
        description='Integer for hour (0-23).')
    sv__minute_: StringProperty(
        name='_minute_',
        update=updateNode,
        description='Integer for minute (0-59).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_month_')
        input_node.prop_name = 'sv__month_'
        input_node.tooltip = 'Integer for month (1-12).'
        input_node = self.inputs.new('SvLBSocket', '_day_')
        input_node.prop_name = 'sv__day_'
        input_node.tooltip = 'Integer for day (1-31).'
        input_node = self.inputs.new('SvLBSocket', '_hour_')
        input_node.prop_name = 'sv__hour_'
        input_node.tooltip = 'Integer for hour (0-23).'
        input_node = self.inputs.new('SvLBSocket', '_minute_')
        input_node.prop_name = 'sv__minute_'
        input_node.tooltip = 'Integer for minute (0-59).'
        output_node = self.outputs.new('SvLBSocket', 'hoy')
        output_node.tooltip = 'Hour of the year.'
        output_node = self.outputs.new('SvLBSocket', 'doy')
        output_node.tooltip = 'Day of the year.'
        output_node = self.outputs.new('SvLBSocket', 'date')
        output_node.tooltip = 'Human readable date time.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate hour of the year from month, day, hour, minute. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['hoy', 'doy', 'date']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_month_', '_day_', '_hour_', '_minute_']
        self.sv_input_types = ['int', 'int', 'int', 'int']
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

    def process_ladybug(self, _month_, _day_, _hour_, _minute_):

        try:
            from ladybug.dt import DateTime
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        try:
            from ladybug_tools.sverchok import turn_off_old_tag
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        turn_off_old_tag(ghenv.Component)
        
        
        month = _month_ or 9
        day = _day_ or 21
        hour = _hour_ if _hour_ is not None else 12
        minute = _minute_ or 0
        
        datetime = DateTime(month, day, hour, minute)
        hoy = datetime.hoy
        doy = datetime.doy
        date = datetime
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvHOY)

def unregister():
    bpy.utils.unregister_class(SvHOY)
