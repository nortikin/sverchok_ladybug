import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvOrientCam(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvOrientCam'
    bl_label = 'LB Orient to Camera'
    sv_icon = 'LB_ORIENTCAM'
    sv__geo: StringProperty(
        name='_geo',
        update=updateNode,
        description='A series of geometries to be oriented to the camera of the active Rhino viewport.')
    sv__position_: StringProperty(
        name='_position_',
        update=updateNode,
        description='A point to be used as the origin around which the the geometry will be oriented. If None, the lower left corner of the bounding box around the geometry will be used.')
    sv_refresh_: StringProperty(
        name='refresh_',
        update=updateNode,
        description='Connect a Grasshopper "button" component to refresh the orientation upon hitting the button. You can also connect a Grasshopper "Timer" component to update the view in real time as you navigate through the Rhino scene.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_geo')
        input_node.prop_name = 'sv__geo'
        input_node.tooltip = 'A series of geometries to be oriented to the camera of the active Rhino viewport.'
        input_node = self.inputs.new('SvLBSocket', '_position_')
        input_node.prop_name = 'sv__position_'
        input_node.tooltip = 'A point to be used as the origin around which the the geometry will be oriented. If None, the lower left corner of the bounding box around the geometry will be used.'
        input_node = self.inputs.new('SvLBSocket', 'refresh_')
        input_node.prop_name = 'sv_refresh_'
        input_node.tooltip = 'Connect a Grasshopper "button" component to refresh the orientation upon hitting the button. You can also connect a Grasshopper "Timer" component to update the view in real time as you navigate through the Rhino scene.'
        output_node = self.outputs.new('SvLBSocket', 'geo')
        output_node.tooltip = 'The input geometry that has been oriented to the camera of the active Rhino viewport.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Orient a series of geometries to the active viewport camera. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['geo']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_geo', '_position_', 'refresh_']
        self.sv_input_types = ['System.Object', 'Point3d', 'System.Object']
        self.sv_input_defaults = [None, None, None]
        self.sv_input_access = ['list', 'item', 'item']
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

    def process_ladybug(self, _geo, _position_, refresh_):

        try:
            from ladybug_tools.sverchok import all_required_inputs
            from ladybug_tools.viewport import orient_to_camera
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            geo = orient_to_camera(_geo, _position_)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvOrientCam)

def unregister():
    bpy.utils.unregister_class(SvOrientCam)
