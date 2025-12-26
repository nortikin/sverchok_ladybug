import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvUTCI(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvUTCI'
    bl_label = 'LB UTCI Comfort'
    sv_icon = 'LB_UTCI'
    sv__air_temp: StringProperty(
        name='_air_temp',
        update=updateNode,
        description='Data Collection or individual value for air temperature in C.')
    sv__mrt_: StringProperty(
        name='_mrt_',
        update=updateNode,
        description='Data Collection or individual value for mean radiant temperature (MRT) in C. Default is the same as the air_temp.')
    sv__rel_humid: StringProperty(
        name='_rel_humid',
        update=updateNode,
        description='Data Collection or individual value for relative humidity in %. Note that percent values are between 0 and 100.')
    sv__wind_vel_: StringProperty(
        name='_wind_vel_',
        update=updateNode,
        description='Data Collection or individual value for meteoroligical wind velocity at 10 m above ground level in m/s. Note that this meteorological velocity at 10 m is simply 1.5 times the speed felt at ground level in the original Fiala model used to create the UTCI model. Therefore, multiplying air speed values at the height of the human subject by 1.5 will make them a suitable input for this component. Default is a low speed of 0.5 m/s, which is the lowest input speed that is recommended for the UTCI model.')
    sv_utci_par_: StringProperty(
        name='utci_par_',
        update=updateNode,
        description='Optional comfort parameters from the "LB UTCI Comfort Parameters" component to specify the temperatures (in Celcius) that are considered acceptable/comfortable. The default will assume a that the comfort range is between 9C and 26C.')
    sv__run: StringProperty(
        name='_run',
        update=updateNode,
        description='Set to True to run the component.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_air_temp')
        input_node.prop_name = 'sv__air_temp'
        input_node.tooltip = 'Data Collection or individual value for air temperature in C.'
        input_node = self.inputs.new('SvLBSocket', '_mrt_')
        input_node.prop_name = 'sv__mrt_'
        input_node.tooltip = 'Data Collection or individual value for mean radiant temperature (MRT) in C. Default is the same as the air_temp.'
        input_node = self.inputs.new('SvLBSocket', '_rel_humid')
        input_node.prop_name = 'sv__rel_humid'
        input_node.tooltip = 'Data Collection or individual value for relative humidity in %. Note that percent values are between 0 and 100.'
        input_node = self.inputs.new('SvLBSocket', '_wind_vel_')
        input_node.prop_name = 'sv__wind_vel_'
        input_node.tooltip = 'Data Collection or individual value for meteoroligical wind velocity at 10 m above ground level in m/s. Note that this meteorological velocity at 10 m is simply 1.5 times the speed felt at ground level in the original Fiala model used to create the UTCI model. Therefore, multiplying air speed values at the height of the human subject by 1.5 will make them a suitable input for this component. Default is a low speed of 0.5 m/s, which is the lowest input speed that is recommended for the UTCI model.'
        input_node = self.inputs.new('SvLBSocket', 'utci_par_')
        input_node.prop_name = 'sv_utci_par_'
        input_node.tooltip = 'Optional comfort parameters from the "LB UTCI Comfort Parameters" component to specify the temperatures (in Celcius) that are considered acceptable/comfortable. The default will assume a that the comfort range is between 9C and 26C.'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to True to run the component.'
        output_node = self.outputs.new('SvLBSocket', 'utci')
        output_node.tooltip = 'Universal Thermal Climate Index (UTCI) in Celcius.'
        output_node = self.outputs.new('SvLBSocket', 'comfort')
        output_node.tooltip = 'Integers noting whether the input conditions result in no thermal stress. . Values are one of the following: * 0 = thermal stress * 1 = no thremal stress'
        output_node = self.outputs.new('SvLBSocket', 'condition')
        output_node.tooltip = 'Integers noting the thermal status of a subject. . Values are one of the following: * -1 = cold *  0 = netural * +1 = hot'
        output_node = self.outputs.new('SvLBSocket', 'category')
        output_node.tooltip = 'Integers noting the category that the UTCI conditions fall under on an 11-point scale. . Values are one of the following: * -5 = Extreme Cold Stress       (UTCI < -40) * -4 = Very Strong Cold Stress   (-40 <= UTCI < -27) * -3 = Strong Cold Stress        (-27 <= UTCI < -13) * -2 = Moderate Cold Stress      (-12 <= UTCI < 0) * -1 = Slight Cold Stress        (0 <= UTCI < 9) *  0 = No Thermal Stress         (9 <= UTCI < 26) * +1 = Slight Heat Stress        (26 <= UTCI < 28) * +2 = Moderate Heat Stress      (28 <= UTCI < 32) * +3 = Strong Heat Stress        (32 <= UTCI < 38) * +4 = Very Strong Heat Stress   (38 <= UTCI < 46) * +5 = Extreme Heat Stress       (46 < UTCI)'
        output_node = self.outputs.new('SvLBSocket', 'comf_obj')
        output_node.tooltip = 'A Python object containing all inputs and results of the analysis.  This can be plugged into components like the "Comfort Statistics" component to get further information.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate Universal Thermal Climate Index (UTCI). - UTCI is a thermal comfort model strictly for the outdoors. It is an international standard for outdoor temperature sensation (aka. "feels-like" temperature) and is one of the most common of such "feels-like" temperatures used by meteorologists. UTCI that attempts to satisfy the following requirements: _ 1) Thermo-physiological significance in the whole range of heat exchange conditions. 2) Valid in all climates, seasons, and scales. 3) Useful for key applications in human biometeorology. _ While UTCI is designed to be valid in all climates and seasons, it assumes that human subjects are walking (with a metabolic rate around 2.4 met) and that they naturally adapt their clothing with the outdoor temperature. For outdoor situations that do not fit these criteria, the Physiological Equivalent Temperature (PET) model is recommended. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['utci', 'comfort', 'condition', 'category', 'comf_obj']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_air_temp', '_mrt_', '_rel_humid', '_wind_vel_', 'utci_par_', '_run']
        self.sv_input_types = ['System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _air_temp, _mrt_, _rel_humid, _wind_vel_, utci_par_, _run):

        try:
            from ladybug.datatype.temperature import Temperature
            from ladybug.datacollection import BaseCollection
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_comfort.collection.utci import UTCI
            from ladybug_comfort.parameter.utci import UTCIParameter
            from ladybug_comfort.utci import universal_thermal_climate_index
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_comfort:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        def extract_collections(input_list):
            """Process inputs into collections and floats."""
            defaults = [None, _air_temp, 0.5, None]
            data_colls = []
            for i, input in enumerate(input_list):
                if input is None:
                    input_list[i] = defaults[i]
                elif isinstance(input, BaseCollection):
                    data_colls.append(input)
                else:
                    try:
                        input_list[i] = float(input)
                    except ValueError as e:
                        raise TypeError('input {} is not valid. Expected float or '
                                        'DataCollection. Got {}'.format(input, type(input)))
            return input_list, data_colls
        
        if all_required_inputs(ghenv.Component) and _run is True:
            # Process inputs and assign defaults.
            input_list = [_air_temp, _mrt_, _wind_vel_, _rel_humid]
            input, data_colls = extract_collections(input_list)
            utci_par = utci_par_ or UTCIParameter()
        
            if data_colls == []:
                # The inputs are all individual values.
                utci = universal_thermal_climate_index(
                    input[0], float(input[1]), input[2], input[3])
                utci_par = UTCIParameter()
                comfort = utci_par.is_comfortable(utci)
                condition = utci_par.thermal_condition(utci)
                category = utci_par.thermal_condition_eleven_point(utci)
            else:
                # The inputs include Data Collections.
                if not isinstance(_air_temp, BaseCollection):
                    _air_temp = data_colls[0].get_aligned_collection(
                        float(_air_temp), Temperature(), 'C')
        
                comf_obj = UTCI(_air_temp, _rel_humid, _mrt_, _wind_vel_, utci_par)
                utci = comf_obj.universal_thermal_climate_index
                comfort = comf_obj.is_comfortable
                condition = comf_obj.thermal_condition
                category = comf_obj.thermal_condition_eleven_point

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvUTCI)

def unregister():
    bpy.utils.unregister_class(SvUTCI)
