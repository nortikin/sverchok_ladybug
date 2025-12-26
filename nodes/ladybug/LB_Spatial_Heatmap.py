import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvHeatmap(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvHeatmap'
    bl_label = 'LB Spatial Heatmap'
    sv_icon = 'LB_HEATMAP'
    sv__values: StringProperty(
        name='_values',
        update=updateNode,
        description='A list of numerical values with which to color the mesh. The number of values must match the number of faces or vertices in the mesh.')
    sv__mesh: StringProperty(
        name='_mesh',
        update=updateNode,
        description='A Mesh object, with a number of faces or vertices that match the number of input values and will be colored with results.')
    sv_offset_dom_: StringProperty(
        name='offset_dom_',
        update=updateNode,
        description='Optional domain (or number for distance), which will be used to offset the mesh faces or verticesto according to the values. Higher values will be offset further.')
    sv_legend_par_: StringProperty(
        name='legend_par_',
        update=updateNode,
        description='Optional legend parameters from the Ladybug \'Legend Parameters\' component.')
    sv_legend_title_: StringProperty(
        name='legend_title_',
        update=updateNode,
        description='A text string for Legend title. Typically, the units of the data are used here but the type of data might also be used. Default is an empty string.')
    sv_global_title_: StringProperty(
        name='global_title_',
        update=updateNode,
        description='A text string to label the entire mesh.  It will be displayed in the lower left of the result mesh. Default is for no title.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_values')
        input_node.prop_name = 'sv__values'
        input_node.tooltip = 'A list of numerical values with which to color the mesh. The number of values must match the number of faces or vertices in the mesh.'
        input_node = self.inputs.new('SvLBSocket', '_mesh')
        input_node.prop_name = 'sv__mesh'
        input_node.tooltip = 'A Mesh object, with a number of faces or vertices that match the number of input values and will be colored with results.'
        input_node = self.inputs.new('SvLBSocket', 'offset_dom_')
        input_node.prop_name = 'sv_offset_dom_'
        input_node.tooltip = 'Optional domain (or number for distance), which will be used to offset the mesh faces or verticesto according to the values. Higher values will be offset further.'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'Optional legend parameters from the Ladybug \'Legend Parameters\' component.'
        input_node = self.inputs.new('SvLBSocket', 'legend_title_')
        input_node.prop_name = 'sv_legend_title_'
        input_node.tooltip = 'A text string for Legend title. Typically, the units of the data are used here but the type of data might also be used. Default is an empty string.'
        input_node = self.inputs.new('SvLBSocket', 'global_title_')
        input_node.prop_name = 'sv_global_title_'
        input_node.tooltip = 'A text string to label the entire mesh.  It will be displayed in the lower left of the result mesh. Default is for no title.'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'The input _mesh that has been colored with results.'
        output_node = self.outputs.new('SvLBSocket', 'legend')
        output_node.tooltip = 'Geometry representing the legend for the mesh.'
        output_node = self.outputs.new('SvLBSocket', 'title')
        output_node.tooltip = 'A text object for the global_title.'
        output_node = self.outputs.new('SvLBSocket', 'colors')
        output_node.tooltip = 'The colors associated with each input value.'
        output_node = self.outputs.new('SvLBSocket', 'legend_par')
        output_node.tooltip = 'The input legend parameters with defaults filled for unset properties.'
        output_node = self.outputs.new('SvLBSocket', 'vis_set')
        output_node.tooltip = 'Script variable Heatmap'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Color a mesh as a heatmap using values that align with the mesh faces or vertices. _ Note that any brep can be converted to a gridded mesh that can be consumed by  this component using the "LB Generate Point Grid" component. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['mesh', 'legend', 'title', 'colors', 'legend_par', 'vis_set']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_values', '_mesh', 'offset_dom_', 'legend_par_', 'legend_title_', 'global_title_']
        self.sv_input_types = ['double', 'Mesh', 'Interval', 'System.Object', 'string', 'string']
        self.sv_input_defaults = [None, None, None, None, None, None]
        self.sv_input_access = ['list', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _values, _mesh, offset_dom_, legend_par_, legend_title_, global_title_):

        try:
            from ladybug.legend import LegendParameters
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_display.visualization import VisualizationSet
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.togeometry import to_mesh3d
            from ladybug_tools.fromgeometry import from_mesh3d
            from ladybug_tools.fromobjects import legend_objects
            from ladybug_tools.text import text_objects
            from ladybug_tools.color import color_to_color
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # translate to Ladybug objects
            lb_mesh = to_mesh3d(_mesh)
            if offset_dom_:
                dom_st, dom_end = offset_dom_
                lb_mesh = lb_mesh.height_field_mesh(_values, (dom_st, dom_end))
        
            # check the values against the mesh
            assert len(_values) == len(lb_mesh.faces) or len(_values) == len(lb_mesh.vertices), \
                'Expected the number of data set values ({}) to align with the number of faces ' \
                '({}) or the number of vertices ({}).\nConsider flattening the _values input ' \
                'and using the "Mesh Join" component to join the _mesh input.'.format(
                    len(_values), len(lb_mesh.faces), len(lb_mesh.vertices))
        
            # create the VisualizationSet and GraphicContainer
            if legend_title_ is not None:
                legend_par_ = legend_par_.duplicate() if legend_par_ is not None \
                    else LegendParameters()
                legend_par_.title = legend_title_
            vis_set = VisualizationSet.from_single_analysis_geo(
                'Data_Mesh', [lb_mesh], _values, legend_par_)
            graphic = vis_set.graphic_container()
        
            # generate titles
            if global_title_ is not None:
                title = text_objects(global_title_, graphic.lower_title_location,
                                     graphic.legend_parameters.text_height * 1.5,
                                     graphic.legend_parameters.font)
        
            # draw tools objects
            lb_mesh.colors = graphic.value_colors
            mesh = from_mesh3d(lb_mesh)
            legend = legend_objects(graphic.legend)
            colors = [color_to_color(col) for col in lb_mesh.colors]
            legend_par = graphic.legend_parameters
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvHeatmap)

def unregister():
    bpy.utils.unregister_class(SvHeatmap)
