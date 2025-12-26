import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvDeconstructVisSet(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvDeconstructVisSet'
    bl_label = 'LB Deconstruct VisualizationSet'
    sv_icon = 'LB_DECONSTRUCTVISSET'
    sv__vis_set: StringProperty(
        name='_vis_set',
        update=updateNode,
        description='VisualizationSet arguments from any Ladybug Tools component with a vis_set output. This can also be the path to a .vsf file that exists on this machine (these files are often written with the "LB Dump VisualizationSet" component). Lastly, this input can be a custom VisualizationSet that has been created with the Ladybug Tools SDK.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_vis_set')
        input_node.prop_name = 'sv__vis_set'
        input_node.tooltip = 'VisualizationSet arguments from any Ladybug Tools component with a vis_set output. This can also be the path to a .vsf file that exists on this machine (these files are often written with the "LB Dump VisualizationSet" component). Lastly, this input can be a custom VisualizationSet that has been created with the Ladybug Tools SDK.'
        output_node = self.outputs.new('SvLBSocket', 'context')
        output_node.tooltip = 'A list of geometry objects that constitute the context geometry of the VisualizationSet. When the VisualizationSet contains multiple context geometry instances, this will be a data tree with one branch for each context object.'
        output_node = self.outputs.new('SvLBSocket', 'analysis')
        output_node.tooltip = 'A list of geometry objects that constitute the analysis geometry of the VisualizationSet. When the VisualizationSet contains multiple analysis geometry instances, this will be a data tree with one branch for each analysis object.'
        output_node = self.outputs.new('SvLBSocket', 'data')
        output_node.tooltip = 'A list of numbers that constitue the data set associated with the analysis geometry. In the event of multiple data sets assigned to the same analysis geometry, this will be a data tree of numbers with one branch for each data set. In the event of multiple analysis geometries, this will be a nested data tree where the first number in the path matches the analysis geometry branch and the last number matches the data set number.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Deconstruct a Ladybug VisualizationSet into all of its constituent objects. _ This includes Context Geometry, Analysis Geometry, and any data sets that are associated with the analysis geometry. The last one is particularly helpful for performing analysis in the data associated with a particular visualization. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['context', 'analysis', 'data']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_vis_set']
        self.sv_input_types = ['System.Object']
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

    def process_ladybug(self, _vis_set):

        try:  # import the honeybee dependencies
            from ladybug_display.geometry3d import DisplayText3D
            from ladybug_display.visualization import ContextGeometry, AnalysisGeometry
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_display:\n\t{}'.format(e))
        
        try:  # import the ladybug_tools dependencies
            from ladybug_tools.fromobjects import from_geometry
            from ladybug_tools.text import text_objects
            from ladybug_tools.visset import process_vis_set
            from ladybug_tools.sverchok import all_required_inputs, list_to_data_tree
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        TEXT_HORIZ = {'Left': 0, 'Center': 1, 'Right': 2}
        TEXT_VERT = {'Top': 0, 'Middle': 3, 'Bottom': 5}
        
        
        if all_required_inputs(ghenv.Component):
            # extract the VisualizationSet object
            _vs = process_vis_set(_vis_set)
        
            # loop through the constituient objects and deconstruct them
            context, analysis, data = [], [], []
            for geo_obj in _vs.geometry:
                if isinstance(geo_obj, ContextGeometry):
                    con_geos = []
                    for g in geo_obj.geometry:
                        if not isinstance(g, DisplayText3D):
                            con_geos.append(from_geometry(g.geometry))
                        else:
                            t_obj = text_objects(
                                g.text, g.plane, g.height, g.font,
                                TEXT_HORIZ[g.horizontal_alignment],
                                TEXT_VERT[g.vertical_alignment])
                            con_geos.append(t_obj)
                    context.append(con_geos)
                elif isinstance(geo_obj, AnalysisGeometry):
                    a_geos, data_sets = [], []
                    for g in geo_obj.geometry:
                        a_geos.append(from_geometry(g))
                    for d in geo_obj.data_sets:
                        data_sets.append(d.values)
                    analysis.append([a_geos])
                    data.append(data_sets)
        
            # convert everything into data trees
            context = list_to_data_tree(context)
            analysis = list_to_data_tree(analysis)
            data = list_to_data_tree(data)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvDeconstructVisSet)

def unregister():
    bpy.utils.unregister_class(SvDeconstructVisSet)
