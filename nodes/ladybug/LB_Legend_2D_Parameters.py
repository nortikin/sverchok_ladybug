import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvLegend2D(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvLegend2D'
    bl_label = 'LB Legend 2D Parameters'
    sv_icon = 'LB_LEGEND2D'
    sv_origin_x_: StringProperty(
        name='origin_x_',
        update=updateNode,
        description='An integer in pixels to note the X coordinate of the base point from where the 2D legend will be generated (assuming an origin in the upper-left corner of the screen with higher positive values of X moving to the right). Alternatively, this can be a text string ending in a % sign to denote the percentage of the screen where the X coordinate exists (eg. 5%). The default is set to make the legend clearly visible in the upper-left corner of the screen (10 pixels).')
    sv_origin_y_: StringProperty(
        name='origin_y_',
        update=updateNode,
        description='An integer in pixels to note the Y coordinate of the base point from where the legend will be generated (assuming an origin in the upper-left corner of the screen with higher positive values of Y moving downward). Alternatively, this can be a text string ending in a % sign to denote the percentage of the screen where the X coordinate exists (eg. 5%). The default is set to make the legend clearly visible in the upper-left corner of the screen (50 pixels).')
    sv_seg_height_: StringProperty(
        name='seg_height_',
        update=updateNode,
        description='A integer in pixels to note the height for each of the legend segments. Alternatively, this can be a text string ending in a % sign to denote the percentage of the screen (eg. 5%). The default is set to make most legends readable on standard resolution screens (25px for horizontal and 36px for vertical).')
    sv_seg_width_: StringProperty(
        name='seg_width_',
        update=updateNode,
        description='An integer in pixels to set the width of each of the legend segments. Alternatively, this can be a text string ending in a % sign to denote the percentage of the screen (eg. 5%). The default is set to make most legends readable on standard resolution screens (36px for horizontal and 25px for vertical).')
    sv_text_height_: StringProperty(
        name='text_height_',
        update=updateNode,
        description='An integer in pixels to set the height for the legend text. Alternatively, this can be a text string ending in a % sign to denote the percentage of the screen (eg. 2%).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', 'origin_x_')
        input_node.prop_name = 'sv_origin_x_'
        input_node.tooltip = 'An integer in pixels to note the X coordinate of the base point from where the 2D legend will be generated (assuming an origin in the upper-left corner of the screen with higher positive values of X moving to the right). Alternatively, this can be a text string ending in a % sign to denote the percentage of the screen where the X coordinate exists (eg. 5%). The default is set to make the legend clearly visible in the upper-left corner of the screen (10 pixels).'
        input_node = self.inputs.new('SvLBSocket', 'origin_y_')
        input_node.prop_name = 'sv_origin_y_'
        input_node.tooltip = 'An integer in pixels to note the Y coordinate of the base point from where the legend will be generated (assuming an origin in the upper-left corner of the screen with higher positive values of Y moving downward). Alternatively, this can be a text string ending in a % sign to denote the percentage of the screen where the X coordinate exists (eg. 5%). The default is set to make the legend clearly visible in the upper-left corner of the screen (50 pixels).'
        input_node = self.inputs.new('SvLBSocket', 'seg_height_')
        input_node.prop_name = 'sv_seg_height_'
        input_node.tooltip = 'A integer in pixels to note the height for each of the legend segments. Alternatively, this can be a text string ending in a % sign to denote the percentage of the screen (eg. 5%). The default is set to make most legends readable on standard resolution screens (25px for horizontal and 36px for vertical).'
        input_node = self.inputs.new('SvLBSocket', 'seg_width_')
        input_node.prop_name = 'sv_seg_width_'
        input_node.tooltip = 'An integer in pixels to set the width of each of the legend segments. Alternatively, this can be a text string ending in a % sign to denote the percentage of the screen (eg. 5%). The default is set to make most legends readable on standard resolution screens (36px for horizontal and 25px for vertical).'
        input_node = self.inputs.new('SvLBSocket', 'text_height_')
        input_node.prop_name = 'sv_text_height_'
        input_node.tooltip = 'An integer in pixels to set the height for the legend text. Alternatively, this can be a text string ending in a % sign to denote the percentage of the screen (eg. 2%).'
        output_node = self.outputs.new('SvLBSocket', 'leg_par2d')
        output_node.tooltip = 'A legend parameter object that can be plugged into any of the Ladybug components with a legend.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Customize the properties of a screen-oreinted 2D legend displaying with the "LB Preview VisualizationSet" component. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['leg_par2d']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['origin_x_', 'origin_y_', 'seg_height_', 'seg_width_', 'text_height_']
        self.sv_input_types = ['string', 'string', 'string', 'string', 'string']
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

    def process_ladybug(self, origin_x_, origin_y_, seg_height_, seg_width_, text_height_):

        
        try:
            from ladybug.legend import Legend2DParameters
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        try:
            from ladybug_tools.sverchok import turn_off_old_tag
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        turn_off_old_tag(ghenv.Component)
        
        
        def parse_dim_text(dim_text):
            """Parse text representing a dimension into an input for legend parameters."""
            try:
                px_txt = int(dim_text)
                return '{}px'.format(px_txt)
            except ValueError:
                return dim_text
        
        
        # parse all of the inputs
        origin_x_ = parse_dim_text(origin_x_) if origin_x_ is not None else None
        origin_y_ = parse_dim_text(origin_y_) if origin_y_ is not None else None
        seg_height_ = parse_dim_text(seg_height_) if seg_height_ is not None else None
        seg_width_ = parse_dim_text(seg_width_) if seg_width_ is not None else None
        text_height_ = parse_dim_text(text_height_) if text_height_ is not None else None
        
        # make the 2D legend parameters
        leg_par2d = Legend2DParameters(origin_x_, origin_y_, seg_height_, seg_width_, text_height_)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvLegend2D)

def unregister():
    bpy.utils.unregister_class(SvLegend2D)
