import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvCreateLegend(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvCreateLegend'
    bl_label = 'LB Create Legend'
    sv_icon = 'LB_CREATELEGEND'
    sv__values: StringProperty(
        name='_values',
        update=updateNode,
        description='A list of numerical values or data collections that the legend refers to. This can also be the minimum and maximum numerical values of the data. The legend\'s maximum and minimum values will be set by the max and min of the data set.')
    sv__base_plane_: StringProperty(
        name='_base_plane_',
        update=updateNode,
        description='An optional plane or point to set the location of the legend. (Default: Rhino origin - (0, 0, 0))')
    sv_title_: StringProperty(
        name='title_',
        update=updateNode,
        description='A text string representing a legend title. Legends are usually titled with the units of the data.')
    sv_legend_par_: StringProperty(
        name='legend_par_',
        update=updateNode,
        description='Optional legend parameters from the "LB Legend Parameters" component.')
    sv_leg_par2d_: StringProperty(
        name='leg_par2d_',
        update=updateNode,
        description='Optional 2D LegendParameters from the "LB Legend Parameters 2D" component, which will be used to customize a legend in the plane of the screen so that it functions like a head-up display (HUD). If unspecified, the VisualizationSet will be rendered with 3D legends in the Rhino scene much like the other native Ladybug Tools components.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_values')
        input_node.prop_name = 'sv__values'
        input_node.tooltip = 'A list of numerical values or data collections that the legend refers to. This can also be the minimum and maximum numerical values of the data. The legend\'s maximum and minimum values will be set by the max and min of the data set.'
        input_node = self.inputs.new('SvLBSocket', '_base_plane_')
        input_node.prop_name = 'sv__base_plane_'
        input_node.tooltip = 'An optional plane or point to set the location of the legend. (Default: Rhino origin - (0, 0, 0))'
        input_node = self.inputs.new('SvLBSocket', 'title_')
        input_node.prop_name = 'sv_title_'
        input_node.tooltip = 'A text string representing a legend title. Legends are usually titled with the units of the data.'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'Optional legend parameters from the "LB Legend Parameters" component.'
        input_node = self.inputs.new('SvLBSocket', 'leg_par2d_')
        input_node.prop_name = 'sv_leg_par2d_'
        input_node.tooltip = 'Optional 2D LegendParameters from the "LB Legend Parameters 2D" component, which will be used to customize a legend in the plane of the screen so that it functions like a head-up display (HUD). If unspecified, the VisualizationSet will be rendered with 3D legends in the Rhino scene much like the other native Ladybug Tools components.'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'A colored mesh for the legend colors.'
        output_node = self.outputs.new('SvLBSocket', 'title_obj')
        output_node.tooltip = 'A text object for the  legend title.'
        output_node = self.outputs.new('SvLBSocket', 'label_objs')
        output_node.tooltip = 'An array of text objects for the label text.'
        output_node = self.outputs.new('SvLBSocket', 'label_text')
        output_node.tooltip = 'An array of text strings for the label text.'
        output_node = self.outputs.new('SvLBSocket', 'colors')
        output_node.tooltip = 'An array of colors that align with the input _values. This can be used to color geometry that aligns with the values.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Create a custom legend for any set of data or range. Creating a legend with this component allows for a bit more flexibility than what can be achieved by working with the legends automatically output from different studies. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['mesh', 'title_obj', 'label_objs', 'label_text', 'colors']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_values', '_base_plane_', 'title_', 'legend_par_', 'leg_par2d_']
        self.sv_input_types = ['System.Object', 'Plane', 'string', 'System.Object', 'System.Object']
        self.sv_input_defaults = [None, None, None, None, None]
        self.sv_input_access = ['list', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _values, _base_plane_, title_, legend_par_, leg_par2d_):


        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvCreateLegend)

def unregister():
    bpy.utils.unregister_class(SvCreateLegend)
