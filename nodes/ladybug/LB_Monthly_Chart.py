import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvMonthlyChart(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvMonthlyChart'
    bl_label = 'LB Monthly Chart'
    sv_icon = 'LB_MONTHLYCHART'
    sv__data: StringProperty(
        name='_data',
        update=updateNode,
        description='Data collections (eg. HourlyCollection, MonthlyCollection, or DailyCollection), which will be used to generate the monthly chart.')
    sv__base_pt_: StringProperty(
        name='_base_pt_',
        update=updateNode,
        description='An optional Point3D to be used as a starting point to generate the geometry of the chart (Default: (0, 0, 0)).')
    sv__x_dim_: StringProperty(
        name='_x_dim_',
        update=updateNode,
        description='An optional number to set the X dimension of each month of the chart. (Default: 10 meters).')
    sv__y_dim_: StringProperty(
        name='_y_dim_',
        update=updateNode,
        description='An optional number to set the Y dimension of the entire chart (Default: 40 meters).')
    sv_stack_: StringProperty(
        name='stack_',
        update=updateNode,
        description='Boolean to note whether multiple connected monthly or daily input _data with the same units should be stacked on top of each other. Otherwise, all bars for monthly/daily data will be placed next to each other.  (Default: False).')
    sv_percentile_: StringProperty(
        name='percentile_',
        update=updateNode,
        description='An optional number between 0 and 50 to be used for the percentile difference from the mean that hourly data meshes display at. For example, using 34 will generate hourly data meshes with a range of one standard deviation from the mean. Note that this input only has significance when the input data collections are hourly. (Default: 34)')
    sv_time_marks_: StringProperty(
        name='time_marks_',
        update=updateNode,
        description='Boolean to note whether the month labels should be replaced with marks for the time of day in each month. This is useful for displaying hourly data, particularly when the input data is only for a month and not the whole year.')
    sv_global_title_: StringProperty(
        name='global_title_',
        update=updateNode,
        description='A text string to label the entire entire chart.  It will be displayed in the lower left of the output chart.  The default will display the metadata of the input _data.')
    sv_y_axis_title_: StringProperty(
        name='y_axis_title_',
        update=updateNode,
        description='A text string to label the Y-axis of the chart.  This can also be a list of 2 Y-axis titles if there are two different types of data connected to _data and there are two axes labels on either side of the chart.  The default will display the data type and units of the first (and possibly the second) data collection connected to _data.')
    sv_legend_par_: StringProperty(
        name='legend_par_',
        update=updateNode,
        description='An optional LegendParameter object to change the display of the chart (Default: None).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_data')
        input_node.prop_name = 'sv__data'
        input_node.tooltip = 'Data collections (eg. HourlyCollection, MonthlyCollection, or DailyCollection), which will be used to generate the monthly chart.'
        input_node = self.inputs.new('SvLBSocket', '_base_pt_')
        input_node.prop_name = 'sv__base_pt_'
        input_node.tooltip = 'An optional Point3D to be used as a starting point to generate the geometry of the chart (Default: (0, 0, 0)).'
        input_node = self.inputs.new('SvLBSocket', '_x_dim_')
        input_node.prop_name = 'sv__x_dim_'
        input_node.tooltip = 'An optional number to set the X dimension of each month of the chart. (Default: 10 meters).'
        input_node = self.inputs.new('SvLBSocket', '_y_dim_')
        input_node.prop_name = 'sv__y_dim_'
        input_node.tooltip = 'An optional number to set the Y dimension of the entire chart (Default: 40 meters).'
        input_node = self.inputs.new('SvLBSocket', 'stack_')
        input_node.prop_name = 'sv_stack_'
        input_node.tooltip = 'Boolean to note whether multiple connected monthly or daily input _data with the same units should be stacked on top of each other. Otherwise, all bars for monthly/daily data will be placed next to each other.  (Default: False).'
        input_node = self.inputs.new('SvLBSocket', 'percentile_')
        input_node.prop_name = 'sv_percentile_'
        input_node.tooltip = 'An optional number between 0 and 50 to be used for the percentile difference from the mean that hourly data meshes display at. For example, using 34 will generate hourly data meshes with a range of one standard deviation from the mean. Note that this input only has significance when the input data collections are hourly. (Default: 34)'
        input_node = self.inputs.new('SvLBSocket', 'time_marks_')
        input_node.prop_name = 'sv_time_marks_'
        input_node.tooltip = 'Boolean to note whether the month labels should be replaced with marks for the time of day in each month. This is useful for displaying hourly data, particularly when the input data is only for a month and not the whole year.'
        input_node = self.inputs.new('SvLBSocket', 'global_title_')
        input_node.prop_name = 'sv_global_title_'
        input_node.tooltip = 'A text string to label the entire entire chart.  It will be displayed in the lower left of the output chart.  The default will display the metadata of the input _data.'
        input_node = self.inputs.new('SvLBSocket', 'y_axis_title_')
        input_node.prop_name = 'sv_y_axis_title_'
        input_node.tooltip = 'A text string to label the Y-axis of the chart.  This can also be a list of 2 Y-axis titles if there are two different types of data connected to _data and there are two axes labels on either side of the chart.  The default will display the data type and units of the first (and possibly the second) data collection connected to _data.'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'An optional LegendParameter object to change the display of the chart (Default: None).'
        output_node = self.outputs.new('SvLBSocket', 'data_mesh')
        output_node.tooltip = 'A list of colored meshes that represent the different input data. These meshes will resemble a bar chart in the case of monthly or daily data and will resemble a band between two ranges for hourly and sub-hourly data. Multiple lists of meshes will be output for several input data streams.'
        output_node = self.outputs.new('SvLBSocket', 'data_lines')
        output_node.tooltip = 'A list of polylines that represent the input data. These will represent the average or total at each hour whenever the input data is hourly or monthly-per-hour data.'
        output_node = self.outputs.new('SvLBSocket', 'col_lines')
        output_node.tooltip = 'A list of colored polylines that represent the input data. These will only be output when the input data are monthly per hour.'
        output_node = self.outputs.new('SvLBSocket', 'legend')
        output_node.tooltip = 'Geometry representing the legend for the chart, noting which colors correspond to which input data.'
        output_node = self.outputs.new('SvLBSocket', 'borders')
        output_node.tooltip = 'A list of lines and polylines representing the axes and intervals of the chart.'
        output_node = self.outputs.new('SvLBSocket', 'labels')
        output_node.tooltip = 'A list of text objects that label the borders with month name and the intervals of the Y-axis.'
        output_node = self.outputs.new('SvLBSocket', 'y_title')
        output_node.tooltip = 'A text oject for the Y-axis title.'
        output_node = self.outputs.new('SvLBSocket', 'title')
        output_node.tooltip = 'A text object for the global_title.'
        output_node = self.outputs.new('SvLBSocket', 'vis_set')
        output_node.tooltip = 'An object containing VisualizationSet arguments for drawing a detailed version of the Monthly Chart in the Rhino scene. This can be connected to the "LB Preview Visualization Set" component to display this version of the Monthly Chart in Rhino.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Create a chart in the Rhino scene with data organized by month. _ Data will display as a bar chart if the input data is monthly or daily. If the data is hourly or sub-hourly, it will be plotted with lines and/or a colored mesh that shows the range of the data within specific percentiles. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['data_mesh', 'data_lines', 'col_lines', 'legend', 'borders', 'labels', 'y_title', 'title', 'vis_set']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_data', '_base_pt_', '_x_dim_', '_y_dim_', 'stack_', 'percentile_', 'time_marks_', 'global_title_', 'y_axis_title_', 'legend_par_']
        self.sv_input_types = ['System.Object', 'Point3d', 'double', 'double', 'bool', 'double', 'bool', 'string', 'string', 'System.Object']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['list', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'list', 'list']
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

    def process_ladybug(self, _data, _base_pt_, _x_dim_, _y_dim_, stack_, percentile_, time_marks_, global_title_, y_axis_title_, legend_par_):

        try:
            from ladybug_geometry.geometry2d.pointvector import Point2D
            from ladybug_geometry.geometry3d.pointvector import Vector3D, Point3D
            from ladybug_geometry.geometry3d.plane import Plane
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug.monthlychart import MonthlyChart
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import conversion_to_meters, tolerance
            from ladybug_tools.color import color_to_color
            from ladybug_tools.togeometry import to_point2d
            from ladybug_tools.fromgeometry import from_mesh2d, from_mesh2d_to_outline, \
                from_polyline2d, from_linesegment2d
            from ladybug_tools.text import text_objects
            from ladybug_tools.colorize import ColoredPolyline
            from ladybug_tools.fromobjects import legend_objects
            from ladybug_tools.sverchok import all_required_inputs, objectify_output, \
                schedule_solution
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component) and None not in _data:
            # set default values for the chart dimensions
            z_val = _base_pt_.Z if _base_pt_ is not None else 0
            z_val_tol = z_val + tolerance
            _base_pt_ = to_point2d(_base_pt_) if _base_pt_ is not None else Point2D()
            _x_dim_ = _x_dim_ if _x_dim_ is not None else 10.0 / conversion_to_meters()
            _y_dim_ = _y_dim_ if _y_dim_ is not None else 40.0 / conversion_to_meters()
            stack_ = stack_ if stack_ is not None else False
            percentile_ = percentile_ if percentile_ is not None else 34.0
            lpar = legend_par_[0] if len(legend_par_) != 0 else None
        
            # create the monthly chart object and get the main pieces of geometry
            month_chart = MonthlyChart(_data, lpar, _base_pt_, _x_dim_, _y_dim_,
                                       stack_, percentile_)
            if len(legend_par_) > 1:
                if legend_par_[1].min is not None:
                    month_chart.set_minimum_by_index(legend_par_[1].min, 1)
                if legend_par_[1].max is not None:
                    month_chart.set_maximum_by_index(legend_par_[1].max, 1)
        
            #  get the main pieces of geometry
            data_lines = []
            d_meshes = month_chart.data_meshes
            if d_meshes is not None:
                data_mesh = [from_mesh2d(msh, z_val_tol) for msh in d_meshes]
                if month_chart.time_interval == 'Monthly':
                    data_lines += [l for msh in d_meshes for l in
                                   from_mesh2d_to_outline(msh, z_val_tol)]
            d_lines = month_chart.data_polylines
            if d_lines is not None:
                data_lines += [from_polyline2d(lin, z_val_tol) for lin in d_lines]
            borders = [from_polyline2d(month_chart.chart_border, z_val)] + \
                    [from_linesegment2d(line, z_val) for line in month_chart.y_axis_lines] + \
                    [from_linesegment2d(line, z_val_tol) for line in month_chart.month_lines]
            leg = month_chart.legend
            if z_val != 0 and leg.legend_parameters.is_base_plane_default:
                nl_par = leg.legend_parameters.duplicate()
                m_vec = Vector3D(0, 0, z_val)
                nl_par.base_plane = nl_par.base_plane.move(m_vec)
                leg._legend_par = nl_par
            legend = legend_objects(leg)
        
            # process all of the text-related outputs
            title_txt = month_chart.title_text if global_title_ is None else global_title_
            txt_hgt = month_chart.legend_parameters.text_height
            font = month_chart.legend_parameters.font
            ttl_tp = month_chart.lower_title_location
            if z_val != 0:
                ttl_tp = Plane(n=ttl_tp.n, o=Point3D(ttl_tp.o.x, ttl_tp.o.y, z_val), x=ttl_tp.x)
            title = text_objects(title_txt, ttl_tp, txt_hgt, font)
        
            # process the first y axis
            y1_txt = month_chart.y_axis_title_text1 if len(y_axis_title_) == 0 else y_axis_title_[0]
            y1_tp = month_chart.y_axis_title_location1
            if z_val != 0:
                y1_tp = Plane(n=y1_tp.n, o=Point3D(y1_tp.o.x, y1_tp.o.y, z_val), x=y1_tp.x)
            y_title = text_objects(y1_txt, y1_tp, txt_hgt, font)
            if time_marks_:
                txt_h = _x_dim_ / 20 if _x_dim_ / 20 < txt_hgt * 0.75 else txt_hgt * 0.75
                label1 = [text_objects(txt, Plane(o=Point3D(pt.x, pt.y, z_val)), txt_h, font, 1, 0)
                          for txt, pt in zip(month_chart.time_labels, month_chart.time_label_points)]
                borders.extend([from_linesegment2d(line, z_val_tol) for line in month_chart.time_ticks])
            else:
                label1 = [text_objects(txt, Plane(o=Point3D(pt.x, pt.y, z_val)), txt_hgt, font, 1, 0)
                          for txt, pt in zip(month_chart.month_labels, month_chart.month_label_points)]
            label2 = [text_objects(txt, Plane(o=Point3D(pt.x, pt.y, z_val)), txt_hgt, font, 2, 3)
                      for txt, pt in zip(month_chart.y_axis_labels1, month_chart.y_axis_label_points1)]
            labels = label1 + label2
        
            # process the second y axis if it exists
            if month_chart.y_axis_title_text2 is not None:
                y2_txt = month_chart.y_axis_title_text2 if len(y_axis_title_) <= 1 else y_axis_title_[1]
                y2_tp = month_chart.y_axis_title_location2
                if z_val != 0:
                    y2_tp = Plane(n=y2_tp.n, o=Point3D(y2_tp.o.x, y2_tp.o.y, z_val), x=y2_tp.x)
                y_title2 = text_objects(y2_txt, y2_tp, txt_hgt, font)
                y_title = [y_title, y_title2]
                label3 = [text_objects(txt, Plane(o=Point3D(pt.x, pt.y, z_val)), txt_hgt, font, 0, 3)
                         for txt, pt in zip(month_chart.y_axis_labels2, month_chart.y_axis_label_points2)]
                labels = labels + label3
        
            # if there are colored lines, then process them to be output from the component
            if month_chart.time_interval == 'MonthlyPerHour':
                cols = [color_to_color(col) for col in month_chart.colors]
                col_lines, month_count = [], len(data_lines) / len(_data)
                for i, pline in enumerate(data_lines):
                    col_line = ColoredPolyline(pline)
                    col_line.color = cols[int(i / month_count)]
                    col_line.thickness = 3
                    col_lines.append(col_line)
                # CWM: I don't know why we have to re-schedule the solution but this is the
                # only way I found to get the colored polylines to appear (redraw did not work).
                schedule_solution(ghenv.Component, 2)
        
            # output arguments for the visualization set
            vis_set = [month_chart, z_val, time_marks_, global_title_, y_axis_title_]
            vis_set = objectify_output('VisualizationSet Aruments [MonthlyChart]', vis_set)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvMonthlyChart)

def unregister():
    bpy.utils.unregister_class(SvMonthlyChart)
