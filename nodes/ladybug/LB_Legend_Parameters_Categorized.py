import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvLegendParCategorized(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvLegendParCategorized'
    bl_label = 'LB Legend Parameters Categorized'
    sv_icon = 'LB_LEGENDPARCATEGORIZED'
    sv__domain: StringProperty(
        name='_domain',
        update=updateNode,
        description='A list of one or more numbers noting the bondaries of the data categories. For example, [100, 2000] creates three categories of (<100, 100-2000, >2000). Values must always be ordered from lowest to highest.')
    sv__colors: StringProperty(
        name='_colors',
        update=updateNode,
        description='An list of color objects with a length equal to the number of items in the domain + 1. These are used to color each of the categories of data.')
    sv_categories_: StringProperty(
        name='categories_',
        update=updateNode,
        description='An optional list of text strings with a length equal to the colors. These will be used to name each of the categories in the legend. If None, the legend text will simply mark the numerical ranges of the categories. (Default: None).')
    sv_continuous_cols_: StringProperty(
        name='continuous_cols_',
        update=updateNode,
        description='Boolean noting whether colors generated are continuous or discrete. If True, the colors generated from the corresponding legend will be in a continuous gradient. If False, they will be categorized in incremental groups according to the segment_count.')
    sv_continuous_leg_: StringProperty(
        name='continuous_leg_',
        update=updateNode,
        description='Boolean. If True, the colors along the legend will be in a continuous gradient. If False, they will be categorized in incremental groups according to the number_of_segments. Default is False for depicting discrete categories.')
    sv_num_decimals_: StringProperty(
        name='num_decimals_',
        update=updateNode,
        description='An optional integer to set the number of decimal places for the numbers in the legend text. Default is 2.')
    sv_larger_smaller_: StringProperty(
        name='larger_smaller_',
        update=updateNode,
        description='Boolean noting whether to include larger than and smaller than (> and <) values after the upper and lower legend segment text. Default is False.')
    sv_vert_or_horiz_: StringProperty(
        name='vert_or_horiz_',
        update=updateNode,
        description='Boolean. If True, the legend mesh and text points will be generated vertically.  If False, they will genrate a horizontal legend. Default is True for a vertically-oriented legend.')
    sv_base_plane_: StringProperty(
        name='base_plane_',
        update=updateNode,
        description='A Plane to note the starting point and orientation from where the legend will be genrated. The default is the world XY plane at origin (0, 0, 0).')
    sv_seg_height_: StringProperty(
        name='seg_height_',
        update=updateNode,
        description='An optional number to set the height of each of the legend segments. Default is 1.')
    sv_seg_width_: StringProperty(
        name='seg_width_',
        update=updateNode,
        description='An optional number to set the width of each of the legend segments. Default is 1 when legend is vertical. When horizontal, the default is (text_height * (number_decimal_places + 2)).')
    sv_text_height_: StringProperty(
        name='text_height_',
        update=updateNode,
        description='An optional number to set the size of the text in model units. Default is half of the segment_height.')
    sv_font_: StringProperty(
        name='font_',
        update=updateNode,
        description='An optional text string to specify the font to be used for the text. Examples include "Arial", "Times New Roman", "Courier" (all without quotations). Default is "Arial".')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_domain')
        input_node.prop_name = 'sv__domain'
        input_node.tooltip = 'A list of one or more numbers noting the bondaries of the data categories. For example, [100, 2000] creates three categories of (<100, 100-2000, >2000). Values must always be ordered from lowest to highest.'
        input_node = self.inputs.new('SvLBSocket', '_colors')
        input_node.prop_name = 'sv__colors'
        input_node.tooltip = 'An list of color objects with a length equal to the number of items in the domain + 1. These are used to color each of the categories of data.'
        input_node = self.inputs.new('SvLBSocket', 'categories_')
        input_node.prop_name = 'sv_categories_'
        input_node.tooltip = 'An optional list of text strings with a length equal to the colors. These will be used to name each of the categories in the legend. If None, the legend text will simply mark the numerical ranges of the categories. (Default: None).'
        input_node = self.inputs.new('SvLBSocket', 'continuous_cols_')
        input_node.prop_name = 'sv_continuous_cols_'
        input_node.tooltip = 'Boolean noting whether colors generated are continuous or discrete. If True, the colors generated from the corresponding legend will be in a continuous gradient. If False, they will be categorized in incremental groups according to the segment_count.'
        input_node = self.inputs.new('SvLBSocket', 'continuous_leg_')
        input_node.prop_name = 'sv_continuous_leg_'
        input_node.tooltip = 'Boolean. If True, the colors along the legend will be in a continuous gradient. If False, they will be categorized in incremental groups according to the number_of_segments. Default is False for depicting discrete categories.'
        input_node = self.inputs.new('SvLBSocket', 'num_decimals_')
        input_node.prop_name = 'sv_num_decimals_'
        input_node.tooltip = 'An optional integer to set the number of decimal places for the numbers in the legend text. Default is 2.'
        input_node = self.inputs.new('SvLBSocket', 'larger_smaller_')
        input_node.prop_name = 'sv_larger_smaller_'
        input_node.tooltip = 'Boolean noting whether to include larger than and smaller than (> and <) values after the upper and lower legend segment text. Default is False.'
        input_node = self.inputs.new('SvLBSocket', 'vert_or_horiz_')
        input_node.prop_name = 'sv_vert_or_horiz_'
        input_node.tooltip = 'Boolean. If True, the legend mesh and text points will be generated vertically.  If False, they will genrate a horizontal legend. Default is True for a vertically-oriented legend.'
        input_node = self.inputs.new('SvLBSocket', 'base_plane_')
        input_node.prop_name = 'sv_base_plane_'
        input_node.tooltip = 'A Plane to note the starting point and orientation from where the legend will be genrated. The default is the world XY plane at origin (0, 0, 0).'
        input_node = self.inputs.new('SvLBSocket', 'seg_height_')
        input_node.prop_name = 'sv_seg_height_'
        input_node.tooltip = 'An optional number to set the height of each of the legend segments. Default is 1.'
        input_node = self.inputs.new('SvLBSocket', 'seg_width_')
        input_node.prop_name = 'sv_seg_width_'
        input_node.tooltip = 'An optional number to set the width of each of the legend segments. Default is 1 when legend is vertical. When horizontal, the default is (text_height * (number_decimal_places + 2)).'
        input_node = self.inputs.new('SvLBSocket', 'text_height_')
        input_node.prop_name = 'sv_text_height_'
        input_node.tooltip = 'An optional number to set the size of the text in model units. Default is half of the segment_height.'
        input_node = self.inputs.new('SvLBSocket', 'font_')
        input_node.prop_name = 'sv_font_'
        input_node.tooltip = 'An optional text string to specify the font to be used for the text. Examples include "Arial", "Times New Roman", "Courier" (all without quotations). Default is "Arial".'
        output_node = self.outputs.new('SvLBSocket', 'leg_par')
        output_node.tooltip = 'A legend parameter object that can be plugged into any of the Ladybug components with a legend.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Use this component to change the colors, range, and display of any Ladybug legend along with the corresponding colored mesh that the legend refers to. - The legend parameters from this component have more limitations than the normal Legend Parameters. However, these legend parameters will do auto-categorization of data, binning values into groups based on custom ranges. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['leg_par']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_domain', '_colors', 'categories_', 'continuous_cols_', 'continuous_leg_', 'num_decimals_', 'larger_smaller_', 'vert_or_horiz_', 'base_plane_', 'seg_height_', 'seg_width_', 'text_height_', 'font_']
        self.sv_input_types = ['double', 'System.Drawing.Color', 'string', 'bool', 'bool', 'int', 'bool', 'bool', 'Plane', 'double', 'double', 'double', 'string']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['list', 'list', 'list', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _domain, _colors, categories_, continuous_cols_, continuous_leg_, num_decimals_, larger_smaller_, vert_or_horiz_, base_plane_, seg_height_, seg_width_, text_height_, font_):

        
        try:
            from ladybug.legend import LegendParametersCategorized
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.togeometry import to_plane
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            if base_plane_:
                base_plane_ = to_plane(base_plane_)
            if len(categories_) == 0:
                categories_ = None
        
            leg_par = LegendParametersCategorized(
                domain=_domain, colors=_colors, category_names=categories_,
                base_plane=base_plane_)
        
            leg_par.continuous_colors = continuous_cols_
            leg_par.continuous_legend = continuous_leg_
            leg_par.decimal_count = num_decimals_
            leg_par.include_larger_smaller = larger_smaller_
            leg_par.vertical = vert_or_horiz_
            leg_par.segment_height = seg_height_
            leg_par.segment_width = seg_width_
            leg_par.text_height = text_height_
            leg_par.font = font_
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvLegendParCategorized)

def unregister():
    bpy.utils.unregister_class(SvLegendParCategorized)
