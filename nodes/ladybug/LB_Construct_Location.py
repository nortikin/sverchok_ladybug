import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvConstrLoc(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvConstrLoc'
    bl_label = 'LB Construct Location'
    sv_icon = 'LB_CONSTRLOC'
    sv__name_: StringProperty(
        name='_name_',
        update=updateNode,
        description='A name for the location you are constructing. For example, "Steventon Island, Antarctica". (Default: "-")')
    sv__latitude_: StringProperty(
        name='_latitude_',
        update=updateNode,
        description='Location latitude between -90 and 90 (Default: 0).')
    sv__longitude_: StringProperty(
        name='_longitude_',
        update=updateNode,
        description='Location longitude between -180 (west) and 180 (east) (Default: 0).')
    sv__time_zone_: StringProperty(
        name='_time_zone_',
        update=updateNode,
        description='Time zone between -12 hours (west) and 12 hours (east). If None, the time zone will be an estimated integer value derived from the longitude in accordance with solar time (Default: None).')
    sv__elevation_: StringProperty(
        name='_elevation_',
        update=updateNode,
        description='A number for elevation of the location in meters. (Default: 0).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_name_')
        input_node.prop_name = 'sv__name_'
        input_node.tooltip = 'A name for the location you are constructing. For example, "Steventon Island, Antarctica". (Default: "-")'
        input_node = self.inputs.new('SvLBSocket', '_latitude_')
        input_node.prop_name = 'sv__latitude_'
        input_node.tooltip = 'Location latitude between -90 and 90 (Default: 0).'
        input_node = self.inputs.new('SvLBSocket', '_longitude_')
        input_node.prop_name = 'sv__longitude_'
        input_node.tooltip = 'Location longitude between -180 (west) and 180 (east) (Default: 0).'
        input_node = self.inputs.new('SvLBSocket', '_time_zone_')
        input_node.prop_name = 'sv__time_zone_'
        input_node.tooltip = 'Time zone between -12 hours (west) and 12 hours (east). If None, the time zone will be an estimated integer value derived from the longitude in accordance with solar time (Default: None).'
        input_node = self.inputs.new('SvLBSocket', '_elevation_')
        input_node.prop_name = 'sv__elevation_'
        input_node.tooltip = 'A number for elevation of the location in meters. (Default: 0).'
        output_node = self.outputs.new('SvLBSocket', 'location')
        output_node.tooltip = 'Location data (use this output to construct the sun path).'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Construct location from latitude, lognitude, and time zone data. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['location']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_name_', '_latitude_', '_longitude_', '_time_zone_', '_elevation_']
        self.sv_input_types = ['string', 'double', 'double', 'double', 'double']
        self.sv_input_defaults = [None, None, None, None, 0]
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

    def process_ladybug(self, _name_, _latitude_, _longitude_, _time_zone_, _elevation_):

        try:
            from ladybug.location import Location
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        try:
            from ladybug_tools.sverchok import turn_off_old_tag
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        turn_off_old_tag(ghenv.Component)
        
        
        location = Location(_name_, '-', '-', _latitude_, _longitude_, _time_zone_, _elevation_)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvConstrLoc)

def unregister():
    bpy.utils.unregister_class(SvConstrLoc)
