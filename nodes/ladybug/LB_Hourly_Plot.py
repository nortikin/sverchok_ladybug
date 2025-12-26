import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvHourlyPlot(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvHourlyPlot'
    bl_label = 'LB Hourly Plot'
    sv_icon = 'LB_HOURLYPLOT'
    sv__data: StringProperty(
        name='_data',
        update=updateNode,
        description='A HourlyContinuousCollection or HourlyDiscontinuousCollection which will be used to generate the hourly plot.')
    sv__base_pt_: StringProperty(
        name='_base_pt_',
        update=updateNode,
        description='An optional Point3D to be used as a starting point to generate the geometry of the plot (Default: (0, 0, 0)).')
    sv__x_dim_: StringProperty(
        name='_x_dim_',
        update=updateNode,
        description='A number to set the X dimension of the mesh cells (Default: 1 meters).')
    sv__y_dim_: StringProperty(
        name='_y_dim_',
        update=updateNode,
        description='A number to set the Y dimension of the mesh cells (Default: 4 meters).')
    sv__z_dim_: StringProperty(
        name='_z_dim_',
        update=updateNode,
        description='A number to set the Z dimension of the entire chart. This will be used to make the colored_mesh3d of the chart vary in the Z dimension according to the data. The value input here should usually be several times larger than the x_dim or y_dim in order to be noticable (e.g. 100). If 0, the colored_mesh3d will simply be flat. (Default: 0).')
    sv_reverse_y_: StringProperty(
        name='reverse_y_',
        update=updateNode,
        description='Boolean to note whether the Y-axis of the chart is reversed If True, time over the course of the day will flow from the top of the chart to the bottom instead of the bottom to the top.')
    sv_clock_24_: StringProperty(
        name='clock_24_',
        update=updateNode,
        description='Boolean to note whether the hour labels on the Y-Axis of the chart should be in 24-hour clock format (eg. 18:00) or they should be in 12-hour clock format (eg. 6PM).')
    sv_legend_par_: StringProperty(
        name='legend_par_',
        update=updateNode,
        description='An optional LegendParameter object to change the display of the HourlyPlot. This can also be a list of legend parameters to be applied to the different connected _data.')
    sv_statement_: StringProperty(
        name='statement_',
        update=updateNode,
        description='A conditional statement as a string (e.g. a > 25). . The variable of the first data collection should always be named \'a\' (without quotations), the variable of the second list should be named \'b\', and so on. . For example, if three data collections are connected to _data and the following statement is applied: \'18 < a < 26 and b < 80 and c > 2\' The resulting collections will only include values where the first data collection is between 18 and 26, the second collection is less than 80 and the third collection is greater than 2.')
    sv_period_: StringProperty(
        name='period_',
        update=updateNode,
        description='A Ladybug analysis period to be applied to all of the input _data.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_data')
        input_node.prop_name = 'sv__data'
        input_node.tooltip = 'A HourlyContinuousCollection or HourlyDiscontinuousCollection which will be used to generate the hourly plot.'
        input_node = self.inputs.new('SvLBSocket', '_base_pt_')
        input_node.prop_name = 'sv__base_pt_'
        input_node.tooltip = 'An optional Point3D to be used as a starting point to generate the geometry of the plot (Default: (0, 0, 0)).'
        input_node = self.inputs.new('SvLBSocket', '_x_dim_')
        input_node.prop_name = 'sv__x_dim_'
        input_node.tooltip = 'A number to set the X dimension of the mesh cells (Default: 1 meters).'
        input_node = self.inputs.new('SvLBSocket', '_y_dim_')
        input_node.prop_name = 'sv__y_dim_'
        input_node.tooltip = 'A number to set the Y dimension of the mesh cells (Default: 4 meters).'
        input_node = self.inputs.new('SvLBSocket', '_z_dim_')
        input_node.prop_name = 'sv__z_dim_'
        input_node.tooltip = 'A number to set the Z dimension of the entire chart. This will be used to make the colored_mesh3d of the chart vary in the Z dimension according to the data. The value input here should usually be several times larger than the x_dim or y_dim in order to be noticable (e.g. 100). If 0, the colored_mesh3d will simply be flat. (Default: 0).'
        input_node = self.inputs.new('SvLBSocket', 'reverse_y_')
        input_node.prop_name = 'sv_reverse_y_'
        input_node.tooltip = 'Boolean to note whether the Y-axis of the chart is reversed If True, time over the course of the day will flow from the top of the chart to the bottom instead of the bottom to the top.'
        input_node = self.inputs.new('SvLBSocket', 'clock_24_')
        input_node.prop_name = 'sv_clock_24_'
        input_node.tooltip = 'Boolean to note whether the hour labels on the Y-Axis of the chart should be in 24-hour clock format (eg. 18:00) or they should be in 12-hour clock format (eg. 6PM).'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'An optional LegendParameter object to change the display of the HourlyPlot. This can also be a list of legend parameters to be applied to the different connected _data.'
        input_node = self.inputs.new('SvLBSocket', 'statement_')
        input_node.prop_name = 'sv_statement_'
        input_node.tooltip = 'A conditional statement as a string (e.g. a > 25). . The variable of the first data collection should always be named \'a\' (without quotations), the variable of the second list should be named \'b\', and so on. . For example, if three data collections are connected to _data and the following statement is applied: \'18 < a < 26 and b < 80 and c > 2\' The resulting collections will only include values where the first data collection is between 18 and 26, the second collection is less than 80 and the third collection is greater than 2.'
        input_node = self.inputs.new('SvLBSocket', 'period_')
        input_node.prop_name = 'sv_period_'
        input_node.tooltip = 'A Ladybug analysis period to be applied to all of the input _data.'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'A colored mesh derived from the input _data. Multiple meshes will be output for several data collections are input.'
        output_node = self.outputs.new('SvLBSocket', 'legend')
        output_node.tooltip = 'Geometry representing the legend for each mesh.'
        output_node = self.outputs.new('SvLBSocket', 'borders')
        output_node.tooltip = 'A list of lines and polylines representing different time intervals of the plot.'
        output_node = self.outputs.new('SvLBSocket', 'labels')
        output_node.tooltip = 'A list of text objects that label the borders with the time intervals that they demarcate.'
        output_node = self.outputs.new('SvLBSocket', 'title')
        output_node.tooltip = 'A text object for the global_title.'
        output_node = self.outputs.new('SvLBSocket', 'vis_set')
        output_node.tooltip = 'An object containing VisualizationSet arguments for drawing a detailed version of the Hourly Plot in the Rhino scene. This can be connected to the "LB Preview Visualization Set" component to display this version of the Hourly Plot in Rhino.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Create a colored plot of any hourly data collection. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['mesh', 'legend', 'borders', 'labels', 'title', 'vis_set']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_data', '_base_pt_', '_x_dim_', '_y_dim_', '_z_dim_', 'reverse_y_', 'clock_24_', 'legend_par_', 'statement_', 'period_']
        self.sv_input_types = ['System.Object', 'Point3d', 'double', 'double', 'double', 'bool', 'bool', 'System.Object', 'string', 'System.Object']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['list', 'item', 'item', 'item', 'item', 'item', 'item', 'list', 'item', 'item']
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

    def process_ladybug(self, _data, _base_pt_, _x_dim_, _y_dim_, _z_dim_, reverse_y_, clock_24_, legend_par_, statement_, period_):

        try:
            from ladybug.datacollection import HourlyContinuousCollection
            from ladybug.hourlyplot import HourlyPlot
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_geometry.geometry3d.pointvector import Point3D
            from ladybug_geometry.geometry3d.plane import Plane
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import conversion_to_meters
            from ladybug_tools.togeometry import to_point3d
            from ladybug_tools.fromgeometry import from_mesh3d, from_mesh2d, \
                from_polyline2d, from_linesegment2d
            from ladybug_tools.text import text_objects
            from ladybug_tools.fromobjects import legend_objects
            from ladybug_tools.sverchok import all_required_inputs, list_to_data_tree, \
                objectify_output
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # apply any analysis periods and conditional statements to the input collections
            if period_ is not None:
                _data = [coll.filter_by_analysis_period(period_) for coll in _data]
            if statement_ is not None:
                _data = HourlyContinuousCollection.filter_collections_by_statement(
                    _data, statement_)
        
            # set default values for the chart dimensions
            _base_pt_ = to_point3d(_base_pt_) if _base_pt_ is not None else Point3D()
            _x_dim_ = _x_dim_ if _x_dim_ is not None else 1.0 / conversion_to_meters()
            _y_dim_ = _y_dim_ if _y_dim_ is not None else 4.0 / conversion_to_meters()
            _z_dim_ = _z_dim_ if _z_dim_ is not None else 0
            reverse_y_ = reverse_y_ if reverse_y_ is not None else False
        
            # empty lists of objects to be filled with visuals
            mesh, title, all_legends, all_borders, all_labels, vis_set = [], [], [], [], [], []
        
            for i, data_coll in enumerate(_data):
                try:  # sense when several legend parameters are connected
                    lpar = legend_par_[i]
                except IndexError:
                    lpar = None if len(legend_par_) == 0 else legend_par_[-1].duplicate()
        
                # create the hourly plot object and get the main pieces of geometry
                hour_plot = HourlyPlot(data_coll, lpar, _base_pt_,
                                       _x_dim_, _y_dim_, _z_dim_, reverse_y_)
                
                msh = from_mesh2d(hour_plot.colored_mesh2d, _base_pt_.z) if _z_dim_ == 0 else \
                    from_mesh3d(hour_plot.colored_mesh3d)
                mesh.append(msh)
                border = [from_polyline2d(hour_plot.chart_border2d, _base_pt_.z)] + \
                    [from_linesegment2d(line, _base_pt_.z) for line in hour_plot.hour_lines2d] + \
                    [from_linesegment2d(line, _base_pt_.z) for line in hour_plot.month_lines2d]
                all_borders.append(border)
                legnd = legend_objects(hour_plot.legend)
                all_legends.append(legnd)
                tit_txt = text_objects(hour_plot.title_text, hour_plot.lower_title_location,
                                       hour_plot.legend_parameters.text_height,
                                       hour_plot.legend_parameters.font)
                title.append(tit_txt)
        
                # create the text label objects
                hr_text = hour_plot.hour_labels_24 if clock_24_ else hour_plot.hour_labels
                label1 = [text_objects(txt, Plane(o=Point3D(pt.x, pt.y, _base_pt_.z)),
                                       hour_plot.legend_parameters.text_height,
                                       hour_plot.legend_parameters.font, 2, 3)
                          for txt, pt in zip(hr_text, hour_plot.hour_label_points2d)]
                label2 = [text_objects(txt, Plane(o=Point3D(pt.x, pt.y, _base_pt_.z)),
                                       hour_plot.legend_parameters.text_height,
                                       hour_plot.legend_parameters.font, 1, 0)
                          for txt, pt in zip(hour_plot.month_labels, hour_plot.month_label_points2d)]
                all_labels.append(label1 + label2)
        
                # increment the base point so that the next chart doesn't overlap this one
                try:
                    next_aper = _data[i + 1].header.analysis_period
                    next_tstep = next_aper.timestep
                    next_hour = next_aper.end_hour - next_aper.st_hour + 1
                except IndexError:
                    next_tstep = 1
                    next_hour = 24
                txt_dist = hour_plot.legend_parameters.text_height * (len(_data[i].header.metadata) + 6) * 1.5
                increment = (next_hour * next_tstep * _y_dim_) + txt_dist
                _base_pt_ = Point3D(_base_pt_.x, _base_pt_.y - increment, _base_pt_.z)
        
                # append the VisualizationSet arguments with fixed geometry
                hp_leg_par3d = hour_plot.legend_parameters.properties_3d
                hp_leg_par3d.base_plane = hp_leg_par3d.base_plane
                hp_leg_par3d.segment_height = hp_leg_par3d.segment_height
                hp_leg_par3d.segment_width = hp_leg_par3d.segment_width
                hp_leg_par3d.text_height = hp_leg_par3d.text_height
                vis_set.append((hour_plot, _base_pt_.z))
        
            # convert nexted lists into data trees
            legend = list_to_data_tree(all_legends)
            borders = list_to_data_tree(all_borders)
            labels = list_to_data_tree(all_labels)
            vis_set = objectify_output('VisualizationSet Aruments [HourlyPlot]', vis_set)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvHourlyPlot)

def unregister():
    bpy.utils.unregister_class(SvHourlyPlot)
