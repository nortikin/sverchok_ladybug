import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvGenPts(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvGenPts'
    bl_label = 'LB Generate Point Grid'
    sv_icon = 'LB_GENPTS'
    sv__geometry: StringProperty(
        name='_geometry',
        update=updateNode,
        description='Brep or Mesh from which to generate the points and grid.')
    sv__grid_size: StringProperty(
        name='_grid_size',
        update=updateNode,
        description='Number for the size of the test grid.')
    sv__offset_dist_: StringProperty(
        name='_offset_dist_',
        update=updateNode,
        description='Number for the distance to move points from the surfaces of the input _geometry.  Typically, this should be a small positive number to ensure points are not blocked by the mesh. (Default: 0).')
    sv_quad_only_: StringProperty(
        name='quad_only_',
        update=updateNode,
        description='Boolean to note whether meshing should be done using Rhino\'s defaults (False), which fills the entire _geometry to the edges with both quad and tringulated faces, or a mesh with only quad faces should be generated. _ FOR ADVANCED USERS: This input can also be a vector object that will be used to set the orientation of the quad-only grid. Note that, if a vector is input here that is not aligned with the plane of the input _geometry, an error will be raised.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_geometry')
        input_node.prop_name = 'sv__geometry'
        input_node.tooltip = 'Brep or Mesh from which to generate the points and grid.'
        input_node = self.inputs.new('SvLBSocket', '_grid_size')
        input_node.prop_name = 'sv__grid_size'
        input_node.tooltip = 'Number for the size of the test grid.'
        input_node = self.inputs.new('SvLBSocket', '_offset_dist_')
        input_node.prop_name = 'sv__offset_dist_'
        input_node.tooltip = 'Number for the distance to move points from the surfaces of the input _geometry.  Typically, this should be a small positive number to ensure points are not blocked by the mesh. (Default: 0).'
        input_node = self.inputs.new('SvLBSocket', 'quad_only_')
        input_node.prop_name = 'sv_quad_only_'
        input_node.tooltip = 'Boolean to note whether meshing should be done using Rhino\'s defaults (False), which fills the entire _geometry to the edges with both quad and tringulated faces, or a mesh with only quad faces should be generated. _ FOR ADVANCED USERS: This input can also be a vector object that will be used to set the orientation of the quad-only grid. Note that, if a vector is input here that is not aligned with the plane of the input _geometry, an error will be raised.'
        output_node = self.outputs.new('SvLBSocket', 'points')
        output_node.tooltip = 'Test points at the center of each mesh face.'
        output_node = self.outputs.new('SvLBSocket', 'vectors')
        output_node.tooltip = 'Vectors for the normal direction at each of the points.'
        output_node = self.outputs.new('SvLBSocket', 'face_areas')
        output_node.tooltip = 'Area of each mesh face.'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'Analysis mesh that can be passed to the "LB Spatial Heatmap" component.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Genrate a mesh with corresponding test points from a Rhino Brep (or Mesh). _ The resulting mesh will be in a format that the "LB Spatial Heatmap" component will accept. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['points', 'vectors', 'face_areas', 'mesh']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_geometry', '_grid_size', '_offset_dist_', 'quad_only_']
        self.sv_input_types = ['GeometryBase', 'double', 'double', 'System.Object']
        self.sv_input_defaults = [None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item']
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

    def process_ladybug(self, _geometry, _grid_size, _offset_dist_, quad_only_):

        try:
            from ladybug_geometry.geometry3d.plane import Plane
            from ladybug_geometry.geometry3d.face import Face3D
            from ladybug_geometry.geometry3d.mesh import Mesh3D
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.togeometry import to_gridded_mesh3d, to_mesh3d, \
                to_face3d, to_vector3d
            from ladybug_tools.fromgeometry import from_mesh3d, from_point3d, from_vector3d
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # check the input and generate the mesh.
            _offset_dist_ = _offset_dist_ or 0
            if quad_only_:  # use Ladybug's built-in meshing methods
                lb_faces = to_face3d(_geometry)
                try:
                    x_axis = to_vector3d(quad_only_)
                    lb_faces = [Face3D(f.boundary, Plane(f.normal, f[0], x_axis), f.holes)
                                for f in lb_faces]
                except AttributeError:
                    pass  # no plane connected; juse use default orientation
                lb_meshes = []
                for geo in lb_faces:
                    try:
                        lb_meshes.append(geo.mesh_grid(_grid_size, offset=_offset_dist_))
                    except AssertionError:  # tiny geometry not compatible with quad faces
                        continue
                if len(lb_meshes) == 0:
                    lb_mesh = None
                elif len(lb_meshes) == 1:
                    lb_mesh = lb_meshes[0]
                elif len(lb_meshes) > 1:
                    lb_mesh = Mesh3D.join_meshes(lb_meshes)
            else:  # use Blender Ladybug's default meshing
                try:  # assume it's a Blender Ladybug Brep
                    lb_mesh = to_gridded_mesh3d(_geometry, _grid_size, _offset_dist_)
                except TypeError:  # assume it's a Blender Ladybug Mesh
                    try:
                        lb_mesh = to_mesh3d(_geometry)
                    except TypeError:  # unidientified geometry type
                        raise TypeError(
                            '_geometry must be a Brep or a Mesh. Got {}.'.format(type(_geometry)))
        
            # generate the test points, vectors, and areas.
            if lb_mesh is not None:
                points = [from_point3d(pt) for pt in lb_mesh.face_centroids]
                vectors = [from_vector3d(vec) for vec in lb_mesh.face_normals]
                face_areas = lb_mesh.face_areas
                mesh = [from_mesh3d(lb_mesh)]
            else:
                mesh = []

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvGenPts)

def unregister():
    bpy.utils.unregister_class(SvGenPts)
