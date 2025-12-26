import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvAnalysisPeriod(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvAnalysisPeriod'
    bl_label = 'LB Analysis Period'
    sv_icon = 'LB_ANALYSISPERIOD'
    sv__start_month_: StringProperty(
        name='_start_month_',
        update=updateNode,
        description='Start month (1-12).')
    sv__start_day_: StringProperty(
        name='_start_day_',
        update=updateNode,
        description='Start day (1-31).')
    sv__start_hour_: StringProperty(
        name='_start_hour_',
        update=updateNode,
        description='Start hour (0-23).')
    sv__end_month_: StringProperty(
        name='_end_month_',
        update=updateNode,
        description='End month (1-12).')
    sv__end_day_: StringProperty(
        name='_end_day_',
        update=updateNode,
        description='End day (1-31).')
    sv__end_hour_: StringProperty(
        name='_end_hour_',
        update=updateNode,
        description='End hour (0-23).')
    sv__timestep_: StringProperty(
        name='_timestep_',
        update=updateNode,
        description='An integer number for the number of time steps per hours. Acceptable inputs include: 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_start_month_')
        input_node.prop_name = 'sv__start_month_'
        input_node.tooltip = 'Start month (1-12).'
        input_node = self.inputs.new('SvLBSocket', '_start_day_')
        input_node.prop_name = 'sv__start_day_'
        input_node.tooltip = 'Start day (1-31).'
        input_node = self.inputs.new('SvLBSocket', '_start_hour_')
        input_node.prop_name = 'sv__start_hour_'
        input_node.tooltip = 'Start hour (0-23).'
        input_node = self.inputs.new('SvLBSocket', '_end_month_')
        input_node.prop_name = 'sv__end_month_'
        input_node.tooltip = 'End month (1-12).'
        input_node = self.inputs.new('SvLBSocket', '_end_day_')
        input_node.prop_name = 'sv__end_day_'
        input_node.tooltip = 'End day (1-31).'
        input_node = self.inputs.new('SvLBSocket', '_end_hour_')
        input_node.prop_name = 'sv__end_hour_'
        input_node.tooltip = 'End hour (0-23).'
        input_node = self.inputs.new('SvLBSocket', '_timestep_')
        input_node.prop_name = 'sv__timestep_'
        input_node.tooltip = 'An integer number for the number of time steps per hours. Acceptable inputs include: 1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60'
        output_node = self.outputs.new('SvLBSocket', 'period')
        output_node.tooltip = 'Analysis period.'
        output_node = self.outputs.new('SvLBSocket', 'hoys')
        output_node.tooltip = 'List of dates in this analysis period.'
        output_node = self.outputs.new('SvLBSocket', 'dates')
        output_node.tooltip = 'List of hours of the year in this analysis period.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Create an Analysis Period to describe a slice of time during the year. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['period', 'hoys', 'dates']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_start_month_', '_start_day_', '_start_hour_', '_end_month_', '_end_day_', '_end_hour_', '_timestep_']
        self.sv_input_types = ['int', 'int', 'int', 'int', 'int', 'int', 'int']
        self.sv_input_defaults = [1, 1, 0, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _start_month_, _start_day_, _start_hour_, _end_month_, _end_day_, _end_hour_, _timestep_):

        try:
            import ladybug.analysisperiod as ap
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import wrap_output, turn_off_old_tag
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        turn_off_old_tag(ghenv.Component)
        
        
        anp = ap.AnalysisPeriod(
            _start_month_, _start_day_, _start_hour_,
            _end_month_, _end_day_, _end_hour_, _timestep_)
        
        if anp:
            period = anp
            dates = wrap_output(anp.datetimes)
            hoys = anp.hoys

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvAnalysisPeriod)

def unregister():
    bpy.utils.unregister_class(SvAnalysisPeriod)
