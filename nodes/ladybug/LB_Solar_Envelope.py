import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvSolarEnvelope(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvSolarEnvelope'
    bl_label = 'LB Solar Envelope'
    sv_icon = 'LB_SOLARENVELOPE'
    sv__geometry: StringProperty(
        name='_geometry',
        update=updateNode,
        description='Rhino Breps and/or Rhino Meshes for which the solar envelope will be computed. If Breps are input, they will be subdivided using the _grid_size to yeild individual points at which analysis will occur. If a Mesh is input, the analysis will be performed for each vertex of the mesh instead of subdividing it.')
    sv__obstacles: StringProperty(
        name='_obstacles',
        update=updateNode,
        description='A list of horizontal planar Breps or curves indicating the tops (in the case of solar collection) or bottoms (in the case of solar rights) of context geometries. Being above a solar collection boundary ensures these top surfaces don\'t block the sun vectors to ones position. Being below a solar rights boundary ensures these bottom surfaces are protected from shade.')
    sv__vectors: StringProperty(
        name='_vectors',
        update=updateNode,
        description='Sun vectors from the "LB SunPath" component, which determine the times of the year when sun should be accessible.')
    sv__grid_size: StringProperty(
        name='_grid_size',
        update=updateNode,
        description='A positive number in Rhino model units for the size of grid cells at which the input _geometry will be subdivided for envelope analysis. The smaller the grid size, the higher the resolution of the analysis and the longer the calculation will take.  So it is recommended that one start with a large value here and decrease the value as needed. The default will be a relativel coarse auto-calculated from the bounding box around the _geometry.')
    sv__height_limit_: StringProperty(
        name='_height_limit_',
        update=updateNode,
        description='A positive number for the minimum distance below (for collections) or maximum distance above (for rights) the average _geometry height that the envelope points can be. This is used when there are no vectors blocked for a given point. (Default: 100 meters).')
    sv_solar_rights_: StringProperty(
        name='solar_rights_',
        update=updateNode,
        description='Set to True to compute a solar rights boundary and False to compute a solar collection boundary. Solar rights boundaries represent the boundary below which one can build without shading the surrounding obstacles from any of the _vectors. Solar collection boundaries represent the boundary above which one will have direct solar access to all of the input _vectors. (Default: False).')
    sv__run: StringProperty(
        name='_run',
        update=updateNode,
        description='Set to "True" to run the component and get a solar envelope.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_geometry')
        input_node.prop_name = 'sv__geometry'
        input_node.tooltip = 'Rhino Breps and/or Rhino Meshes for which the solar envelope will be computed. If Breps are input, they will be subdivided using the _grid_size to yeild individual points at which analysis will occur. If a Mesh is input, the analysis will be performed for each vertex of the mesh instead of subdividing it.'
        input_node = self.inputs.new('SvLBSocket', '_obstacles')
        input_node.prop_name = 'sv__obstacles'
        input_node.tooltip = 'A list of horizontal planar Breps or curves indicating the tops (in the case of solar collection) or bottoms (in the case of solar rights) of context geometries. Being above a solar collection boundary ensures these top surfaces don\'t block the sun vectors to ones position. Being below a solar rights boundary ensures these bottom surfaces are protected from shade.'
        input_node = self.inputs.new('SvLBSocket', '_vectors')
        input_node.prop_name = 'sv__vectors'
        input_node.tooltip = 'Sun vectors from the "LB SunPath" component, which determine the times of the year when sun should be accessible.'
        input_node = self.inputs.new('SvLBSocket', '_grid_size')
        input_node.prop_name = 'sv__grid_size'
        input_node.tooltip = 'A positive number in Rhino model units for the size of grid cells at which the input _geometry will be subdivided for envelope analysis. The smaller the grid size, the higher the resolution of the analysis and the longer the calculation will take.  So it is recommended that one start with a large value here and decrease the value as needed. The default will be a relativel coarse auto-calculated from the bounding box around the _geometry.'
        input_node = self.inputs.new('SvLBSocket', '_height_limit_')
        input_node.prop_name = 'sv__height_limit_'
        input_node.tooltip = 'A positive number for the minimum distance below (for collections) or maximum distance above (for rights) the average _geometry height that the envelope points can be. This is used when there are no vectors blocked for a given point. (Default: 100 meters).'
        input_node = self.inputs.new('SvLBSocket', 'solar_rights_')
        input_node.prop_name = 'sv_solar_rights_'
        input_node.tooltip = 'Set to True to compute a solar rights boundary and False to compute a solar collection boundary. Solar rights boundaries represent the boundary below which one can build without shading the surrounding obstacles from any of the _vectors. Solar collection boundaries represent the boundary above which one will have direct solar access to all of the input _vectors. (Default: False).'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to "True" to run the component and get a solar envelope.'
        output_node = self.outputs.new('SvLBSocket', 'readMe!')
        output_node.tooltip = '...'
        output_node = self.outputs.new('SvLBSocket', 'points')
        output_node.tooltip = 'The grid of points above the test _geometry representing the height to which the solar envelope boundary reaches.'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'A mesh representing the solar envelope. For solar collections (the default), this represents the boundary above which the one will have direct solar access to all of the input _vectors. For solar rights envelopes, this represents the boundary below which one can build without shading the surrounding obstacles from any of the _vectors.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Generate a solar envelope boundary for a given geometry, set of sun vectors, and context (obstacle) geometry. _ Solar collection envelopes show the height above which one will have solar access to certain sun positions on a given site. _ Solar rights envelopes illustrate the volume in which one can build while ensuring that a new development does not shade the surrounding properties for certain sun positions. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['readMe!', 'points', 'mesh']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_geometry', '_obstacles', '_vectors', '_grid_size', '_height_limit_', 'solar_rights_', '_run']
        self.sv_input_types = ['GeometryBase', 'Brep', 'Vector3d', 'double', 'int', 'bool', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None, None]
        self.sv_input_access = ['list', 'list', 'list', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _geometry, _obstacles, _vectors, _grid_size, _height_limit_, solar_rights_, _run):

        try:
            from ladybug.solarenvelope import SolarEnvelope
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import conversion_to_meters
            from ladybug_tools.togeometry import to_joined_gridded_mesh3d, to_face3d, \
                to_vector3d
            from ladybug_tools.fromgeometry import from_mesh3d, from_point3d
            from ladybug_tools.sverchok import all_required_inputs, hide_output
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component) and _run:
            # set the default offset distance
            _height_limit_ = _height_limit_ if _height_limit_ is not None \
                else 100 / conversion_to_meters()
        
            # convert geometry, objstacles, and vectors to ladybug_geomtery
            study_mesh = to_joined_gridded_mesh3d(_geometry, _grid_size)
            obstacle_faces = [g for geo in _obstacles for g in to_face3d(geo)]
            sun_vectors = [to_vector3d(vec) for vec in _vectors]
        
            # compute the solar envelope
            solar_obj = SolarEnvelope(
                study_mesh, obstacle_faces, sun_vectors, _height_limit_, solar_rights_)
            lb_mesh = solar_obj.envelope_mesh()
            mesh = from_mesh3d(lb_mesh)
            points = [from_point3d(pt) for pt in lb_mesh.vertices]
            hide_output(ghenv.Component, 1)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvSolarEnvelope)

def unregister():
    bpy.utils.unregister_class(SvSolarEnvelope)
