import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvSolarBodyPar(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvSolarBodyPar'
    bl_label = 'LB Solar Body Parameters'
    sv_icon = 'LB_SOLARBODYPAR'
    sv__posture_: StringProperty(
        name='_posture_',
        update=updateNode,
        description='A text string indicating the posture of the body. Letters must be lowercase. Default is "standing". Choose from the following: - standing - seated - supine')
    sv__sharp_: StringProperty(
        name='_sharp_',
        update=updateNode,
        description='A number between 0 and 180 representing the solar horizontal angle relative to front of person (SHARP). 0 signifies sun that is shining directly into the person\'s face and 180 signifies sun that is shining at the person\'s back. Default is 135, asuming that a person typically faces their side or back to the sun to avoid glare.')
    sv__body_az_: StringProperty(
        name='_body_az_',
        update=updateNode,
        description='A number between 0 and 360 representing the direction that the human is facing in degrees (0=North, 90=East, 180=South, 270=West). Default is None, which will assume that the sharp input dictates the degrees the human is facing from the sun.')
    sv__absorptivity_: StringProperty(
        name='_absorptivity_',
        update=updateNode,
        description='A number between 0 and 1 representing the average shortwave absorptivity of the body (including clothing and skin color). Typical clothing values - white: 0.2, khaki: 0.57, black: 0.88 Typical skin values - white: 0.57, brown: 0.65, black: 0.84 Default is 0.7 for average (brown) skin and medium clothing.')
    sv__emissivity_: StringProperty(
        name='_emissivity_',
        update=updateNode,
        description='A number between 0 and 1 representing the average longwave emissivity of the body.  Default is 0.95, which is almost always the case except in rare situations of wearing metalic clothing.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_posture_')
        input_node.prop_name = 'sv__posture_'
        input_node.tooltip = 'A text string indicating the posture of the body. Letters must be lowercase. Default is "standing". Choose from the following: - standing - seated - supine'
        input_node = self.inputs.new('SvLBSocket', '_sharp_')
        input_node.prop_name = 'sv__sharp_'
        input_node.tooltip = 'A number between 0 and 180 representing the solar horizontal angle relative to front of person (SHARP). 0 signifies sun that is shining directly into the person\'s face and 180 signifies sun that is shining at the person\'s back. Default is 135, asuming that a person typically faces their side or back to the sun to avoid glare.'
        input_node = self.inputs.new('SvLBSocket', '_body_az_')
        input_node.prop_name = 'sv__body_az_'
        input_node.tooltip = 'A number between 0 and 360 representing the direction that the human is facing in degrees (0=North, 90=East, 180=South, 270=West). Default is None, which will assume that the sharp input dictates the degrees the human is facing from the sun.'
        input_node = self.inputs.new('SvLBSocket', '_absorptivity_')
        input_node.prop_name = 'sv__absorptivity_'
        input_node.tooltip = 'A number between 0 and 1 representing the average shortwave absorptivity of the body (including clothing and skin color). Typical clothing values - white: 0.2, khaki: 0.57, black: 0.88 Typical skin values - white: 0.57, brown: 0.65, black: 0.84 Default is 0.7 for average (brown) skin and medium clothing.'
        input_node = self.inputs.new('SvLBSocket', '_emissivity_')
        input_node.prop_name = 'sv__emissivity_'
        input_node.tooltip = 'A number between 0 and 1 representing the average longwave emissivity of the body.  Default is 0.95, which is almost always the case except in rare situations of wearing metalic clothing.'
        output_node = self.outputs.new('SvLBSocket', 'sol_body_par')
        output_node.tooltip = 'A solar body parameter object that can be plugged into any of the components that estimate mean radiant temperature (MRT) deltas as a result of being in the sun.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Create a set of parameters that define the characteristics of a human in relation to the sun that falls on them. - These parameters can be plugged into any of the components that estimate mean radiant temperature (MRT) deltas as a result of being in the sun. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['sol_body_par']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_posture_', '_sharp_', '_body_az_', '_absorptivity_', '_emissivity_']
        self.sv_input_types = ['string', 'double', 'double', 'double', 'double']
        self.sv_input_defaults = [None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _posture_, _sharp_, _body_az_, _absorptivity_, _emissivity_):

        try:
            from ladybug_comfort.parameter.solarcal import SolarCalParameter
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_comfort:\n\t{}'.format(e))
        try:
            from ladybug_tools.sverchok import turn_off_old_tag
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        turn_off_old_tag(ghenv.Component)
        
        
        sol_body_par = SolarCalParameter(_posture_, _sharp_, _body_az_,
                                        _absorptivity_, _emissivity_)

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvSolarBodyPar)

def unregister():
    bpy.utils.unregister_class(SvSolarBodyPar)
