import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvTrueNorth(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvTrueNorth'
    bl_label = 'LB Magnetic to True North'
    sv_icon = 'LB_TRUENORTH'
    sv__location: StringProperty(
        name='_location',
        update=updateNode,
        description='A ladybug Location that has been output from the "LB Import EPW" component or the "LB Construct Location" component. This is used to determine the difference between magnetic and true North.')
    sv__mag_north: StringProperty(
        name='_mag_north',
        update=updateNode,
        description='A number between -360 and 360 for the counterclockwise difference between Magnetic North and the positive Y-axis in degrees. Counterclockwise means "90 is West and 270 is East". This can also be Vector for the magnetic North direction.')
    sv__year_: StringProperty(
        name='_year_',
        update=updateNode,
        description='A number for the year in which the Magnetic North was evaluated. Decimal values are accepted. This is needed as the location of Magnetic North has been moving at a rate of roughly 50 km/year for the past couple of decades. (Default: 2025).')
    sv_cof_file_: StringProperty(
        name='cof_file_',
        update=updateNode,
        description='An optional path to a .COF file containing the coefficients that form the inputs for the World Magnetic Model (WMM). A new set of coefficients is published roughly every 5 years as the magnetic poles continue to move. If unspecified, coefficients will be taken from the most recent model. COF files with the most recent coefficients and historical values are available at:')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_location')
        input_node.prop_name = 'sv__location'
        input_node.tooltip = 'A ladybug Location that has been output from the "LB Import EPW" component or the "LB Construct Location" component. This is used to determine the difference between magnetic and true North.'
        input_node = self.inputs.new('SvLBSocket', '_mag_north')
        input_node.prop_name = 'sv__mag_north'
        input_node.tooltip = 'A number between -360 and 360 for the counterclockwise difference between Magnetic North and the positive Y-axis in degrees. Counterclockwise means "90 is West and 270 is East". This can also be Vector for the magnetic North direction.'
        input_node = self.inputs.new('SvLBSocket', '_year_')
        input_node.prop_name = 'sv__year_'
        input_node.tooltip = 'A number for the year in which the Magnetic North was evaluated. Decimal values are accepted. This is needed as the location of Magnetic North has been moving at a rate of roughly 50 km/year for the past couple of decades. (Default: 2025).'
        input_node = self.inputs.new('SvLBSocket', 'cof_file_')
        input_node.prop_name = 'sv_cof_file_'
        input_node.tooltip = 'An optional path to a .COF file containing the coefficients that form the inputs for the World Magnetic Model (WMM). A new set of coefficients is published roughly every 5 years as the magnetic poles continue to move. If unspecified, coefficients will be taken from the most recent model. COF files with the most recent coefficients and historical values are available at:'
        output_node = self.outputs.new('SvLBSocket', 'mag_declination')
        output_node.tooltip = 'The magnetic declination in degrees. Magnetic declination is the difference between magnetic North and true North at a given location on the globe (expressed in terms of degrees).'
        output_node = self.outputs.new('SvLBSocket', 'true_north')
        output_node.tooltip = 'A number between -360 and 360 for the True North angle in degrees.'
        output_node = self.outputs.new('SvLBSocket', 'true_north_vec')
        output_node.tooltip = 'A vector for the True North direction. This can be plugged into any of the north_ inputs of the other LAdybug Tools components.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Compute a True North angle and vector from Magnetic North at a given location. _ This component uses then World Magnetic Model (WMM) developed and maintained by NOAA. https://www.ncei.noaa.gov/products/world-magnetic-model -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['mag_declination', 'true_north', 'true_north_vec']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_location', '_mag_north', '_year_', 'cof_file_']
        self.sv_input_types = ['System.Object', 'System.Object', 'double', 'string']
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

    def process_ladybug(self, _location, _mag_north, _year_, cof_file_):

        import math
        
        try:
            from ladybug_geometry.geometry2d.pointvector import Vector2D
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug.north import WorldMagneticModel
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.togeometry import to_vector2d
            from ladybug_tools.fromgeometry import from_vector2d
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # process the _magn_north and the year
            try:
                _mag_north = math.degrees(to_vector2d(_mag_north).angle_clockwise(Vector2D(0, 1)))
            except AttributeError:  # north angle instead of vector
                _mag_north = float(_mag_north)
            _year_ = _year_ if _year_ is not None else 2025
        
            # initialize the WorldMagneticModel and convert the north angle
            wmm_obj = WorldMagneticModel(cof_file_)
            true_north = wmm_obj.magnetic_to_true_north(_location, _mag_north, _year_)
            mag_declination = true_north - _mag_north
        
            # convert the true north angle to a vector
            st_north = Vector2D(0, 1).rotate(math.radians(_mag_north))
            true_north_vec = st_north.rotate(math.radians(true_north))
            true_north_vec = from_vector2d(true_north_vec)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvTrueNorth)

def unregister():
    bpy.utils.unregister_class(SvTrueNorth)
