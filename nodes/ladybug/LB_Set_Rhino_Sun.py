import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvRhinoSun(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvRhinoSun'
    bl_label = 'LB Set Rhino Sun'
    sv_icon = 'LB_RHINOSUN'
    sv_north_: StringProperty(
        name='north_',
        update=updateNode,
        description='A number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. 90 is West and 270 is East. This can also be Vector for the direction to North. (Default: 0)')
    sv__location: StringProperty(
        name='_location',
        update=updateNode,
        description='A ladybug Location that has been output from the "LB Import EPW" component or the "LB Construct Location" component.')
    sv__hoy: StringProperty(
        name='_hoy',
        update=updateNode,
        description='Script variable rhinoSun')
    sv__run: StringProperty(
        name='_run',
        update=updateNode,
        description='Set to True to run the component set the Rhino Sun.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', 'north_')
        input_node.prop_name = 'sv_north_'
        input_node.tooltip = 'A number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. 90 is West and 270 is East. This can also be Vector for the direction to North. (Default: 0)'
        input_node = self.inputs.new('SvLBSocket', '_location')
        input_node.prop_name = 'sv__location'
        input_node.tooltip = 'A ladybug Location that has been output from the "LB Import EPW" component or the "LB Construct Location" component.'
        input_node = self.inputs.new('SvLBSocket', '_hoy')
        input_node.prop_name = 'sv__hoy'
        input_node.tooltip = 'Script variable rhinoSun'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to True to run the component set the Rhino Sun.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Set the sun in the Rhino scene to correspond to a given location and date/time. _ This can be help coordinate Rhino visualizations with Ladybug analyses. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = []
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['north_', '_location', '_hoy', '_run']
        self.sv_input_types = ['System.Object', 'System.Object', 'double', 'bool']
        self.sv_input_defaults = [None, None, None, None]
        self.sv_input_access = ['item', 'item', 'list', 'item']
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

    def process_ladybug(self, north_, _location, _hoy, _run):

        import math
        
        try:
            from ladybug_geometry.geometry2d.pointvector import Vector2D
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.togeometry import to_vector2d
            from ladybug_tools.light import set_sun, disable_sun, set_suns
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component) and _run:
            disable_sun()
            if north_ is not None:  # process the north_
                try:
                    north_ = math.degrees(
                        to_vector2d(north_).angle_clockwise(Vector2D(0, 1)))
                except AttributeError:  # north angle instead of vector
                    north_ = float(north_)
            else:
                north_ = 0
            if len(_hoy) == 1:
                set_sun(_location, _hoy[0], north_)
            else:
                set_suns(_location, _hoy, north_)
        else:
            disable_sun()
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvRhinoSun)

def unregister():
    bpy.utils.unregister_class(SvRhinoSun)
