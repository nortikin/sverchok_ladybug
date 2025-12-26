import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvViewPercent(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvViewPercent'
    bl_label = 'LB View Percent'
    sv_icon = 'LB_VIEWPERCENT'
    sv__view_type: StringProperty(
        name='_view_type',
        update=updateNode,
        description='Text or an integer representing the type of view analysis to conduct.  Choose from the following options. _ 0 - HorizontalRadial - The percentage of the 360 horizontal view plane that is not blocked by the context geometry. _ 1 - Horizontal30DegreeOffset - The percentage of the 360 horizontal view band bounded on top and bottom by a 30 degree offset from the horizontal plane. 30 degrees corresponds roughly to the vertical limit of human peripheral vision. _ 2 - Spherical - The percentage of the sphere surrounding each of the test points that is not blocked by context geometry. This is equivalent to a solid angle and gives equal weight to all portions of the sphere. _ 3 - SkyExposure - The percentage of the sky that is visible from each of the the test points. This is distinct from SkyView, which is the amount of sky seen by a surface. SkyExposure is equivalent to a solid angle and gives equal weight to all portions of the sky. _ 4 - SkyView - The percentage of the sky that is visible from the _geometry surfaces. This is distinct from SkyExposure, which treats each part of the sky with equal weight. SkyView weights the portions of the sky according to thier projection into the plane of the surface being evaluated. So SkyView for a horizontal surface would give more importance to the sky patches that are overhead vs. those near the horizon.')
    sv__resolution_: StringProperty(
        name='_resolution_',
        update=updateNode,
        description='A positive integer for the number of times that the original view vectors are subdivided. 1 indicates that 145 evenly-spaced vectors are used to describe a hemisphere, 2 indicates that 577 vectors describe a hemisphere, and each successive value will roughly quadruple the number of view vectors used. Setting this to a high value will result in a more accurate analysis but will take longer to run. (Default: 1).')
    sv__geometry: StringProperty(
        name='_geometry',
        update=updateNode,
        description='Rhino Breps and/or Rhino Meshes for which view analysis will be conducted. If Breps are input, they will be subdivided using the _grid_size to yeild individual points at which analysis will occur. If a Mesh is input, view analysis analysis will be performed for each face of this mesh instead of subdividing it.')
    sv_context_: StringProperty(
        name='context_',
        update=updateNode,
        description='Rhino Breps and/or Rhino Meshes representing context geometry that can block view from the test _geometry.')
    sv__grid_size: StringProperty(
        name='_grid_size',
        update=updateNode,
        description='A positive number in Rhino model units for the size of grid cells at which the input _geometry will be subdivided for direct sun analysis. The smaller the grid size, the higher the resolution of the analysis and the longer the calculation will take.  So it is recommended that one start with a large value here and decrease the value as needed. However, the grid size should usually be smaller than the dimensions of the smallest piece of the _geometry and context_ in order to yield meaningful results.')
    sv__offset_dist_: StringProperty(
        name='_offset_dist_',
        update=updateNode,
        description='A number for the distance to move points from the surfaces of the input _geometry.  Typically, this should be a small positive number to ensure points are not blocked by the mesh. (Default: 10 cm in the equivalent Rhino Model units).')
    sv__geo_block_: StringProperty(
        name='_geo_block_',
        update=updateNode,
        description='Set to "True" to count the input _geometry as opaque and set to "False" to discount the _geometry from the calculation and only look at context_ that blocks the view.  The default depends on the _view_type used. _ It is "True" for: * SkyExposure * SkyView _ It is "False" for: * HorizontalRadial * Horizonta30DegreeOffset * Spherical')
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
        description='Set to "True" to run the component and perform view analysis of the input _geometry.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_view_type')
        input_node.prop_name = 'sv__view_type'
        input_node.tooltip = 'Text or an integer representing the type of view analysis to conduct.  Choose from the following options. _ 0 - HorizontalRadial - The percentage of the 360 horizontal view plane that is not blocked by the context geometry. _ 1 - Horizontal30DegreeOffset - The percentage of the 360 horizontal view band bounded on top and bottom by a 30 degree offset from the horizontal plane. 30 degrees corresponds roughly to the vertical limit of human peripheral vision. _ 2 - Spherical - The percentage of the sphere surrounding each of the test points that is not blocked by context geometry. This is equivalent to a solid angle and gives equal weight to all portions of the sphere. _ 3 - SkyExposure - The percentage of the sky that is visible from each of the the test points. This is distinct from SkyView, which is the amount of sky seen by a surface. SkyExposure is equivalent to a solid angle and gives equal weight to all portions of the sky. _ 4 - SkyView - The percentage of the sky that is visible from the _geometry surfaces. This is distinct from SkyExposure, which treats each part of the sky with equal weight. SkyView weights the portions of the sky according to thier projection into the plane of the surface being evaluated. So SkyView for a horizontal surface would give more importance to the sky patches that are overhead vs. those near the horizon.'
        input_node = self.inputs.new('SvLBSocket', '_resolution_')
        input_node.prop_name = 'sv__resolution_'
        input_node.tooltip = 'A positive integer for the number of times that the original view vectors are subdivided. 1 indicates that 145 evenly-spaced vectors are used to describe a hemisphere, 2 indicates that 577 vectors describe a hemisphere, and each successive value will roughly quadruple the number of view vectors used. Setting this to a high value will result in a more accurate analysis but will take longer to run. (Default: 1).'
        input_node = self.inputs.new('SvLBSocket', '_geometry')
        input_node.prop_name = 'sv__geometry'
        input_node.tooltip = 'Rhino Breps and/or Rhino Meshes for which view analysis will be conducted. If Breps are input, they will be subdivided using the _grid_size to yeild individual points at which analysis will occur. If a Mesh is input, view analysis analysis will be performed for each face of this mesh instead of subdividing it.'
        input_node = self.inputs.new('SvLBSocket', 'context_')
        input_node.prop_name = 'sv_context_'
        input_node.tooltip = 'Rhino Breps and/or Rhino Meshes representing context geometry that can block view from the test _geometry.'
        input_node = self.inputs.new('SvLBSocket', '_grid_size')
        input_node.prop_name = 'sv__grid_size'
        input_node.tooltip = 'A positive number in Rhino model units for the size of grid cells at which the input _geometry will be subdivided for direct sun analysis. The smaller the grid size, the higher the resolution of the analysis and the longer the calculation will take.  So it is recommended that one start with a large value here and decrease the value as needed. However, the grid size should usually be smaller than the dimensions of the smallest piece of the _geometry and context_ in order to yield meaningful results.'
        input_node = self.inputs.new('SvLBSocket', '_offset_dist_')
        input_node.prop_name = 'sv__offset_dist_'
        input_node.tooltip = 'A number for the distance to move points from the surfaces of the input _geometry.  Typically, this should be a small positive number to ensure points are not blocked by the mesh. (Default: 10 cm in the equivalent Rhino Model units).'
        input_node = self.inputs.new('SvLBSocket', '_geo_block_')
        input_node.prop_name = 'sv__geo_block_'
        input_node.tooltip = 'Set to "True" to count the input _geometry as opaque and set to "False" to discount the _geometry from the calculation and only look at context_ that blocks the view.  The default depends on the _view_type used. _ It is "True" for: * SkyExposure * SkyView _ It is "False" for: * HorizontalRadial * Horizonta30DegreeOffset * Spherical'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'Optional legend parameters from the "LB Legend Parameters" that will be used to customize the display of the results.'
        input_node = self.inputs.new('SvLBSocket', '_cpu_count_')
        input_node.prop_name = 'sv__cpu_count_'
        input_node.tooltip = 'An integer to set the number of CPUs used in the execution of the intersection calculation. If unspecified, it will automatically default to one less than the number of CPUs currently available on the machine or 1 if only one processor is available.'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to "True" to run the component and perform view analysis of the input _geometry.'
        output_node = self.outputs.new('SvLBSocket', 'points')
        output_node.tooltip = 'The grid of points on the test _geometry that are be used to perform the view analysis.'
        output_node = self.outputs.new('SvLBSocket', 'view_vecs')
        output_node.tooltip = 'A list of vectors which are projected from each of the points to evaluate view.'
        output_node = self.outputs.new('SvLBSocket', 'results')
        output_node.tooltip = 'A list of numbers that aligns with the points. Each number indicates the percentage of the view_vecs that are not blocked by context geometry.'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'A colored mesh of the test _geometry representing the percentage of the input _geometry\'s view that is not blocked by context.'
        output_node = self.outputs.new('SvLBSocket', 'legend')
        output_node.tooltip = 'A legend that correspond to the colors of the mesh and shows the percentage of the view_vecs that are not blocked by context geometry.'
        output_node = self.outputs.new('SvLBSocket', 'title')
        output_node.tooltip = 'A text object for the study title.'
        output_node = self.outputs.new('SvLBSocket', 'int_mtx')
        output_node.tooltip = 'A Matrix object that can be connected to the "LB Deconstruct Matrix" component to obtain detailed vector-by-vector results of the study. Each sub-list (aka. branch of the Data Tree) represents one of the points used for analysis. The length of each sub-list matches the number of view_vecs used for the analysis. Each value in the sub-list is either a "1", indicating that the vector is visible for that vector, or a "0", indicating that the vector is not visible for that vector.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Evaluate the percent view to the outdoors or sky from input geometry through context. _ Such view calculations can be used to estimate the quality of a view to the outdoors from a given location on the indoors. They can also be used on the outdoors to evaluate the openness of street canyons to the sky, which has implications for the pedestrian expereince as well as the rate of radiant heat loss from urban surfaces and the sky at night. _ Note that this component uses the CAD environment\'s ray intersection methods, which can be fast for geometries with low complexity but does not scale well for complex geometries or many test points. For such complex studies, honeybee-radiance should be used. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['points', 'view_vecs', 'results', 'mesh', 'legend', 'title', 'int_mtx']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_view_type', '_resolution_', '_geometry', 'context_', '_grid_size', '_offset_dist_', '_geo_block_', 'legend_par_', '_cpu_count_', '_run']
        self.sv_input_types = ['string', 'int', 'GeometryBase', 'GeometryBase', 'double', 'double', 'bool', 'System.Object', 'int', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'list', 'list', 'item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _view_type, _resolution_, _geometry, context_, _grid_size, _offset_dist_, _geo_block_, legend_par_, _cpu_count_, _run):

        import math
        try:  # python 2
            from itertools import izip as zip
        except ImportError:  # python 3
            pass
        
        try:
            from ladybug.viewsphere import view_sphere
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
            from ladybug_tools.intersect import join_geometry_to_mesh, intersect_mesh_rays
            from ladybug_tools.sverchok import all_required_inputs, hide_output, \
                show_output, objectify_output, recommended_processor_count
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        # dictionary to record all available view types
        VIEW_TYPES = {
            'HorizontalRadial': 'Horizontal Radial',
            'Horizontal30DegreeOffset': 'Horizontal 30-Degree Offset',
            'Spherical': 'Spherical',
            'SkyExposure': 'Sky Exposure',
            'SkyView': 'Sky View',
            '0': 'Horizontal Radial',
            '1': 'Horizontal 30-Degree Offset',
            '2': 'Spherical',
            '3': 'Sky Exposure',
            '4': 'Sky View'
        }
        
        
        if all_required_inputs(ghenv.Component) and _run:
            # process the view_type_ and set the default values
            vt_str = VIEW_TYPES[_view_type]
            _resolution_ = _resolution_ if _resolution_ is not None else 1
            _offset_dist_ = _offset_dist_ if _offset_dist_ is not None \
                else 0.1 / conversion_to_meters()
            if _geo_block_ is None:
                _geo_block_ = True if vt_str in ('Sky Exposure', 'Sky View') else False
            workers = _cpu_count_ if _cpu_count_ is not None else recommended_processor_count()
        
            # create the gridded mesh from the geometry
            study_mesh = to_joined_gridded_mesh3d(_geometry, _grid_size)
            points = [from_point3d(pt.move(vec * _offset_dist_)) for pt, vec in
                      zip(study_mesh.face_centroids, study_mesh.face_normals)]
            hide_output(ghenv.Component, 1)
        
            # get the view vectors based on the view type
            patch_wghts = None
            if vt_str == 'Horizontal Radial':
                lb_vecs = view_sphere.horizontal_radial_vectors(30 * _resolution_)
            elif vt_str == 'Horizontal 30-Degree Offset':
                patch_mesh, lb_vecs = view_sphere.horizontal_radial_patches(30, _resolution_)
                patch_wghts = view_sphere.horizontal_radial_patch_weights(30, _resolution_)
            elif vt_str == 'Spherical':
                patch_mesh, lb_vecs = view_sphere.sphere_patches(_resolution_)
                patch_wghts = view_sphere.sphere_patch_weights(_resolution_)
            else:
                patch_mesh, lb_vecs = view_sphere.dome_patches(_resolution_)
                patch_wghts = view_sphere.dome_patch_weights(_resolution_)
            view_vecs = [from_vector3d(pt) for pt in lb_vecs]
        
            # mesh the geometry and context
            shade_mesh = join_geometry_to_mesh(_geometry + context_) if _geo_block_ \
                else join_geometry_to_mesh(context_)
        
            # intersect the rays with the mesh
            if vt_str == 'Sky View':  # account for the normals of the surface
                normals = [from_vector3d(vec) for vec in study_mesh.face_normals]
                int_matrix, angles = intersect_mesh_rays(
                    shade_mesh, points, view_vecs, normals, cpu_count=workers)
            else:
                int_matrix, angles = intersect_mesh_rays(
                    shade_mesh, points, view_vecs, cpu_count=workers)
        
            # compute the results
            int_mtx = objectify_output('View Intersection Matrix', int_matrix)
            vec_count = len(view_vecs)
            results = []
            if vt_str == 'Sky View':  # weight intersections by angle before output
                for int_vals, angles in zip(int_matrix, angles):
                    w_res = (ival * 2 * math.cos(ang) for ival, ang in zip(int_vals, angles))
                    weight_result = sum(r * w for r, w in zip(w_res, patch_wghts))
                    results.append(weight_result * 100 / vec_count)
            else:
                if patch_wghts:
                    for int_list in int_matrix:
                        weight_result = sum(r * w for r, w in zip(int_list, patch_wghts))
                        results.append(weight_result * 100 / vec_count)
                else:
                    results = [sum(int_list) * 100 / vec_count for int_list in int_matrix]
        
            # create the mesh and legend outputs
            graphic = GraphicContainer(results, study_mesh.min, study_mesh.max, legend_par_)
            graphic.legend_parameters.title = '%'
            if legend_par_ is None or legend_par_.are_colors_default:
                graphic.legend_parameters.colors = Colorset.view_study()
            title_txt = vt_str if vt_str in ('Sky Exposure', 'Sky View') else \
                '{} View'.format(vt_str)
            title = text_objects(
                title_txt, graphic.lower_title_location,
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
    bpy.utils.register_class(SvViewPercent)

def unregister():
    bpy.utils.unregister_class(SvViewPercent)
