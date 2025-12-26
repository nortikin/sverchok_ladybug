import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvIndoorSolarMRT(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvIndoorSolarMRT'
    bl_label = 'LB Indoor Solar MRT'
    sv_icon = 'LB_INDOORSOLARMRT'
    sv__location: StringProperty(
        name='_location',
        update=updateNode,
        description='A Ladybug Location object, used to determine the altitude and azimuth of the sun.')
    sv__longwave_mrt: StringProperty(
        name='_longwave_mrt',
        update=updateNode,
        description='A single number or an hourly data collection with the long-wave mean radiant temperature around the person in degrees C. This includes the temperature of the ground and any other surfaces between the person and their view to the sky. Typically, indoor air temperature is used when such surface temperatures are unknown.')
    sv__dir_norm_rad: StringProperty(
        name='_dir_norm_rad',
        update=updateNode,
        description='Hourly Data Collection with the direct normal solar irradiance in W/m2.')
    sv__diff_horiz_rad: StringProperty(
        name='_diff_horiz_rad',
        update=updateNode,
        description='Hourly Data Collection with diffuse horizontal solar irradiance in W/m2.')
    sv_fract_body_exp_: StringProperty(
        name='fract_body_exp_',
        update=updateNode,
        description='A single number between 0 and 1 or a data collection for the fraction of the body exposed to direct sunlight. The "LB Human to Sky Relationship" component can be used to estimate this input for a given set of context geometry and position of the human. Note that this parameter does NOT include the body’s self-shading. It only includes the shading from furniture and surroundings. (Default: 1 for an area surrounded by glass).')
    sv_sky_exposure_: StringProperty(
        name='sky_exposure_',
        update=updateNode,
        description='A single number between 0 and 1 or a data collection representing the fraction of the sky vault in the human subject’s view. The "LB Human to Sky Relationship" component can be used to estimate this input for a given set of context geometry and position of the human. (Default: 0.5 for a person next to an all glass facade).')
    sv__ground_ref_: StringProperty(
        name='_ground_ref_',
        update=updateNode,
        description='A single number between 0 and 1 or a data collection that represents the reflectance of the floor. Default is for 0.25 which is characteristic of concrete.')
    sv__window_trans_: StringProperty(
        name='_window_trans_',
        update=updateNode,
        description='A Data Collection or number between 0 and 1 that represents the broadband solar transmittance of the window through which the sun is coming. Such values tend to be slightly less than the SHGC. Values might be as low as 0.2 and could be as high as 0.85 for a single pane of glass. Default is 0.4 assuming a double pane window with a relatively mild low-e coating.')
    sv__solar_body_par_: StringProperty(
        name='_solar_body_par_',
        update=updateNode,
        description='Optional solar body parameters from the "LB Solar Body Parameters" object to specify the properties of the human geometry assumed in the shortwave MRT calculation. The default assumes average skin/clothing absorptivity and a human subject always has their back to the sun at a 45-degree angle (SHARP = 135).')
    sv__run: StringProperty(
        name='_run',
        update=updateNode,
        description='Set to True to run the component.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_location')
        input_node.prop_name = 'sv__location'
        input_node.tooltip = 'A Ladybug Location object, used to determine the altitude and azimuth of the sun.'
        input_node = self.inputs.new('SvLBSocket', '_longwave_mrt')
        input_node.prop_name = 'sv__longwave_mrt'
        input_node.tooltip = 'A single number or an hourly data collection with the long-wave mean radiant temperature around the person in degrees C. This includes the temperature of the ground and any other surfaces between the person and their view to the sky. Typically, indoor air temperature is used when such surface temperatures are unknown.'
        input_node = self.inputs.new('SvLBSocket', '_dir_norm_rad')
        input_node.prop_name = 'sv__dir_norm_rad'
        input_node.tooltip = 'Hourly Data Collection with the direct normal solar irradiance in W/m2.'
        input_node = self.inputs.new('SvLBSocket', '_diff_horiz_rad')
        input_node.prop_name = 'sv__diff_horiz_rad'
        input_node.tooltip = 'Hourly Data Collection with diffuse horizontal solar irradiance in W/m2.'
        input_node = self.inputs.new('SvLBSocket', 'fract_body_exp_')
        input_node.prop_name = 'sv_fract_body_exp_'
        input_node.tooltip = 'A single number between 0 and 1 or a data collection for the fraction of the body exposed to direct sunlight. The "LB Human to Sky Relationship" component can be used to estimate this input for a given set of context geometry and position of the human. Note that this parameter does NOT include the body’s self-shading. It only includes the shading from furniture and surroundings. (Default: 1 for an area surrounded by glass).'
        input_node = self.inputs.new('SvLBSocket', 'sky_exposure_')
        input_node.prop_name = 'sv_sky_exposure_'
        input_node.tooltip = 'A single number between 0 and 1 or a data collection representing the fraction of the sky vault in the human subject’s view. The "LB Human to Sky Relationship" component can be used to estimate this input for a given set of context geometry and position of the human. (Default: 0.5 for a person next to an all glass facade).'
        input_node = self.inputs.new('SvLBSocket', '_ground_ref_')
        input_node.prop_name = 'sv__ground_ref_'
        input_node.tooltip = 'A single number between 0 and 1 or a data collection that represents the reflectance of the floor. Default is for 0.25 which is characteristic of concrete.'
        input_node = self.inputs.new('SvLBSocket', '_window_trans_')
        input_node.prop_name = 'sv__window_trans_'
        input_node.tooltip = 'A Data Collection or number between 0 and 1 that represents the broadband solar transmittance of the window through which the sun is coming. Such values tend to be slightly less than the SHGC. Values might be as low as 0.2 and could be as high as 0.85 for a single pane of glass. Default is 0.4 assuming a double pane window with a relatively mild low-e coating.'
        input_node = self.inputs.new('SvLBSocket', '_solar_body_par_')
        input_node.prop_name = 'sv__solar_body_par_'
        input_node.tooltip = 'Optional solar body parameters from the "LB Solar Body Parameters" object to specify the properties of the human geometry assumed in the shortwave MRT calculation. The default assumes average skin/clothing absorptivity and a human subject always has their back to the sun at a 45-degree angle (SHARP = 135).'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to True to run the component.'
        output_node = self.outputs.new('SvLBSocket', 'erf')
        output_node.tooltip = 'Data collection of effective radiant field (ERF) in W/m2.'
        output_node = self.outputs.new('SvLBSocket', 'dmrt')
        output_node.tooltip = 'Data collection of mean radiant temperature delta in C.'
        output_node = self.outputs.new('SvLBSocket', 'mrt')
        output_node.tooltip = 'Data collection of mean radiant temperature in C.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate Mean Radiant Temperature (MRT) as a result of outdoor shortwave solar shining directly onto people as well as longwave radiant exchange with the sky. - This component uses the SolarCal model of ASHRAE-55 to estimate the effects of shortwave solar and a simple sky exposure method to determine longwave radiant exchange. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['erf', 'dmrt', 'mrt']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_location', '_longwave_mrt', '_dir_norm_rad', '_diff_horiz_rad', 'fract_body_exp_', 'sky_exposure_', '_ground_ref_', '_window_trans_', '_solar_body_par_', '_run']
        self.sv_input_types = ['System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _location, _longwave_mrt, _dir_norm_rad, _diff_horiz_rad, fract_body_exp_, sky_exposure_, _ground_ref_, _window_trans_, _solar_body_par_, _run):

        try:
            from ladybug_comfort.collection.solarcal import IndoorSolarCal
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component) and _run is True:
            sky_exposure_ = 0.5 if sky_exposure_ is None else sky_exposure_
            solar_mrt_obj = IndoorSolarCal(_location, _dir_norm_rad,
                                           _diff_horiz_rad, _longwave_mrt,
                                           fract_body_exp_, sky_exposure_,
                                           _ground_ref_, _window_trans_, _solar_body_par_)
        
            erf = solar_mrt_obj.effective_radiant_field
            dmrt = solar_mrt_obj.mrt_delta
            mrt = solar_mrt_obj.mean_radiant_temperature

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvIndoorSolarMRT)

def unregister():
    bpy.utils.unregister_class(SvIndoorSolarMRT)
