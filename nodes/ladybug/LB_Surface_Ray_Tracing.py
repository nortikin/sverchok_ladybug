import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvSrfRayTrace(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvSrfRayTrace'
    bl_label = 'LB Surface Ray Tracing'
    sv_icon = 'LB_SRFRAYTRACE'
    sv__vector: StringProperty(
        name='_vector',
        update=updateNode,
        description='A sun vector (typically from the "LB SunPath" component), which will be used to evaluate the light boucing off of the _source_geo and through the context_.')
    sv__source_geo: StringProperty(
        name='_source_geo',
        update=updateNode,
        description='A brep or mesh representing a surface off of which sun rays first bounce. Lists of breps or meshes are also acceptable. These surfaces will be used to generate the initial sun rays in a grid-like pattern.')
    sv_context_: StringProperty(
        name='context_',
        update=updateNode,
        description='Breps or meshes for conext geometry, which will reflect the sun rays after they bounce off of the _source_geo.')
    sv__grid_size: StringProperty(
        name='_grid_size',
        update=updateNode,
        description='A positive number in Rhino model units for the average distance between sun ray points to generate along the _source_geo.')
    sv__bounce_count_: StringProperty(
        name='_bounce_count_',
        update=updateNode,
        description='An positive integer for the number of ray bounces to trace the sun rays forward. (Default: 1).')
    sv__first_length_: StringProperty(
        name='_first_length_',
        update=updateNode,
        description='A positive number in Rhino model units for the length of the sun ray before the first bounce. If unspecified, this will be the diagonal of the bounding box surrounding all input geometries.')
    sv__last_length_: StringProperty(
        name='_last_length_',
        update=updateNode,
        description='A positive number in Rhino model units representing the length of the sun ray after the last bounce. If unspecified, this will be the diagonal of the bounding box surrounding all input geometries.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_vector')
        input_node.prop_name = 'sv__vector'
        input_node.tooltip = 'A sun vector (typically from the "LB SunPath" component), which will be used to evaluate the light boucing off of the _source_geo and through the context_.'
        input_node = self.inputs.new('SvLBSocket', '_source_geo')
        input_node.prop_name = 'sv__source_geo'
        input_node.tooltip = 'A brep or mesh representing a surface off of which sun rays first bounce. Lists of breps or meshes are also acceptable. These surfaces will be used to generate the initial sun rays in a grid-like pattern.'
        input_node = self.inputs.new('SvLBSocket', 'context_')
        input_node.prop_name = 'sv_context_'
        input_node.tooltip = 'Breps or meshes for conext geometry, which will reflect the sun rays after they bounce off of the _source_geo.'
        input_node = self.inputs.new('SvLBSocket', '_grid_size')
        input_node.prop_name = 'sv__grid_size'
        input_node.tooltip = 'A positive number in Rhino model units for the average distance between sun ray points to generate along the _source_geo.'
        input_node = self.inputs.new('SvLBSocket', '_bounce_count_')
        input_node.prop_name = 'sv__bounce_count_'
        input_node.tooltip = 'An positive integer for the number of ray bounces to trace the sun rays forward. (Default: 1).'
        input_node = self.inputs.new('SvLBSocket', '_first_length_')
        input_node.prop_name = 'sv__first_length_'
        input_node.tooltip = 'A positive number in Rhino model units for the length of the sun ray before the first bounce. If unspecified, this will be the diagonal of the bounding box surrounding all input geometries.'
        input_node = self.inputs.new('SvLBSocket', '_last_length_')
        input_node.prop_name = 'sv__last_length_'
        input_node.tooltip = 'A positive number in Rhino model units representing the length of the sun ray after the last bounce. If unspecified, this will be the diagonal of the bounding box surrounding all input geometries.'
        output_node = self.outputs.new('SvLBSocket', 'rays')
        output_node.tooltip = 'A list of polylines representing the sun rays traced forward onto the _source_geo and then through the context_.'
        output_node = self.outputs.new('SvLBSocket', 'int_pts')
        output_node.tooltip = 'A data tree of intersection points one one branch for each of the rays above.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Get a ray tracing visualization of direct sunlight rays reflected off of _source_geo and subsequently bouncing through a set of context_ geometries. _ Examples where this visualization could be useful include understading the reflection of light by a light shelf or testing to see whether a parabolic glass or metal building geometry might focus sunlight to dangerous levels at certain times of the year. _ Note that this component assumes that all sun light is reflected specularly (like a mirror) and, for more detailed raytracing analysis with diffuse scattering, the Honeybee Radiance components should be used. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['rays', 'int_pts']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_vector', '_source_geo', 'context_', '_grid_size', '_bounce_count_', '_first_length_', '_last_length_']
        self.sv_input_types = ['Vector3d', 'GeometryBase', 'GeometryBase', 'double', 'int', 'double', 'double']
        self.sv_input_defaults = [None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'list', 'list', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _vector, _source_geo, context_, _grid_size, _bounce_count_, _first_length_, _last_length_):

        import math
        
        try:
            from ladybug_geometry.geometry3d.ray import Ray3D
            from ladybug_geometry.geometry3d.polyline import Polyline3D
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.togeometry import to_joined_gridded_mesh3d, to_point3d, \
                to_vector3d
            from ladybug_tools.fromgeometry import from_point3d, from_vector3d, from_ray3d, \
                from_polyline3d
            from ladybug_tools.intersect import join_geometry_to_brep, bounding_box_extents, \
                trace_ray, normal_at_point
            from ladybug_tools.sverchok import all_required_inputs, list_to_data_tree, \
                hide_output
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # check the _bounce_count_
            _bounce_count_ = 0 if _bounce_count_ is None else _bounce_count_ - 1
            assert _bounce_count_ >= 0, 'The input _bounce_count_ must be greater '  \
                'than zero. Got {}.'.format(_bounce_count_ + 1)
            # process the input sun vector
            lb_vec = to_vector3d(_vector).normalize()
            neg_lb_vec = -lb_vec
            vec = from_vector3d(lb_vec)
        
            # convert all of the _source_geo and contex into a single Brep for ray tracing
            rtrace_brep = join_geometry_to_brep(_source_geo + context_)
        
            # autocompute the first and last bounce length if it's unspecified
            if _first_length_ is None or _last_length_ is None:
                max_pt, min_pt = (to_point3d(p) for p in bounding_box_extents(rtrace_brep))
                diag_dist = max_pt.distance_to_point(min_pt)
                _first_length_ = diag_dist if _first_length_ is None else _first_length_
                _last_length_ = diag_dist if _last_length_ is None else _last_length_
        
            # create the gridded mesh from the _source_geo and set up the starting rays
            study_mesh = to_joined_gridded_mesh3d(_source_geo, _grid_size)
            move_vec = neg_lb_vec * _first_length_
            source_points = [pt + move_vec for pt in study_mesh.face_centroids]
            lb_rays = [Ray3D(pt, lb_vec) for pt in source_points]
            start_rays = [from_ray3d(ray) for ray in lb_rays]
        
            # trace each ray through the geometry
            cutoff_ang = math.pi / 2
            rtrace_geo = [rtrace_brep]
            rays, int_pts = [], []
            for ray, pt, norm in zip(start_rays, source_points, study_mesh.face_normals):
                if norm.angle(neg_lb_vec) < cutoff_ang:
                    pl_pts = trace_ray(ray, rtrace_geo, _bounce_count_ + 2)
                    # if the intersection was successful, create a polyline represeting the ray
                    if pl_pts:
                        # gather all of the intersection points
                        all_pts = [pt]
                        for i_pt in pl_pts:
                            all_pts.append(to_point3d(i_pt))
                        # compute the last point
                        if len(pl_pts) < _bounce_count_ + 2:
                            int_norm = normal_at_point(rtrace_brep, pl_pts[-1])
                            int_norm = to_vector3d(int_norm)
                            last_vec = all_pts[-2] - all_pts[-1]
                            last_vec = last_vec.normalize()
                            final_vec = last_vec.reflect(int_norm).reverse()
                            final_pt = all_pts[-1] + (final_vec * _last_length_)
                            all_pts.append(final_pt)
                        # create a Polyline3D from the points
                        lb_ray_line = Polyline3D(all_pts)
                        rays.append(from_polyline3d(lb_ray_line))
                        int_pts.append([from_point3d(p) for p in all_pts])
        
            # convert the intersection points to a data tree
            int_pts = list_to_data_tree(int_pts)
            hide_output(ghenv.Component, 1)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvSrfRayTrace)

def unregister():
    bpy.utils.unregister_class(SvSrfRayTrace)
