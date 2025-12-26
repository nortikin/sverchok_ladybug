import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvVisibilityPercent(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvVisibilityPercent'
    bl_label = 'LB Visibility Percent'
    sv_icon = 'LB_VISIBILITYPERCENT'
    sv__view_points: StringProperty(
        name='_view_points',
        update=updateNode,
        description='A list of points that characterize an area of interest to which visibility is being evaluated. If the area of interest is more like a surface than an individual point, the "LB Generate Point Grid" component can be used to obtain a list of points that are evenly distributed over the surface.')
    sv_pt_weights_: StringProperty(
        name='pt_weights_',
        update=updateNode,
        description='An optional list of numbers that align with the _view_points and represent weights of importance for each point.  Weighted values should be between 0 and 1 and should be closer to 1 if a certain point is more important. The default value for all points is 0, which means they all have an equal importance.')
    sv__geometry: StringProperty(
        name='_geometry',
        update=updateNode,
        description='Rhino Breps and/or Rhino Meshes for which visibility analysis will be conducted. If Breps are input, they will be subdivided using the _grid_size to yeild individual points at which analysis will occur. If a Mesh is input, visibility analysis analysis will be performed for each face of this mesh instead of subdividing it.')
    sv_context_: StringProperty(
        name='context_',
        update=updateNode,
        description='Rhino Breps and/or Rhino Meshes representing context geometry that can block visibility from the test _geometry.')
    sv__grid_size: StringProperty(
        name='_grid_size',
        update=updateNode,
        description='A positive number in Rhino model units for the size of grid cells at which the input _geometry will be subdivided for direct sun analysis. The smaller the grid size, the higher the resolution of the analysis and the longer the calculation will take.  So it is recommended that one start with a large value here and decrease the value as needed. However, the grid size should usually be smaller than the dimensions of the smallest piece of the _geometry and context_ in order to yield meaningful results.')
    sv__offset_dist_: StringProperty(
        name='_offset_dist_',
        update=updateNode,
        description='A number for the distance to move points from the surfaces of the input _geometry.  Typically, this should be a small positive number to ensure points are not blocked by the mesh. (Default: 10 cm in the equivalent Rhino Model units).')
    sv_max_dist_: StringProperty(
        name='max_dist_',
        update=updateNode,
        description='An optional number to set the maximum distance beyond which the end_points are no longer considered visible by the start_points. If None, points with an unobstructed view to one another will be considered visible no matter how far they are from one another.')
    sv__geo_block_: StringProperty(
        name='_geo_block_',
        update=updateNode,
        description='Set to "True" to count the input _geometry as opaque and set to "False" to discount the _geometry from the calculation and only look at context_ that blocks the visibility. (Default: True)')
    sv_legend_par_: StringProperty(
        name='legend_par_',
        update=updateNode,
        description='Optional legend parameters from the "LB Legend Parameters" that will be used to customize the display of the results.')
    sv__cpu_count_: StringProperty(
        name='_cpu_count_',
        update=updateNode,
        description='An integer to set the number of CPUs used in the execution of the intersection calculation. If unspecified, it will automatically default to one less than the number of CPUs currently available on the machine or 1 if only one processor is available.')
    sv__run: StringProperty(
        name='_run',
        update=updateNode,
        description='Set to "True" to run the component and perform visibility analysis of the input _geometry.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_view_points')
        input_node.prop_name = 'sv__view_points'
        input_node.tooltip = 'A list of points that characterize an area of interest to which visibility is being evaluated. If the area of interest is more like a surface than an individual point, the "LB Generate Point Grid" component can be used to obtain a list of points that are evenly distributed over the surface.'
        input_node = self.inputs.new('SvLBSocket', 'pt_weights_')
        input_node.prop_name = 'sv_pt_weights_'
        input_node.tooltip = 'An optional list of numbers that align with the _view_points and represent weights of importance for each point.  Weighted values should be between 0 and 1 and should be closer to 1 if a certain point is more important. The default value for all points is 0, which means they all have an equal importance.'
        input_node = self.inputs.new('SvLBSocket', '_geometry')
        input_node.prop_name = 'sv__geometry'
        input_node.tooltip = 'Rhino Breps and/or Rhino Meshes for which visibility analysis will be conducted. If Breps are input, they will be subdivided using the _grid_size to yeild individual points at which analysis will occur. If a Mesh is input, visibility analysis analysis will be performed for each face of this mesh instead of subdividing it.'
        input_node = self.inputs.new('SvLBSocket', 'context_')
        input_node.prop_name = 'sv_context_'
        input_node.tooltip = 'Rhino Breps and/or Rhino Meshes representing context geometry that can block visibility from the test _geometry.'
        input_node = self.inputs.new('SvLBSocket', '_grid_size')
        input_node.prop_name = 'sv__grid_size'
        input_node.tooltip = 'A positive number in Rhino model units for the size of grid cells at which the input _geometry will be subdivided for direct sun analysis. The smaller the grid size, the higher the resolution of the analysis and the longer the calculation will take.  So it is recommended that one start with a large value here and decrease the value as needed. However, the grid size should usually be smaller than the dimensions of the smallest piece of the _geometry and context_ in order to yield meaningful results.'
        input_node = self.inputs.new('SvLBSocket', '_offset_dist_')
        input_node.prop_name = 'sv__offset_dist_'
        input_node.tooltip = 'A number for the distance to move points from the surfaces of the input _geometry.  Typically, this should be a small positive number to ensure points are not blocked by the mesh. (Default: 10 cm in the equivalent Rhino Model units).'
        input_node = self.inputs.new('SvLBSocket', 'max_dist_')
        input_node.prop_name = 'sv_max_dist_'
        input_node.tooltip = 'An optional number to set the maximum distance beyond which the end_points are no longer considered visible by the start_points. If None, points with an unobstructed view to one another will be considered visible no matter how far they are from one another.'
        input_node = self.inputs.new('SvLBSocket', '_geo_block_')
        input_node.prop_name = 'sv__geo_block_'
        input_node.tooltip = 'Set to "True" to count the input _geometry as opaque and set to "False" to discount the _geometry from the calculation and only look at context_ that blocks the visibility. (Default: True)'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'Optional legend parameters from the "LB Legend Parameters" that will be used to customize the display of the results.'
        input_node = self.inputs.new('SvLBSocket', '_cpu_count_')
        input_node.prop_name = 'sv__cpu_count_'
        input_node.tooltip = 'An integer to set the number of CPUs used in the execution of the intersection calculation. If unspecified, it will automatically default to one less than the number of CPUs currently available on the machine or 1 if only one processor is available.'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to "True" to run the component and perform visibility analysis of the input _geometry.'
        output_node = self.outputs.new('SvLBSocket', 'points')
        output_node.tooltip = 'The grid of points on the test _geometry that are be used to perform the visibility analysis.'
        output_node = self.outputs.new('SvLBSocket', 'results')
        output_node.tooltip = 'A list of numbers that aligns with the points. Each number indicates the percentage of the _view_points that are not blocked by context geometry.'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'A colored mesh of the test _geometry representing the percentage of the input _geometry\'s visibility that is not blocked by context.'
        output_node = self.outputs.new('SvLBSocket', 'legend')
        output_node.tooltip = 'A legend showing the number of hours that correspond to the colors of the mesh.'
        output_node = self.outputs.new('SvLBSocket', 'title')
        output_node.tooltip = 'A text object for the study title.'
        output_node = self.outputs.new('SvLBSocket', 'int_mtx')
        output_node.tooltip = 'A Matrix object that can be connected to the "LB Deconstruct Matrix" component to obtain detailed point-by-point results of the study. Each sub-list (aka. branch of the Data Tree) represents one of the geometry points used for analysis. The length of each sub-list matches the number of _view_points used for the analysis. Each value in the sub-list is either a "1", indicating that the vector is visible for that vector, or a "0", indicating that the vector is not visible for that vector.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Evaluate the percent visibility from geometry to a specific set of points. _ Such visibility calculations can be used to understand the portions of a building facade that can see a skyline or landmark when used on the outdoors. When used on the indoors, they can evaluate the spectator view of a stage, screen, or other point of interest. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['points', 'results', 'mesh', 'legend', 'title', 'int_mtx']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_view_points', 'pt_weights_', '_geometry', 'context_', '_grid_size', '_offset_dist_', 'max_dist_', '_geo_block_', 'legend_par_', '_cpu_count_', '_run']
        self.sv_input_types = ['Point3d', 'double', 'GeometryBase', 'GeometryBase', 'double', 'double', 'double', 'bool', 'System.Object', 'int', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['list', 'list', 'list', 'list', 'item', 'item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _view_points, pt_weights_, _geometry, context_, _grid_size, _offset_dist_, max_dist_, _geo_block_, legend_par_, _cpu_count_, _run):

        try:
            from ladybug.color import Colorset
            from ladybug.graphic import GraphicContainer
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import conversion_to_meters
            from ladybug_tools.togeometry import to_joined_gridded_mesh3d, to_vector3d
            from ladybug_tools.fromgeometry import from_mesh3d, from_point3d, from_vector3d
            from ladybug_tools.fromobjects import legend_objects
            from ladybug_tools.text import text_objects
            from ladybug_tools.intersect import join_geometry_to_mesh, intersect_mesh_lines
            from ladybug_tools.sverchok import all_required_inputs, hide_output, \
                show_output, objectify_output, recommended_processor_count
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component) and _run:
                # set the default values
                _offset_dist_ = _offset_dist_ if _offset_dist_ is not None \
                    else 0.1 / conversion_to_meters()
                if pt_weights_:
                    assert len(pt_weights_) == len(_view_points), \
                        'The number of pt_weights_({}) must match the number of _view_points ' \
                        '({}).'.format(len(pt_weights_), len(_view_points))
                workers = _cpu_count_ if _cpu_count_ is not None else recommended_processor_count()
        
                # create the gridded mesh from the geometry
                study_mesh = to_joined_gridded_mesh3d(_geometry, _grid_size)
                points = [from_point3d(pt.move(vec * _offset_dist_)) for pt, vec in
                          zip(study_mesh.face_centroids, study_mesh.face_normals)]
                hide_output(ghenv.Component, 1)
        
                # mesh the geometry and context
                shade_mesh = join_geometry_to_mesh(_geometry + context_) if _geo_block_ \
                    or _geo_block_ is None else join_geometry_to_mesh(context_)
        
                # intersect the lines with the mesh
                int_matrix = intersect_mesh_lines(
                    shade_mesh, points, _view_points, max_dist_, cpu_count=workers)
        
                # compute the results
                int_mtx = objectify_output('Visibility Intersection Matrix', int_matrix)
                vec_count = len(_view_points)
                if pt_weights_:  # weight intersections by the input point weights
                    tot_wght = sum(pt_weights_) / vec_count
                    adj_weights = [wght / tot_wght for wght in pt_weights_]
                    results = []
                    for int_vals in int_matrix:
                        w_res = [ival * wght for ival, wght in zip(int_vals, adj_weights)]
                        results.append(sum(w_res) * 100 / vec_count)
                else:  # no need to wieght results
                    results = [sum(int_list) * 100 / vec_count for int_list in int_matrix]
        
                # create the mesh and legend outputs
                graphic = GraphicContainer(results, study_mesh.min, study_mesh.max, legend_par_)
                graphic.legend_parameters.title = '%'
                if legend_par_ is None or legend_par_.are_colors_default:
                    graphic.legend_parameters.colors = Colorset.view_study()
                title = text_objects(
                    'Visibility Percent', graphic.lower_title_location,
                    graphic.legend_parameters.text_height * 1.5,
                    graphic.legend_parameters.font)
        
                # create all of the visual outputs
                study_mesh.colors = graphic.value_colors
                mesh = from_mesh3d(study_mesh)
                legend = legend_objects(graphic.legend)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvVisibilityPercent)

def unregister():
    bpy.utils.unregister_class(SvVisibilityPercent)
