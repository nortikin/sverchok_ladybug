import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvAdaptPar(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvAdaptPar'
    bl_label = 'LB Adaptive Comfort Parameters'
    sv_icon = 'LB_ADAPTPAR'
    sv__ashrae_or_en_: StringProperty(
        name='_ashrae_or_en_',
        update=updateNode,
        description='A boolean to note whether to use the ASHRAE-55 neutral temperature function (True) or the european neutral function (False), which is consistent with both EN-15251 and EN-16798. Note that this input will also determine default values for many of the other properties of this object.')
    sv__neutral_offset_: StringProperty(
        name='_neutral_offset_',
        update=updateNode,
        description='The number of degrees Celcius from the neutral temperature where the input operative temperature is considered acceptable. The default is 2.5C when the neutral temperature function is ASHRAE-55 (consistent with 90% PPD) and 3C when the neutral temperature function is EN (consistent with comfort class II). _ For ASHRAE-55, the following neutral offsets apply. * 90 PPD - 2.5C * 80 PPD - 3.5C _ For the EN standard, the following neutral offsets apply. * Class I - 2C * Class II - 3C * Class III - 4C')
    sv__avgm_or_runmean_: StringProperty(
        name='_avgm_or_runmean_',
        update=updateNode,
        description='A boolean to note whether the prevailing outdoor temperature is computed from the average monthly temperature (True) or a weighted running mean of the last week (False).  The default is True when the neutral temperature function is ASHRAE-55 and False when the neutral temperature function is EN.')
    sv__discr_or_cont_vel_: StringProperty(
        name='_discr_or_cont_vel_',
        update=updateNode,
        description='A boolean to note whether discrete categories should be used to assess the effect of elevated air speed (True) or whether a continuous function should be used (False). Note that continuous air speeds were only used in the older EN-15251 standard and are not a part of the more recent EN-16798 standard. When unassigned, this will be True for discrete air speeds.')
    sv__cold_prevail_limit_: StringProperty(
        name='_cold_prevail_limit_',
        update=updateNode,
        description='A number indicating the prevailing outdoor temperature below which acceptable indoor operative temperatures flat line. The default is 10C, which is consistent with both ASHRAE-55 and EN-16798. However, 15C was used for the older EN-15251 standard. This number cannot be greater than 22C and cannot be less than 10C.')
    sv__conditioning_: StringProperty(
        name='_conditioning_',
        update=updateNode,
        description='A number between 0 and 1 that represents how "conditioned" vs. "free-running" the building is. 0 = free-running (completely passive with no air conditioning) 1 = conditioned (no operable windows and fully air conditioned) The default is 0 since both the ASHRAE-55 and the EN standards prohibit the use of adaptive comfort methods when a heating/cooling system is active. When set to a non-zero number, a neutral temperature function for heated/cooled operation derived from the SCATs database will be used. For more information on how adaptive comfort methods can be applied to conditioned buildings, see the neutral_temperature_conditioned function in the ladybug_comfort documentation.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_ashrae_or_en_')
        input_node.prop_name = 'sv__ashrae_or_en_'
        input_node.tooltip = 'A boolean to note whether to use the ASHRAE-55 neutral temperature function (True) or the european neutral function (False), which is consistent with both EN-15251 and EN-16798. Note that this input will also determine default values for many of the other properties of this object.'
        input_node = self.inputs.new('SvLBSocket', '_neutral_offset_')
        input_node.prop_name = 'sv__neutral_offset_'
        input_node.tooltip = 'The number of degrees Celcius from the neutral temperature where the input operative temperature is considered acceptable. The default is 2.5C when the neutral temperature function is ASHRAE-55 (consistent with 90% PPD) and 3C when the neutral temperature function is EN (consistent with comfort class II). _ For ASHRAE-55, the following neutral offsets apply. * 90 PPD - 2.5C * 80 PPD - 3.5C _ For the EN standard, the following neutral offsets apply. * Class I - 2C * Class II - 3C * Class III - 4C'
        input_node = self.inputs.new('SvLBSocket', '_avgm_or_runmean_')
        input_node.prop_name = 'sv__avgm_or_runmean_'
        input_node.tooltip = 'A boolean to note whether the prevailing outdoor temperature is computed from the average monthly temperature (True) or a weighted running mean of the last week (False).  The default is True when the neutral temperature function is ASHRAE-55 and False when the neutral temperature function is EN.'
        input_node = self.inputs.new('SvLBSocket', '_discr_or_cont_vel_')
        input_node.prop_name = 'sv__discr_or_cont_vel_'
        input_node.tooltip = 'A boolean to note whether discrete categories should be used to assess the effect of elevated air speed (True) or whether a continuous function should be used (False). Note that continuous air speeds were only used in the older EN-15251 standard and are not a part of the more recent EN-16798 standard. When unassigned, this will be True for discrete air speeds.'
        input_node = self.inputs.new('SvLBSocket', '_cold_prevail_limit_')
        input_node.prop_name = 'sv__cold_prevail_limit_'
        input_node.tooltip = 'A number indicating the prevailing outdoor temperature below which acceptable indoor operative temperatures flat line. The default is 10C, which is consistent with both ASHRAE-55 and EN-16798. However, 15C was used for the older EN-15251 standard. This number cannot be greater than 22C and cannot be less than 10C.'
        input_node = self.inputs.new('SvLBSocket', '_conditioning_')
        input_node.prop_name = 'sv__conditioning_'
        input_node.tooltip = 'A number between 0 and 1 that represents how "conditioned" vs. "free-running" the building is. 0 = free-running (completely passive with no air conditioning) 1 = conditioned (no operable windows and fully air conditioned) The default is 0 since both the ASHRAE-55 and the EN standards prohibit the use of adaptive comfort methods when a heating/cooling system is active. When set to a non-zero number, a neutral temperature function for heated/cooled operation derived from the SCATs database will be used. For more information on how adaptive comfort methods can be applied to conditioned buildings, see the neutral_temperature_conditioned function in the ladybug_comfort documentation.'
        output_node = self.outputs.new('SvLBSocket', 'adapt_par')
        output_node.tooltip = 'An Adaptive comfort parameter object that can be plugged into any of the components that compute Adaptive thermal comfort.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Create a set of parameters that define the acceptable conditions of the Adaptive thermal comfort model. - These parameters can be plugged into any of the components that compute Adaptive thermal comfort. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['adapt_par']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_ashrae_or_en_', '_neutral_offset_', '_avgm_or_runmean_', '_discr_or_cont_vel_', '_cold_prevail_limit_', '_conditioning_']
        self.sv_input_types = ['bool', 'double', 'bool', 'bool', 'double', 'double']
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

    def process_ladybug(self, _ashrae_or_en_, _neutral_offset_, _avgm_or_runmean_, _discr_or_cont_vel_, _cold_prevail_limit_, _conditioning_):

        try:
            from ladybug_comfort.parameter.adaptive import AdaptiveParameter
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_comfort:\n\t{}'.format(e))
        try:
            from ladybug_tools.sverchok import turn_off_old_tag
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        turn_off_old_tag(ghenv.Component)
        
        
        adapt_par = AdaptiveParameter(_ashrae_or_en_, _neutral_offset_,
                                      _avgm_or_runmean_, _discr_or_cont_vel_,
                                      _cold_prevail_limit_, _conditioning_)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvAdaptPar)

def unregister():
    bpy.utils.unregister_class(SvAdaptPar)
