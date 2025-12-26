import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvShadeBenefit(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvShadeBenefit'
    bl_label = 'LB Shade Benefit'
    sv_icon = 'LB_SHADEBENEFIT'
    sv__vectors: StringProperty(
        name='_vectors',
        update=updateNode,
        description='Sun vectors from the "LB SunPath" component, which will be used to determine the number of hours of sun blocked by the _shade_geo. When evaluating shade benefit in terms of glare reduction, these vectors are typically for any sun-up hour of the year since looking into the sun at practically any hour is likely to induce glare. When using this component to approximate reductions to cooling demand or human heat stress, it\'s more appropriate to filter sun vectors using a conditional statement or use other types of shade benefit analysis like the "LB Thermal Shade Benefit" component or the "HB Energy Shade Benefit" component.')
    sv__study_points: StringProperty(
        name='_study_points',
        update=updateNode,
        description='Points representing an location in space for which shading desirability is being evaluated. For a study of shade desirability for reducing glare, this is often the location of the human subject\'s view. For a study of shade desirability over a surface like a desk or a window, the "LB Generate Point Grid" component can be used to create a set of points over the surface to input here.')
    sv_study_directs_: StringProperty(
        name='study_directs_',
        update=updateNode,
        description='Optional Vectors that align with the _study_points and represent the direction in which shade desirability is being evaluated. For a study of shade desirability for reducing glare, this is the direction in which human subject is looking. For a study of shade desirability over a surface like a desk or a window, the vectors output of the "LB Generate Point Grid" component should be input here. If not supplied, sun vectors coming from any direction will be used to evualuate shade desirability.')
    sv__shade_geo: StringProperty(
        name='_shade_geo',
        update=updateNode,
        description='Rhino Breps and/or Rhino Meshes representing shading to be evaluated in terms of its benefit. Note that, in the case that multiple shading geometries are connected, this component does not account for the interaction between the different shading surfaces and will just evaluate each part of the shade independently.')
    sv_context_: StringProperty(
        name='context_',
        update=updateNode,
        description='Rhino Breps and/or Rhino Meshes representing context geometry that can block sunlight to the _study_points, therefore discounting any benefit or harm that could come to the region.')
    sv__grid_size: StringProperty(
        name='_grid_size',
        update=updateNode,
        description='A positive number in Rhino model units for the size of grid cells at which the input _shade_geo will be subdivided for shade benefit analysis. The smaller the grid size, the higher the resolution of the analysis and the longer the calculation will take.  So it is recommended that one start with a large value here and decrease the value as needed. However, the grid size should usually be smaller than the dimensions of the smallest piece of the _shade_geo and context_ in order to yield meaningful results.')
    sv__timestep_: StringProperty(
        name='_timestep_',
        update=updateNode,
        description='A positive integer for the number of timesteps per hour at which the "LB SunPath" component generated sun vectors. This is used to correctly interpret the time duration represented by each of the input sun vectors. (Default: 1 for 1 vector per hour).')
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
        description='Set to "True" to run the component and perform shade benefit analysis.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_vectors')
        input_node.prop_name = 'sv__vectors'
        input_node.tooltip = 'Sun vectors from the "LB SunPath" component, which will be used to determine the number of hours of sun blocked by the _shade_geo. When evaluating shade benefit in terms of glare reduction, these vectors are typically for any sun-up hour of the year since looking into the sun at practically any hour is likely to induce glare. When using this component to approximate reductions to cooling demand or human heat stress, it\'s more appropriate to filter sun vectors using a conditional statement or use other types of shade benefit analysis like the "LB Thermal Shade Benefit" component or the "HB Energy Shade Benefit" component.'
        input_node = self.inputs.new('SvLBSocket', '_study_points')
        input_node.prop_name = 'sv__study_points'
        input_node.tooltip = 'Points representing an location in space for which shading desirability is being evaluated. For a study of shade desirability for reducing glare, this is often the location of the human subject\'s view. For a study of shade desirability over a surface like a desk or a window, the "LB Generate Point Grid" component can be used to create a set of points over the surface to input here.'
        input_node = self.inputs.new('SvLBSocket', 'study_directs_')
        input_node.prop_name = 'sv_study_directs_'
        input_node.tooltip = 'Optional Vectors that align with the _study_points and represent the direction in which shade desirability is being evaluated. For a study of shade desirability for reducing glare, this is the direction in which human subject is looking. For a study of shade desirability over a surface like a desk or a window, the vectors output of the "LB Generate Point Grid" component should be input here. If not supplied, sun vectors coming from any direction will be used to evualuate shade desirability.'
        input_node = self.inputs.new('SvLBSocket', '_shade_geo')
        input_node.prop_name = 'sv__shade_geo'
        input_node.tooltip = 'Rhino Breps and/or Rhino Meshes representing shading to be evaluated in terms of its benefit. Note that, in the case that multiple shading geometries are connected, this component does not account for the interaction between the different shading surfaces and will just evaluate each part of the shade independently.'
        input_node = self.inputs.new('SvLBSocket', 'context_')
        input_node.prop_name = 'sv_context_'
        input_node.tooltip = 'Rhino Breps and/or Rhino Meshes representing context geometry that can block sunlight to the _study_points, therefore discounting any benefit or harm that could come to the region.'
        input_node = self.inputs.new('SvLBSocket', '_grid_size')
        input_node.prop_name = 'sv__grid_size'
        input_node.tooltip = 'A positive number in Rhino model units for the size of grid cells at which the input _shade_geo will be subdivided for shade benefit analysis. The smaller the grid size, the higher the resolution of the analysis and the longer the calculation will take.  So it is recommended that one start with a large value here and decrease the value as needed. However, the grid size should usually be smaller than the dimensions of the smallest piece of the _shade_geo and context_ in order to yield meaningful results.'
        input_node = self.inputs.new('SvLBSocket', '_timestep_')
        input_node.prop_name = 'sv__timestep_'
        input_node.tooltip = 'A positive integer for the number of timesteps per hour at which the "LB SunPath" component generated sun vectors. This is used to correctly interpret the time duration represented by each of the input sun vectors. (Default: 1 for 1 vector per hour).'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'Optional legend parameters from the "LB Legend Parameters" that will be used to customize the display of the results.'
        input_node = self.inputs.new('SvLBSocket', '_cpu_count_')
        input_node.prop_name = 'sv__cpu_count_'
        input_node.tooltip = 'An integer to set the number of CPUs used in the execution of the intersection calculation. If unspecified, it will automatically default to one less than the number of CPUs currently available on the machine or 1 if only one processor is available.'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to "True" to run the component and perform shade benefit analysis.'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'A colored mesh of the _shade_geo showing where shading is helpful (in blue), and where it does not make much of a difference (white or desaturated colors). Note that the colors can change depending upon the input legend_par_.'
        output_node = self.outputs.new('SvLBSocket', 'legend')
        output_node.tooltip = 'Legend showing the numeric values of hrs / square unit that correspond to the colors in the shade mesh.'
        output_node = self.outputs.new('SvLBSocket', 'title')
        output_node.tooltip = 'A text object for the study title.'
        output_node = self.outputs.new('SvLBSocket', 'shade_help')
        output_node.tooltip = 'The cumulative hrs / square unit helped by shading the given cell. If a given square meter of _shade_geo has a shade helpfulness of 10 hrs/m2, this means that a shade in this location blocks an average of 10 hours to each of the _study_points.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Visualize the desirability of shade in terms of the time period of blocked sun vectors for each part of a shade geometry. _ The calculation assumes that all input _vectors represent sun to be blocked, which is often the case when evaluating shade in terms of its benefit for glare reduction and occupant visual comfort. It can also be the case when sun vectors have been filtered to account for times of peak cooling demand or for the heat stress of human subjects. _ The component outputs a colored mesh of the shade illustrating the helpfulness of shading each part of the _shade_geo. A higher saturation of blue indicates that shading the cell blocks more hours of sun and is therefore more desirable. _ The units for shade desirability are hrs/square Rhino unit, which note the amount of time that sun is blocked by a given cell. So, if a given square meter of input _shade_geo has a shade desirability of 10 hrs/m2, this means that a shade in this location blocks an average of 10 hours to each of the _study_points. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['mesh', 'legend', 'title', 'shade_help']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_vectors', '_study_points', 'study_directs_', '_shade_geo', 'context_', '_grid_size', '_timestep_', 'legend_par_', '_cpu_count_', '_run']
        self.sv_input_types = ['System.Object', 'Point3d', 'Vector3d', 'GeometryBase', 'GeometryBase', 'double', 'int', 'System.Object', 'int', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['list', 'list', 'list', 'list', 'list', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _vectors, _study_points, study_directs_, _shade_geo, context_, _grid_size, _timestep_, legend_par_, _cpu_count_, _run):

        
        try:
            from ladybug.color import Colorset
            from ladybug.graphic import GraphicContainer
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import units_abbreviation
            from ladybug_tools.togeometry import to_joined_gridded_mesh3d, to_vector3d
            from ladybug_tools.fromgeometry import from_mesh3d, from_point3d, from_vector3d
            from ladybug_tools.fromobjects import legend_objects
            from ladybug_tools.text import text_objects
            from ladybug_tools.intersect import join_geometry_to_mesh, generate_intersection_rays, \
                intersect_rays_with_mesh_faces
            from ladybug_tools.sverchok import all_required_inputs, recommended_processor_count
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component) and _run:
            # set the defaults and process all of the inputs
            workers = _cpu_count_ if _cpu_count_ is not None else recommended_processor_count()
            _timestep_ = 1 if _timestep_ is None else _timestep_
            study_directs_ = None if len(study_directs_) == 0 else study_directs_
        
            # create the gridded mesh from the geometry
            analysis_mesh = to_joined_gridded_mesh3d(_shade_geo, _grid_size)
            mesh = from_mesh3d(analysis_mesh)
        
            # create a series of rays that represent the sun projected through the shade
            rev_vec = [from_vector3d(to_vector3d(vec).reverse()) for vec in _vectors]
            int_rays = generate_intersection_rays(_study_points, rev_vec)
        
            # if there is context, remove any rays that are blocked by the context
            shade_mesh = join_geometry_to_mesh(context_) \
                if len(context_) != 0 and context_[0] is not None else None
        
            # intersect the sun rays with the shade mesh
            face_int = intersect_rays_with_mesh_faces(
                mesh, int_rays, shade_mesh, study_directs_, cpu_count=workers)
        
            # loop through the face intersection result and evaluate the benefit
            pt_count = len(_study_points)
            shade_help = []
            for face_res, face_area in zip(face_int, analysis_mesh.face_areas):
                # Normalize by the area of the cell so there's is a consistent metric
                # between cells of different areas.
                # Also, divide the number of study points so people get a sense of
                # the average hours of blocked sun.
                shd_help = ((len(face_res) / face_area) / _timestep_) / pt_count
                shade_help.append(shd_help)
        
            # create the mesh and legend outputs
            graphic = GraphicContainer(shade_help, analysis_mesh.min, analysis_mesh.max, legend_par_)
            graphic.legend_parameters.title = 'hrs/{}2'.format(units_abbreviation())
            if legend_par_ is None or legend_par_.are_colors_default:
                graphic.legend_parameters.colors = Colorset.shade_benefit()
            if legend_par_ is None or legend_par_.min is None:
                graphic.legend_parameters.min = 0
            title = text_objects('Shade Benefit', graphic.lower_title_location,
                                 graphic.legend_parameters.text_height * 1.5,
                                 graphic.legend_parameters.font)
        
            # create all of the visual outputs
            analysis_mesh.colors = graphic.value_colors
            mesh = from_mesh3d(analysis_mesh)
            legend = legend_objects(graphic.legend)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvShadeBenefit)

def unregister():
    bpy.utils.unregister_class(SvShadeBenefit)
