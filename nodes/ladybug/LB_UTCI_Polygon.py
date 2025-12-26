import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvUTCI_Polygon(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvUTCI_Polygon'
    bl_label = 'LB UTCI Polygon'
    sv_icon = 'LB_UTCI_POLYGON'
    sv__psych_chart: StringProperty(
        name='_psych_chart',
        update=updateNode,
        description='A hourly, daily, or sub-hourly data collection of temperature values or a single temperature value in Celcius to be used for the whole analysis. If this input data collection is in in Farenheit, the entire chart will be drawn using IP units. Operative temperature should be used if it is available. Otherwise, air temperature (aka. dry bulb temperature) is suitable.')
    sv__mrt_: StringProperty(
        name='_mrt_',
        update=updateNode,
        description='A number or list of numbers for the mean radiant temperature. These should be in Celsius if the Psychrometric Chart is in SI and Farenheit if the Psychrometric Chart is in IP. If None, a polygon for operative temperature will be plot, assuming that radiant temperature and air temperature are the same. (Default: None).')
    sv__wind_speed_: StringProperty(
        name='_wind_speed_',
        update=updateNode,
        description='A number or list of numbers for for the meteorological wind speed values in m/s (measured 10 m above the ground). If None, this will default to a low wind speed of 0.5 m/s, which is the lowest input speed that is recommended for the UTCI model.')
    sv_utci_par_: StringProperty(
        name='utci_par_',
        update=updateNode,
        description='Optional UTCIParameter object to specify parameters under which conditions are considered acceptable. If None, default will assume comfort thresholds consistent with those used by meteorologists to categorize outdoor conditions.')
    sv_merge_poly_: StringProperty(
        name='merge_poly_',
        update=updateNode,
        description='Boolean to note whether all comfort polygons should be merged into a single polygon instead of separate polygons for each set of input conditions. (Default: False).')
    sv_plot_stress_: StringProperty(
        name='plot_stress_',
        update=updateNode,
        description='Boolean to note whether polygons for heat/cold stress should be plotted in the output. This will include 3 polygons on either side of the comfort polygon(s) for... _ * Moderate Stress * Strong Stress * Very Strong Stress')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_psych_chart')
        input_node.prop_name = 'sv__psych_chart'
        input_node.tooltip = 'A hourly, daily, or sub-hourly data collection of temperature values or a single temperature value in Celcius to be used for the whole analysis. If this input data collection is in in Farenheit, the entire chart will be drawn using IP units. Operative temperature should be used if it is available. Otherwise, air temperature (aka. dry bulb temperature) is suitable.'
        input_node = self.inputs.new('SvLBSocket', '_mrt_')
        input_node.prop_name = 'sv__mrt_'
        input_node.tooltip = 'A number or list of numbers for the mean radiant temperature. These should be in Celsius if the Psychrometric Chart is in SI and Farenheit if the Psychrometric Chart is in IP. If None, a polygon for operative temperature will be plot, assuming that radiant temperature and air temperature are the same. (Default: None).'
        input_node = self.inputs.new('SvLBSocket', '_wind_speed_')
        input_node.prop_name = 'sv__wind_speed_'
        input_node.tooltip = 'A number or list of numbers for for the meteorological wind speed values in m/s (measured 10 m above the ground). If None, this will default to a low wind speed of 0.5 m/s, which is the lowest input speed that is recommended for the UTCI model.'
        input_node = self.inputs.new('SvLBSocket', 'utci_par_')
        input_node.prop_name = 'sv_utci_par_'
        input_node.tooltip = 'Optional UTCIParameter object to specify parameters under which conditions are considered acceptable. If None, default will assume comfort thresholds consistent with those used by meteorologists to categorize outdoor conditions.'
        input_node = self.inputs.new('SvLBSocket', 'merge_poly_')
        input_node.prop_name = 'sv_merge_poly_'
        input_node.tooltip = 'Boolean to note whether all comfort polygons should be merged into a single polygon instead of separate polygons for each set of input conditions. (Default: False).'
        input_node = self.inputs.new('SvLBSocket', 'plot_stress_')
        input_node.prop_name = 'sv_plot_stress_'
        input_node.tooltip = 'Boolean to note whether polygons for heat/cold stress should be plotted in the output. This will include 3 polygons on either side of the comfort polygon(s) for... _ * Moderate Stress * Strong Stress * Very Strong Stress'
        output_node = self.outputs.new('SvLBSocket', 'total_comfort')
        output_node.tooltip = 'The percent of the data on the psychrometric chart that are inside all comfort polygons.'
        output_node = self.outputs.new('SvLBSocket', 'total_comf_data')
        output_node.tooltip = 'Data collection or a 0/1 value noting whether each of the data points on the psychrometric chart lies inside of a comfort polygon. _ This can be connected to the "LB Create Legend" component to generate a list of colors that can be used to color the points output from "LB Psychrometric Chart" component to see exactly which points are comfortable and which are not. _ Values are one of the following: 0 = uncomfortable 1 = comfortable'
        output_node = self.outputs.new('SvLBSocket', 'polygons')
        output_node.tooltip = 'A list of Breps representing the range of comfort (or heat/cold stress) for the input mrt and air speed.'
        output_node = self.outputs.new('SvLBSocket', 'polygon_names')
        output_node.tooltip = 'A list of names for each of the polygons which correspond with the polygons output above. This will include both the comfort polygons and the cold/heat stress polygons.'
        output_node = self.outputs.new('SvLBSocket', 'polygon_data')
        output_node.tooltip = 'A list of data collections or 0/1 values indicating whether each  of the data points on the psychrometric chart lies inside each of the comfort polygons. Each data collection or here corresponds to the names in the polygon_names output above. _ Values are one of the following: 0 = outside 1 = inside'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Draw thermal comfort polygons on a Psychrometric Chart using the UTCI outdoor thermal comfort model. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['total_comfort', 'total_comf_data', 'polygons', 'polygon_names', 'polygon_data']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_psych_chart', '_mrt_', '_wind_speed_', 'utci_par_', 'merge_poly_', 'plot_stress_']
        self.sv_input_types = ['System.Object', 'double', 'double', 'System.Object', 'bool', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None]
        self.sv_input_access = ['item', 'list', 'list', 'item', 'item', 'item']
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

    def process_ladybug(self, _psych_chart, _mrt_, _wind_speed_, utci_par_, merge_poly_, plot_stress_):

        try:
            from ladybug.psychchart import PsychrometricChart
            from ladybug.datacollection import BaseCollection
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_comfort.chart.polygonutci import PolygonUTCI
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_comfort:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import tolerance
            from ladybug_tools.fromgeometry import from_polyline2d_to_offset_brep
            from ladybug_tools.sverchok import all_required_inputs, \
                list_to_data_tree, give_warning
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
            # convert the temperature values to C if the polygon is in IP
            assert isinstance(_psych_chart, PsychrometricChart), 'PolygonUTCI ' \
                'psychrometric chart must be a ladybug PsychrometricChart. ' \
                'Got {}.'.format(type(_psych_chart))
            z = _psych_chart.z
            offset = _psych_chart.x_dim * 0.25
            if _psych_chart.use_ip:
                _mrt_ = PolygonUTCI.TEMP_TYPE.to_unit(_mrt_, 'C', 'F')
        
            # create the PolygonUTCI object
            poly_obj = PolygonUTCI(_psych_chart, _mrt_, _wind_speed_, comfort_parameter=utci_par_)
        
            # draw the comfort polygon
            polygon_names = []
            comfort_data = []
            if merge_poly_:
                polygons = [from_polyline2d_to_offset_brep(poly_obj.merged_comfort_polygon, offset, z)]
                comfort_data.append(poly_obj.merged_comfort_data)
                polygon_names.append('Comfort')
            else:
                polygons = [
                    from_polyline2d_to_offset_brep(poly, offset, z)
                    for poly in poly_obj.comfort_polygons
                ]
                comfort_data.extend(poly_obj.comfort_data)
                if len(polygons) == 1:
                    polygon_names.append('Comfort')
                else:
                    names = ('Comfort {}'.format(i + 1) for i in range(len(polygons)))
                    polygon_names.extend(names)
        
            # draw the cold/heat stress polygons if requested
            polygon_data = comfort_data[:]
            if plot_stress_:
                stress_polys = (
                    poly_obj.moderate_cold_polygon, poly_obj.strong_cold_polygon,
                    poly_obj.very_strong_cold_polygon, poly_obj.moderate_heat_polygon,
                    poly_obj.strong_heat_polygon, poly_obj.very_strong_heat_polygon
                )
                stress_names = (
                    'Moderate Cold Stress', 'Strong Cold Stress',
                    'Very Strong Cold Stress', 'Moderate Heat Stress',
                    'Strong Heat Stress', 'Very Strong Heat Stress'
                )
                for poly, name in zip(stress_polys, stress_names):
                    stress_data = poly_obj.evaluate_inside(poly[0], poly[2], name)
                    if 'Cold' in name:
                        polygons.insert(0, from_polyline2d_to_offset_brep(poly, offset, z))
                        polygon_names.insert(0, name)
                        polygon_data.insert(0, stress_data)
                    else:
                        polygons.append(from_polyline2d_to_offset_brep(poly, offset, z))
                        polygon_names.append(name)
                        polygon_data.append(stress_data)
        
            # compute total comfort values
            polygon_comfort = [dat.average * 100 for dat in comfort_data] if \
                isinstance(comfort_data[0], BaseCollection) else \
                [dat * 100 for dat in comfort_data]
            if isinstance(comfort_data[0], BaseCollection):
                merged_vals = merge_polygon_data(comfort_data)
                total_comf_data = poly_obj.create_collection(merged_vals, 'Total Comfort')
                total_comfort = total_comf_data.average * 100
            else:
                total_comf_data = 1 if sum(comfort_data) > 0 else 0
                total_comfort = total_comf_data * 100
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvUTCI_Polygon)

def unregister():
    bpy.utils.unregister_class(SvUTCI_Polygon)
