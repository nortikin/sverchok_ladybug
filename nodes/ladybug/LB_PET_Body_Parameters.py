import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvPETPar(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvPETPar'
    bl_label = 'LB PET Body Parameters'
    sv_icon = 'LB_PETPAR'
    sv__age_: StringProperty(
        name='_age_',
        update=updateNode,
        description='The age of the human subject in years. (Default: 36 years for middle age of the average worldwide life expectancy).')
    sv__sex_: StringProperty(
        name='_sex_',
        update=updateNode,
        description='A value between 0 and 1 to indicate the sex of the human subject, which influences the computation of basal metabolism. 0 indicates male. 1 indicates female and any number in between denotes a weighted average between the two. (Default: 0.5).')
    sv__height_: StringProperty(
        name='_height_',
        update=updateNode,
        description='The height of the human subject in meters. Average male height is around 1.75m while average female height is 1.55m. (Default: 1.65m for a worldwide average between male and female height).')
    sv__body_mass_: StringProperty(
        name='_body_mass_',
        update=updateNode,
        description='The body mass of the human subject in kilograms. (Default: 62 kg for the worldwide average adult human body mass).')
    sv__posture_: StringProperty(
        name='_posture_',
        update=updateNode,
        description='A text string indicating the posture of the body. Letters must be lowercase. Default is "standing". Choose from the following: _ * standing * seated * crouching')
    sv_humid_acclim_: StringProperty(
        name='humid_acclim_',
        update=updateNode,
        description='A boolean to note whether the human subject is acclimated to a humid/tropical climate (True) or is acclimated to a temperate climate (False). When True, the categories developed by Lin and Matzarakis (2008) will be used to assess comfort instead of the original categories developed by Matzarakis and Mayer (1996).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_age_')
        input_node.prop_name = 'sv__age_'
        input_node.tooltip = 'The age of the human subject in years. (Default: 36 years for middle age of the average worldwide life expectancy).'
        input_node = self.inputs.new('SvLBSocket', '_sex_')
        input_node.prop_name = 'sv__sex_'
        input_node.tooltip = 'A value between 0 and 1 to indicate the sex of the human subject, which influences the computation of basal metabolism. 0 indicates male. 1 indicates female and any number in between denotes a weighted average between the two. (Default: 0.5).'
        input_node = self.inputs.new('SvLBSocket', '_height_')
        input_node.prop_name = 'sv__height_'
        input_node.tooltip = 'The height of the human subject in meters. Average male height is around 1.75m while average female height is 1.55m. (Default: 1.65m for a worldwide average between male and female height).'
        input_node = self.inputs.new('SvLBSocket', '_body_mass_')
        input_node.prop_name = 'sv__body_mass_'
        input_node.tooltip = 'The body mass of the human subject in kilograms. (Default: 62 kg for the worldwide average adult human body mass).'
        input_node = self.inputs.new('SvLBSocket', '_posture_')
        input_node.prop_name = 'sv__posture_'
        input_node.tooltip = 'A text string indicating the posture of the body. Letters must be lowercase. Default is "standing". Choose from the following: _ * standing * seated * crouching'
        input_node = self.inputs.new('SvLBSocket', 'humid_acclim_')
        input_node.prop_name = 'sv_humid_acclim_'
        input_node.tooltip = 'A boolean to note whether the human subject is acclimated to a humid/tropical climate (True) or is acclimated to a temperate climate (False). When True, the categories developed by Lin and Matzarakis (2008) will be used to assess comfort instead of the original categories developed by Matzarakis and Mayer (1996).'
        output_node = self.outputs.new('SvLBSocket', 'pet_par')
        output_node.tooltip = 'A PET comfort parameter object that can be plugged into any of the components that compute PET thermal comfort.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Create a set of parameters that define the body characteristics for the PET model. - These parameters can be plugged into any of the components that compute PET thermal comfort. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['pet_par']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_age_', '_sex_', '_height_', '_body_mass_', '_posture_', 'humid_acclim_']
        self.sv_input_types = ['double', 'double', 'double', 'double', 'string', 'bool']
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

    def process_ladybug(self, _age_, _sex_, _height_, _body_mass_, _posture_, humid_acclim_):

        try:
            from ladybug_comfort.parameter.pet import PETParameter
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_comfort:\n\t{}'.format(e))
        try:
            from ladybug_tools.sverchok import turn_off_old_tag
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        turn_off_old_tag(ghenv.Component)
        
        
        pet_par = PETParameter(_age_, _sex_, _height_, _body_mass_, _posture_, humid_acclim_)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvPETPar)

def unregister():
    bpy.utils.unregister_class(SvPETPar)
