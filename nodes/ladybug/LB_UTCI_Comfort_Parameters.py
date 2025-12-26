import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvUTCIPar(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvUTCIPar'
    bl_label = 'LB UTCI Comfort Parameters'
    sv_icon = 'LB_UTCIPAR'
    sv__cold_thresh_: StringProperty(
        name='_cold_thresh_',
        update=updateNode,
        description='Temperature in Celsius below which the UTCI represents cold stress. (Default: 9C).')
    sv__heat_thresh_: StringProperty(
        name='_heat_thresh_',
        update=updateNode,
        description='A number between 0 and 1 indicating the upper limit of humidity ratio that is considered acceptable. Default is 1 for essentially no limit.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_cold_thresh_')
        input_node.prop_name = 'sv__cold_thresh_'
        input_node.tooltip = 'Temperature in Celsius below which the UTCI represents cold stress. (Default: 9C).'
        input_node = self.inputs.new('SvLBSocket', '_heat_thresh_')
        input_node.prop_name = 'sv__heat_thresh_'
        input_node.tooltip = 'A number between 0 and 1 indicating the upper limit of humidity ratio that is considered acceptable. Default is 1 for essentially no limit.'
        output_node = self.outputs.new('SvLBSocket', 'utci_par')
        output_node.tooltip = 'A UTCI comfort parameter object that can be plugged into any of the components that compute UTCI thermal comfort.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Create a set of parameters that define the acceptable conditions of the Universal Thermal Climate Index (UTCI) comfort model. - These parameters can be plugged into any of the components that compute UTCI comfort. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['utci_par']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_cold_thresh_', '_heat_thresh_']
        self.sv_input_types = ['double', 'double']
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

    def process_ladybug(self, _cold_thresh_, _heat_thresh_):

        try:
            from ladybug_comfort.parameter.utci import UTCIParameter
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_comfort:\n\t{}'.format(e))
        try:
            from ladybug_tools.sverchok import turn_off_old_tag
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        turn_off_old_tag(ghenv.Component)
        
        
        moderate_cold, moderate_heat = None, None
        if _cold_thresh_ and _cold_thresh_ < 0:
            moderate_cold = _cold_thresh_
        if _heat_thresh_ and _heat_thresh_ > 28:
            moderate_heat = _heat_thresh_
        
        utci_par = UTCIParameter(
            cold_thresh=_cold_thresh_,
            heat_thresh=_heat_thresh_,
            moderate_cold_thresh=moderate_cold,
            moderate_heat_thresh=moderate_heat
        )
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvUTCIPar)

def unregister():
    bpy.utils.unregister_class(SvUTCIPar)
