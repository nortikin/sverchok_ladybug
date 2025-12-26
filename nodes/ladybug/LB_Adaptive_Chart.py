import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvAdaptiveChart(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvAdaptiveChart'
    bl_label = 'LB Adaptive Chart'
    sv_icon = 'LB_ADAPTIVECHART'
    sv__out_temp: StringProperty(
        name='_out_temp',
        update=updateNode,
        description='Outdoor temperatures in one of the following formats: * A Data Collection of outdoor dry bulb temperatures recorded over the entire year. This Data Collection must be continouous and must either be an Hourly Collection or Daily Collection. In the event that the input adapt_par_ has a _avgm_or_runmean_ set to True, Monthly collections are also acceptable here. Note that, because an annual input is required, this input collection does not have to align with the _air_temp or _mrt_ inputs. * A Data Collection of prevailing outdoor temperature values in C. This Data Collection must align with the _air_temp or _mrt_ inputs and bear the PrevailingOutdoorTemperature data type in its header. * A single prevailing outdoor temperature value in C to be used for all of the _air_temp or _mrt_ inputs.')
    sv__air_temp: StringProperty(
        name='_air_temp',
        update=updateNode,
        description='A hourly, daily, or sub-hourly data collection of temperature values for indoor air temperature (or operative temperature). If this input data collection is in in Farenheit, the entire chart will be drawn using IP units.')
    sv__mrt_: StringProperty(
        name='_mrt_',
        update=updateNode,
        description='A hourly, daily, or sub-hourly data collection for mean radiant temperature (MRT) in C. Default is the same as the air_temp, effectively interpreting the _air_temp as operative tempreature.')
    sv__air_speed_: StringProperty(
        name='_air_speed_',
        update=updateNode,
        description='A number for the air speed values in m/s. Note that higher air speeds in the adaptive model only widen the upper boundary of the comfort range at temperatures above 24 C and will not affect the lower temperature of the comfort range. Default is a very low speed of 0.1 m/s.')
    sv_adapt_par_: StringProperty(
        name='adapt_par_',
        update=updateNode,
        description='Optional comfort parameters from the "LB Adaptive Comfort Parameters" component to specify the criteria under which conditions are considered acceptable/comfortable. The default will use ASHRAE-55 adaptive comfort criteria.')
    sv__base_pt_: StringProperty(
        name='_base_pt_',
        update=updateNode,
        description='A point to be used as the bottom-left-most point from which all geometry of the plot will be generated. (Default: (0, 0, 0)).')
    sv__scale_: StringProperty(
        name='_scale_',
        update=updateNode,
        description='A number to set the dimensions of the chart. (Default: 1).')
    sv__prevail_range_: StringProperty(
        name='_prevail_range_',
        update=updateNode,
        description='An optional domain (or number for the upper temperature), which will be used to set the lower and upper boundaries of prevailing outdoor temperature on the chart. These should be in Celsius if the chart is plotted in Celsius and and Fahrenheit if it is in Fahrenheit. The default is 10C to 33C when ASHRAE-55 is used and 10C to 30C when the EN standard is used. This translates to 50F to 92F for ASHRAE-55 and 50F to 86F for the EN standard.')
    sv__operat_range_: StringProperty(
        name='_operat_range_',
        update=updateNode,
        description='An optional domain (or number for the upper temperature), which will be used to set the lower and upper boundaries of indoor operative temperature on the chart. These should be in Celsius if the chart is plotted in Celsius and and Fahrenheit if it is in Fahrenheit. The default is 14C to 40C, which translates to 58F to 104F.')
    sv_legend_par_: StringProperty(
        name='legend_par_',
        update=updateNode,
        description='An optional LegendParameter object from the "LB Legend Parameters" component to change the display of the Adaptive Chart.')
    sv_data_: StringProperty(
        name='data_',
        update=updateNode,
        description='Optional data collections, which are aligned with the input _air_temp, which will be output from the data of this component and can be used to color points with data. This data can also be used along with the statement_ below to select out data that meets certain conditions.')
    sv_statement_: StringProperty(
        name='statement_',
        update=updateNode,
        description='A conditional statement as a string (e.g. a > 25). . The variable of the first data collection should always be named \'a\' (without quotations), the variable of the second list should be named \'b\', and so on. . For example, if three data collections are connected to _data and the following statement is applied: \'10 < a < 30 and b < 33 and c > 2\' The resulting collections will only include values where the first data collection is between 10 and 30, the second collection is less than 33 and the third collection is greater than 2. . For this component, the input indoor air temperature will always be the last (or seconf-to-last) letter and this will be followed by the input _mrt_ (if it is present).')
    sv_period_: StringProperty(
        name='period_',
        update=updateNode,
        description='A Ladybug analysis period to be applied to the _out_temp and _air_temp of the input data_.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_out_temp')
        input_node.prop_name = 'sv__out_temp'
        input_node.tooltip = 'Outdoor temperatures in one of the following formats: * A Data Collection of outdoor dry bulb temperatures recorded over the entire year. This Data Collection must be continouous and must either be an Hourly Collection or Daily Collection. In the event that the input adapt_par_ has a _avgm_or_runmean_ set to True, Monthly collections are also acceptable here. Note that, because an annual input is required, this input collection does not have to align with the _air_temp or _mrt_ inputs. * A Data Collection of prevailing outdoor temperature values in C. This Data Collection must align with the _air_temp or _mrt_ inputs and bear the PrevailingOutdoorTemperature data type in its header. * A single prevailing outdoor temperature value in C to be used for all of the _air_temp or _mrt_ inputs.'
        input_node = self.inputs.new('SvLBSocket', '_air_temp')
        input_node.prop_name = 'sv__air_temp'
        input_node.tooltip = 'A hourly, daily, or sub-hourly data collection of temperature values for indoor air temperature (or operative temperature). If this input data collection is in in Farenheit, the entire chart will be drawn using IP units.'
        input_node = self.inputs.new('SvLBSocket', '_mrt_')
        input_node.prop_name = 'sv__mrt_'
        input_node.tooltip = 'A hourly, daily, or sub-hourly data collection for mean radiant temperature (MRT) in C. Default is the same as the air_temp, effectively interpreting the _air_temp as operative tempreature.'
        input_node = self.inputs.new('SvLBSocket', '_air_speed_')
        input_node.prop_name = 'sv__air_speed_'
        input_node.tooltip = 'A number for the air speed values in m/s. Note that higher air speeds in the adaptive model only widen the upper boundary of the comfort range at temperatures above 24 C and will not affect the lower temperature of the comfort range. Default is a very low speed of 0.1 m/s.'
        input_node = self.inputs.new('SvLBSocket', 'adapt_par_')
        input_node.prop_name = 'sv_adapt_par_'
        input_node.tooltip = 'Optional comfort parameters from the "LB Adaptive Comfort Parameters" component to specify the criteria under which conditions are considered acceptable/comfortable. The default will use ASHRAE-55 adaptive comfort criteria.'
        input_node = self.inputs.new('SvLBSocket', '_base_pt_')
        input_node.prop_name = 'sv__base_pt_'
        input_node.tooltip = 'A point to be used as the bottom-left-most point from which all geometry of the plot will be generated. (Default: (0, 0, 0)).'
        input_node = self.inputs.new('SvLBSocket', '_scale_')
        input_node.prop_name = 'sv__scale_'
        input_node.tooltip = 'A number to set the dimensions of the chart. (Default: 1).'
        input_node = self.inputs.new('SvLBSocket', '_prevail_range_')
        input_node.prop_name = 'sv__prevail_range_'
        input_node.tooltip = 'An optional domain (or number for the upper temperature), which will be used to set the lower and upper boundaries of prevailing outdoor temperature on the chart. These should be in Celsius if the chart is plotted in Celsius and and Fahrenheit if it is in Fahrenheit. The default is 10C to 33C when ASHRAE-55 is used and 10C to 30C when the EN standard is used. This translates to 50F to 92F for ASHRAE-55 and 50F to 86F for the EN standard.'
        input_node = self.inputs.new('SvLBSocket', '_operat_range_')
        input_node.prop_name = 'sv__operat_range_'
        input_node.tooltip = 'An optional domain (or number for the upper temperature), which will be used to set the lower and upper boundaries of indoor operative temperature on the chart. These should be in Celsius if the chart is plotted in Celsius and and Fahrenheit if it is in Fahrenheit. The default is 14C to 40C, which translates to 58F to 104F.'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'An optional LegendParameter object from the "LB Legend Parameters" component to change the display of the Adaptive Chart.'
        input_node = self.inputs.new('SvLBSocket', 'data_')
        input_node.prop_name = 'sv_data_'
        input_node.tooltip = 'Optional data collections, which are aligned with the input _air_temp, which will be output from the data of this component and can be used to color points with data. This data can also be used along with the statement_ below to select out data that meets certain conditions.'
        input_node = self.inputs.new('SvLBSocket', 'statement_')
        input_node.prop_name = 'sv_statement_'
        input_node.tooltip = 'A conditional statement as a string (e.g. a > 25). . The variable of the first data collection should always be named \'a\' (without quotations), the variable of the second list should be named \'b\', and so on. . For example, if three data collections are connected to _data and the following statement is applied: \'10 < a < 30 and b < 33 and c > 2\' The resulting collections will only include values where the first data collection is between 10 and 30, the second collection is less than 33 and the third collection is greater than 2. . For this component, the input indoor air temperature will always be the last (or seconf-to-last) letter and this will be followed by the input _mrt_ (if it is present).'
        input_node = self.inputs.new('SvLBSocket', 'period_')
        input_node.prop_name = 'sv_period_'
        input_node.tooltip = 'A Ladybug analysis period to be applied to the _out_temp and _air_temp of the input data_.'
        output_node = self.outputs.new('SvLBSocket', 'total_comfort')
        output_node.tooltip = 'The percent of the data on the adaptive chart that is inside the comfort polygon.'
        output_node = self.outputs.new('SvLBSocket', 'comfort_data')
        output_node.tooltip = 'Data collection or a 0/1 value noting whether each of the data points on the chart lies inside of the comfort polygon. _ This can be connected to the "LB Create Legend" component to generate a list of colors that can be used to color the points output from "LB Adaptive Chart" component to see exactly which points are comfortable and which are not. _ Values are one of the following: 0 = uncomfortable 1 = comfortable'
        output_node = self.outputs.new('SvLBSocket', 'condition_data')
        output_node.tooltip = 'Data collection of integers noting the thermal status of the human subject according to the assigned comfort parameters. _ This can be connected to the "LB Create Legend" component to generate a list of colors that can be used to color the points output from "LB Adaptive Chart" component to see exactly which points are hot, cold, and neutral. _ Values are one of the following: * -1 = cold *  0 = netural * +1 = hot'
        output_node = self.outputs.new('SvLBSocket', 'polygon')
        output_node.tooltip = 'Brep representing the range of comfort for the input parameters.'
        output_node = self.outputs.new('SvLBSocket', 'title')
        output_node.tooltip = 'Text objects for the chart title and axes titles as well as a polyline for the outer border of the chart.'
        output_node = self.outputs.new('SvLBSocket', 'prevail_lines')
        output_node.tooltip = 'A list of line segments and text objects for the outdoor prevailing temperature labels on the chart.'
        output_node = self.outputs.new('SvLBSocket', 'operative_lines')
        output_node.tooltip = 'A list of line segments and text objects for the indoor operative temperature labels on the chart.'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'A colored mesh showing the number of input hours that happen in each part of the adaptive chart.'
        output_node = self.outputs.new('SvLBSocket', 'legend')
        output_node.tooltip = 'A colored legend showing the number of hours that correspond to each color.'
        output_node = self.outputs.new('SvLBSocket', 'points')
        output_node.tooltip = 'Points representing each of the input prevailing and operative temperature values. By default, this ouput is hidden and it should be connected it to a native Grasshopper preview component to view it.'
        output_node = self.outputs.new('SvLBSocket', 'data')
        output_node.tooltip = 'The input data_ with the input statements or the periods applied to it. These can be deconstructed with the "LB Deconstruct Data" component and the resulting values can be plugged into the "LB Create Legend" component to generate colors that can be used to color the points above using the native Grasshopper "Custom Preview" component.'
        output_node = self.outputs.new('SvLBSocket', 'vis_set')
        output_node.tooltip = 'An object containing VisualizationSet arguments for drawing a detailed version of the Adaptive Chart in the Rhino scene. This can be connected to the "LB Preview Visualization Set" component to display this version of the Adaptive Chart in Rhino.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Draw an adaptive comfort chart in the Rhino scene and plot a set of prevailing and indoor operative temperature values on it. _ Connected data can include outdoor temperatures from imported EPW weather data as well as indoor temperatures from an energy simulation. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['total_comfort', 'comfort_data', 'condition_data', 'polygon', 'title', 'prevail_lines', 'operative_lines', 'mesh', 'legend', 'points', 'data', 'vis_set']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_out_temp', '_air_temp', '_mrt_', '_air_speed_', 'adapt_par_', '_base_pt_', '_scale_', '_prevail_range_', '_operat_range_', 'legend_par_', 'data_', 'statement_', 'period_']
        self.sv_input_types = ['System.Object', 'System.Object', 'System.Object', 'System.Object', 'System.Object', 'Point3d', 'double', 'Interval', 'Interval', 'System.Object', 'System.Object', 'string', 'System.Object']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['list', 'list', 'list', 'item', 'item', 'item', 'item', 'item', 'item', 'list', 'list', 'item', 'item']
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

    def process_ladybug(self, _out_temp, _air_temp, _mrt_, _air_speed_, adapt_par_, _base_pt_, _scale_, _prevail_range_, _operat_range_, legend_par_, data_, statement_, period_):

        try:
            from ladybug_geometry.geometry2d import Point2D, Vector2D, LineSegment2D
            from ladybug_geometry.geometry3d import Point3D, Vector3D, Plane
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug.datacollection import BaseCollection
            from ladybug.datatype.temperature import PrevailingOutdoorTemperature
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_comfort.chart.adaptive import AdaptiveChart
            from ladybug_comfort.parameter.adaptive import AdaptiveParameter
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_comfort:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import conversion_to_meters
            from ladybug_tools.togeometry import to_point2d, to_point3d
            from ladybug_tools.fromgeometry import from_mesh2d, from_polygon2d, \
                from_polyline2d, from_linesegment2d, from_point2d, \
                from_polyline2d_to_offset_brep
            from ladybug_tools.text import text_objects
            from ladybug_tools.fromobjects import legend_objects
            from ladybug_tools.sverchok import all_required_inputs, list_to_data_tree, \
                hide_output, longest_list, objectify_output
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        def leg_par_by_index(i):
            """Get legend parameters associated with a given index of the chart."""
            try:
                return legend_par_[i]
            except IndexError:
                return None
        
        
        def small_labels(adapt_chart, labels, points, x_align, y_align, factor=1.0):
            """Translate a list of psych chart text labels into the Blender Ladybug scene."""
            return [text_objects(txt, Plane(o=Point3D(pt.x, pt.y, z)),
                                 adapt_chart.legend_parameters.text_height * factor,
                                 adapt_chart.legend_parameters.font, x_align, y_align)
                    for txt, pt in zip(labels, points)]
        
        
        def plane_from_point(point_2d, align_vec=Vector3D(1, 0, 0)):
            """Get a Plane from a Point2D.
        
            Args:
                point_2d: A Point2D to serve as the origin of the plane.
                align_vec: A Vector3D to serve as the X-Axis of the plane.
            """
            return Plane(o=Point3D(point_2d.x, point_2d.y, z), x=align_vec)
        
        
        def draw_adapt_chart(adapt_chart):
            """Draw a given adaptive chart object into Blender Ladybug geometry.
        
            This will NOT translate any colored meshes or data points.
            """
            # output the comfort polygon and neutral lines
            polygon_i = [from_polyline2d_to_offset_brep([adapt_chart.comfort_polygon], offset, z)]
            nl = adapt_chart.neutral_polyline
            if isinstance(nl, LineSegment2D):
                polygon_i.append(from_linesegment2d(nl, z))
            else:
                polygon_i.append(from_polyline2d(nl, z))
        
            # output all of the lines/polylines for the various axes
            title_i = [from_polygon2d(adapt_chart.chart_border, z)]
            prev_lines_i = [from_linesegment2d(tpl, z) for tpl in adapt_chart.prevailing_lines]
            op_lines_i = [from_linesegment2d(tol, z) for tol in adapt_chart.operative_lines]
        
            # add the text to the various lines
            title_i.append(text_objects(
                adapt_chart.x_axis_text, plane_from_point(adapt_chart.x_axis_location),
                adapt_chart.legend_parameters.text_height * 1.5,
                adapt_chart.legend_parameters.font, 1, 0))
            title_i.append(text_objects(
                adapt_chart.y_axis_text, plane_from_point(adapt_chart.y_axis_location, Vector3D(0, 1)),
                adapt_chart.legend_parameters.text_height * 1.5,
                adapt_chart.legend_parameters.font, 1, 0))
            prev_lines_i = prev_lines_i + small_labels(
                adapt_chart, adapt_chart.prevailing_labels, adapt_chart.prevailing_label_points, 1, 0)
            op_lines_i = op_lines_i + small_labels(
                adapt_chart, adapt_chart.operative_labels, adapt_chart.operative_label_points, 0, 3)
        
            # add all of the objects to the base list
            polygon.append(polygon_i)
            title.append(title_i)
            prevail_lines.append(prev_lines_i)
            operative_lines.append(op_lines_i)
        
        
        if all_required_inputs(ghenv.Component):
            # process the base point
            bp = to_point2d(_base_pt_) if _base_pt_ is not None else Point2D()
            z = to_point3d(_base_pt_).z if _base_pt_ is not None else 0
        
            # create lists to be filled with objects
            total_comfort = []
            comfort_data = []
            condition_data = []
            polygon = []
            title = []
            prevail_lines = []
            operative_lines = []
            mesh = []
            legend = []
            points = []
            data_colls = []
            vis_set = []
        
            # loop through the input temperatures and humidity and plot psych charts
            for j, temperature in enumerate(_air_temp):
                # process the out_temp and mrt inputs
                out_temp = longest_list(_out_temp, j)
                mrt = None
                if len(_mrt_) != 0:
                    mrt = longest_list(_mrt_, j)
        
                # sense if the input temperature is in Farenheit
                use_ip = False
                if temperature.header.unit != 'C':  # convert to C and set chart to use_ip
                    temperature = temperature.to_si()
                    out_temp = out_temp.to_si()
                    if mrt is not None:
                        mrt = mrt.to_si()
                    use_ip = True
        
                # set default values for the chart dimensions
                adapt_par = adapt_par_ if adapt_par_ is not None else AdaptiveParameter()
                _scale_ = 1.0 if _scale_ is None else _scale_
                xy_dim = _scale_ * 2 / conversion_to_meters()
                xy_dim = xy_dim * (9 / 5) if use_ip else xy_dim
                offset = xy_dim * 0.25
                if use_ip:
                    tp_min, tp_max = (50, 92) if adapt_par.ashrae_or_en else (50, 86)
                    to_min, to_max = 58, 104
                else:
                    tp_min, tp_max = (10, 33) if adapt_par.ashrae_or_en else (10, 30)
                    to_min, to_max = 14, 40
                if _prevail_range_ is not None:
                    tp_min, tp_max = _prevail_range_
                if _operat_range_ is not None:
                    to_min, to_max = _operat_range_
                y_move_dist = -xy_dim * 0.04 * j
                base_pt = bp.move(Vector2D(0, y_move_dist))
        
                # apply any analysis periods and conditional statements to the input collections
                original_temperature = temperature
                all_data = data_ + [temperature]
                if mrt is not None:
                    all_data.append(mrt)
                if period_ is not None:
                    all_data = [coll.filter_by_analysis_period(period_) for coll in all_data]
                if statement_ is not None:
                    all_data = BaseCollection.filter_collections_by_statement(all_data, statement_)
        
                # create the adaptive chart object and draw it in the Blender Ladybug scene
                if mrt is not None:
                    mrt = all_data.pop(-1)
                adapt_chart = AdaptiveChart.from_air_and_rad_temp(
                    out_temp, all_data[-1], mrt, _air_speed_, adapt_par,
                    leg_par_by_index(0), base_pt, xy_dim, xy_dim,
                    tp_min, tp_max, to_min, to_max, use_ip=use_ip)
                draw_adapt_chart(adapt_chart)
                ttl_tp = adapt_chart.container.lower_title_location.move(
                    Vector3D(0, -adapt_chart.legend_parameters.text_height * 3))
                if z != 0:
                    ttl_tp = Plane(n=ttl_tp.n, o=Point3D(ttl_tp.o.x, ttl_tp.o.y, z), x=ttl_tp.x)
                title[j + j * len(data_)].append(text_objects(
                    adapt_chart.title_text, ttl_tp,
                    adapt_chart.legend_parameters.text_height * 1.5,
                    adapt_chart.legend_parameters.font, 0, 0))
                vs_args = [adapt_chart]
        
                # plot the data on the chart
                lb_points = adapt_chart.data_points
                points.append([from_point2d(pt) for pt in lb_points])
                hide_output(ghenv.Component, 10)
                mesh.append(from_mesh2d(adapt_chart.colored_mesh, z))
                leg = adapt_chart.legend
                if z != 0 and leg.legend_parameters.is_base_plane_default:
                    nl_par = leg.legend_parameters.duplicate()
                    m_vec = Vector3D(0, 0, z)
                    nl_par.base_plane = nl_par.base_plane.move(m_vec)
                    leg._legend_par = nl_par
                legend.append(legend_objects(leg))
        
                # process the comfort-related outputs
                total_comfort.append(adapt_chart.percent_comfortable)
                comfort_data.append(adapt_chart.is_comfortable)
                condition_data.append(adapt_chart.thermal_condition)
        
                # process any of the connected data into a legend and colors
                if len(data_) != 0:
                    data_colls.append(all_data[:-1])
                    move_dist = xy_dim * (adapt_chart.max_prevailing - adapt_chart.min_prevailing + 20)
                    vs_leg_par = []
                    for i, d in enumerate(all_data[:-1]):
                        # create a new adaptive chart offset from the original
                        new_pt = Point2D(base_pt.x + move_dist * (i + 1), base_pt.y)
                        adapt_chart = AdaptiveChart.from_air_and_rad_temp(
                            out_temp, all_data[-1], mrt, _air_speed_, adapt_par,
                            leg_par_by_index(0), new_pt, xy_dim, xy_dim,
                            tp_min, tp_max, to_min, to_max, use_ip=use_ip)
                        draw_adapt_chart(adapt_chart)
                        lb_mesh, container = adapt_chart.data_mesh(d, leg_par_by_index(i + 1))
                        mesh.append(from_mesh2d(lb_mesh, z))
                        leg = container.legend
                        vs_leg_par.append(leg.legend_parameters)
                        if z != 0 and leg.legend_parameters.is_base_plane_default:
                            nl_par = leg.legend_parameters.duplicate()
                            m_vec = Vector3D(0, 0, z)
                            nl_par.base_plane = nl_par.base_plane.move(m_vec)
                            leg._legend_par = nl_par
                        legend.append(legend_objects(leg))
                        move_vec = Vector2D(base_pt.x + move_dist * (i + 1), 0)
                        points.append([from_point2d(pt.move(move_vec)) for pt in lb_points])
        
                        # add a title for the new chart
                        title_items = ['Adaptive Chart'] +\
                            ['{} [{}]'.format(d.header.data_type, d.header.unit)] + \
                            ['{}: {}'.format(key, val) for key, val in list(d.header.metadata.items())]
                        ttl_tp = adapt_chart.container.lower_title_location.move(
                            Vector3D(0, -adapt_chart.legend_parameters.text_height * 3))
                        if z != 0:
                            ttl_tp = Plane(n=ttl_tp.n, o=Point3D(ttl_tp.o.x, ttl_tp.o.y, z), x=ttl_tp.x)
                        title[j + j * len(data_) + (i + 1)].append(text_objects(
                            '\n'.join(title_items), ttl_tp,
                            adapt_chart.legend_parameters.text_height * 1.5,
                            adapt_chart.legend_parameters.font, 0, 0))
                    vs_args.extend([all_data[:-2], vs_leg_par, z])
                else:
                    vs_args.extend([None, None, z])
                vis_set.append(vs_args)
        
            # upack all of the python matrices into data trees
            polygon = list_to_data_tree(polygon)
            title = list_to_data_tree(title)
            prevail_lines = list_to_data_tree(prevail_lines)
            operative_lines = list_to_data_tree(operative_lines)
            legend = list_to_data_tree(legend)
            points = list_to_data_tree(points)
            data = list_to_data_tree(data_colls)
        
            # output arguments for the visualization set
            vis_set = objectify_output('VisualizationSet Aruments [AdaptiveChart]', vis_set)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvAdaptiveChart)

def unregister():
    bpy.utils.unregister_class(SvAdaptiveChart)
