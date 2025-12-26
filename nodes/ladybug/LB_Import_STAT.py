import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvImportSTAT(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvImportSTAT'
    bl_label = 'LB Import STAT'
    sv_icon = 'LB_IMPORTSTAT'
    sv__stat_file: StringProperty(
        name='_stat_file',
        update=updateNode,
        description='A .stat file path on your system as a string.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_stat_file')
        input_node.prop_name = 'sv__stat_file'
        input_node.tooltip = 'A .stat file path on your system as a string.'
        output_node = self.outputs.new('SvLBSocket', 'location')
        output_node.tooltip = 'A Ladybug Location object describing the location data in the STAT file.'
        output_node = self.outputs.new('SvLBSocket', 'ashrae_zone')
        output_node.tooltip = 'The ASHRAE climate zone of the STAT file. Numbers in the zone denote average temperature (0 = Hottest; 8 = Coldest). Letters in the zone denote wetness (A = Humid; B = Dry; C = Marine)'
        output_node = self.outputs.new('SvLBSocket', 'koppen_zone')
        output_node.tooltip = 'The Koppen climate zone of the STAT file. The Koppen climate system uses vegetation as in indicator fo climate and combines average monthly temperatures, precipitation, and the seasonality of precipitation.'
        output_node = self.outputs.new('SvLBSocket', 'clear_dir_norm_rad')
        output_node.tooltip = 'The hourly "Clear Sky" Direct Normal Radiation in Wh/m2. Such clear sky radiation is typically used for sizing cooling systems. If monthly optical depths are found within the STAT file, these values will come from the Revised ASHARAE Clear Sky (Tau model). If no optical depths are found, they will come from the original ASHARE lear sky model.'
        output_node = self.outputs.new('SvLBSocket', 'clear_diff_horiz_rad')
        output_node.tooltip = 'The hourly "Clear Sky" Diffuse Horizontal Radiation in Wh/m2. Such clear sky radiation is typically used for sizing cooling systems. If monthly optical depths are found within the STAT file, these values will come from the Revised ASHARAE Clear Sky (Tau model). If no optical depths are found, they will come from the original ASHARE lear sky model.'
        output_node = self.outputs.new('SvLBSocket', 'ann_heat_dday_996')
        output_node.tooltip = 'A DesignDay object representing the annual 99.6% heating design day.'
        output_node = self.outputs.new('SvLBSocket', 'ann_heat_dday_990')
        output_node.tooltip = 'A DesignDay object representing the annual 99.0% heating design day.'
        output_node = self.outputs.new('SvLBSocket', 'ann_cool_dday_004')
        output_node.tooltip = 'A DesignDay object representing the annual 0.4% cooling design day.'
        output_node = self.outputs.new('SvLBSocket', 'ann_cool_dday_010')
        output_node.tooltip = 'A DesignDay object representing the annual 1.0% cooling design day.'
        output_node = self.outputs.new('SvLBSocket', 'monthly_ddays_050')
        output_node.tooltip = 'A list of 12 DesignDay objects representing monthly 5.0% cooling design days.'
        output_node = self.outputs.new('SvLBSocket', 'monthly_ddays_100')
        output_node.tooltip = 'A list of 12 DesignDay objects representing monthly 10.0% cooling design days.'
        output_node = self.outputs.new('SvLBSocket', 'extreme_cold_week')
        output_node.tooltip = 'A Ladybug AnalysisPeriod object representing the coldest week within the corresponding EPW.'
        output_node = self.outputs.new('SvLBSocket', 'extreme_hot_week')
        output_node.tooltip = 'A Ladybug AnalysisPeriod object representing the hottest week within the corresponding EPW.'
        output_node = self.outputs.new('SvLBSocket', 'typical_weeks')
        output_node.tooltip = 'A list of Ladybug AnalysisPeriod objects representing typical weeks within the corresponding EPW. The type of week can vary depending on the climate. _ For mid and high lattitude climates with 4 seasons (eg. New York), these weeks are for each of the 4 seasons ordered as follows: Winter, Spring, Summer, Autumn _ For low lattitude climates with wet/dry seasons (eg. Mumbai), these weeks might also include: Wet Season, Dry Season _ For equitorial climates with no seasons (eg. Singapore), This output is usually a single week representing typical conditions of the entire year.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Import data from a standard .stat file. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['location', 'ashrae_zone', 'koppen_zone', 'clear_dir_norm_rad', 'clear_diff_horiz_rad', 'ann_heat_dday_996', 'ann_heat_dday_990', 'ann_cool_dday_004', 'ann_cool_dday_010', 'monthly_ddays_050', 'monthly_ddays_100', 'extreme_cold_week', 'extreme_hot_week', 'typical_weeks']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_stat_file']
        self.sv_input_types = ['string']
        self.sv_input_defaults = [None]
        self.sv_input_access = ['item']
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

    def process_ladybug(self, _stat_file):

        
        try:
            from ladybug.stat import STAT
            from ladybug.wea import Wea
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            stat_obj = STAT(_stat_file)
        
            # output location and climate zone
            location = stat_obj.location
            ashrae_zone = stat_obj.ashrae_climate_zone
            koppen_zone = stat_obj.koppen_climate_zone
        
            # output clear sky radiation
            try:  # first see if we can get the values from monthly optical depths
                wea = Wea.from_stat_file(_stat_file)
            except:  # no optical data was found; use the original clear sky
                wea = Wea.from_ashrae_clear_sky(location)
            clear_dir_norm_rad = wea.direct_normal_irradiance
            clear_diff_horiz_rad = wea.diffuse_horizontal_irradiance
        
            # output design day objects
            ann_heat_dday_996 = stat_obj.annual_heating_design_day_996
            ann_heat_dday_990 = stat_obj.annual_heating_design_day_990
            ann_cool_dday_004 = stat_obj.annual_cooling_design_day_004
            ann_cool_dday_010 = stat_obj.annual_cooling_design_day_010
            monthly_ddays_050 = stat_obj.monthly_cooling_design_days_050
            monthly_ddays_100 = stat_obj.monthly_cooling_design_days_100
        
            # output extreme and typical weeks
            extreme_cold_week = stat_obj.extreme_cold_week
            extreme_hot_week = stat_obj.extreme_hot_week
            typical_weeks = []
            seasonal_wks = [stat_obj.typical_winter_week, stat_obj.typical_spring_week,
                           stat_obj.typical_summer_week, stat_obj.typical_autumn_week]
            for wk in seasonal_wks:
                if wk is not None:
                    typical_weeks.append(wk)
            typical_weeks.extend(stat_obj.other_typical_weeks)

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvImportSTAT)

def unregister():
    bpy.utils.unregister_class(SvImportSTAT)
