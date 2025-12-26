import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvFilterNormal(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvFilterNormal'
    bl_label = 'LB Filter by Normal'
    sv_icon = 'LB_FILTERNORMAL'
    sv_north_: StringProperty(
        name='north_',
        update=updateNode,
        description='A number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. 90 is West and 270 is East. This can also be Vector for the direction to North. (Default: 0)')
    sv__geometry: StringProperty(
        name='_geometry',
        update=updateNode,
        description='Rhino Breps and/or Rhino Meshes which will be broken down into individual planar faces and filtered based on the direction they face.')
    sv__orientation: StringProperty(
        name='_orientation',
        update=updateNode,
        description='Text for the direction that the geometry is facing. This can also be a number between 0 and 360 for the azimuth (clockwise horizontal degrees from North) that the geometry should face. Choose from the following: _ * N = North * NE = Northeast * E = East * SE = Southeast * S = South * SW = Southwest * W = West * NW = Northwest * Up = Upwards * Down = Downwards')
    sv__up_angle_: StringProperty(
        name='_up_angle_',
        update=updateNode,
        description='A number in degrees for the maximum declination angle from the positive Z Axis that is considerd up. This should be between 0 and 90 for the results to be practical. (Default: 30).')
    sv__down_angle_: StringProperty(
        name='_down_angle_',
        update=updateNode,
        description='A number in degrees for the maximum angle difference from the newative Z Axis that is considerd down. This should be between 0 and 90 for the results to be practical. (Default: 30).')
    sv__horiz_angle_: StringProperty(
        name='_horiz_angle_',
        update=updateNode,
        description='Angle in degrees for the horizontal deviation from _orientation that is still considered to face that orientation. This should be between 0 and 90 for the results to be practical. Note that this input has no effect when the input orientation is "Up" or "Down". (Default: 23).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', 'north_')
        input_node.prop_name = 'sv_north_'
        input_node.tooltip = 'A number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. 90 is West and 270 is East. This can also be Vector for the direction to North. (Default: 0)'
        input_node = self.inputs.new('SvLBSocket', '_geometry')
        input_node.prop_name = 'sv__geometry'
        input_node.tooltip = 'Rhino Breps and/or Rhino Meshes which will be broken down into individual planar faces and filtered based on the direction they face.'
        input_node = self.inputs.new('SvLBSocket', '_orientation')
        input_node.prop_name = 'sv__orientation'
        input_node.tooltip = 'Text for the direction that the geometry is facing. This can also be a number between 0 and 360 for the azimuth (clockwise horizontal degrees from North) that the geometry should face. Choose from the following: _ * N = North * NE = Northeast * E = East * SE = Southeast * S = South * SW = Southwest * W = West * NW = Northwest * Up = Upwards * Down = Downwards'
        input_node = self.inputs.new('SvLBSocket', '_up_angle_')
        input_node.prop_name = 'sv__up_angle_'
        input_node.tooltip = 'A number in degrees for the maximum declination angle from the positive Z Axis that is considerd up. This should be between 0 and 90 for the results to be practical. (Default: 30).'
        input_node = self.inputs.new('SvLBSocket', '_down_angle_')
        input_node.prop_name = 'sv__down_angle_'
        input_node.tooltip = 'A number in degrees for the maximum angle difference from the newative Z Axis that is considerd down. This should be between 0 and 90 for the results to be practical. (Default: 30).'
        input_node = self.inputs.new('SvLBSocket', '_horiz_angle_')
        input_node.prop_name = 'sv__horiz_angle_'
        input_node.tooltip = 'Angle in degrees for the horizontal deviation from _orientation that is still considered to face that orientation. This should be between 0 and 90 for the results to be practical. Note that this input has no effect when the input orientation is "Up" or "Down". (Default: 23).'
        output_node = self.outputs.new('SvLBSocket', 'sel_geo')
        output_node.tooltip = 'Selected faces of the input geometry that are facing the direction corresponding to the input criteria.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Filter or select faces of geometry based on their orientation.'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['sel_geo']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['north_', '_geometry', '_orientation', '_up_angle_', '_down_angle_', '_horiz_angle_']
        self.sv_input_types = ['System.Object', 'Brep', 'string', 'double', 'double', 'double']
        self.sv_input_defaults = [None, None, None, None, None, None]
        self.sv_input_access = ['item', 'list', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, north_, _geometry, _orientation, _up_angle_, _down_angle_, _horiz_angle_):

        import math
        
        try:
            from ladybug_geometry.geometry2d import Vector2D
            from ladybug_geometry.geometry3d import Vector3D
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.togeometry import to_face3d, to_vector2d
            from ladybug_tools.fromgeometry import from_face3d
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        ORIENT_MAP = {
            'N': 0,
            'NE': 45,
            'E': 90,
            'SE': 135,
            'S': 180,
            'SW': 225,
            'W': 270,
            'NW': 315,
            'NORTH': 0,
            'NORTHEAST': 45,
            'EAST': 90,
            'SOUTHEAST': 135,
            'SOUTH': 180,
            'SOUTHWEST': 225,
            'WEST': 270,
            'NORTHWEST': 315,
            'UP': 'UP',
            'DOWN': 'DOWN',
            'UPWARDS': 'UP',
            'DOWNWARDS': 'DOWN'
        }
        
        
        if all_required_inputs(ghenv.Component):
            # process all of the global inputs
            if north_ is not None:  # process the north_
                try:
                    north_ = to_vector2d(north_).angle_clockwise(Vector2D(0, 1))
                except AttributeError:  # north angle instead of vector
                    north_ = math.radians(float(north_))
            else:
                north_ = 0
            up_angle = math.radians(_up_angle_) if _up_angle_ is not None else math.radians(30)
            down_angle = math.radians(_down_angle_) if _down_angle_ is not None else math.radians(30)
            horiz_angle =  math.radians(_horiz_angle_) if _horiz_angle_ is not None else math.radians(23)
            up_vec, down_vec = Vector3D(0, 0, 1), Vector3D(0, 0, -1)
        
            # process the geometry and the orientation
            all_geo = [f for geo in _geometry for f in to_face3d(geo)]
            try:
                orient = ORIENT_MAP[_orientation.upper()]
            except KeyError:
                try:
                    orient = float(_orientation)
                except Exception:
                    msg = 'Orientation must be text (eg. N, E, S W) or a number for the\n' \
                        'azimuth of the geometry. Got {}.'.format(_orientation)
                    raise TypeError(msg)
        
            # filter the geometry by the orientation
            if orient == 'UP':
                sel_geo = [f for f in all_geo if f.normal.angle(up_vec) < up_angle]
            elif orient == 'DOWN':
                sel_geo = [f for f in all_geo if f.normal.angle(down_vec) < down_angle]
            else:
                sel_geo = []
                dir_vec = Vector2D(0, 1).rotate(north_).rotate(-math.radians(orient))
                full_down_ang = math.pi - down_angle
                for f in all_geo:
                    if up_angle <= f.normal.angle(up_vec) <= full_down_ang:
                        norm_2d = Vector2D(f.normal.x, f.normal.y)
                        if -horiz_angle <= norm_2d.angle(dir_vec) <= horiz_angle:
                            sel_geo.append(f)
        
            # translate the Face3D back to Blender Ladybug geometry
            sel_geo = [from_face3d(f) for f in sel_geo]
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvFilterNormal)

def unregister():
    bpy.utils.unregister_class(SvFilterNormal)
