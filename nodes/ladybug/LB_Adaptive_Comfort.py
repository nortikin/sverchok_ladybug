import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvAdaptive(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvAdaptive'
    bl_label = 'LB Adaptive Comfort'
    sv_icon = 'LB_ADAPTIVE'
    sv__out_temp: StringProperty(
        name='_out_temp',
        update=updateNode,
        description='Outdoor temperatures in one of the following formats: * A Data Collection of outdoor dry bulb temperatures recorded over the entire year. This Data Collection must be continouous and must either be an Hourly Collection or Daily Collection. In the event that the input adapt_par_ has a _avgm_or_runmean_ set to True, Monthly collections are also acceptable here. Note that, because an annual input is required, this input collection does not have to align with the _air_temp or _mrt_ inputs. * A Data Collection of prevailing outdoor temperature values in C. This Data Collection must align with the _air_temp or _mrt_ inputs and bear the PrevailingOutdoorTemperature data type in its header. * A single prevailing outdoor temperature value in C to be used for all of the _air_temp or _mrt_ inputs.')
    sv__air_temp: StringProperty(
        name='_air_temp',
        update=updateNode,
        description='Data Collection or individual value for air temperature in C.')
    sv__mrt_: StringProperty(
        name='_mrt_',
        update=updateNode,
        description='Data Collection or individual value for mean radiant temperature (MRT) in C. Default is the same as the air_temp.')
    sv__air_speed_: StringProperty(
        name='_air_speed_',
        update=updateNode,
        description='Data Collection or individual value for air speed in m/s. Note that higher air speeds in the adaptive model only widen the upper boundary of the comfort range at temperatures above 24 C and will not affect the lower temperature of the comfort range. Default is a very low speed of 0.1 m/s.')
    sv_adapt_par_: StringProperty(
        name='adapt_par_',
        update=updateNode,
        description='Optional comfort parameters from the "LB Adaptive Comfort Parameters" component to specify the criteria under which conditions are considered acceptable/comfortable. The default will use ASHRAE-55 adaptive comfort criteria.')
    sv__run: StringProperty(
        name='_run',
        update=updateNode,
        description='Set to True to run the component.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_out_temp')
        input_node.prop_name = 'sv__out_temp'
        input_node.tooltip = 'Outdoor temperatures in one of the following formats: * A Data Collection of outdoor dry bulb temperatures recorded over the entire year. This Data Collection must be continouous and must either be an Hourly Collection or Daily Collection. In the event that the input adapt_par_ has a _avgm_or_runmean_ set to True, Monthly collections are also acceptable here. Note that, because an annual input is required, this input collection does not have to align with the _air_temp or _mrt_ inputs. * A Data Collection of prevailing outdoor temperature values in C. This Data Collection must align with the _air_temp or _mrt_ inputs and bear the PrevailingOutdoorTemperature data type in its header. * A single prevailing outdoor temperature value in C to be used for all of the _air_temp or _mrt_ inputs.'
        input_node = self.inputs.new('SvLBSocket', '_air_temp')
        input_node.prop_name = 'sv__air_temp'
        input_node.tooltip = 'Data Collection or individual value for air temperature in C.'
        input_node = self.inputs.new('SvLBSocket', '_mrt_')
        input_node.prop_name = 'sv__mrt_'
        input_node.tooltip = 'Data Collection or individual value for mean radiant temperature (MRT) in C. Default is the same as the air_temp.'
        input_node = self.inputs.new('SvLBSocket', '_air_speed_')
        input_node.prop_name = 'sv__air_speed_'
        input_node.tooltip = 'Data Collection or individual value for air speed in m/s. Note that higher air speeds in the adaptive model only widen the upper boundary of the comfort range at temperatures above 24 C and will not affect the lower temperature of the comfort range. Default is a very low speed of 0.1 m/s.'
        input_node = self.inputs.new('SvLBSocket', 'adapt_par_')
        input_node.prop_name = 'sv_adapt_par_'
        input_node.tooltip = 'Optional comfort parameters from the "LB Adaptive Comfort Parameters" component to specify the criteria under which conditions are considered acceptable/comfortable. The default will use ASHRAE-55 adaptive comfort criteria.'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to True to run the component.'
        output_node = self.outputs.new('SvLBSocket', 'prevail_temp')
        output_node.tooltip = 'Data Collection of prevailing outdoor temperature in degrees C.'
        output_node = self.outputs.new('SvLBSocket', 'neutral_temp')
        output_node.tooltip = 'Data Collection of the desired neutral temperature in degrees C.'
        output_node = self.outputs.new('SvLBSocket', 'deg_neutral')
        output_node.tooltip = 'Data Collection of the degrees from desired neutral temperature in degrees C.'
        output_node = self.outputs.new('SvLBSocket', 'comfort')
        output_node.tooltip = 'Integers noting whether the input conditions are acceptable according to the assigned comfort_parameter. _ Values are one of the following: * 0 = uncomfortable * 1 = comfortable'
        output_node = self.outputs.new('SvLBSocket', 'condition')
        output_node.tooltip = 'Integers noting the thermal status of a subject according to the assigned comfort_parameter. _ Values are one of the following: * -1 = cold *  0 = netural * +1 = hot'
        output_node = self.outputs.new('SvLBSocket', 'comf_obj')
        output_node.tooltip = 'A Python object containing all inputs and results of the analysis.  This can be plugged into components like the "Comfort Statistics" component to get further information.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate Adaptive thermal comfort. - The Adaptive thermal comfort model is for use on the interior of buildings where a heating or cooling system is not operational and occupants have the option to open windows for natural ventilation. - Note that, for fully conditioned buildings, the PMV thermal comfort model should be used. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['prevail_temp', 'neutral_temp', 'deg_neutral', 'comfort', 'condition', 'comf_obj']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_out_temp', '_air_temp', '_mrt_', '_air_speed_', 'adapt_par_', '_run']
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

    def process_ladybug(self, _out_temp, _air_temp, _mrt_, _air_speed_, adapt_par_, _run):

        try:
            from ladybug.datatype.temperature import Temperature
            from ladybug.datacollection import BaseCollection
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_comfort.collection.adaptive import Adaptive
            from ladybug_comfort.parameter.adaptive import AdaptiveParameter
            from ladybug_comfort.adaptive import t_operative, \
                adaptive_comfort_ashrae55, adaptive_comfort_en15251, \
                cooling_effect_ashrae55, cooling_effect_en15251, \
                adaptive_comfort_conditioned
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_comfort:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        def extract_collections(input_list):
            """Process inputs into collections and floats."""
            defaults = [None, None, _air_temp, 0.1]
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
            input_list = [_out_temp, _air_temp, _mrt_, _air_speed_]
            input, data_colls = extract_collections(input_list)
            adapt_par = adapt_par_ or AdaptiveParameter()
        
            if data_colls == []:
                # The inputs are all individual values.
                prevail_temp = input[0]
                to = t_operative(input[1], float(input[2]))
                
                # Determine the ralationship to the neutral temperature
                if adapt_par.conditioning != 0:
                    comf_result = adaptive_comfort_conditioned(prevail_temp, to,
                        adapt_par.conditioning, adapt_par.standard)
                elif adapt_par.ashrae55_or_en15251 is True:
                    comf_result = adaptive_comfort_ashrae55(prevail_temp, to)
                else:
                    comf_result = adaptive_comfort_en15251(prevail_temp, to)
                
                # Determine the cooling effect
                if adapt_par.discrete_or_continuous_air_speed is True:
                    ce = cooling_effect_ashrae55(input[3], to)
                else:
                    ce = cooling_effect_en15251(input[3], to)
                
                # Output results
                neutral_temp = comf_result['t_comf']
                deg_neutral = comf_result['deg_comf']
                comfort = adapt_par.is_comfortable(comf_result, ce)
                condition = adapt_par.thermal_condition(comf_result, ce)
            else:
                # The inputs include Data Collections.
                if not isinstance(_air_temp, BaseCollection):
                    _air_temp = data_colls[0].get_aligned_collection(
                        float(_air_temp), Temperature(), 'C')
                
                comf_obj = Adaptive.from_air_and_rad_temp(_out_temp, _air_temp, _mrt_,
                                                         _air_speed_, adapt_par)
                prevail_temp = comf_obj.prevailing_outdoor_temperature
                neutral_temp = comf_obj.neutral_temperature
                deg_neutral = comf_obj.degrees_from_neutral
                comfort = comf_obj.is_comfortable
                condition = comf_obj.thermal_condition

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvAdaptive)

def unregister():
    bpy.utils.unregister_class(SvAdaptive)
