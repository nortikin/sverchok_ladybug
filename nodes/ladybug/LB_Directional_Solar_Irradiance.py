import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvDirSolar(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvDirSolar'
    bl_label = 'LB Directional Solar Irradiance'
    sv_icon = 'LB_DIRSOLAR'
    sv__location: StringProperty(
        name='_location',
        update=updateNode,
        description='A Ladybug Location object, used to determine the altitude and azimuth of the sun at each hour.')
    sv__direct_norm: StringProperty(
        name='_direct_norm',
        update=updateNode,
        description='Hourly Data Collection with the direct normal solar irradiance in W/m2 or Illuminance in lux.')
    sv__diffuse_horiz: StringProperty(
        name='_diffuse_horiz',
        update=updateNode,
        description='Hourly Data Collection with diffuse horizontal solar irradiance in W/m2 or Illuminance in lux.')
    sv__srf_azimuth_: StringProperty(
        name='_srf_azimuth_',
        update=updateNode,
        description='A number between 0 and 360 that represents the azimuth at which irradiance is being evaluated in degrees.  0 = North, 90 = East, 180 = South, and 270 = West.  (Default: 180).')
    sv__srf_altitude_: StringProperty(
        name='_srf_altitude_',
        update=updateNode,
        description='A number between -90 and 90 that represents the altitude at which irradiance is being evaluated in degrees. A value of 0 means the surface is facing the horizon and a value of 90 means a surface is facing straight up. (Default: 0).')
    sv__ground_ref_: StringProperty(
        name='_ground_ref_',
        update=updateNode,
        description='A number between 0 and 1 that represents the reflectance of the ground. (Default: 0.2). Some common ground reflectances are: *   urban: 0.18 *   grass: 0.20 *   fresh grass: 0.26 *   soil: 0.17 *   sand: 0.40 *   snow: 0.65 *   fresh_snow: 0.75 *   asphalt: 0.12 *   concrete: 0.30 *   sea: 0.06')
    sv_anisotrophic_: StringProperty(
        name='anisotrophic_',
        update=updateNode,
        description='A boolean value that sets whether an anisotropic sky is used (as opposed to an isotropic sky). An isotrophic sky assumes an even distribution of diffuse irradiance across the sky while an anisotropic sky places more diffuse irradiance near the solar disc. (Default: False).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_location')
        input_node.prop_name = 'sv__location'
        input_node.tooltip = 'A Ladybug Location object, used to determine the altitude and azimuth of the sun at each hour.'
        input_node = self.inputs.new('SvLBSocket', '_direct_norm')
        input_node.prop_name = 'sv__direct_norm'
        input_node.tooltip = 'Hourly Data Collection with the direct normal solar irradiance in W/m2 or Illuminance in lux.'
        input_node = self.inputs.new('SvLBSocket', '_diffuse_horiz')
        input_node.prop_name = 'sv__diffuse_horiz'
        input_node.tooltip = 'Hourly Data Collection with diffuse horizontal solar irradiance in W/m2 or Illuminance in lux.'
        input_node = self.inputs.new('SvLBSocket', '_srf_azimuth_')
        input_node.prop_name = 'sv__srf_azimuth_'
        input_node.tooltip = 'A number between 0 and 360 that represents the azimuth at which irradiance is being evaluated in degrees.  0 = North, 90 = East, 180 = South, and 270 = West.  (Default: 180).'
        input_node = self.inputs.new('SvLBSocket', '_srf_altitude_')
        input_node.prop_name = 'sv__srf_altitude_'
        input_node.tooltip = 'A number between -90 and 90 that represents the altitude at which irradiance is being evaluated in degrees. A value of 0 means the surface is facing the horizon and a value of 90 means a surface is facing straight up. (Default: 0).'
        input_node = self.inputs.new('SvLBSocket', '_ground_ref_')
        input_node.prop_name = 'sv__ground_ref_'
        input_node.tooltip = 'A number between 0 and 1 that represents the reflectance of the ground. (Default: 0.2). Some common ground reflectances are: *   urban: 0.18 *   grass: 0.20 *   fresh grass: 0.26 *   soil: 0.17 *   sand: 0.40 *   snow: 0.65 *   fresh_snow: 0.75 *   asphalt: 0.12 *   concrete: 0.30 *   sea: 0.06'
        input_node = self.inputs.new('SvLBSocket', 'anisotrophic_')
        input_node.prop_name = 'sv_anisotrophic_'
        input_node.tooltip = 'A boolean value that sets whether an anisotropic sky is used (as opposed to an isotropic sky). An isotrophic sky assumes an even distribution of diffuse irradiance across the sky while an anisotropic sky places more diffuse irradiance near the solar disc. (Default: False).'
        output_node = self.outputs.new('SvLBSocket', 'total')
        output_node.tooltip = 'A data collection of total solar irradiance or illuminance in the direction of the _srf_azimuth_ and _srf_altitude_.'
        output_node = self.outputs.new('SvLBSocket', 'direct')
        output_node.tooltip = 'A data collection of direct solar irradiance or illuminance in the direction of the _srf_azimuth_ and _srf_altitude_.'
        output_node = self.outputs.new('SvLBSocket', 'diff')
        output_node.tooltip = 'A data collection of diffuse sky solar irradiance or illuminance in the direction of the _srf_azimuth_ and _srf_altitude_.'
        output_node = self.outputs.new('SvLBSocket', 'reflect')
        output_node.tooltip = 'A data collection of ground reflected solar irradiance or illuminance in the direction of the _srf_azimuth_ and _srf_altitude_.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Compute the hourly solar irradiance or illuminance falling on an unobstructed surface that faces any direction. _ The calculation method of this component is faster than running "LB Incident Radiation" studies on an hour-by-hour basis and it is slighty more realistic since it accounts for ground reflection. However, this comes at the cost of not being able to account for any obstructions that block the sun. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['total', 'direct', 'diff', 'reflect']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_location', '_direct_norm', '_diffuse_horiz', '_srf_azimuth_', '_srf_altitude_', '_ground_ref_', 'anisotrophic_']
        self.sv_input_types = ['System.Object', 'System.Object', 'System.Object', 'double', 'double', 'double', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _location, _direct_norm, _diffuse_horiz, _srf_azimuth_, _srf_altitude_, _ground_ref_, anisotrophic_):

        
        try:
            from ladybug.wea import Wea
            from ladybug.datacollection import HourlyContinuousCollection
            from ladybug.header import Header
            from ladybug.datatype.illuminance import Illuminance
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        def rad_to_ill(data):
            """Change the data type of an input collection from irradiane to illuminance."""
            head = data.header
            new_header = Header(Illuminance(), 'lux', head.analysis_period, head.metadata)
            return HourlyContinuousCollection(new_header, data.values) if \
                isinstance(data, HourlyContinuousCollection) else \
                data.__class__(new_header, data.values, data.datetimes)
        
        
        if all_required_inputs(ghenv.Component):
            # set default values
            az = _srf_azimuth_ if _srf_azimuth_ is not None else 180
            alt = _srf_altitude_ if _srf_altitude_ is not None else 0
            gref = _ground_ref_ if _ground_ref_ is not None else 0.2
            isot = not anisotrophic_
        
            # create the Wea and output irradaince
            wea = Wea(_location, _direct_norm, _diffuse_horiz)
            total, direct, diff, reflect = \
                wea.directional_irradiance(alt, az, gref, isot)
            for dat in (total, direct, diff, reflect):
                dat.header.metadata['altitude'] = alt
                dat.header.metadata['azimuth'] = az
        
            # convert to illuminace if input data was illuiminance
            if isinstance(_direct_norm.header.data_type, Illuminance):
                total = rad_to_ill(total)
                direct = rad_to_ill(direct)
                diff = rad_to_ill(diff)
                reflect = rad_to_ill(reflect)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvDirSolar)

def unregister():
    bpy.utils.unregister_class(SvDirSolar)
