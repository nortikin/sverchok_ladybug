import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvCompass(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvCompass'
    bl_label = 'LB Compass'
    sv_icon = 'LB_COMPASS'
    sv__north_: StringProperty(
        name='_north_',
        update=updateNode,
        description='A number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. Counterclockwise means "90 is West and 270 is East". This can also be Vector for the direction to North. (Default: 0)')
    sv__center_: StringProperty(
        name='_center_',
        update=updateNode,
        description='A point for the center position of the compass in the Rhino scene. (Default: (0, 0, 0) aka. the Rhino scene origin).')
    sv__scale_: StringProperty(
        name='_scale_',
        update=updateNode,
        description='A number to set the scale of the compass. The default is 1, which corresponds to a radius of 10 meters in the current Rhino model\'s unit system.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_north_')
        input_node.prop_name = 'sv__north_'
        input_node.tooltip = 'A number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. Counterclockwise means "90 is West and 270 is East". This can also be Vector for the direction to North. (Default: 0)'
        input_node = self.inputs.new('SvLBSocket', '_center_')
        input_node.prop_name = 'sv__center_'
        input_node.tooltip = 'A point for the center position of the compass in the Rhino scene. (Default: (0, 0, 0) aka. the Rhino scene origin).'
        input_node = self.inputs.new('SvLBSocket', '_scale_')
        input_node.prop_name = 'sv__scale_'
        input_node.tooltip = 'A number to set the scale of the compass. The default is 1, which corresponds to a radius of 10 meters in the current Rhino model\'s unit system.'
        output_node = self.outputs.new('SvLBSocket', 'compass')
        output_node.tooltip = 'A set of circles, lines and text objects that mark the cardinal directions in the Rhino scene.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Create a compass sign that indicates the direction of North in the Rhino scene. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['compass']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_north_', '_center_', '_scale_']
        self.sv_input_types = ['System.Object', 'Point3d', 'double']
        self.sv_input_defaults = [None, None, None]
        self.sv_input_access = ['item', 'item', 'item']
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

    def process_ladybug(self, _north_, _center_, _scale_):

        import math
        
        try:
            from ladybug_geometry.geometry2d.pointvector import Vector2D, Point2D
            from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
            from ladybug_geometry.geometry3d.plane import Plane
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug.compass import Compass
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import conversion_to_meters
            from ladybug_tools.togeometry import to_vector2d, to_point2d, to_point3d
            from ladybug_tools.fromgeometry import from_arc2d, from_linesegment2d
            from ladybug_tools.text import text_objects
            from ladybug_tools.sverchok import turn_off_old_tag
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        turn_off_old_tag(ghenv.Component)
        
        
        def translate_compass(compass, z=0, font='Arial'):
            """Translate a Ladybug Compass object into  geometry.
        
            Args:
                compass: A Ladybug Compass object to be converted to Blender Ladybug geometry.
                z: A number for the Z-coordinate to be used in translation. (Default: 0)
                font: Optional text for the font to be used in creating the text.
                    (Default: 'Arial')
        
            Returns:
                A list of Blender Ladybug geometries in the following order.
                -   all_boundary_circles -- Three Circle objects for the compass boundary.
                -   major_azimuth_ticks -- Line objects for the major azimuth labels.
                -   major_azimuth_text -- Bake-able text objects for the major azimuth labels.
             """
            # set default variables based on the compass properties
            maj_txt = compass.radius / 2.5
            xaxis = Vector3D(1, 0, 0).rotate_xy(math.radians(compass.north_angle))
            result = []  # list to hold all of the returned objects
        
            # create the boundary circles
            for circle in compass.all_boundary_circles:
                result.append(from_arc2d(circle, z))
        
            # generate the labels and tick marks for the azimuths
            for line in compass.major_azimuth_ticks:
                result.append(from_linesegment2d(line, z))
            for txt, pt in zip(compass.MAJOR_TEXT, compass.major_azimuth_points):
                result.append(text_objects(
                    txt, Plane(o=Point3D(pt.x, pt.y, z), x=xaxis), maj_txt, font, 1, 3))
            return result
        
        
        # set defaults for all of the
        if _north_ is not None:  # process the _north_
            try:
                _north_ = math.degrees(to_vector2d(_north_).angle_clockwise(Vector2D(0, 1)))
            except AttributeError:  # north angle instead of vector
                _north_ = float(_north_)
        else:
            _north_ = 0
        if _center_ is not None:  # process the center point into a Point2D
            center_pt, z = to_point2d(_center_), to_point3d(_center_).z
        else:
            center_pt, z = Point2D(), 0
        _scale_ = 1 if _scale_ is None else _scale_ # process the scale into a radius
        radius = (10 * _scale_) / conversion_to_meters()
        
        # create the compass
        compass = translate_compass(Compass(radius, center_pt, _north_, 1), z)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvCompass)

def unregister():
    bpy.utils.unregister_class(SvCompass)
