import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvRelHumid(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvRelHumid'
    bl_label = 'LB Relative Humidity from Dew Point'
    sv_icon = 'LB_RELHUMID'
    sv__dry_bulb: StringProperty(
        name='_dry_bulb',
        update=updateNode,
        description='A value or data collection representing dry bulb temperature [C]')
    sv__dew_point: StringProperty(
        name='_dew_point',
        update=updateNode,
        description='A value or data collection representing dew point temperature [C]')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_dry_bulb')
        input_node.prop_name = 'sv__dry_bulb'
        input_node.tooltip = 'A value or data collection representing dry bulb temperature [C]'
        input_node = self.inputs.new('SvLBSocket', '_dew_point')
        input_node.prop_name = 'sv__dew_point'
        input_node.tooltip = 'A value or data collection representing dew point temperature [C]'
        output_node = self.outputs.new('SvLBSocket', 'rel_humid')
        output_node.tooltip = 'A data collection or value indicating the relative humidity [%]'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate relative humidity from Dry Bulb Temperature and Dew Point Temperature. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['rel_humid']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_dry_bulb', '_dew_point']
        self.sv_input_types = ['System.Object', 'System.Object']
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

    def process_ladybug(self, _dry_bulb, _dew_point):

        try:
            from ladybug.psychrometrics import rel_humid_from_db_dpt
            from ladybug.datacollection import HourlyContinuousCollection
            from ladybug.datatype.fraction import RelativeHumidity
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            rel_humid = HourlyContinuousCollection.compute_function_aligned(
                rel_humid_from_db_dpt, [_dry_bulb, _dew_point], RelativeHumidity(), '%')
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvRelHumid)

def unregister():
    bpy.utils.unregister_class(SvRelHumid)
