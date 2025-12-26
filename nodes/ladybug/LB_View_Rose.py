import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvViewRose(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvViewRose'
    bl_label = 'LB View Rose'
    sv_icon = 'LB_VIEWROSE'
    sv__context: StringProperty(
        name='_context',
        update=updateNode,
        description='Rhino Breps or Meshes representing context geometry that can block the view around the center point.')
    sv__center_pt: StringProperty(
        name='_center_pt',
        update=updateNode,
        description='A point for the center of the view rose from which view openness will be evaluated.')
    sv__radius_: StringProperty(
        name='_radius_',
        update=updateNode,
        description='A number for the radius of the view rose in Rhino model units. This is also used to evaluate the distance at which context is no longer able to block the view from the center point. This value should typically be increased if the view rose does not extend past the _context geometry. (Default: 100 meters in the current Rhino model units system).')
    sv__view_type_: StringProperty(
        name='_view_type_',
        update=updateNode,
        description='Text or an integer representing the type of view analysis to conduct. Choose from the following options. (Default: 0 - HorizontalRadial) _ 0 - HorizontalRadial - The percentage of the 360 horizontal view plane that is not blocked by the context geometry. _ 1 - Horizontal30DegreeOffset - The percentage of the 360 horizontal view band bounded on top and bottom by a 30 degree offset from the horizontal plane. 30 degrees corresponds roughly to the vertical limit of human peripheral vision. _ 2 - Spherical - The percentage of the sphere surrounding each of the test points that is not blocked by context geometry. This is equivalent to a solid angle and gives equal weight to all portions of the sphere. _ 3 - SkyExposure - The percentage of the sky that is visible from each of the the test points.')
    sv__resolution_: StringProperty(
        name='_resolution_',
        update=updateNode,
        description='A positive integer for the number of times that the original view vectors are subdivided. For a circle, 1 indicates that 72 evenly-spaced vectors are used to describe a circle, 2 indicates that 144 vectors describe a circle, and each successive value will roughly double the number of view vectors used. For a dome, 1 indicates that 1225 are used to describe the dome, 2 indicates that 5040 view vectors describe the some and each successive value will roughly quadruple the number of view vectors used. Setting this to a high value will result in a more accurate analysis but will take longer to run. (Default: 1).')
    sv_legend_par_: StringProperty(
        name='legend_par_',
        update=updateNode,
        description='Optional legend parameters from the "LB Legend Parameters" that will be used to customize the display of the results.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_context')
        input_node.prop_name = 'sv__context'
        input_node.tooltip = 'Rhino Breps or Meshes representing context geometry that can block the view around the center point.'
        input_node = self.inputs.new('SvLBSocket', '_center_pt')
        input_node.prop_name = 'sv__center_pt'
        input_node.tooltip = 'A point for the center of the view rose from which view openness will be evaluated.'
        input_node = self.inputs.new('SvLBSocket', '_radius_')
        input_node.prop_name = 'sv__radius_'
        input_node.tooltip = 'A number for the radius of the view rose in Rhino model units. This is also used to evaluate the distance at which context is no longer able to block the view from the center point. This value should typically be increased if the view rose does not extend past the _context geometry. (Default: 100 meters in the current Rhino model units system).'
        input_node = self.inputs.new('SvLBSocket', '_view_type_')
        input_node.prop_name = 'sv__view_type_'
        input_node.tooltip = 'Text or an integer representing the type of view analysis to conduct. Choose from the following options. (Default: 0 - HorizontalRadial) _ 0 - HorizontalRadial - The percentage of the 360 horizontal view plane that is not blocked by the context geometry. _ 1 - Horizontal30DegreeOffset - The percentage of the 360 horizontal view band bounded on top and bottom by a 30 degree offset from the horizontal plane. 30 degrees corresponds roughly to the vertical limit of human peripheral vision. _ 2 - Spherical - The percentage of the sphere surrounding each of the test points that is not blocked by context geometry. This is equivalent to a solid angle and gives equal weight to all portions of the sphere. _ 3 - SkyExposure - The percentage of the sky that is visible from each of the the test points.'
        input_node = self.inputs.new('SvLBSocket', '_resolution_')
        input_node.prop_name = 'sv__resolution_'
        input_node.tooltip = 'A positive integer for the number of times that the original view vectors are subdivided. For a circle, 1 indicates that 72 evenly-spaced vectors are used to describe a circle, 2 indicates that 144 vectors describe a circle, and each successive value will roughly double the number of view vectors used. For a dome, 1 indicates that 1225 are used to describe the dome, 2 indicates that 5040 view vectors describe the some and each successive value will roughly quadruple the number of view vectors used. Setting this to a high value will result in a more accurate analysis but will take longer to run. (Default: 1).'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'Optional legend parameters from the "LB Legend Parameters" that will be used to customize the display of the results.'
        output_node = self.outputs.new('SvLBSocket', 'view_vecs')
        output_node.tooltip = 'A list of vectors which are projected from each of the points to evaluate view.'
        output_node = self.outputs.new('SvLBSocket', 'results')
        output_node.tooltip = 'A list of numbers that aligns with the vertices of the mesh. Each number indicates the distance from the _center_pt at which the view is blocked from a particular direction.'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'A colored mesh representing the visible area from the viewpoint past the _context geometry. Colors indicate how open the view is from a given direction.'
        output_node = self.outputs.new('SvLBSocket', 'legend')
        output_node.tooltip = 'A legend that correspond to the colors of the mesh and shows the distance at which vectors are blocked.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Visualize the view openness around a given point as a colored mesh that fills a circle, sphere, or hemisphere (depending on the specified view type). _ The input context will block the view, resulting in a decresed view rose size and a change in the view rose color. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['view_vecs', 'results', 'mesh', 'legend']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_context', '_center_pt', '_radius_', '_view_type_', '_resolution_', 'legend_par_']
        self.sv_input_types = ['GeometryBase', 'Point3d', 'double', 'string', 'int', 'System.Object']
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

    def process_ladybug(self, _context, _center_pt, _radius_, _view_type_, _resolution_, legend_par_):

        try:
            from ladybug_geometry.geometry3d import Mesh3D
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug.viewsphere import view_sphere
            from ladybug.color import Colorset
            from ladybug.graphic import GraphicContainer
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import conversion_to_meters, units_abbreviation
            from ladybug_tools.togeometry import to_point3d
            from ladybug_tools.fromgeometry import from_mesh3d, from_vector3d
            from ladybug_tools.fromobjects import legend_objects
            from ladybug_tools.intersect import join_geometry_to_mesh, \
                intersect_mesh_rays_distance
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        # dictionary to record all available view types
        VIEW_TYPES = {
            None: (0, view_sphere.horizontal_circle_view_mesh),
            'HorizontalRadial': (0, view_sphere.horizontal_circle_view_mesh),
            'Horizontal30DegreeOffset': (1, view_sphere.horizontal_radial_view_mesh),
            'Spherical': (2, view_sphere.sphere_view_mesh),
            'SkyExposure': (3, view_sphere.dome_view_mesh),
            '0': (0, view_sphere.horizontal_circle_view_mesh),
            '1': (1, view_sphere.horizontal_radial_view_mesh),
            '2': (2, view_sphere.sphere_view_mesh),
            '3': (3, view_sphere.dome_view_mesh)
        }
        
        
        if all_required_inputs(ghenv.Component):
            # process the view_type_ and set the default values
            vt_int, view_method = VIEW_TYPES[_view_type_]
            _radius_ = int(100 / conversion_to_meters()) if _radius_ is None else _radius_
            resolution_ = _resolution_ if _resolution_ is not None else 1
            az_count = 72 * resolution_
            alt_count = 6 * resolution_ if vt_int == 1 else 18 * resolution_
        
            # get the view vectors and mesh based on the inputs
            lb_point = to_point3d(_center_pt)
            if vt_int == 0:
                study_mesh, lb_vecs = view_method(
                    center_point=lb_point, radius=_radius_, azimuth_count=az_count)
            else:
                study_mesh, lb_vecs = view_method(
                    center_point=lb_point, radius=_radius_,
                    azimuth_count=az_count, altitude_count=alt_count)
            view_vecs = [from_vector3d(pt) for pt in lb_vecs]
        
            # process the input geometry
            shade_mesh = join_geometry_to_mesh(_context)
        
            # intersect the rays with the mesh
            results = intersect_mesh_rays_distance(shade_mesh, _center_pt, view_vecs, _radius_)
        
            # adjust the mesh based on the distance
            move_vecs = [vec * -(_radius_ - dist) for vec, dist, in zip(lb_vecs, results)]
            new_verts = [lb_point] if vt_int in (0, 1) else []
            iter_verts = study_mesh.vertices[1:] if  vt_int in (0, 1) else study_mesh.vertices
            for pt, mv in zip(iter_verts, move_vecs):
                new_verts.append(pt.move(mv))
            study_mesh = Mesh3D(new_verts, study_mesh.faces)
        
            # add a value at the start to align with the vertices
            if vt_int in (0, 1):
                avg_val = sum(results) / len(results)
                results.insert(0, avg_val)
        
            # create the mesh and legend outputs
            graphic = GraphicContainer(results, study_mesh.min, study_mesh.max, legend_par_)
            graphic.legend_parameters.title = units_abbreviation()
            if legend_par_ is None or legend_par_.are_colors_default:
                graphic.legend_parameters.colors = Colorset.view_study()
        
            # create all of the visual outputs
            study_mesh.colors = graphic.value_colors
            mesh = from_mesh3d(study_mesh)
            legend = legend_objects(graphic.legend)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvViewRose)

def unregister():
    bpy.utils.unregister_class(SvViewRose)
