import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvColRange(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvColRange'
    bl_label = 'LB Color Range'
    sv_icon = 'LB_COLRANGE'
    sv__index_: StringProperty(
        name='_index_',
        update=updateNode,
        description='An index refering to one of the following possible gradients: 0 - Original Ladybug 1 - Nuanced Ladybug 2 - Multi-colored Ladybug 3 - Ecotect 4 - View Study 5 - Shadow Study 6 - Glare Study 7 - Annual Comfort 8 - Thermal Comfort 9 - Peak Load Balance 10 - Heat Sensation 11 - Cold Sensation 12 - Benefit/Harm 13 - Harm 14 - Benefit 15 - Shade Benefit/Harm 16 - Shade Harm 17 - Shade Benefit 18 - Energy Balance 19 - Energy Balance w/ Storage 20 - THERM 21 - Cloud Cover 22 - Black to White 23 - Blue, Green, Red 24 - Multicolored 2 25 - Multicolored 3 26 - OpenStudio Palette 27 - Cividis (colorblind friendly) 28 - Viridis (colorblind friendly) 29 - Parula (colorblind friendly)')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_index_')
        input_node.prop_name = 'sv__index_'
        input_node.tooltip = 'An index refering to one of the following possible gradients: 0 - Original Ladybug 1 - Nuanced Ladybug 2 - Multi-colored Ladybug 3 - Ecotect 4 - View Study 5 - Shadow Study 6 - Glare Study 7 - Annual Comfort 8 - Thermal Comfort 9 - Peak Load Balance 10 - Heat Sensation 11 - Cold Sensation 12 - Benefit/Harm 13 - Harm 14 - Benefit 15 - Shade Benefit/Harm 16 - Shade Harm 17 - Shade Benefit 18 - Energy Balance 19 - Energy Balance w/ Storage 20 - THERM 21 - Cloud Cover 22 - Black to White 23 - Blue, Green, Red 24 - Multicolored 2 25 - Multicolored 3 26 - OpenStudio Palette 27 - Cividis (colorblind friendly) 28 - Viridis (colorblind friendly) 29 - Parula (colorblind friendly)'
        output_node = self.outputs.new('SvLBSocket', 'colors')
        output_node.tooltip = 'A series of colors to be plugged into the "LB Legend Parameters" component.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Use this component to access a library of typical gradients useful throughout Ladybug.  The output from this component should be plugged into the colors_ input of the "Legend Parameters" component. - Note that the colorblind friendly schemes have prioritized readability for red-green colorblindness (deuteranomaly, protanomaly, protanopia, and deuteranopia), which is by far more common than blue-yellow colorblindness. However, they are not necessarily ideal for all types of color blindness, though they are monotonic and perceptually uniform to all forms of color vision. This means that they should be readable as a dark-to-light scale by anyone. - For an image of each of the gardients in the library, check here: https://github.com/ladybug-tools/lbt-grasshopper/blob/master/gradients.png -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['colors']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_index_']
        self.sv_input_types = ['int']
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

    def process_ladybug(self, _index_):

        try:
            from ladybug.color import Colorset
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.color import color_to_color
            from ladybug_tools.sverchok import turn_off_old_tag
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        turn_off_old_tag(ghenv.Component)
        
        
        _index_ = _index_ or 0
        cs = Colorset()
        colors = [color_to_color(col) for col in cs[_index_]]
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvColRange)

def unregister():
    bpy.utils.unregister_class(SvColRange)
