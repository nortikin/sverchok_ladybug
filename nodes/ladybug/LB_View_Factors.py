import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvViewFactors(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvViewFactors'
    bl_label = 'LB View Factors'
    sv_icon = 'LB_VIEWFACTORS'
    sv__study_point: StringProperty(
        name='_study_point',
        update=updateNode,
        description='A point or plane from which view vectors will be projected. Note that, if a point is connected, all view vectors will be weighted evenly (assuming no directional bias). However, if a plane is connected, vectors will be weighted based on their angle to the plane normal, producing view factors for a surface in the connected plane. The first is useful for MRT calculations while the latter is needed for radiant assymetry calculations. This input can also be a list of several points or planes.')
    sv__view_geo: StringProperty(
        name='_view_geo',
        update=updateNode,
        description='A list of breps, surfaces, or meshes to which you want to compute view factors. Note that by meshing and joining several goemtries together, the combined view factor to these geometries can be computed.')
    sv_context_: StringProperty(
        name='context_',
        update=updateNode,
        description='Optional context geometry as breps, surfaces, or meshes that can block the view to the _view_geo.')
    sv__resolution_: StringProperty(
        name='_resolution_',
        update=updateNode,
        description='A positive integer for the number of times that the original view vectors are subdivided. 1 indicates that 145 evenly-spaced vectors are used to describe a hemisphere, 2 indicates that 577 vectors describe a hemisphere, and each successive value will roughly quadruple the number of view vectors used. Setting this to a high value will result in a more accurate analysis but will take longer to run. (Default: 1).')
    sv__cpu_count_: StringProperty(
        name='_cpu_count_',
        update=updateNode,
        description='An integer to set the number of CPUs used in the execution of the intersection calculation. If unspecified, it will automatically default to one less than the number of CPUs currently available on the machine or 1 if only one processor is available.')
    sv__run: StringProperty(
        name='_run',
        update=updateNode,
        description='Set to True to run the component and claculate view factors.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_study_point')
        input_node.prop_name = 'sv__study_point'
        input_node.tooltip = 'A point or plane from which view vectors will be projected. Note that, if a point is connected, all view vectors will be weighted evenly (assuming no directional bias). However, if a plane is connected, vectors will be weighted based on their angle to the plane normal, producing view factors for a surface in the connected plane. The first is useful for MRT calculations while the latter is needed for radiant assymetry calculations. This input can also be a list of several points or planes.'
        input_node = self.inputs.new('SvLBSocket', '_view_geo')
        input_node.prop_name = 'sv__view_geo'
        input_node.tooltip = 'A list of breps, surfaces, or meshes to which you want to compute view factors. Note that by meshing and joining several goemtries together, the combined view factor to these geometries can be computed.'
        input_node = self.inputs.new('SvLBSocket', 'context_')
        input_node.prop_name = 'sv_context_'
        input_node.tooltip = 'Optional context geometry as breps, surfaces, or meshes that can block the view to the _view_geo.'
        input_node = self.inputs.new('SvLBSocket', '_resolution_')
        input_node.prop_name = 'sv__resolution_'
        input_node.tooltip = 'A positive integer for the number of times that the original view vectors are subdivided. 1 indicates that 145 evenly-spaced vectors are used to describe a hemisphere, 2 indicates that 577 vectors describe a hemisphere, and each successive value will roughly quadruple the number of view vectors used. Setting this to a high value will result in a more accurate analysis but will take longer to run. (Default: 1).'
        input_node = self.inputs.new('SvLBSocket', '_cpu_count_')
        input_node.prop_name = 'sv__cpu_count_'
        input_node.tooltip = 'An integer to set the number of CPUs used in the execution of the intersection calculation. If unspecified, it will automatically default to one less than the number of CPUs currently available on the machine or 1 if only one processor is available.'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to True to run the component and claculate view factors.'
        output_node = self.outputs.new('SvLBSocket', 'view_vecs')
        output_node.tooltip = 'A list of vectors which are projected from each of the points to evaluate view.'
        output_node = self.outputs.new('SvLBSocket', 'patch_mesh')
        output_node.tooltip = 'A mesh that represents the sphere of view patches around the _study_point at the input _resolution_. There is one face per patch and this can be used along with the int_mtx to create a colored visualization of patches corresponding to different geometries around the point. Specifically, the "LB Spaital Heatmap" component is recommended for such visualizations. Note that only one sphere is ever output from here and, in the event that several _study_points are connected, this sphere will be located at the first point. Therefore, to create visualizations for the other points, this mesh should be moved using the difference between the first study point and following study points.'
        output_node = self.outputs.new('SvLBSocket', 'view_factors')
        output_node.tooltip = 'A list of view factors that describe the fraction of sperical view taken up by the input surfaces.  These values range from 0 (no view) to 1 (full view).  If multiple _study_points have been connected, this output will be a data tree with one list for each point.'
        output_node = self.outputs.new('SvLBSocket', 'int_mtx')
        output_node.tooltip = 'A Matrix object that can be connected to the "LB Deconstruct Matrix" component to obtain detailed vector-by-vector results of the study. Each sub-list (aka. branch of the Data Tree) represents one of the points used for analysis. Each value in this sub-list corresponds to a vector used in the study and the value denotes the index of the geometry that each view vector hit. This can be used to identify which view pathces are intersected by each geometry. If no geometry is intersected by a given vector, the value will be -1.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate view factors from a point or plane to a set of geometries. _ View factors are used in many thermal comfort calculations such as mean radiant temperture (MRT) or discomfort from radiant assymetry.  -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['view_vecs', 'patch_mesh', 'view_factors', 'int_mtx']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_study_point', '_view_geo', 'context_', '_resolution_', '_cpu_count_', '_run']
        self.sv_input_types = ['System.Object', 'Mesh', 'GeometryBase', 'int', 'int', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None]
        self.sv_input_access = ['list', 'list', 'list', 'item', 'item', 'item']
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

    def process_ladybug(self, _study_point, _view_geo, context_, _resolution_, _cpu_count_, _run):

        try:
            from ladybug.viewsphere import view_sphere
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.togeometry import to_plane, to_vector3d
            from ladybug_tools.fromgeometry import from_mesh3d, from_point3d, from_vector3d
            from ladybug_tools.intersect import join_geometry_to_mesh, intersect_view_factor
            from ladybug_tools.sverchok import all_required_inputs, hide_output, \
                show_output, objectify_output, list_to_data_tree, recommended_processor_count
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component) and _run:
            # set up the defaults
            _resolution_ = _resolution_ if _resolution_ is not None else 1
            workers = _cpu_count_ if _cpu_count_ is not None else recommended_processor_count()
        
            # process the input points and determine whether they are points or planes
            points, normals = [], []
            for geo in _study_point:
                try:
                    test_plane = to_plane(geo)
                    points.append(from_point3d(test_plane.o))
                    normals.append(from_vector3d(test_plane.n))
                except AttributeError:  # it is a point
                    points.append(geo)
                    normals.append(None)
            if all(n is None for n in normals):
                normals = None  # none of the inputs were planes
        
            # generate the view vectors based on the resolution
            patch_mesh, lb_vecs = view_sphere.sphere_patches(_resolution_)
            patch_wghts = view_sphere.sphere_patch_weights(_resolution_)
            # correct for the fact that the last patch has several mesh faces
            patch_count = 144 * (_resolution_ ** 2) + 1
            extend_count = ((6 * _resolution_) - 1)
            up_dome, down_dome = list(lb_vecs[:patch_count]), list(lb_vecs[patch_count:])
            up_dome.extend([up_dome[-1]] * extend_count)
            down_dome.extend([down_dome[-1]] * extend_count)
            lb_vecs = up_dome + down_dome
            up_weights, down_weights = list(patch_wghts[:patch_count]), list(patch_wghts[patch_count:])
            up_weights.extend([up_weights[-1] / extend_count] * extend_count)
            down_weights.extend([down_weights[-1] / extend_count] * extend_count)
            patch_wghts = up_weights + down_weights
        
            # process the context if it is input
            context_mesh = join_geometry_to_mesh(context_) if len(context_) != 0 else None
        
            # perform the intersection to compute view factors
            view_vecs = [from_vector3d(pt) for pt in lb_vecs]
            view_factors, mesh_indices = intersect_view_factor(
                _view_geo, points, view_vecs, patch_wghts,
                context_mesh, normals, cpu_count=workers)
        
            # convert the outputs into the correct  format
            view_factors = list_to_data_tree(view_factors)
            int_mtx = objectify_output('View Factor Intersection Matrix', mesh_indices)
            patch_mesh = from_mesh3d(patch_mesh.move(to_vector3d(points[0])))
            hide_output(ghenv.Component, 2)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvViewFactors)

def unregister():
    bpy.utils.unregister_class(SvViewFactors)
