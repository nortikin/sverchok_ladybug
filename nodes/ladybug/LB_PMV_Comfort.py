import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvPMV(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvPMV'
    bl_label = 'LB PMV Comfort'
    sv_icon = 'LB_PMV'
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
    sv__met_rate_: StringProperty(
        name='_met_rate_',
        update=updateNode,
        description='Data Collection or individual value of metabolic rate in met. Default is set to 1.1 met for seated, typing. Typical values include the following. _ * 1 met = Metabolic rate of a resting seated person * 1.2 met = Metabolic rate of a standing person * 2.4 met = Metabolic rate of a person walking at ~1 m/s (2 mph)')
    sv__clothing_: StringProperty(
        name='_clothing_',
        update=updateNode,
        description='Data Collection or individual value of clothing insulation in clo. Default is set to 0.7 clo for long sleeve shirt and pants. Typical values include the following. _ * 1 clo = Three-piece suit * 0.5 clo = Shorts + T-shirt * 0 clo = No clothing')
    sv_pmv_par_: StringProperty(
        name='pmv_par_',
        update=updateNode,
        description='Optional comfort parameters from the "LB PMV Comfort Parameters" component to specify the criteria under which conditions are considered acceptable/comfortable. The default will assume a PPD threshold of 10% and no absolute humidity constraints.')
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
        input_node = self.inputs.new('SvLBSocket', '_met_rate_')
        input_node.prop_name = 'sv__met_rate_'
        input_node.tooltip = 'Data Collection or individual value of metabolic rate in met. Default is set to 1.1 met for seated, typing. Typical values include the following. _ * 1 met = Metabolic rate of a resting seated person * 1.2 met = Metabolic rate of a standing person * 2.4 met = Metabolic rate of a person walking at ~1 m/s (2 mph)'
        input_node = self.inputs.new('SvLBSocket', '_clothing_')
        input_node.prop_name = 'sv__clothing_'
        input_node.tooltip = 'Data Collection or individual value of clothing insulation in clo. Default is set to 0.7 clo for long sleeve shirt and pants. Typical values include the following. _ * 1 clo = Three-piece suit * 0.5 clo = Shorts + T-shirt * 0 clo = No clothing'
        input_node = self.inputs.new('SvLBSocket', 'pmv_par_')
        input_node.prop_name = 'sv_pmv_par_'
        input_node.tooltip = 'Optional comfort parameters from the "LB PMV Comfort Parameters" component to specify the criteria under which conditions are considered acceptable/comfortable. The default will assume a PPD threshold of 10% and no absolute humidity constraints.'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to True to run the component.'
        output_node = self.outputs.new('SvLBSocket', 'pmv')
        output_node.tooltip = 'Predicted Mean Vote (PMV). _ PMV is a seven-point scale from cold (-3) to hot (+3) that was used in comfort surveys of P.O. Fanger. _ Each interger value of the scale indicates the following: * -3 = Cold * -2 = Cool * -1 = Slightly Cool *  0 = Neutral * +1 = Slightly Warm * +2 = Warm * +3 = Hot'
        output_node = self.outputs.new('SvLBSocket', 'ppd')
        output_node.tooltip = 'Percentage of People Dissatisfied (PPD). _ Specifically, this is defined by the percent of people who would have a PMV beyond acceptable thresholds (typically <-0.5 and >+0.5). Note that, with the PMV model, the best possible PPD achievable is 5% and most standards aim to have a PPD below 10%.'
        output_node = self.outputs.new('SvLBSocket', 'set')
        output_node.tooltip = 'Standard Effective Temperature (SET) in Celcius. _ These temperatures describe what the given input conditions "feel like" in relation to a standard environment of 50% relative humidity, <0.1 m/s average air speed, and mean radiant temperature equal to average air temperature, in which the total heat loss from the skin of an imaginary occupant with an activity level of 1.0 met and a clothing level of 0.6 clo is the same as that from a person in the actual environment.'
        output_node = self.outputs.new('SvLBSocket', 'comfort')
        output_node.tooltip = 'Integers noting whether the input conditions are acceptable according to the assigned comfort_parameter. _ Values are one of the following: * 0 = uncomfortable * 1 = comfortable'
        output_node = self.outputs.new('SvLBSocket', 'condition')
        output_node.tooltip = 'Integers noting the thermal status of a subject according to the assigned comfort_parameter. _ Values are one of the following: * -2 = too dry (but thermally neutral) * -1 = cold *  0 = netural * +1 = hot * +2 = too humid (but thermally neutral)'
        output_node = self.outputs.new('SvLBSocket', 'heat_loss')
        output_node.tooltip = 'A list of 6 terms for heat loss from the human energy balance calculation that underlies PMV. Valeus are in W. _ The terms are ordered as follows: - Conduction - Sweating - Latent Respiration - Dry Respiration - Radiation - Convection'
        output_node = self.outputs.new('SvLBSocket', 'comf_obj')
        output_node.tooltip = 'A Python object containing all inputs and results of the analysis.  This can be plugged into components like the "Comfort Statistics" component to get further information.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate Predicted Mean Vote (PMV). - PMV is a thermal comfort model for use on the interior of buildings where a heating or cooling system is operational. For naturally ventilated buildings, the Adaptive thermal comfort model is recommended and, for outdoor conditions, models such as Universal Thermal Climate Index (UTCI) or Physiological Equivalent Temperature (PET) are recommended. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['pmv', 'ppd', 'set', 'comfort', 'condition', 'heat_loss', 'comf_obj']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_air_temp', '_mrt_', '_rel_humid', '_air_speed_', '_met_rate_', '_clothing_', 'pmv_par_', '_run']
        self.sv_input_types = ['System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _air_temp, _mrt_, _rel_humid, _air_speed_, _met_rate_, _clothing_, pmv_par_, _run):

        try:
            from ladybug.psychrometrics import humid_ratio_from_db_rh
            from ladybug.datatype.temperature import Temperature
            from ladybug.datacollection import BaseCollection
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_comfort.collection.pmv import PMV
            from ladybug_comfort.parameter.pmv import PMVParameter
            from ladybug_comfort.pmv import predicted_mean_vote
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_comfort:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        def extract_collections(input_list):
            """Process inputs into collections and floats."""
            defaults = [None, _air_temp, 0.1, None, 1.1, 0.7]
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
            input_list = [_air_temp, _mrt_, _air_speed_, _rel_humid, _met_rate_, _clothing_]
            input, data_colls = extract_collections(input_list)
            pmv_par = pmv_par_ or PMVParameter()
            
            if data_colls == []:
                # The inputs are all individual values.
                pmv_result = predicted_mean_vote(input[0], float(input[1]), input[2],
                                                 input[3], input[4], input[5], 0,
                                                 pmv_par.still_air_threshold)
                pmv = pmv_result['pmv']
                ppd = pmv_result['ppd']
                set = pmv_result['set']
                hr = humid_ratio_from_db_rh(input[0], input[3])
                comfort = pmv_par.is_comfortable(pmv_result['ppd'], hr)
                condition = pmv_par.discomfort_reason(pmv_result['pmv'], pmv_result['ppd'])
                heat_loss = [pmv_result['heat_loss']['cond'],
                            pmv_result['heat_loss']['sweat'],
                            pmv_result['heat_loss']['res_l'],
                            pmv_result['heat_loss']['res_s'],
                            pmv_result['heat_loss']['rad'],
                            pmv_result['heat_loss']['conv']]
            else:
                # The inputs include Data Collections.
                if not isinstance(_air_temp, BaseCollection):
                    _air_temp = data_colls[0].get_aligned_collection(
                        float(_air_temp), Temperature(), 'C')
                
                comf_obj = PMV(_air_temp, _rel_humid, _mrt_, _air_speed_, _met_rate_,
                    _clothing_, 0, pmv_par)
                pmv = comf_obj.predicted_mean_vote
                ppd = comf_obj.percentage_people_dissatisfied
                set = comf_obj.standard_effective_temperature
                comfort = comf_obj.is_comfortable
                condition = comf_obj.discomfort_reason
                heat_loss = [comf_obj.heat_loss_conduction,
                            comf_obj.heat_loss_sweating,
                            comf_obj.heat_loss_latent_respiration,
                            comf_obj.heat_loss_dry_respiration,
                            comf_obj.heat_loss_radiation,
                            comf_obj.heat_loss_convection]
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvPMV)

def unregister():
    bpy.utils.unregister_class(SvPMV)
