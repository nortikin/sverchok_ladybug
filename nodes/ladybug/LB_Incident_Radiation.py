import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvIncidentRadiation(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvIncidentRadiation'
    bl_label = 'LB Incident Radiation'
    sv_icon = 'LB_INCIDENTRADIATION'
    sv__sky_mtx: StringProperty(
        name='_sky_mtx',
        update=updateNode,
        description='A Sky Matrix from the "LB Cumulative Sky Matrix" component or the "LB Benefit Sky Matrix" component, which describes the radiation coming from the various patches of the sky. The "LB Sky Dome" component can be used to visualize any sky matrix to understand its relationship to the test geometry.')
    sv__geometry: StringProperty(
        name='_geometry',
        update=updateNode,
        description='Rhino Breps and/or Rhino Meshes for which incident radiation analysis will be conducted. If Breps are input, they will be subdivided using the _grid_size to yeild individual points at which analysis will occur. If a Mesh is input, radiation analysis analysis will be performed for each face of this mesh instead of subdividing it.')
    sv_context_: StringProperty(
        name='context_',
        update=updateNode,
        description='Rhino Breps and/or Rhino Meshes representing context geometry that can block solar radiation to the test _geometry.')
    sv__grid_size: StringProperty(
        name='_grid_size',
        update=updateNode,
        description='A positive number in Rhino model units for the size of grid cells at which the input _geometry will be subdivided for incident radiation analysis. The smaller the grid size, the higher the resolution of the analysis and the longer the calculation will take. So it is recommended that one start with a large value here and decrease the value as needed. However, the grid size should usually be smaller than the dimensions of the smallest piece of the _geometry and context_ in order to yield meaningful results.')
    sv__offset_dist_: StringProperty(
        name='_offset_dist_',
        update=updateNode,
        description='A number for the distance to move points from the surfaces of the input _geometry.  Typically, this should be a small positive number to ensure points are not blocked by the mesh. (Default: 10 cm in the equivalent Rhino Model units).')
    sv_irradiance_: StringProperty(
        name='irradiance_',
        update=updateNode,
        description='Boolean to note whether the study should output units of cumulative Radiation (kWh/m2) [False] or units of average Irradiance (W/m2) [True].  (Default: False).')
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
        description='Set to "True" to run the component and perform incident radiation analysis.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_sky_mtx')
        input_node.prop_name = 'sv__sky_mtx'
        input_node.tooltip = 'A Sky Matrix from the "LB Cumulative Sky Matrix" component or the "LB Benefit Sky Matrix" component, which describes the radiation coming from the various patches of the sky. The "LB Sky Dome" component can be used to visualize any sky matrix to understand its relationship to the test geometry.'
        input_node = self.inputs.new('SvLBSocket', '_geometry')
        input_node.prop_name = 'sv__geometry'
        input_node.tooltip = 'Rhino Breps and/or Rhino Meshes for which incident radiation analysis will be conducted. If Breps are input, they will be subdivided using the _grid_size to yeild individual points at which analysis will occur. If a Mesh is input, radiation analysis analysis will be performed for each face of this mesh instead of subdividing it.'
        input_node = self.inputs.new('SvLBSocket', 'context_')
        input_node.prop_name = 'sv_context_'
        input_node.tooltip = 'Rhino Breps and/or Rhino Meshes representing context geometry that can block solar radiation to the test _geometry.'
        input_node = self.inputs.new('SvLBSocket', '_grid_size')
        input_node.prop_name = 'sv__grid_size'
        input_node.tooltip = 'A positive number in Rhino model units for the size of grid cells at which the input _geometry will be subdivided for incident radiation analysis. The smaller the grid size, the higher the resolution of the analysis and the longer the calculation will take. So it is recommended that one start with a large value here and decrease the value as needed. However, the grid size should usually be smaller than the dimensions of the smallest piece of the _geometry and context_ in order to yield meaningful results.'
        input_node = self.inputs.new('SvLBSocket', '_offset_dist_')
        input_node.prop_name = 'sv__offset_dist_'
        input_node.tooltip = 'A number for the distance to move points from the surfaces of the input _geometry.  Typically, this should be a small positive number to ensure points are not blocked by the mesh. (Default: 10 cm in the equivalent Rhino Model units).'
        input_node = self.inputs.new('SvLBSocket', 'irradiance_')
        input_node.prop_name = 'sv_irradiance_'
        input_node.tooltip = 'Boolean to note whether the study should output units of cumulative Radiation (kWh/m2) [False] or units of average Irradiance (W/m2) [True].  (Default: False).'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'Optional legend parameters from the "LB Legend Parameters" that will be used to customize the display of the results.'
        input_node = self.inputs.new('SvLBSocket', '_cpu_count_')
        input_node.prop_name = 'sv__cpu_count_'
        input_node.tooltip = 'An integer to set the number of CPUs used in the execution of the intersection calculation. If unspecified, it will automatically default to one less than the number of CPUs currently available on the machine or 1 if only one processor is available.'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to "True" to run the component and perform incident radiation analysis.'
        output_node = self.outputs.new('SvLBSocket', 'points')
        output_node.tooltip = 'The grid of points on the test _geometry that are be used to perform the incident radiation analysis.'
        output_node = self.outputs.new('SvLBSocket', 'results')
        output_node.tooltip = 'A list of numbers that aligns with the points. Each number indicates the cumulative incident radiation received by each of the points from the sky matrix in kWh/m2.'
        output_node = self.outputs.new('SvLBSocket', 'total')
        output_node.tooltip = 'A number for the total incident solar energy falling on all input geometry in kWh. Note that, unlike the radiation results above, which are normlaized by area, these values are not area-normalized and so the input geometry must be represented correctly in the Rhino model\'s unit system in order for this output to be meaningful.'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'A colored mesh of the test _geometry representing the cumulative incident radiation received by the input _geometry.'
        output_node = self.outputs.new('SvLBSocket', 'legend')
        output_node.tooltip = 'A legend showing the kWh/m2 that correspond to the colors of the mesh.'
        output_node = self.outputs.new('SvLBSocket', 'title')
        output_node.tooltip = 'A text object for the study title.'
        output_node = self.outputs.new('SvLBSocket', 'int_mtx')
        output_node.tooltip = 'A Matrix object that can be connected to the "LB Deconstruct Matrix" component to obtain detailed patch-by-patch results of the study. Each sub-list of the matrix (aka. branch of the Data Tree) represents one of the points used for analysis. The length of each sub-list matches the number of sky patches in the input sky matrix (145 for the default Tregenza sky and 577 for the high_density Reinhart sky). Each value in the sub-list is a value between 0 and 1 indicating the relationship between the point and the patch of the sky. A value of "0", indicates that the patch is not visible for that point at all while a value of "1" indicates that the patch hits the surface that the point represents head on.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate the incident radiation on geometry using a sky matrix from the "Cumulative Sky Matrix" component. _ Such studies of incident radiation can be used to apprxomiate the energy that can be collected from photovoltaic or solar thermal systems. They are also useful for evaluating the impact of a building\'s orientation on both energy use and the size/cost of cooling systems. For studies of photovoltaic potential or building energy use impact, a sky matrix from EPW radiation should be used. For studies of cooling system size/cost, a sky matrix derived from the STAT file\'s clear sky radiation should be used. _ NOTE THAT NO REFLECTIONS OF SOLAR ENERGY ARE INCLUDED IN THE ANALYSIS PERFORMED BY THIS COMPONENT. _ Ground reflected irradiance is crudely acounted for by means of an emissive "ground hemisphere," which is like the sky dome hemisphere and is derived from the ground reflectance that is associated with the connected _sky_mtx. This means that including geometry that represents the ground surface will effectively block such crude ground reflection. _ Also note that this component uses the CAD environment\'s ray intersection methods, which can be fast for geometries with low complexity but does not scale well for complex geometries or many test points. For such complex cases and situations where relfection of solar energy are important, honeybee-radiance should be used. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['points', 'results', 'total', 'mesh', 'legend', 'title', 'int_mtx']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_sky_mtx', '_geometry', 'context_', '_grid_size', '_offset_dist_', 'irradiance_', 'legend_par_', '_cpu_count_', '_run']
        self.sv_input_types = ['System.Object', 'GeometryBase', 'GeometryBase', 'double', 'double', 'bool', 'System.Object', 'int', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'list', 'list', 'item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _sky_mtx, _geometry, context_, _grid_size, _offset_dist_, irradiance_, legend_par_, _cpu_count_, _run):

        import math
        try:  # python 2
            from itertools import izip as zip
        except ImportError:  # python 3
            pass
        
        try:
            from ladybug.viewsphere import view_sphere
            from ladybug.graphic import GraphicContainer
            from ladybug.legend import LegendParameters
            from ladybug.color import Colorset
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import conversion_to_meters
            from ladybug_tools.togeometry import to_joined_gridded_mesh3d
            from ladybug_tools.fromgeometry import from_mesh3d, from_point3d, from_vector3d
            from ladybug_tools.fromobjects import legend_objects
            from ladybug_tools.text import text_objects
            from ladybug_tools.intersect import join_geometry_to_mesh, intersect_mesh_rays
            from ladybug_tools.sverchok import all_required_inputs, hide_output, \
                show_output, objectify_output, de_objectify_output, recommended_processor_count
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component) and _run:
            # set the default offset distance and _cpu_count
            _offset_dist_ = _offset_dist_ if _offset_dist_ is not None \
                else 0.1 / conversion_to_meters()
            workers = _cpu_count_ if _cpu_count_ is not None else recommended_processor_count()
        
            # create the gridded mesh from the geometry
            study_mesh = to_joined_gridded_mesh3d(_geometry, _grid_size)
            points = [from_point3d(pt.move(vec * _offset_dist_)) for pt, vec in
                      zip(study_mesh.face_centroids, study_mesh.face_normals)]
            hide_output(ghenv.Component, 1)
        
            # mesh the geometry and context
            shade_mesh = join_geometry_to_mesh(_geometry + context_)
        
            # deconstruct the matrix and get the sky dome vectors
            mtx = de_objectify_output(_sky_mtx)
            total_sky_rad = [dir_rad + dif_rad for dir_rad, dif_rad in zip(mtx[1], mtx[2])]
            ground_rad = [(sum(total_sky_rad) / len(total_sky_rad)) * mtx[0][1]] * len(total_sky_rad)
            all_rad = total_sky_rad + ground_rad 
            lb_vecs = view_sphere.tregenza_dome_vectors if len(total_sky_rad) == 145 \
                else view_sphere.reinhart_dome_vectors
            if mtx[0][0] != 0:  # there is a north input for sky; rotate vectors
                north_angle = math.radians(mtx[0][0])
                lb_vecs = tuple(vec.rotate_xy(north_angle) for vec in lb_vecs)
            lb_grnd_vecs = tuple(vec.reverse() for vec in lb_vecs)
            all_vecs = [from_vector3d(vec) for vec in lb_vecs + lb_grnd_vecs]
        
            # intersect the rays with the mesh
            normals = [from_vector3d(vec) for vec in study_mesh.face_normals]
            int_matrix_init, angles = intersect_mesh_rays(
                shade_mesh, points, all_vecs, normals, cpu_count=workers)
        
            # compute the results
            results = []
            int_matrix = []
            for int_vals, angs in zip(int_matrix_init, angles):
                pt_rel = [ival * math.cos(ang) for ival, ang in zip(int_vals, angs)]
                int_matrix.append(pt_rel)
                rad_result = sum(r * w for r, w in zip(pt_rel, all_rad))
                results.append(rad_result)
        
            # convert to irradiance if requested
            study_name = 'Incident Radiation'
            if irradiance_:
                study_name = 'Incident Irradiance'
                factor = 1000 / _sky_mtx.wea_duration if hasattr(_sky_mtx, 'wea_duration') \
                    else 1000 / (((mtx[0][3] - mtx[0][2]).total_seconds() / 3600) + 1)
                results = [r * factor for r in results]
        
            # output the intersection matrix and compute total radiation
            int_mtx = objectify_output('Geometry/Sky Intersection Matrix', int_matrix)
            unit_conv = conversion_to_meters() ** 2
            total = 0
            for rad, area in zip(results, study_mesh.face_areas):
                total += rad * area * unit_conv
        
            # create the mesh and legend outputs
            l_par = legend_par_ if legend_par_ is not None else LegendParameters()
            if hasattr(_sky_mtx, 'benefit_matrix') and _sky_mtx.benefit_matrix is not None:
                study_name = '{} Benefit/Harm'.format(study_name)
                if l_par.are_colors_default:
                    l_par.colors = reversed(Colorset.benefit_harm())
                if l_par.min is None:
                    l_par.min = min((min(results), -max(results)))
                if l_par.max is None:
                    l_par.max = max((-min(results), max(results)))
            graphic = GraphicContainer(results, study_mesh.min, study_mesh.max, l_par)
            graphic.legend_parameters.title = 'kWh/m2' if not irradiance_ else 'W/m2'
            title = text_objects(
                study_name, graphic.lower_title_location,
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
    bpy.utils.register_class(SvIncidentRadiation)

def unregister():
    bpy.utils.unregister_class(SvIncidentRadiation)
