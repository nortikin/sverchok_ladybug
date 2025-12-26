import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvWindProfile(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvWindProfile'
    bl_label = 'LB Wind Profile'
    sv_icon = 'LB_WINDPROFILE'
    sv_north_: StringProperty(
        name='north_',
        update=updateNode,
        description='A number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. 90 is West and 270 is East. This can also be Vector for the direction to North. (Default: 0)')
    sv__met_wind_vel: StringProperty(
        name='_met_wind_vel',
        update=updateNode,
        description='A data collection of meteorological wind speed measured at the _met_height_ with the _met_terrian [m/s]. Typically, this comes from the "LB Import EPW" component. This can also be a single number for the meteorological wind speed in m/s.')
    sv_met_wind_dir_: StringProperty(
        name='met_wind_dir_',
        update=updateNode,
        description='An optional number between 0 and 360 representing the degrees from north that the meteorological wind is blowing. 0 = North, 90 = East, 180 = South, 270 = West. This can also a data collection of meteorological wind directions. in which case the wind profile will be oriented towards the prevailing wind (unless a profile_dir_ is connected). When unspecified, the wind profile is simply drawn in the XY plane.')
    sv_profile_dir_: StringProperty(
        name='profile_dir_',
        update=updateNode,
        description='An optional text string representing the cardinal direction that the wind profile represents. This input only has an effect when a data collection is connected for met_wind_dir_. It will be used to draw a wind profile for only the hours of the data collection where the wind is blowing in the specified direction. This can also be an integer that codes for a particular orientation. Choose from the following. _ 0 = N 1 = NE 2 = E 3 = SE 4 = S 5 = SW 6 = W 7 = NW')
    sv__terrain_: StringProperty(
        name='_terrain_',
        update=updateNode,
        description='Text string that sets the terrain class associated with the wind profile. This can also be an integer that codes for the terrain. (Default: city). Must be one the following. _ 0 = city - 50% of buildings above 21m over a distance of at least 2000m upwind. 1 = suburban - suburbs, wooded areas. 2 = country - open, with scattered objects generally less than 10m high. 3 = water - flat areas downwind of a large water body (max 500m inland).')
    sv__met_height_: StringProperty(
        name='_met_height_',
        update=updateNode,
        description='A number for the height above the ground at which the meteorological wind speed is measured in meters. (Default: 10 meters, which is the standard used by most airports and EPW files).')
    sv__met_terrain_: StringProperty(
        name='_met_terrain_',
        update=updateNode,
        description='Text string that sets the terrain class associated with the meteorological wind speed. This can also be an integer that codes for the terrain. (Default: country, which is typical of most airports where wind measurements are taken). Must be one the following. _ 0 = city - 50% of buildings above 21m over a distance of at least 2000m upwind. 1 = suburban - suburbs, wooded areas. 2 = country - open, with scattered objects generally less than 10m high. 3 = water - flat areas downwind of a large water body (max 500m inland).')
    sv_log_law_: StringProperty(
        name='log_law_',
        update=updateNode,
        description='A boolean to note whether the wind profile should use a logarithmic law to determine wind speeds instead of the default power law, which is used by EnergyPlus. (Default: False).')
    sv__base_pt_: StringProperty(
        name='_base_pt_',
        update=updateNode,
        description='A point that sets the ground level frm which the wind profile is drawn. By default, the profile is generated at the scene origin.')
    sv__max_speed_: StringProperty(
        name='_max_speed_',
        update=updateNode,
        description='Script variable WindProfile')
    sv__profile_height_: StringProperty(
        name='_profile_height_',
        update=updateNode,
        description='A number in meters to specify the maximum height of the wind profile. (Default: 30 meters).')
    sv__vec_spacing_: StringProperty(
        name='_vec_spacing_',
        update=updateNode,
        description='A number in meters to specify the difference in height between each of the mesh arrows. (Default 2 meters).')
    sv__vec_scale_: StringProperty(
        name='_vec_scale_',
        update=updateNode,
        description='A number to denote the length dimension of a 1 m/s wind vector in meters. This can be used to change the scale of the wind vector meshes in relation to the height of the wind profile curve. (Default: 5 meters).')
    sv_legend_par_: StringProperty(
        name='legend_par_',
        update=updateNode,
        description='An optional LegendParameter object to change the display of the wind profile.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', 'north_')
        input_node.prop_name = 'sv_north_'
        input_node.tooltip = 'A number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. 90 is West and 270 is East. This can also be Vector for the direction to North. (Default: 0)'
        input_node = self.inputs.new('SvLBSocket', '_met_wind_vel')
        input_node.prop_name = 'sv__met_wind_vel'
        input_node.tooltip = 'A data collection of meteorological wind speed measured at the _met_height_ with the _met_terrian [m/s]. Typically, this comes from the "LB Import EPW" component. This can also be a single number for the meteorological wind speed in m/s.'
        input_node = self.inputs.new('SvLBSocket', 'met_wind_dir_')
        input_node.prop_name = 'sv_met_wind_dir_'
        input_node.tooltip = 'An optional number between 0 and 360 representing the degrees from north that the meteorological wind is blowing. 0 = North, 90 = East, 180 = South, 270 = West. This can also a data collection of meteorological wind directions. in which case the wind profile will be oriented towards the prevailing wind (unless a profile_dir_ is connected). When unspecified, the wind profile is simply drawn in the XY plane.'
        input_node = self.inputs.new('SvLBSocket', 'profile_dir_')
        input_node.prop_name = 'sv_profile_dir_'
        input_node.tooltip = 'An optional text string representing the cardinal direction that the wind profile represents. This input only has an effect when a data collection is connected for met_wind_dir_. It will be used to draw a wind profile for only the hours of the data collection where the wind is blowing in the specified direction. This can also be an integer that codes for a particular orientation. Choose from the following. _ 0 = N 1 = NE 2 = E 3 = SE 4 = S 5 = SW 6 = W 7 = NW'
        input_node = self.inputs.new('SvLBSocket', '_terrain_')
        input_node.prop_name = 'sv__terrain_'
        input_node.tooltip = 'Text string that sets the terrain class associated with the wind profile. This can also be an integer that codes for the terrain. (Default: city). Must be one the following. _ 0 = city - 50% of buildings above 21m over a distance of at least 2000m upwind. 1 = suburban - suburbs, wooded areas. 2 = country - open, with scattered objects generally less than 10m high. 3 = water - flat areas downwind of a large water body (max 500m inland).'
        input_node = self.inputs.new('SvLBSocket', '_met_height_')
        input_node.prop_name = 'sv__met_height_'
        input_node.tooltip = 'A number for the height above the ground at which the meteorological wind speed is measured in meters. (Default: 10 meters, which is the standard used by most airports and EPW files).'
        input_node = self.inputs.new('SvLBSocket', '_met_terrain_')
        input_node.prop_name = 'sv__met_terrain_'
        input_node.tooltip = 'Text string that sets the terrain class associated with the meteorological wind speed. This can also be an integer that codes for the terrain. (Default: country, which is typical of most airports where wind measurements are taken). Must be one the following. _ 0 = city - 50% of buildings above 21m over a distance of at least 2000m upwind. 1 = suburban - suburbs, wooded areas. 2 = country - open, with scattered objects generally less than 10m high. 3 = water - flat areas downwind of a large water body (max 500m inland).'
        input_node = self.inputs.new('SvLBSocket', 'log_law_')
        input_node.prop_name = 'sv_log_law_'
        input_node.tooltip = 'A boolean to note whether the wind profile should use a logarithmic law to determine wind speeds instead of the default power law, which is used by EnergyPlus. (Default: False).'
        input_node = self.inputs.new('SvLBSocket', '_base_pt_')
        input_node.prop_name = 'sv__base_pt_'
        input_node.tooltip = 'A point that sets the ground level frm which the wind profile is drawn. By default, the profile is generated at the scene origin.'
        input_node = self.inputs.new('SvLBSocket', '_max_speed_')
        input_node.prop_name = 'sv__max_speed_'
        input_node.tooltip = 'Script variable WindProfile'
        input_node = self.inputs.new('SvLBSocket', '_profile_height_')
        input_node.prop_name = 'sv__profile_height_'
        input_node.tooltip = 'A number in meters to specify the maximum height of the wind profile. (Default: 30 meters).'
        input_node = self.inputs.new('SvLBSocket', '_vec_spacing_')
        input_node.prop_name = 'sv__vec_spacing_'
        input_node.tooltip = 'A number in meters to specify the difference in height between each of the mesh arrows. (Default 2 meters).'
        input_node = self.inputs.new('SvLBSocket', '_vec_scale_')
        input_node.prop_name = 'sv__vec_scale_'
        input_node.tooltip = 'A number to denote the length dimension of a 1 m/s wind vector in meters. This can be used to change the scale of the wind vector meshes in relation to the height of the wind profile curve. (Default: 5 meters).'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'An optional LegendParameter object to change the display of the wind profile.'
        output_node = self.outputs.new('SvLBSocket', 'wind_speeds')
        output_node.tooltip = 'A list of wind speeds in [m/s] that correspond to the wind vectors slong the height of the wind profile visualization.'
        output_node = self.outputs.new('SvLBSocket', 'wind_vectors')
        output_node.tooltip = 'A list of vectors that built the profile. Note that the magnitude of these vectors is scaled based on the _vec_scale_ input and a _vec_scale_ of 1 will make the magnitude of the vector equal to the wind speed in [m/s].'
        output_node = self.outputs.new('SvLBSocket', 'anchor_pts')
        output_node.tooltip = 'A list of anchor points for each of the vectors above, which correspond to the height above the ground for each of the vectors.'
        output_node = self.outputs.new('SvLBSocket', 'mesh_arrows')
        output_node.tooltip = 'A list of colored mesh objects that represent the wind speeds along the height of the wind profile.'
        output_node = self.outputs.new('SvLBSocket', 'profile_curve')
        output_node.tooltip = 'A curve outlining the wind speed as it changes with height.'
        output_node = self.outputs.new('SvLBSocket', 'speed_axis')
        output_node.tooltip = 'A list of line segments and text objects that mark the X axis, which relates to the wind speed in (m/s).'
        output_node = self.outputs.new('SvLBSocket', 'height_axis')
        output_node.tooltip = 'A list of line segments and text objects that mark the Y axis, which relates to the the height above the ground in Rhino model units.'
        output_node = self.outputs.new('SvLBSocket', 'legend')
        output_node.tooltip = 'A legend for the colored mesh_arrows, which notes their speed.'
        output_node = self.outputs.new('SvLBSocket', 'title')
        output_node.tooltip = 'A text object for the global_title.'
        output_node = self.outputs.new('SvLBSocket', 'vis_set')
        output_node.tooltip = 'An object containing VisualizationSet arguments for drawing a detailed version of the Wind Profile in the Rhino scene. This can be connected to the "LB Preview Visualization Set" component to display this version of the Wind Profile in Rhino.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Visualize a wind profile curve for a given terrain type. _ Wind profiles assist with understanding how wind speed decreases as one approaches the ground or increases as one leaves the ground.  _ By default, the wind profile output by this component will be an average over the _met_wind_vel data collection (or it can be for a single meteorological wind velocity for point-in-time studies). _ If a met_wind_dir_ data collection is connected, the wind profile will point in the direction of prevailing wind direction by default. A profile_dir_ can then be connected to understand the average wind profile from a specific cardinal direction (eg. NE). -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['wind_speeds', 'wind_vectors', 'anchor_pts', 'mesh_arrows', 'profile_curve', 'speed_axis', 'height_axis', 'legend', 'title', 'vis_set']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['north_', '_met_wind_vel', 'met_wind_dir_', 'profile_dir_', '_terrain_', '_met_height_', '_met_terrain_', 'log_law_', '_base_pt_', '_max_speed_', '_profile_height_', '_vec_spacing_', '_vec_scale_', 'legend_par_']
        self.sv_input_types = ['System.Object', 'System.Object', 'System.Object', 'string', 'string', 'double', 'string', 'bool', 'Point3d', 'double', 'double', 'double', 'double', 'System.Object']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, north_, _met_wind_vel, met_wind_dir_, profile_dir_, _terrain_, _met_height_, _met_terrain_, log_law_, _base_pt_, _max_speed_, _profile_height_, _vec_spacing_, _vec_scale_, legend_par_):

        import math
        
        try:
            from ladybug_geometry.geometry2d import Vector2D
            from ladybug_geometry.geometry3d import Point3D
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug.datatype.speed import WindSpeed
            from ladybug.datacollection import BaseCollection
            from ladybug.graphic import GraphicContainer
            from ladybug.windprofile import WindProfile
            from ladybug.windrose import WindRose
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.togeometry import to_point3d, to_vector2d
            from ladybug_tools.fromgeometry import from_point3d, from_vector3d, \
                from_mesh3d, from_linesegment3d, from_polyline3d
            from ladybug_tools.text import text_objects
            from ladybug_tools.fromobjects import legend_objects
            from ladybug_tools.sverchok import all_required_inputs, objectify_output
            from ladybug_tools.config import conversion_to_meters, units_system
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        # dictionary to map integers to terrain types
        TERRAIN_TYPES = {
            '0': 'city',
            '1': 'suburban',
            '2': 'country',
            '3': 'water',
            'city': 'city',
            'suburban': 'suburban',
            'country': 'country',
            'water': 'water'
        }
        
        # dictionary to map integers to cardinal directions
        DIR_TEXT = {
            '0': 'N', '1': 'NE', '2': 'E', '3': 'SE', '4': 'S', '5': 'SW', '6': 'W', '7': 'NW',
            'N': 'N', 'NE': 'NE', 'E': 'E', 'SE': 'SE', 'S': 'S', 'SW': 'SW', 'W': 'W', 'NW': 'NW'
        }
        DIR_RANGE = {
            'N': (337.5, 22.5), 'NE': (22.5, 67.5), 'E': (67.5, 112.5), 'SE': (112.5, 157.5),
            'S': (157.5, 202.5), 'SW': (202.5, 247.5), 'W': (247.5, 292.5), 'NW': (292.5, 337.5)
        }
        
        
        if all_required_inputs(ghenv.Component):
            # interpret the model units
            scale_fac = 1 / conversion_to_meters()
            unit_sys = units_system()
        
            # set default values
            if north_ is not None:  # process the north_
                try:
                    north_ = math.degrees(
                        to_vector2d(north_).angle_clockwise(Vector2D(0, 1)))
                except AttributeError:  # north angle instead of vector
                    north_ = float(north_)
            else:
                north_ = 0
            _terrain_ = 'city' if _terrain_ is None else TERRAIN_TYPES[_terrain_.lower()]
            _met_height_ = 10 if _met_height_ is None else _met_height_
            _met_terrain_ = 'country' if _met_terrain_ is None \
                else TERRAIN_TYPES[_met_terrain_.lower()]
            log_law_ = False if log_law_ is None else log_law_
            bp = Point3D(0, 0, 0) if _base_pt_ is None else to_point3d(_base_pt_)
            if unit_sys in ('Feet', 'Inches'):
                _profile_height_ = 30.48 if _profile_height_ is None else _profile_height_
                _vec_spacing_ = 3.048 if _vec_spacing_ is None else _vec_spacing_
                feet_labels = True
            else:
                _profile_height_ = 30 if _profile_height_ is None else _profile_height_
                _vec_spacing_ = 2 if _vec_spacing_ is None else _vec_spacing_
                feet_labels = False
            _vec_scale_ = 5 if _vec_scale_ is None else _vec_scale_
            len_d, height_d = _vec_scale_, _vec_scale_ / 5
        
            # process the data collections and wind direction if reuqested
            if isinstance(met_wind_dir_, BaseCollection):
                if profile_dir_ is not None:
                    dir_label = DIR_TEXT[profile_dir_]
                    dir_txt = '\nWind Direction = {}'.format(dir_label)
                else:  # get the prevailing wind direction
                    prev_dir = WindRose.prevailing_direction_from_data(met_wind_dir_, 8)[0]
                    dir_label = DIR_TEXT[str(int(prev_dir / 45))]
                    dir_txt = '\nPrevailing Wind Direction = {}'.format(dir_label)
                dir_range = DIR_RANGE[dir_label]
                met_wd = sum(dir_range) / 2 if dir_range != (337.5, 22.5) else 0
                if isinstance(_met_wind_vel, BaseCollection):
                    lw, hg = dir_range
                    if dir_range == (337.5, 22.5):
                        pattern = [lw < v or v < hg for v in met_wind_dir_]
                    else:
                        pattern = [lw < v < hg for v in met_wind_dir_]
                    _met_wind_vel = _met_wind_vel.filter_by_pattern(pattern)
            else:
                met_wd = float(met_wind_dir_) if met_wind_dir_ is not None else None
                dir_txt = '\nWind Direction = {} degrees'.format(int(met_wd)) \
                    if met_wind_dir_ is not None else ''
            if isinstance(_met_wind_vel, BaseCollection):
                met_ws = _met_wind_vel.average
                head = _met_wind_vel.header
                loc_txt = '{} Terrain'.format(_terrain_.title()) if 'city' not in head.metadata \
                    else '{} - {} Terrain'.format(head.metadata['city'], _terrain_.title())
                title_txt = '{}{}\nAverage Met Wind Speed = {} m/s'.format(
                    loc_txt, dir_txt, round(met_ws, 2))
            else:
                met_ws = float(_met_wind_vel)
                title_txt = '{} Terrain{}\nMeteorological Speed = {} m/s'.format(
                    _terrain_.title(), dir_txt, round(met_ws, 2))
            if met_wd is not None and north_ != 0:
                met_wd = met_wd - north_
        
            # create the wind profile and the graphic container
            profile = WindProfile(_terrain_, _met_terrain_, _met_height_, log_law_)
            _, mesh_ars, wind_speeds, wind_vectors, anchor_pts = \
                profile.mesh_arrow_profile(
                    met_ws, _profile_height_, _vec_spacing_, met_wd, bp,
                    len_d, height_d, scale_fac)
            profile_polyline, _, _ = profile.profile_polyline3d(
                    met_ws, _profile_height_, 0.1,
                    met_wd, bp, len_d, scale_fac)
            max_speed = round(wind_speeds[-1]) if _max_speed_ is None else _max_speed_
            max_pt = Point3D(bp.x + ((max_speed + 2) * len_d * scale_fac),
                             bp.y + (30 * scale_fac), bp.z)
            graphic = GraphicContainer(
                wind_speeds, bp, max_pt, legend_par_, WindSpeed(), 'm/s')
        
            # draw profile geometry and mesh arrows in the scene
            mesh_arrows = []
            for mesh, col in zip(mesh_ars, graphic.value_colors):
                mesh.colors = [col] * len(mesh)
                mesh_arrows.append(from_mesh3d(mesh))
            profile_curve = from_polyline3d(profile_polyline)
        
            # draw axes and legend in the scene
            txt_h = graphic.legend_parameters.text_height
            axis_line, axis_arrow, axis_ticks, text_planes, text = \
                profile.speed_axis(max_speed, met_wd, bp, len_d, scale_fac, txt_h)
            speed_axis = [from_linesegment3d(axis_line), from_mesh3d(axis_arrow)]
            for tic in axis_ticks:
                speed_axis.append(from_linesegment3d(tic))
            for i, (pl, txt) in enumerate(zip(text_planes, text)):
                txt_i_h = txt_h if i != len(text) - 1 else txt_h * 1.25
                txt_obj = text_objects(txt, pl, txt_i_h, graphic.legend_parameters.font, 1, 0)
                speed_axis.append(txt_obj)
            axis_line, axis_arrow, axis_ticks, text_planes, text = \
                profile.height_axis(_profile_height_, _vec_spacing_ * 2, met_wd, bp,
                                    scale_fac, txt_h, feet_labels)
            height_axis = [from_linesegment3d(axis_line), from_mesh3d(axis_arrow)]
            for tic in axis_ticks:
                height_axis.append(from_linesegment3d(tic))
            for i, (pl, txt) in enumerate(zip(text_planes, text)):
                if i != len(text) - 1:
                    txt_i_h, ha, va = txt_h, 2, 3
                else:
                    txt_i_h, ha, va = txt_h * 1.25, 1, 5
                txt_obj = text_objects(txt, pl, txt_i_h, graphic.legend_parameters.font, ha, va)
                height_axis.append(txt_obj)
            
            # draw the legend and the title
            if graphic.legend_parameters.is_base_plane_default:
                graphic.legend_parameters.base_plane = \
                    profile.legend_plane(max_speed, met_wd, bp, len_d, scale_fac)
            legend = legend_objects(graphic.legend)
            title_pl = profile.title_plane(met_wd, bp, len_d, scale_fac, txt_h)
            title = text_objects(title_txt, title_pl, txt_h, graphic.legend_parameters.font, 0, 0)
        
            # process the output lists of data
            anchor_pts = [from_point3d(pt) for pt in anchor_pts]
            wind_vectors = [from_vector3d(vec) for vec in wind_vectors]
            wind_speeds.insert(0, 0)  # insert 0 wind speed for bottom of curve
        
            # create the output VisualizationSet arguments
            vis_set = [profile, met_ws, met_wd, legend_par_, bp, _profile_height_,
                       _vec_spacing_, len_d, height_d, max_speed, scale_fac, feet_labels]
            vis_set = objectify_output('VisualizationSet Aruments [WindProfile]', vis_set)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvWindProfile)

def unregister():
    bpy.utils.unregister_class(SvWindProfile)
