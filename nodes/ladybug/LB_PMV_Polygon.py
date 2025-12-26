import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvPMV_Polygon(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvPMV_Polygon'
    bl_label = 'LB PMV Polygon'
    sv_icon = 'LB_PMV_POLYGON'
    sv__psych_chart: StringProperty(
        name='_psych_chart',
        update=updateNode,
        description='A hourly, daily, or sub-hourly data collection of temperature values or a single temperature value in Celcius to be used for the whole analysis. If this input data collection is in in Farenheit, the entire chart will be drawn using IP units. Operative temperature should be used if it is available. Otherwise, air temperature (aka. dry bulb temperature) is suitable.')
    sv__mrt_: StringProperty(
        name='_mrt_',
        update=updateNode,
        description='A number or list of numbers for the mean radiant temperature. These should be in Celsius if the Psychrometric Chart is in SI and Farenheit if the Psychrometric Chart is in IP. If None, a polygon for operative temperature will be plot, assuming that radiant temperature and air temperature are the same. (Default: None).')
    sv__air_speed_: StringProperty(
        name='_air_speed_',
        update=updateNode,
        description='A number or list of numbers for the air speed values in m/s. If None, a low air speed of 0.1 m/s wil be used for all polygons. (Default: None).')
    sv__met_rate_: StringProperty(
        name='_met_rate_',
        update=updateNode,
        description='A number or list of numbers for the metabolic rate in met. If None, a met rate of 1.1 met will be used for all polygons, indicating a human subject who is seated, typing. (Default: None).')
    sv__clothing_: StringProperty(
        name='_clothing_',
        update=updateNode,
        description='A number or list of numbers for the clothing level in clo. If None, a clo level of 0.7 clo will be used for all polygons, indicating a human subject with a long sleeve shirt and pants. (Default: None).')
    sv_pmv_par_: StringProperty(
        name='pmv_par_',
        update=updateNode,
        description='Optional PMVParameter object to specify parameters under which conditions are considered acceptable. If None, default will assume a PPD threshold of 10%, no absolute humidity constraints and a still air threshold of 0.1 m/s.')
    sv_merge_poly_: StringProperty(
        name='merge_poly_',
        update=updateNode,
        description='Boolean to note whether all comfort polygons should be merged into a single polygon instead of separate polygons for each set of input conditions. (Default: False).')
    sv_strategies_: StringProperty(
        name='strategies_',
        update=updateNode,
        description='An optional text input of passive strategies to be plot on the psychrometric chart as polygons.  It is recommended that the "LB Passive Strategy" component be used to select which polygons to plot.')
    sv_strategy_par_: StringProperty(
        name='strategy_par_',
        update=updateNode,
        description='Optional passive strategy parameters from the "LB Passive Strategy Parameters" component. This can be used to adjust various inputs used to generate strategy polygons including the maximum comfortable air speed, the building balance temperature, and the temperature limits for thermal mass and night flushing.')
    sv_solar_data_: StringProperty(
        name='solar_data_',
        update=updateNode,
        description='An annual hourly continuous data collection of irradiance (or radiation) in W/m2 (or Wh/m2) that aligns with the data points on the psychrometric chart. This is only required when plotting a "Passive Solar Heating" strategy polygon on the chart. The irradiance values should be incident on the orientation of the passive solar heated windows. So using global horizontal radiation assumes that all windows are skylights (like a greenhouse). The "LB Directional Irradiance" component can be used to get irradiance data for a specific surface orientation.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_psych_chart')
        input_node.prop_name = 'sv__psych_chart'
        input_node.tooltip = 'A hourly, daily, or sub-hourly data collection of temperature values or a single temperature value in Celcius to be used for the whole analysis. If this input data collection is in in Farenheit, the entire chart will be drawn using IP units. Operative temperature should be used if it is available. Otherwise, air temperature (aka. dry bulb temperature) is suitable.'
        input_node = self.inputs.new('SvLBSocket', '_mrt_')
        input_node.prop_name = 'sv__mrt_'
        input_node.tooltip = 'A number or list of numbers for the mean radiant temperature. These should be in Celsius if the Psychrometric Chart is in SI and Farenheit if the Psychrometric Chart is in IP. If None, a polygon for operative temperature will be plot, assuming that radiant temperature and air temperature are the same. (Default: None).'
        input_node = self.inputs.new('SvLBSocket', '_air_speed_')
        input_node.prop_name = 'sv__air_speed_'
        input_node.tooltip = 'A number or list of numbers for the air speed values in m/s. If None, a low air speed of 0.1 m/s wil be used for all polygons. (Default: None).'
        input_node = self.inputs.new('SvLBSocket', '_met_rate_')
        input_node.prop_name = 'sv__met_rate_'
        input_node.tooltip = 'A number or list of numbers for the metabolic rate in met. If None, a met rate of 1.1 met will be used for all polygons, indicating a human subject who is seated, typing. (Default: None).'
        input_node = self.inputs.new('SvLBSocket', '_clothing_')
        input_node.prop_name = 'sv__clothing_'
        input_node.tooltip = 'A number or list of numbers for the clothing level in clo. If None, a clo level of 0.7 clo will be used for all polygons, indicating a human subject with a long sleeve shirt and pants. (Default: None).'
        input_node = self.inputs.new('SvLBSocket', 'pmv_par_')
        input_node.prop_name = 'sv_pmv_par_'
        input_node.tooltip = 'Optional PMVParameter object to specify parameters under which conditions are considered acceptable. If None, default will assume a PPD threshold of 10%, no absolute humidity constraints and a still air threshold of 0.1 m/s.'
        input_node = self.inputs.new('SvLBSocket', 'merge_poly_')
        input_node.prop_name = 'sv_merge_poly_'
        input_node.tooltip = 'Boolean to note whether all comfort polygons should be merged into a single polygon instead of separate polygons for each set of input conditions. (Default: False).'
        input_node = self.inputs.new('SvLBSocket', 'strategies_')
        input_node.prop_name = 'sv_strategies_'
        input_node.tooltip = 'An optional text input of passive strategies to be plot on the psychrometric chart as polygons.  It is recommended that the "LB Passive Strategy" component be used to select which polygons to plot.'
        input_node = self.inputs.new('SvLBSocket', 'strategy_par_')
        input_node.prop_name = 'sv_strategy_par_'
        input_node.tooltip = 'Optional passive strategy parameters from the "LB Passive Strategy Parameters" component. This can be used to adjust various inputs used to generate strategy polygons including the maximum comfortable air speed, the building balance temperature, and the temperature limits for thermal mass and night flushing.'
        input_node = self.inputs.new('SvLBSocket', 'solar_data_')
        input_node.prop_name = 'sv_solar_data_'
        input_node.tooltip = 'An annual hourly continuous data collection of irradiance (or radiation) in W/m2 (or Wh/m2) that aligns with the data points on the psychrometric chart. This is only required when plotting a "Passive Solar Heating" strategy polygon on the chart. The irradiance values should be incident on the orientation of the passive solar heated windows. So using global horizontal radiation assumes that all windows are skylights (like a greenhouse). The "LB Directional Irradiance" component can be used to get irradiance data for a specific surface orientation.'
        output_node = self.outputs.new('SvLBSocket', 'total_comfort')
        output_node.tooltip = 'The percent of the data on the psychrometric chart that are inside all comfort and passive strategy polygons.'
        output_node = self.outputs.new('SvLBSocket', 'total_comf_data')
        output_node.tooltip = 'Data collection or a 0/1 value noting whether each of the data points on the psychrometric chart lies inside of a comfort polygon or a strategy polygon. _ This can be connected to the "LB Create Legend" component to generate a list of colors that can be used to color the points output from "LB Psychrometric Chart" component to see exactly which points are comfortable and which are not. _ Values are one of the following: 0 = uncomfortable 1 = comfortable'
        output_node = self.outputs.new('SvLBSocket', 'polygon_names')
        output_node.tooltip = 'A list of names for each of the polygons. This will include both the comfort polygons and the passive strategy polygons. The order of these names correspondsto the total_strategies and strategies_data outputs.'
        output_node = self.outputs.new('SvLBSocket', 'polygon_comfort')
        output_node.tooltip = 'The percent of the input data that are in each of the comfort or passive strategy polygons. Each number here corresponds to the names in the polygon_names output above.'
        output_node = self.outputs.new('SvLBSocket', 'polygon_data')
        output_node.tooltip = 'A list of data collections or 0/1 values indicating whether each  of the data points on the psychrometric chart lies inside each of the comfort or a strategy polygons. Each data collection or here corresponds to the names in the polygon_names output above. _ Values are one of the following: 0 = uncomfortable 1 = comfortable'
        output_node = self.outputs.new('SvLBSocket', 'comfort_poly')
        output_node.tooltip = 'Brep representing the range of comfort for the input mrt, air speed, metabolic rate and clothing level. If multiple values have been input, multiple polygons will be output here.'
        output_node = self.outputs.new('SvLBSocket', 'strategy_poly')
        output_node.tooltip = 'Brep representing the area of the chart made comfortable by any input passive strategies. If multiple strategies have been input to the strategies_ input, multiple polygons will be output here.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Draw thermal comfort polygons on a Psychrometric Chart using the PMV model for indoor thermal comfort. _ This component can also plot passive strategy polygons on the psychrometric chart and can compute the number of hours that lie inside each of the comfort / strategy polygons. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['total_comfort', 'total_comf_data', 'polygon_names', 'polygon_comfort', 'polygon_data', 'comfort_poly', 'strategy_poly']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_psych_chart', '_mrt_', '_air_speed_', '_met_rate_', '_clothing_', 'pmv_par_', 'merge_poly_', 'strategies_', 'strategy_par_', 'solar_data_']
        self.sv_input_types = ['System.Object', 'double', 'double', 'double', 'double', 'System.Object', 'bool', 'string', 'System.Object', 'System.Object']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'list', 'list', 'list', 'list', 'item', 'item', 'list', 'item', 'item']
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

    def process_ladybug(self, _psych_chart, _mrt_, _air_speed_, _met_rate_, _clothing_, pmv_par_, merge_poly_, strategies_, strategy_par_, solar_data_):

        try:
            from ladybug.psychchart import PsychrometricChart
            from ladybug.datacollection import BaseCollection
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_comfort.chart.polygonpmv import PolygonPMV
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_comfort:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import tolerance
            from ladybug_tools.fromgeometry import from_polyline2d_to_offset_brep
            from ladybug_tools.sverchok import all_required_inputs, \
                list_to_data_tree, give_warning, de_objectify_output
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        def strategy_warning(polygon_name):
            """Give a warning about a polygon not fitting on the chart."""
            msg = 'Polygon "{}" could not fit on the chart given the current location of ' \
                'the comfort polygon(s).\nTry moving the comfort polygon(s) by changing ' \
                'its criteria to see the missing polygon.'.format(polygon_name)
            give_warning(ghenv.Component, msg)
            print(msg)
        
        
        def process_polygon(polygon_name, polygon):
            """Process a strategy polygon that does not require any special treatment."""
            if polygon is not None:
                polygon_names.append(polygon_name)
                strategy_poly.append(from_polyline2d_to_offset_brep(polygon, offset, z))
                dat = poly_obj.evaluate_polygon(polygon, tolerance)
                dat = dat[0] if len(dat) == 1 else poly_obj.create_collection(dat, polygon_name)
                polygon_data.append(dat)
            else:
                strategy_warning(polygon_name)
        
        
        def merge_polygon_data(poly_data):
            """Merge an array of polygon comfort conditions into a single data list."""
            val_mtx = [dat.values for dat in poly_data]
            merged_values = []
            for hr_data in zip(*val_mtx):
                hr_val = 1 if 1 in hr_data else 0
                merged_values.append(hr_val)
            return merged_values
        
        
        if all_required_inputs(ghenv.Component):
            # unpack any passive strategy parameters
            if strategy_par_ is None:
                day_above, night_below, fan_spd, bal_temp, solar_cap, tim_c = \
                    (12.0, 3.0, 1.0, 12.8, 50.0, 8)
            else:
                day_above, night_below, fan_spd, bal_temp, solar_cap, tim_c = \
                    de_objectify_output(strategy_par_)
        
            # convert the temperature values to C if the polygon is in IP
            assert isinstance(_psych_chart, PsychrometricChart), 'PolygonPMV ' \
                'psychrometric chart must be a ladybug PsychrometricChart. ' \
                'Got {}.'.format(type(_psych_chart))
            z = _psych_chart.z
            offset = _psych_chart.x_dim * 0.25
            if _psych_chart.use_ip:
                _mrt_ = PolygonPMV.TEMP_TYPE.to_unit(_mrt_, 'C', 'F')
        
            # create the PolygonPMV object
            poly_obj = PolygonPMV(_psych_chart, _mrt_, _air_speed_, _met_rate_, _clothing_,
                                  comfort_parameter=pmv_par_)
        
            # draw the comfort polygon
            polygon_names = []
            polygon_data = []
            if merge_poly_:
                comfort_poly = from_polyline2d_to_offset_brep(
                    poly_obj.merged_comfort_polygon, offset, z)
                polygon_data.append(poly_obj.merged_comfort_data)
                polygon_names.append('Comfort')
            else:
                comfort_poly = [from_polyline2d_to_offset_brep(poly, offset, z)
                                for poly in poly_obj.comfort_polygons]
                polygon_data.extend(poly_obj.comfort_data)
                if len(comfort_poly) == 1:
                    polygon_names.append('Comfort')
                else:
                    names = ('Comfort {}'.format(i + 1) for i in range(len(comfort_poly)))
                    polygon_names.extend(names)
        
            # draw passive strategies if requested
            if len(strategies_) != 0:
                strategy_poly = []
                if 'Evaporative Cooling' in strategies_:
                    ec_poly = poly_obj.evaporative_cooling_polygon()
                    process_polygon('Evaporative Cooling', ec_poly)
                if 'Mass + Night Vent' in strategies_:
                    nf_poly = poly_obj.night_flush_polygon(day_above)
                    p_name = 'Mass + Night Vent'
                    if nf_poly is not None:
                        polygon_names.append(p_name)
                        strategy_poly.append(from_polyline2d_to_offset_brep(nf_poly, offset, z))
                        dat = poly_obj.evaluate_night_flush_polygon(
                            nf_poly, _psych_chart.original_temperature, night_below, tim_c, tolerance)
                        dat = dat[0] if len(dat) == 1 else poly_obj.create_collection(dat, p_name)
                        polygon_data.append(dat)
                    else:
                        strategy_warning(p_name)
                if 'Occupant Use of Fans' in strategies_:
                    fan_poly = poly_obj.fan_use_polygon(fan_spd)
                    process_polygon('Occupant Use of Fans', fan_poly)
                if 'Capture Internal Heat' in strategies_:
                    iht_poly = poly_obj.internal_heat_polygon(bal_temp)
                    process_polygon('Capture Internal Heat', iht_poly)
                if 'Passive Solar Heating' in strategies_:
                    p_name = 'Passive Solar Heating'
                    if solar_data_ is None:
                        msg = 'In order to plot a "{}" polygon, solar_data_ ' \
                            'must be plugged into this component.'.format(p_name)
                        print(msg)
                        give_warning(ghenv.Component, msg)
                    else:
                        bal_t = bal_temp if 'Capture Internal Heat' in strategies_ else None
                        dat, delta = poly_obj.evaluate_passive_solar(
                            solar_data_, solar_cap, tim_c, bal_t)
                        sol_poly = poly_obj.passive_solar_polygon(delta, bal_t)
                        if sol_poly is not None:
                            polygon_names.append(p_name)
                            strategy_poly.append(from_polyline2d_to_offset_brep(sol_poly, offset, z))
                            dat = dat[0] if len(dat) == 1 else poly_obj.create_collection(dat, p_name)
                            polygon_data.append(dat)
                        else:
                            strategy_warning(p_name)
        
            # compute total comfort values
            polygon_comfort = [dat.average * 100 for dat in polygon_data] if \
                isinstance(polygon_data[0], BaseCollection) else \
                [dat * 100 for dat in polygon_data]
            if isinstance(polygon_data[0], BaseCollection):
                merged_vals = merge_polygon_data(polygon_data)
                total_comf_data = poly_obj.create_collection(merged_vals, 'Total Comfort')
                total_comfort = total_comf_data.average * 100
            else:
                total_comf_data = 1 if sum(polygon_data) > 0 else 0
                total_comfort = total_comf_data * 100
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvPMV_Polygon)

def unregister():
    bpy.utils.unregister_class(SvPMV_Polygon)
