import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvVisSet(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvVisSet'
    bl_label = 'LB Preview VisualizationSet'
    sv_icon = 'LB_VISSET'
    sv__vis_set: StringProperty(
        name='_vis_set',
        update=updateNode,
        description='VisualizationSet arguments from any Ladybug Tools component with a vis_set output. This can also be the path to a .vsf file that exists on this machine (these files are often written with the "LB Dump VisualizationSet" component). Lastly, this input can be a custom VisualizationSet that has been created with the Ladybug Tools SDK.')
    sv_leg_par_: StringProperty(
        name='leg_par_',
        update=updateNode,
        description='Script variable VisSet')
    sv_leg_par2d_: StringProperty(
        name='leg_par2d_',
        update=updateNode,
        description='Optional 2D LegendParameters from the "LB Legend Parameters 2D" component, which will be used to customize a legend in the plane of the screen so that it functions like a head-up display (HUD). If unspecified, the VisualizationSet will be rendered with 3D legends in the Rhino scene much like the other native Ladybug Tools components.')
    sv_data_set_: StringProperty(
        name='data_set_',
        update=updateNode,
        description='Optional text or an integer to select a specific data set from analysis geometries within the Visualization Set. Note that this input only has meaning for Visualization Sets that contain multiple data sets assigned to the same geometry. When using an integer, this will refer to the index of the data set to be visualized (starting with 0). When using text, this will refer to the name of the data type for the data set to be displayed.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_vis_set')
        input_node.prop_name = 'sv__vis_set'
        input_node.tooltip = 'VisualizationSet arguments from any Ladybug Tools component with a vis_set output. This can also be the path to a .vsf file that exists on this machine (these files are often written with the "LB Dump VisualizationSet" component). Lastly, this input can be a custom VisualizationSet that has been created with the Ladybug Tools SDK.'
        input_node = self.inputs.new('SvLBSocket', 'leg_par_')
        input_node.prop_name = 'sv_leg_par_'
        input_node.tooltip = 'Script variable VisSet'
        input_node = self.inputs.new('SvLBSocket', 'leg_par2d_')
        input_node.prop_name = 'sv_leg_par2d_'
        input_node.tooltip = 'Optional 2D LegendParameters from the "LB Legend Parameters 2D" component, which will be used to customize a legend in the plane of the screen so that it functions like a head-up display (HUD). If unspecified, the VisualizationSet will be rendered with 3D legends in the Rhino scene much like the other native Ladybug Tools components.'
        input_node = self.inputs.new('SvLBSocket', 'data_set_')
        input_node.prop_name = 'sv_data_set_'
        input_node.tooltip = 'Optional text or an integer to select a specific data set from analysis geometries within the Visualization Set. Note that this input only has meaning for Visualization Sets that contain multiple data sets assigned to the same geometry. When using an integer, this will refer to the index of the data set to be visualized (starting with 0). When using text, this will refer to the name of the data type for the data set to be displayed.'
        output_node = self.outputs.new('SvLBSocket', 'vs')
        output_node.tooltip = 'A VisualizationSet object that can be baked into the Rhino document by running "Bake" on this component or written to a standalone file using the "LB Dump VisualizationSet" component.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Preview a VisualizationSet from any component with a vis_set output. _ The VisualizationSet is often a much more detailed view of the geometry that the component typically generates and includes features like recommended line weights/types, display modes (eg. wireframe vs. shaded), transparency, and more. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['vs']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_vis_set', 'leg_par_', 'leg_par2d_', 'data_set_']
        self.sv_input_types = ['System.Object', 'System.Object', 'System.Object', 'string']
        self.sv_input_defaults = [None, None, None, None]
        self.sv_input_access = ['list', 'item', 'item', 'item']
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

    def process_ladybug(self, _vis_set, leg_par_, leg_par2d_, data_set_):


        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvVisSet)

def unregister():
    bpy.utils.unregister_class(SvVisSet)
