import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvViewFromSun(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvViewFromSun'
    bl_label = 'LB View From Sun'
    sv_icon = 'LB_VIEWFROMSUN'
    sv__vector: StringProperty(
        name='_vector',
        update=updateNode,
        description='A sun vector from which the the Rhino view will be generated. Use the "LB SunPath" component to generate sun vectors.')
    sv__center_pt_: StringProperty(
        name='_center_pt_',
        update=updateNode,
        description='The target point of the camera for the Rhino view that will be generated.  This point should be close to the Rhino geometry that you are interested in viewing from the sun. If no point is provided, the Rhino origin will be used (0, 0, 0).')
    sv_width_: StringProperty(
        name='width_',
        update=updateNode,
        description='An optional interger for the width (in pixels) of the Rhino viewport that will be generated.')
    sv_height_: StringProperty(
        name='height_',
        update=updateNode,
        description='An optional interger for the height (in pixels) of the Rhino viewport that will be generated.')
    sv_mode_: StringProperty(
        name='mode_',
        update=updateNode,
        description='An optional text input for the display mode of the Rhino viewport that will be generated. For example: Wireframe, Shaded, Rendered, etc.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_vector')
        input_node.prop_name = 'sv__vector'
        input_node.tooltip = 'A sun vector from which the the Rhino view will be generated. Use the "LB SunPath" component to generate sun vectors.'
        input_node = self.inputs.new('SvLBSocket', '_center_pt_')
        input_node.prop_name = 'sv__center_pt_'
        input_node.tooltip = 'The target point of the camera for the Rhino view that will be generated.  This point should be close to the Rhino geometry that you are interested in viewing from the sun. If no point is provided, the Rhino origin will be used (0, 0, 0).'
        input_node = self.inputs.new('SvLBSocket', 'width_')
        input_node.prop_name = 'sv_width_'
        input_node.tooltip = 'An optional interger for the width (in pixels) of the Rhino viewport that will be generated.'
        input_node = self.inputs.new('SvLBSocket', 'height_')
        input_node.prop_name = 'sv_height_'
        input_node.tooltip = 'An optional interger for the height (in pixels) of the Rhino viewport that will be generated.'
        input_node = self.inputs.new('SvLBSocket', 'mode_')
        input_node.prop_name = 'sv_mode_'
        input_node.tooltip = 'An optional text input for the display mode of the Rhino viewport that will be generated. For example: Wireframe, Shaded, Rendered, etc.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Open a new viewport in Rhino that shows the parallel-projected view from the sun. _ This is useful for understanding what parts of Rhino geometry are shaded at a particular hour of the day. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = []
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_vector', '_center_pt_', 'width_', 'height_', 'mode_']
        self.sv_input_types = ['Vector3d', 'Point3d', 'int', 'int', 'string']
        self.sv_input_defaults = [None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _vector, _center_pt_, width_, height_, mode_):

        try:
            from ladybug_tools.viewport import viewport_by_name, open_viewport, \
                set_iso_view_direction, set_view_display_mode
            from ladybug_tools.sverchok import all_required_inputs, component_guid, \
                get_sticky_variable, set_sticky_variable
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # get the name of the view and the previous width/height
            view_name = 'ViewFromSun_{}'.format(component_guid(ghenv.Component))
            print(view_name)  # print so that the user has the name if needed
            vw = get_sticky_variable('sun_view_width')
            vh = get_sticky_variable('sun_view_height')
        
            # get the viewport from which the direction will be set
            view_port = None
            if width_ == vw and height_ == vh:  # no need to generate new view; get existing one
                try:
                    view_port = viewport_by_name(view_name)
                except ValueError:  # the viewport does not yet exist
                    pass
            if view_port is None:
                view_port = open_viewport(view_name, width_, height_)
            set_sticky_variable('sun_view_width', width_)
            set_sticky_variable('sun_view_height', height_)
        
            # set the direction of the viewport camera
            set_iso_view_direction(view_port, _vector, _center_pt_)
        
            # set the display mode if requested
            if mode_:
                set_view_display_mode(view_port, mode_)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvViewFromSun)

def unregister():
    bpy.utils.unregister_class(SvViewFromSun)
