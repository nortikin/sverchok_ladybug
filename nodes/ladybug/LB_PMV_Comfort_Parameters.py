import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvPMVPar(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvPMVPar'
    bl_label = 'LB PMV Comfort Parameters'
    sv_icon = 'LB_PMVPAR'
    sv__ppd_thresh_: StringProperty(
        name='_ppd_thresh_',
        update=updateNode,
        description='A number between 5 and 100 that represents the upper threshold of PPD that is considered acceptable. Default is 10, which charcterizes most buildings in the ASHRAE-55 and EN-15251 standards.')
    sv__hr_upper_: StringProperty(
        name='_hr_upper_',
        update=updateNode,
        description='A number between 0 and 1 indicating the upper limit of humidity ratio that is considered acceptable. Default is 1 for essentially no limit.')
    sv__hr_lower_: StringProperty(
        name='_hr_lower_',
        update=updateNode,
        description='A number between 0 and 1 indicating the lower limit of humidity ratio considered acceptable. Default is 0 for essentially no limit.')
    sv__still_air_thresh_: StringProperty(
        name='_still_air_thresh_',
        update=updateNode,
        description='The air speed threshold in m/s at which the standard effective temperature (SET) model will be used to correct for the cooling effect of elevated air speeds. Default is 0.1 m/s, which is the limit according to ASHRAE-55.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_ppd_thresh_')
        input_node.prop_name = 'sv__ppd_thresh_'
        input_node.tooltip = 'A number between 5 and 100 that represents the upper threshold of PPD that is considered acceptable. Default is 10, which charcterizes most buildings in the ASHRAE-55 and EN-15251 standards.'
        input_node = self.inputs.new('SvLBSocket', '_hr_upper_')
        input_node.prop_name = 'sv__hr_upper_'
        input_node.tooltip = 'A number between 0 and 1 indicating the upper limit of humidity ratio that is considered acceptable. Default is 1 for essentially no limit.'
        input_node = self.inputs.new('SvLBSocket', '_hr_lower_')
        input_node.prop_name = 'sv__hr_lower_'
        input_node.tooltip = 'A number between 0 and 1 indicating the lower limit of humidity ratio considered acceptable. Default is 0 for essentially no limit.'
        input_node = self.inputs.new('SvLBSocket', '_still_air_thresh_')
        input_node.prop_name = 'sv__still_air_thresh_'
        input_node.tooltip = 'The air speed threshold in m/s at which the standard effective temperature (SET) model will be used to correct for the cooling effect of elevated air speeds. Default is 0.1 m/s, which is the limit according to ASHRAE-55.'
        output_node = self.outputs.new('SvLBSocket', 'pmv_par')
        output_node.tooltip = 'A PMV comfort parameter object that can be plugged into any of the components that compute PMV thermal comfort.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Create a set of parameters that define the acceptable conditions of the Predicted Mean Vote (PMV) thermal comfort model. - These parameters can be plugged into any of the components that compute PMV thermal comfort. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['pmv_par']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_ppd_thresh_', '_hr_upper_', '_hr_lower_', '_still_air_thresh_']
        self.sv_input_types = ['double', 'double', 'double', 'double']
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

    def process_ladybug(self, _ppd_thresh_, _hr_upper_, _hr_lower_, _still_air_thresh_):

        try:
            from ladybug_comfort.parameter.pmv import PMVParameter
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_comfort:\n\t{}'.format(e))
        try:
            from ladybug_tools.sverchok import turn_off_old_tag
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        turn_off_old_tag(ghenv.Component)
        
        
        pmv_par = PMVParameter(_ppd_thresh_, _hr_upper_, _hr_lower_, _still_air_thresh_)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvPMVPar)

def unregister():
    bpy.utils.unregister_class(SvPMVPar)
