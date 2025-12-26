import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvText2D(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvText2D'
    bl_label = 'LB Screen Oriented Text'
    sv_icon = 'LB_TEXT2D'
    sv__text: StringProperty(
        name='_text',
        update=updateNode,
        description='Text string to be displayed in the plane of the screen.')
    sv_leg_par2d_: StringProperty(
        name='leg_par2d_',
        update=updateNode,
        description='Optional 2D LegendParameters from the "LB Legend Parameters 2D" component, which will be used to customize a text in the plane of the screen. Note that only the text_height, origin_x and origin_y inputs of this component affect the placement of the text.')
    sv__font_: StringProperty(
        name='_font_',
        update=updateNode,
        description='An optional text string to specify the font to be used for the text. Examples include "Arial", "Times New Roman", "Courier" (all without quotations). Default is "Arial".')
    sv__color_: StringProperty(
        name='_color_',
        update=updateNode,
        description='An optional color to set the color of the text. If unspecified, it will be black.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_text')
        input_node.prop_name = 'sv__text'
        input_node.tooltip = 'Text string to be displayed in the plane of the screen.'
        input_node = self.inputs.new('SvLBSocket', 'leg_par2d_')
        input_node.prop_name = 'sv_leg_par2d_'
        input_node.tooltip = 'Optional 2D LegendParameters from the "LB Legend Parameters 2D" component, which will be used to customize a text in the plane of the screen. Note that only the text_height, origin_x and origin_y inputs of this component affect the placement of the text.'
        input_node = self.inputs.new('SvLBSocket', '_font_')
        input_node.prop_name = 'sv__font_'
        input_node.tooltip = 'An optional text string to specify the font to be used for the text. Examples include "Arial", "Times New Roman", "Courier" (all without quotations). Default is "Arial".'
        input_node = self.inputs.new('SvLBSocket', '_color_')
        input_node.prop_name = 'sv__color_'
        input_node.tooltip = 'An optional color to set the color of the text. If unspecified, it will be black.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Generate screen-oriented text that displays in the Rhino scene as a head-up display (HUD). _ This is useful when there are certain summary results or information that should always be displayed on-screen. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = []
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_text', 'leg_par2d_', '_font_', '_color_']
        self.sv_input_types = ['string', 'System.Object', 'string', 'System.Drawing.Color']
        self.sv_input_defaults = [None, None, None, None]
        self.sv_input_access = ['list', 'list', 'item', 'item']
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

    def process_ladybug(self, _text, leg_par2d_, _font_, _color_):


        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvText2D)

def unregister():
    bpy.utils.unregister_class(SvText2D)
