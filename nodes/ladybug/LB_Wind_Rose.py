import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvWindRose(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvWindRose'
    bl_label = 'LB Wind Rose'
    sv_icon = 'LB_WINDROSE'
    sv_north_: StringProperty(
        name='north_',
        update=updateNode,
        description='An optional number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. 90 is West and 270 is East. This can also be Vector for the direction to North')
    sv__data: StringProperty(
        name='_data',
        update=updateNode,
        description='A HourlyContinuousCollection or HourlyDiscontinuousCollection of values corresponding to the wind directions, which is "binned" by the direction intervals. This input usually consists of wind speed values, but is not limited to this data type. It can also be a list of data collections in which case multiple wind roses will be output.')
    sv__wind_direction: StringProperty(
        name='_wind_direction',
        update=updateNode,
        description='A HourlyContinuousCollection or HourlyDiscontinuousCollection of wind directions which will be used to "bin" the _data items for the windrose.')
    sv__dir_count_: StringProperty(
        name='_dir_count_',
        update=updateNode,
        description='Number that determines the number of directions to the wind rose will display. The number of directions must be greater then three to plot the wind rose (Default: 36).')
    sv__center_pt_: StringProperty(
        name='_center_pt_',
        update=updateNode,
        description='Point3D to be used as a starting point to generate the geometry of the plot (Default: (0, 0, 0)).')
    sv_show_calm_: StringProperty(
        name='show_calm_',
        update=updateNode,
        description='A boolean to indicate if the wind rose should display the fraction of time with zero wind speed using a circle in the center of the plot. The radius of this circle corresponds to the total amount of time with zero values divided by the number of directions. This means that the time period representing zero values is evenly distrobuted across all directions. (Default: False).')
    sv_show_avg_: StringProperty(
        name='show_avg_',
        update=updateNode,
        description='A boolean to note whether the average value in each wind direction bin should be displayed instead of the complete frequency of _data values. (Default: False).')
    sv__freq_dist_: StringProperty(
        name='_freq_dist_',
        update=updateNode,
        description='The distance for the frequency interval in model units. If  show_calm_ is True, then the initial frequency interval corresponds to the number of calm hours in the data collection, which may not align with this freq_dist_ (Default: 5 meters)')
    sv__freq_hours_: StringProperty(
        name='_freq_hours_',
        update=updateNode,
        description='The number of hours in each frequency interval (Default: 50).')
    sv__max_freq_lines_: StringProperty(
        name='_max_freq_lines_',
        update=updateNode,
        description='A number representing the maximum frequency intervals in the rose, which determines the maximum amount of hours represented by the outermost ring of the windrose. Specifically, this number multiplied by the _freq_hours_ parameter will equal the maximum hours in that outermost ring. By default, this value is determined by the wind direction with the largest number of hours (the highest frequency) but you may want to change this if you have several wind roses that you want to compare to each other. For example, if you have wind roses for different months or seasons, which each have different maximum frequencies.')
    sv_legend_par_: StringProperty(
        name='legend_par_',
        update=updateNode,
        description='An optional LegendParameter object to change the display of the WindRose plot. The number of segments in the legend determines the number of frequency intervals in the wind rose. If nothing is provided, a default LegendParameter object is computed using values from the wind data with 11 segments (Default: None).')
    sv_statement_: StringProperty(
        name='statement_',
        update=updateNode,
        description='A conditional statement as a string (e.g. a > 25) for the _data and _wind_direction inputs. . The variable of the first collection input to _data should always be named \'a\' (without quotations), the variable of the second list should be named \'b\', and so on. The wind direction is always the last variable, though most statements won\'t have a need for it. . For example, if three data collections are connected to _data and the following statement is applied: \'18 < a < 26 and b < 80 and c > 2\' The resulting collections will only include values where the first data collection is between 18 and 26, the second collection is less than 80 and the third collection is greater than 2.')
    sv_period_: StringProperty(
        name='period_',
        update=updateNode,
        description='An optional Ladybug analysis period to be applied to all of the input data.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', 'north_')
        input_node.prop_name = 'sv_north_'
        input_node.tooltip = 'An optional number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. 90 is West and 270 is East. This can also be Vector for the direction to North'
        input_node = self.inputs.new('SvLBSocket', '_data')
        input_node.prop_name = 'sv__data'
        input_node.tooltip = 'A HourlyContinuousCollection or HourlyDiscontinuousCollection of values corresponding to the wind directions, which is "binned" by the direction intervals. This input usually consists of wind speed values, but is not limited to this data type. It can also be a list of data collections in which case multiple wind roses will be output.'
        input_node = self.inputs.new('SvLBSocket', '_wind_direction')
        input_node.prop_name = 'sv__wind_direction'
        input_node.tooltip = 'A HourlyContinuousCollection or HourlyDiscontinuousCollection of wind directions which will be used to "bin" the _data items for the windrose.'
        input_node = self.inputs.new('SvLBSocket', '_dir_count_')
        input_node.prop_name = 'sv__dir_count_'
        input_node.tooltip = 'Number that determines the number of directions to the wind rose will display. The number of directions must be greater then three to plot the wind rose (Default: 36).'
        input_node = self.inputs.new('SvLBSocket', '_center_pt_')
        input_node.prop_name = 'sv__center_pt_'
        input_node.tooltip = 'Point3D to be used as a starting point to generate the geometry of the plot (Default: (0, 0, 0)).'
        input_node = self.inputs.new('SvLBSocket', 'show_calm_')
        input_node.prop_name = 'sv_show_calm_'
        input_node.tooltip = 'A boolean to indicate if the wind rose should display the fraction of time with zero wind speed using a circle in the center of the plot. The radius of this circle corresponds to the total amount of time with zero values divided by the number of directions. This means that the time period representing zero values is evenly distrobuted across all directions. (Default: False).'
        input_node = self.inputs.new('SvLBSocket', 'show_avg_')
        input_node.prop_name = 'sv_show_avg_'
        input_node.tooltip = 'A boolean to note whether the average value in each wind direction bin should be displayed instead of the complete frequency of _data values. (Default: False).'
        input_node = self.inputs.new('SvLBSocket', '_freq_dist_')
        input_node.prop_name = 'sv__freq_dist_'
        input_node.tooltip = 'The distance for the frequency interval in model units. If  show_calm_ is True, then the initial frequency interval corresponds to the number of calm hours in the data collection, which may not align with this freq_dist_ (Default: 5 meters)'
        input_node = self.inputs.new('SvLBSocket', '_freq_hours_')
        input_node.prop_name = 'sv__freq_hours_'
        input_node.tooltip = 'The number of hours in each frequency interval (Default: 50).'
        input_node = self.inputs.new('SvLBSocket', '_max_freq_lines_')
        input_node.prop_name = 'sv__max_freq_lines_'
        input_node.tooltip = 'A number representing the maximum frequency intervals in the rose, which determines the maximum amount of hours represented by the outermost ring of the windrose. Specifically, this number multiplied by the _freq_hours_ parameter will equal the maximum hours in that outermost ring. By default, this value is determined by the wind direction with the largest number of hours (the highest frequency) but you may want to change this if you have several wind roses that you want to compare to each other. For example, if you have wind roses for different months or seasons, which each have different maximum frequencies.'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'An optional LegendParameter object to change the display of the WindRose plot. The number of segments in the legend determines the number of frequency intervals in the wind rose. If nothing is provided, a default LegendParameter object is computed using values from the wind data with 11 segments (Default: None).'
        input_node = self.inputs.new('SvLBSocket', 'statement_')
        input_node.prop_name = 'sv_statement_'
        input_node.tooltip = 'A conditional statement as a string (e.g. a > 25) for the _data and _wind_direction inputs. . The variable of the first collection input to _data should always be named \'a\' (without quotations), the variable of the second list should be named \'b\', and so on. The wind direction is always the last variable, though most statements won\'t have a need for it. . For example, if three data collections are connected to _data and the following statement is applied: \'18 < a < 26 and b < 80 and c > 2\' The resulting collections will only include values where the first data collection is between 18 and 26, the second collection is less than 80 and the third collection is greater than 2.'
        input_node = self.inputs.new('SvLBSocket', 'period_')
        input_node.prop_name = 'sv_period_'
        input_node.tooltip = 'An optional Ladybug analysis period to be applied to all of the input data.'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'A colored mesh representing the wind rose derived from the input data. Multiple meshes will be output for several data collections are input.'
        output_node = self.outputs.new('SvLBSocket', 'compass')
        output_node.tooltip = 'A set of circles, lines and text objects that mark the cardinal directions in relation to the wind rose.'
        output_node = self.outputs.new('SvLBSocket', 'orient_line')
        output_node.tooltip = 'Line geometries representing the edges (or "spokes") of the wind rose directions.'
        output_node = self.outputs.new('SvLBSocket', 'freq_line')
        output_node.tooltip = 'Polygon geometries representing the frequency intervals of the wind rose.'
        output_node = self.outputs.new('SvLBSocket', 'windrose_line')
        output_node.tooltip = 'Polygon geometries representing the windrose outlines. This output is hidden by default and should be connected to a native Grasshopper Geometry component in order to be visualized.'
        output_node = self.outputs.new('SvLBSocket', 'legend')
        output_node.tooltip = 'Geometry representing the legend for the wind rose.'
        output_node = self.outputs.new('SvLBSocket', 'title')
        output_node.tooltip = 'A text object for the global_title.'
        output_node = self.outputs.new('SvLBSocket', 'prevailing')
        output_node.tooltip = 'The predominant direction of the outpt wind rose in clockwise degrees from north. 0 is North, 90 is East, 180 is South, 270 is West.'
        output_node = self.outputs.new('SvLBSocket', 'angles')
        output_node.tooltip = 'A list of angles corresponding to each windrose directions.'
        output_node = self.outputs.new('SvLBSocket', 'calm_hours')
        output_node.tooltip = 'The number of hours with calm wind speeds. Only returns a value if the input _data is wind speed.'
        output_node = self.outputs.new('SvLBSocket', 'histogram')
        output_node.tooltip = 'The input _data in a histogram structure after it has gone through any of  the statement or period operations input to this component.'
        output_node = self.outputs.new('SvLBSocket', 'vis_set')
        output_node.tooltip = 'An object containing VisualizationSet arguments for drawing a detailed version of the Wind Rose in the Rhino scene. This can be connected to the "LB Preview Visualization Set" component to display this version of the Wind Rose in Rhino.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Create a plot of any hourly data by wind directions. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['mesh', 'compass', 'orient_line', 'freq_line', 'windrose_line', 'legend', 'title', 'prevailing', 'angles', 'calm_hours', 'histogram', 'vis_set']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['north_', '_data', '_wind_direction', '_dir_count_', '_center_pt_', 'show_calm_', 'show_avg_', '_freq_dist_', '_freq_hours_', '_max_freq_lines_', 'legend_par_', 'statement_', 'period_']
        self.sv_input_types = ['System.Object', 'System.Object', 'System.Object', 'int', 'Point3d', 'bool', 'bool', 'double', 'int', 'int', 'System.Object', 'string', 'System.Object']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'list', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'list', 'item', 'item']
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

    def process_ladybug(self, north_, _data, _wind_direction, _dir_count_, _center_pt_, show_calm_, show_avg_, _freq_dist_, _freq_hours_, _max_freq_lines_, legend_par_, statement_, period_):

        import math
        
        try:
            from ladybug.datacollection import HourlyContinuousCollection
            from ladybug.windrose import WindRose
            from ladybug.datatype.speed import Speed
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_geometry.geometry2d.pointvector import Point2D, Vector2D
            from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import conversion_to_meters
            from ladybug_tools.togeometry import to_point3d, to_vector2d
            from ladybug_tools.fromgeometry import from_mesh2d, from_linesegment2d, \
                from_polygon2d
            from ladybug_tools.text import text_objects
            from ladybug_tools.fromobjects import legend_objects, compass_objects
            from ladybug_tools.sverchok import all_required_inputs, list_to_data_tree, \
                objectify_output, hide_output
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        def title_text(data_col):
            """Get a text string for the title of the windrose."""
            title_array = ['{} ({})'.format(data_col.header.data_type,
                                            data_col.header.unit)]
            for key, val in list(data_col.header.metadata.items()):
                title_array.append('{}: {}'.format(key, val))
            title_array.append('period: {}'.format(data_col.header.analysis_period))
            return '\n'.join(title_array)
        
        
        if all_required_inputs(ghenv.Component):
            # Apply any analysis periods and conditional statement to the input collections
            if period_ is not None:
                _data = [dat.filter_by_analysis_period(period_) for dat in _data]
                _wind_direction = _wind_direction.filter_by_analysis_period(period_)
            if statement_ is not None and statement_.strip() != "":
                _fdata = HourlyContinuousCollection.filter_collections_by_statement(
                    _data + [_wind_direction], statement_)
                _data = _fdata[:-1]
                _wind_direction = _fdata[-1]
        
            # filter zero speed values out of collections if the speed is input
            pattern = []
            filt_wind_dir = _wind_direction
            for dat in _data:
                if isinstance(dat.header.data_type, Speed):
                    for val in dat.values:
                        pat = True if val > 1e-10 else False
                        pattern.append(pat)
                    break
            if len(pattern) != 0:
                for i, dat in enumerate(_data):
                    if not isinstance(dat.header.data_type, Speed):
                        _data[i] = dat.filter_by_pattern(pattern)
                filt_wind_dir = _wind_direction.filter_by_pattern(pattern)
        
            # check errors in dir_count and process the north input
            _dir_count_ = 36 if _dir_count_ is None else _dir_count_
            assert _dir_count_ > 2, 'The number of directions must be greater than 3 ' \
                'to plot the wind rose. Got: {}'.format(_dir_count_)
            if north_ is not None:  # process the north_
                try:
                    north_ = math.degrees(to_vector2d(north_).angle_clockwise(Vector2D(0, 1)))
                except AttributeError:  # north angle instead of vector
                    north_ = float(north_)
                    assert -360.0 <= north_ <= 360.0, 'The north orientation must be greater ' \
                        'then -360 and less then 360 to plot the wind rose. ' \
                        'Got: {}'.format(north_)
            else:
                north_ = 0.0
        
            # set default values for the center point
            _center_pt_ = to_point3d(_center_pt_) if _center_pt_ is not None else Point3D()
            center_pt_2d = Point2D(_center_pt_.x, _center_pt_.y)
        
            # set defaults frequency hours and distance so chart is same scale as other LB plots
            if _freq_hours_ is None:
                _freq_hours_ = 50.0
            if _freq_dist_ is None:
                _freq_dist_ = 5.0 / conversion_to_meters()
        
            # set default show_freq and show_calm_
            show_calm_ = False if show_calm_ is None else show_calm_
            show_freq_ = True if show_avg_ is None else not show_avg_
        
            # set up empty lists of objects to be filled
            all_windrose_lines = []
            mesh = []
            all_compass = []
            all_orient_line = []
            all_freq_line = []
            all_legends = []
            title = []
            calm_hours = []
            histogram = []
        
            # Calculate _max_freq_lines_ if it's not already set, to use to
            # determine spacing for multiple plots.
            if len(_data) > 1 and _max_freq_lines_ is None:
                max_freqs = []
                for i, _data_item in enumerate(_data):
                    win_dir = _wind_direction if isinstance(_data_item.header.data_type, Speed) \
                        else filt_wind_dir
                    w = WindRose(win_dir, _data_item, _dir_count_)
                    w.frequency_hours = _freq_hours_
                    w.frequency_spacing_distance = _freq_dist_
                    max_freqs.append(w.frequency_intervals_compass)
                _max_freq_lines_ = max(max_freqs)
        
            # plot the windroses
            all_windroses = []
            for i, speed_data in enumerate(_data):
                # make the windrose
                win_dir = _wind_direction if isinstance(speed_data.header.data_type, Speed) \
                    else filt_wind_dir
                windrose = WindRose(win_dir, speed_data, _dir_count_)
                all_windroses.append(windrose)
        
                # set the wind rose properties
                if len(legend_par_) > 0:
                    try:  # sense when several legend parameters are connected
                        lpar = legend_par_[i]
                    except IndexError:
                        lpar = legend_par_[-1]
                    windrose.legend_parameters = lpar
                windrose.frequency_hours = _freq_hours_
                if _max_freq_lines_ is not None:
                    windrose.frequency_intervals_compass = _max_freq_lines_
                windrose.frequency_spacing_distance = _freq_dist_
                windrose.north = north_
                windrose.show_freq = show_freq_
        
                calm_text = ''
                if isinstance(speed_data.header.data_type, Speed):
                    windrose.show_zeros = show_calm_
                    calm_text = '\nCalm for {}% of the time = {} hours.'.format(
                        round(windrose._zero_count / 
                        len(windrose.analysis_values) * 100.0, 2),
                        windrose._zero_count)
                windrose.base_point = Point2D(center_pt_2d.x, center_pt_2d.y)
        
                # Make the mesh
                msh = from_mesh2d(windrose.colored_mesh, _center_pt_.z)
        
                # Make the other graphic outputs
                lb_legend = windrose.legend
                ttl_pt = windrose.container.lower_title_location
                if _center_pt_.z != 0:
                    move_vec = Vector3D(0, 0, _center_pt_.z)
                    ttl_pt = ttl_pt.move(move_vec)
                    if lb_legend.legend_parameters.is_base_plane_default:
                        lb_legend = lb_legend.duplicate()
                        lb_legend.legend_parameters.base_plane = \
                            lb_legend.legend_parameters.base_plane.move(move_vec)
                legend = legend_objects(lb_legend)
                freq_per = windrose._frequency_hours / \
                    len([b for a in windrose.histogram_data for b in a])
                freq_text = '\nEach closed polyline shows frequency of {}% = {} hours.'.format(
                        round(freq_per * 100, 1), windrose._frequency_hours)
                titl = text_objects(title_text(speed_data) + calm_text + freq_text, ttl_pt,
                                    windrose.legend_parameters.text_height,
                                    windrose.legend_parameters.font)
                compass = compass_objects(windrose.compass, _center_pt_.z, None)
                orient_line = [from_linesegment2d(seg, _center_pt_.z)
                               for seg in windrose.orientation_lines]
                freq_line = [from_polygon2d(poly, _center_pt_.z) for poly in windrose.frequency_lines]
                windrose_lines = [from_polygon2d(poly, _center_pt_.z) for poly in windrose.windrose_lines]
                fac = (i + 1) * windrose.compass_radius * 3
                center_pt_2d = Point2D(_center_pt_.x + fac, _center_pt_.y)
        
                # collect everything to be output
                mesh.append(msh)
                all_compass.append(compass)
                all_orient_line.append(orient_line)
                all_freq_line.append(freq_line)
                all_windrose_lines.append(windrose_lines)
                all_legends.append(legend)
                title.append(titl)
                calm = windrose.zero_count if isinstance(speed_data.header.data_type, Speed) else None
                calm_hours.append(calm)
                histogram.append(objectify_output('WindRose {}'.format(i), windrose.histogram_data))
        
            # convert nested lists into data trees
            compass = list_to_data_tree(all_compass)
            orient_line = list_to_data_tree(all_orient_line)
            freq_line = list_to_data_tree(all_freq_line)
            windrose_line = list_to_data_tree(all_windrose_lines)
            legend = list_to_data_tree(all_legends)
            hide_output(ghenv.Component, 5)  # keep the devault visual simple
        
            # compute direction angles and prevailing direction
            theta = 180.0 / _dir_count_
            angles = [(angle + theta) % 360.0 for angle in windrose.angles[:-1]]
            prevailing = windrose.prevailing_direction
            vis_set = []
            for wr in all_windroses:
                vis_set.append(objectify_output('VisualizationSet Aruments [WindRose]', [wr, _center_pt_.z]))
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvWindRose)

def unregister():
    bpy.utils.unregister_class(SvWindRose)
