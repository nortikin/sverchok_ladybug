import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvPET(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvPET'
    bl_label = 'LB PET Comfort'
    sv_icon = 'LB_PET'
    sv__air_temp: StringProperty(
        name='_air_temp',
        update=updateNode,
        description='Data Collection or individual value for air temperature in C.')
    sv__mrt_: StringProperty(
        name='_mrt_',
        update=updateNode,
        description='Data Collection or individual value of mean radiant temperature (MRT) in C. Default is the same as the air_temp.')
    sv__rel_humid: StringProperty(
        name='_rel_humid',
        update=updateNode,
        description='Data Collection or individual value for relative humidity in %. Note that percent values are between 0 and 100.')
    sv__air_speed_: StringProperty(
        name='_air_speed_',
        update=updateNode,
        description='Data Collection or individual value for air speed in m/s. Default is a very low speed of 0.1 m/s, which is typical of the room air speeds induced by HVAC systems.')
    sv__pressure_: StringProperty(
        name='_pressure_',
        update=updateNode,
        description='A value or data collection representing atmospheric pressure [Pa] Default is to use air pressure at sea level (101,325 Pa).')
    sv__met_rate_: StringProperty(
        name='_met_rate_',
        update=updateNode,
        description='Data Collection or individual value of metabolic rate in met. Note that the original PET model requires that the activity of the human subject be accounted for as additional Watts above the basal metabolism, which is often difficult to estimate. In order to accept an input in [met], it is assumed that 1 met refers to Resting Metabolic Rate (RMR) and this is 1.17 times the male Basal Metabolic Rate (BMR) or 1.22 times the female BMR. Default is set to 2.4 met for walking. Typical values include the following. _ * 1 met = Metabolic rate of a resting seated person * 1.2 met = Metabolic rate of a standing person * 2.4 met = Metabolic rate of a person walking at ~1 m/s (2 mph)')
    sv__clothing_: StringProperty(
        name='_clothing_',
        update=updateNode,
        description='Data Collection or individual value of clothing insulation in clo. Default is set to 0.7 clo for long sleeve shirt and pants. Typical values include the following. _ * 1 clo = Three-piece suit * 0.5 clo = Shorts + T-shirt * 0 clo = No clothing')
    sv_pet_par_: StringProperty(
        name='pet_par_',
        update=updateNode,
        description='Optional comfort parameters from the "LB PET Body Parameters" component to specify the body properties of the human subject. This includes the age, height, sex, body mass, and more. The default attempts to model as average of a human body as possible.')
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
        input_node.tooltip = 'Data Collection or individual value of mean radiant temperature (MRT) in C. Default is the same as the air_temp.'
        input_node = self.inputs.new('SvLBSocket', '_rel_humid')
        input_node.prop_name = 'sv__rel_humid'
        input_node.tooltip = 'Data Collection or individual value for relative humidity in %. Note that percent values are between 0 and 100.'
        input_node = self.inputs.new('SvLBSocket', '_air_speed_')
        input_node.prop_name = 'sv__air_speed_'
        input_node.tooltip = 'Data Collection or individual value for air speed in m/s. Default is a very low speed of 0.1 m/s, which is typical of the room air speeds induced by HVAC systems.'
        input_node = self.inputs.new('SvLBSocket', '_pressure_')
        input_node.prop_name = 'sv__pressure_'
        input_node.tooltip = 'A value or data collection representing atmospheric pressure [Pa] Default is to use air pressure at sea level (101,325 Pa).'
        input_node = self.inputs.new('SvLBSocket', '_met_rate_')
        input_node.prop_name = 'sv__met_rate_'
        input_node.tooltip = 'Data Collection or individual value of metabolic rate in met. Note that the original PET model requires that the activity of the human subject be accounted for as additional Watts above the basal metabolism, which is often difficult to estimate. In order to accept an input in [met], it is assumed that 1 met refers to Resting Metabolic Rate (RMR) and this is 1.17 times the male Basal Metabolic Rate (BMR) or 1.22 times the female BMR. Default is set to 2.4 met for walking. Typical values include the following. _ * 1 met = Metabolic rate of a resting seated person * 1.2 met = Metabolic rate of a standing person * 2.4 met = Metabolic rate of a person walking at ~1 m/s (2 mph)'
        input_node = self.inputs.new('SvLBSocket', '_clothing_')
        input_node.prop_name = 'sv__clothing_'
        input_node.tooltip = 'Data Collection or individual value of clothing insulation in clo. Default is set to 0.7 clo for long sleeve shirt and pants. Typical values include the following. _ * 1 clo = Three-piece suit * 0.5 clo = Shorts + T-shirt * 0 clo = No clothing'
        input_node = self.inputs.new('SvLBSocket', 'pet_par_')
        input_node.prop_name = 'sv_pet_par_'
        input_node.tooltip = 'Optional comfort parameters from the "LB PET Body Parameters" component to specify the body properties of the human subject. This includes the age, height, sex, body mass, and more. The default attempts to model as average of a human body as possible.'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to True to run the component.'
        output_node = self.outputs.new('SvLBSocket', 'pet')
        output_node.tooltip = 'Physiological Equivalent Temperature (PET) [C]. PET is a "feels like" temperature value and is defined as the operative temperature of a reference environment that would cause the same physiological response in the human subject as the environment under study. That is, the same skin temperature and core body temperature.'
        output_node = self.outputs.new('SvLBSocket', 'core_temp')
        output_node.tooltip = 'The core body temperature of the human subject [C].'
        output_node = self.outputs.new('SvLBSocket', 'skin_temp')
        output_node.tooltip = 'The skin temperature of the human subject underneath the clothing layer [C].'
        output_node = self.outputs.new('SvLBSocket', 'comfort')
        output_node.tooltip = 'Integers noting whether the input conditions result in no thermal stress (aka. they are comfortable. _ Values are one of the following: * 0 = uncomfortable * 1 = comfortable'
        output_node = self.outputs.new('SvLBSocket', 'condition')
        output_node.tooltip = 'Integers noting the thermal status of a subject. _ Values are one of the following: * -1 = cold *  0 = netural * +1 = hot'
        output_node = self.outputs.new('SvLBSocket', 'category')
        output_node.tooltip = 'Integers noting the thermal status on a nine-point scale. _ Values are one of the following: * -4 = very strong/extreme cold stress * -3 = strong cold stress * -2 = moderate cold stress * -1 = slight cold stress * 0 = no thermal stress * +1 = slight heat stress * +2 = moderate heat stress * +3 = strong heat stress * +4 = very strong/extreme heat stress'
        output_node = self.outputs.new('SvLBSocket', 'core_cond')
        output_node.tooltip = 'Integers noting the classification of core body temperature. _ Values are one of the following: * -2 = Hypothermia * -1 = Cold * 0 = Normal * +1 = Hot * +2 = Hyperthermia'
        output_node = self.outputs.new('SvLBSocket', 'comf_obj')
        output_node.tooltip = 'A Python object containing all inputs and results of the analysis.  This can be plugged into components like the "Comfort Statistics" component to get further information.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate Physiological Equivalent Temperature (PET). _ PET uses the Munich Energy Balance Model (MEMI), which is arguably the most detailed 3-node human energy balance model in common use today. It can account for various physiological features of the human subject, including age, sex, height, and body mass, making it one of the only models that is suitable for forecasting the thermal experience of a specific individual. This also makes it one of the better models for estimating core body temperature and whether a given set of conditions is likely to induce hypothermia or hyperthermia in a specific individual. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['pet', 'core_temp', 'skin_temp', 'comfort', 'condition', 'category', 'core_cond', 'comf_obj']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_air_temp', '_mrt_', '_rel_humid', '_air_speed_', '_pressure_', '_met_rate_', '_clothing_', 'pet_par_', '_run']
        self.sv_input_types = ['System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _air_temp, _mrt_, _rel_humid, _air_speed_, _pressure_, _met_rate_, _clothing_, pet_par_, _run):

        try:
            from ladybug.datatype.temperature import Temperature
            from ladybug.datacollection import BaseCollection
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_comfort.collection.pet import PET
            from ladybug_comfort.parameter.pet import PETParameter
            from ladybug_comfort.pet import physiologic_equivalent_temperature, pet_category, \
                pet_category_humid, core_temperature_category
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_comfort:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        def extract_collections(input_list):
            """Process inputs into collections and floats."""
            defaults = [None, _air_temp, 0.1, None, 2.4, 0.7, 101325]
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
            input_list = [_air_temp, _mrt_, _air_speed_, _rel_humid,
                          _met_rate_, _clothing_, _pressure_]
            input, data_colls = extract_collections(input_list)
            pet_par = pet_par_ or PETParameter()
        
            if data_colls == []:
                # The inputs are all individual values.
                pet_result = physiologic_equivalent_temperature(
                    input[0], float(input[1]), input[2], input[3], input[4], input[5],
                    pet_par.age, pet_par.sex, pet_par.height, pet_par.body_mass,
                    pet_par.posture, input[6])
                pet = pet_result['pet']
                core_temp = pet_result['t_core']
                skin_temp = pet_result['t_skin']
                cat_func = pet_category_humid if pet_par.humid_acclimated else pet_category
                category = cat_func(pet)
                core_cond = core_temperature_category(pet_result['t_core'])
                comfort = category == 0
                condition = 0
                if category < 0:
                    condition = -1
                elif category > 0:
                    condition = 1
            else:
                # The inputs include Data Collections.
                if not isinstance(_air_temp, BaseCollection):
                    _air_temp = data_colls[0].get_aligned_collection(
                        float(_air_temp), Temperature(), 'C')
        
                comf_obj = PET(
                    _air_temp, _rel_humid, _mrt_, _air_speed_, _pressure_,
                    _met_rate_, _clothing_, pet_par)
                pet = comf_obj.physiologic_equivalent_temperature
                core_temp = comf_obj.core_body_temperature
                skin_temp = comf_obj.skin_temperature
                comfort = comf_obj.is_comfortable
                condition = comf_obj.thermal_condition
                category = comf_obj.pet_category
                core_cond = comf_obj.core_temperature_category
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvPET)

def unregister():
    bpy.utils.unregister_class(SvPET)
