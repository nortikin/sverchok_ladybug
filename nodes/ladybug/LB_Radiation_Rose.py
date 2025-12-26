import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvRadRose(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvRadRose'
    bl_label = 'LB Radiation Rose'
    sv_icon = 'LB_RADROSE'
    sv__sky_mtx: StringProperty(
        name='_sky_mtx',
        update=updateNode,
        description='A Sky Matrix from the "LB Cumulative Sky Matrix" component or the "LB Benefit Sky Matrix" component, which describes the radiation coming from the various patches of the sky.')
    sv_context_: StringProperty(
        name='context_',
        update=updateNode,
        description='Rhino Breps and/or Rhino Meshes representing context geometry that can block solar radiation to the center of the radiation rose.')
    sv__dir_count_: StringProperty(
        name='_dir_count_',
        update=updateNode,
        description='An integer greater than or equal to 3, which notes the number of arrows to be generated for the radiation rose. (Default: 36).')
    sv__tilt_angle_: StringProperty(
        name='_tilt_angle_',
        update=updateNode,
        description='A number between 0 and 90 that sets the vertical tilt angle (aka. the altitude) for all of the directions. By default, the Radiation Rose depicts the amount of solar energy received by a vertical wall (tilt_angle=0). The tilt_angle can be changed to a specific value to assess the solar energy falling on geometries that are not perfectly vertical, such as a tilted photovoltaic panel. (Default: 0).')
    sv__center_pt_: StringProperty(
        name='_center_pt_',
        update=updateNode,
        description='A point for the center of the radiation rose. (Default: (0, 0, 0))')
    sv__scale_: StringProperty(
        name='_scale_',
        update=updateNode,
        description='A number to set the scale of the Radiation Rose. The default is 1, which corresponds to a radius of 100 meters in the current Rhino model\'s unit system.')
    sv__arrow_scale_: StringProperty(
        name='_arrow_scale_',
        update=updateNode,
        description='A fractional number to note the scale of the radiation rose arrows in relation to the entire graphic. (Default: 1).')
    sv_max_rad_: StringProperty(
        name='max_rad_',
        update=updateNode,
        description='An optional number to set the level of radiation or irradiance associated with the full radius of the rose. If unspecified, this is determined by the maximum level of radiation in the input data but a number can be specified here to fix this at a specific value. This is particularly useful when comparing different roses to one another.')
    sv_irradiance_: StringProperty(
        name='irradiance_',
        update=updateNode,
        description='Boolean to note whether the radiation rose should be plotted with units of cumulative Radiation (kWh/m2) [False] or with units of average Irradiance (W/m2) [True]. (Default: False).')
    sv_show_comp_: StringProperty(
        name='show_comp_',
        update=updateNode,
        description='Boolean to indicate whether only one rose with total radiation should be displayed (False) or three roses with the solar radiation components (total, direct, and diffuse) should be shown. (Default: False).')
    sv_legend_par_: StringProperty(
        name='legend_par_',
        update=updateNode,
        description='An optional LegendParameter object to change the display of the Radiation Rose.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_sky_mtx')
        input_node.prop_name = 'sv__sky_mtx'
        input_node.tooltip = 'A Sky Matrix from the "LB Cumulative Sky Matrix" component or the "LB Benefit Sky Matrix" component, which describes the radiation coming from the various patches of the sky.'
        input_node = self.inputs.new('SvLBSocket', 'context_')
        input_node.prop_name = 'sv_context_'
        input_node.tooltip = 'Rhino Breps and/or Rhino Meshes representing context geometry that can block solar radiation to the center of the radiation rose.'
        input_node = self.inputs.new('SvLBSocket', '_dir_count_')
        input_node.prop_name = 'sv__dir_count_'
        input_node.tooltip = 'An integer greater than or equal to 3, which notes the number of arrows to be generated for the radiation rose. (Default: 36).'
        input_node = self.inputs.new('SvLBSocket', '_tilt_angle_')
        input_node.prop_name = 'sv__tilt_angle_'
        input_node.tooltip = 'A number between 0 and 90 that sets the vertical tilt angle (aka. the altitude) for all of the directions. By default, the Radiation Rose depicts the amount of solar energy received by a vertical wall (tilt_angle=0). The tilt_angle can be changed to a specific value to assess the solar energy falling on geometries that are not perfectly vertical, such as a tilted photovoltaic panel. (Default: 0).'
        input_node = self.inputs.new('SvLBSocket', '_center_pt_')
        input_node.prop_name = 'sv__center_pt_'
        input_node.tooltip = 'A point for the center of the radiation rose. (Default: (0, 0, 0))'
        input_node = self.inputs.new('SvLBSocket', '_scale_')
        input_node.prop_name = 'sv__scale_'
        input_node.tooltip = 'A number to set the scale of the Radiation Rose. The default is 1, which corresponds to a radius of 100 meters in the current Rhino model\'s unit system.'
        input_node = self.inputs.new('SvLBSocket', '_arrow_scale_')
        input_node.prop_name = 'sv__arrow_scale_'
        input_node.tooltip = 'A fractional number to note the scale of the radiation rose arrows in relation to the entire graphic. (Default: 1).'
        input_node = self.inputs.new('SvLBSocket', 'max_rad_')
        input_node.prop_name = 'sv_max_rad_'
        input_node.tooltip = 'An optional number to set the level of radiation or irradiance associated with the full radius of the rose. If unspecified, this is determined by the maximum level of radiation in the input data but a number can be specified here to fix this at a specific value. This is particularly useful when comparing different roses to one another.'
        input_node = self.inputs.new('SvLBSocket', 'irradiance_')
        input_node.prop_name = 'sv_irradiance_'
        input_node.tooltip = 'Boolean to note whether the radiation rose should be plotted with units of cumulative Radiation (kWh/m2) [False] or with units of average Irradiance (W/m2) [True]. (Default: False).'
        input_node = self.inputs.new('SvLBSocket', 'show_comp_')
        input_node.prop_name = 'sv_show_comp_'
        input_node.tooltip = 'Boolean to indicate whether only one rose with total radiation should be displayed (False) or three roses with the solar radiation components (total, direct, and diffuse) should be shown. (Default: False).'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'An optional LegendParameter object to change the display of the Radiation Rose.'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'A colored mesh of arrows, representing the intensity of radiation from different cardinal directions.'
        output_node = self.outputs.new('SvLBSocket', 'compass')
        output_node.tooltip = 'A set of circles, lines and text objects that mark the cardinal directions in relation to the radiation rose.'
        output_node = self.outputs.new('SvLBSocket', 'orient_lines')
        output_node.tooltip = 'A list of line segments marking the orientation of each arrow.'
        output_node = self.outputs.new('SvLBSocket', 'legend')
        output_node.tooltip = 'A legend showing the kWh/m2 or W/m2 values that correspond to the colors of the mesh.'
        output_node = self.outputs.new('SvLBSocket', 'title')
        output_node.tooltip = 'A text object for the title of the radiation rose.'
        output_node = self.outputs.new('SvLBSocket', 'dir_vecs')
        output_node.tooltip = 'A list of vectors for each of the directions the rose is facing. All vectors are unit vectors.'
        output_node = self.outputs.new('SvLBSocket', 'dir_values')
        output_node.tooltip = 'Radiation values for each of the rose directions in kWh/m2 or W/m2. This will be one list if show_comp_ is "False" and a list of 3 lists (aka. a Data Tree) for total, direct, diffuse if show_comp_ is "True".'
        output_node = self.outputs.new('SvLBSocket', 'vis_set')
        output_node.tooltip = 'Script variable RadRose'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Visualize the solar energy falling on different direction as a rose. _ By default, the Radiation Rose depicts the amount of solar energy received by a vertical wall facing each of the directions of the compass rose. _ This is useful for understanding the radiation harm/benefit experienced by different building orientations or the orientations with the highest peak cooling load (for sky matrices of clear skies). The tilt_angle can be used to assess the solar energy falling on geometries that are not perfectly vertical, such as tilted photovoltaic panels. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['mesh', 'compass', 'orient_lines', 'legend', 'title', 'dir_vecs', 'dir_values', 'vis_set']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_sky_mtx', 'context_', '_dir_count_', '_tilt_angle_', '_center_pt_', '_scale_', '_arrow_scale_', 'max_rad_', 'irradiance_', 'show_comp_', 'legend_par_']
        self.sv_input_types = ['System.Object', 'GeometryBase', 'int', 'double', 'Point3d', 'double', 'double', 'double', 'bool', 'bool', 'System.Object']
        self.sv_input_defaults = [None, None, None, None, None, None, 1, None, None, None, None]
        self.sv_input_access = ['item', 'list', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _sky_mtx, context_, _dir_count_, _tilt_angle_, _center_pt_, _scale_, _arrow_scale_, max_rad_, irradiance_, show_comp_, legend_par_):

        try:
            from ladybug_geometry.geometry3d.pointvector import Point3D
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug.viewsphere import view_sphere
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_radiance.visualize.radrose import RadiationRose
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_radiance:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import conversion_to_meters
            from ladybug_tools.togeometry import to_point3d
            from ladybug_tools.fromgeometry import from_point3d, from_vector3d, \
                from_linesegment3d, from_mesh3d
            from ladybug_tools.intersect import join_geometry_to_mesh, intersect_mesh_rays
            from ladybug_tools.fromobjects import legend_objects, compass_objects
            from ladybug_tools.text import text_objects
            from ladybug_tools.sverchok import all_required_inputs, \
                objectify_output, list_to_data_tree
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        def translate_rose(lb_mesh, lb_orient_lines, lb_compass, graphic, title_txt):
            """Translate radiation rose geometry into a format suitable for Blender Ladybug.
        
            Args:
                lb_mesh: A ladybug Mesh3D for the rose.
                lb_compass: A ladybug Compass object.
                graphic: A GraphicContainer for the rose.
                title_txt: Text for title of the rose.
        
            Returns:
                rose_mesh: A Blender Ladybug colored mesh for the rose.
                rose_compass: Blender Ladybug objects for the rose compass.
                rose_legend:  Blender Ladybug objects for the rose legend.
                rose_title: A bake-able title for the rose.
            """
            # translate the rose visualization, including legend and compass
            rose_mesh = from_mesh3d(lb_mesh)
            rose_legend = legend_objects(graphic.legend)
            rose_angles = list(range(0, 360, int(360 / _dir_count_)))
            start, stop, step, rose_angles = 0, 360, 360 / _dir_count_, []
            while start < stop:
                rose_angles.append(start)
                start += step
            rose_angles = [int(n) for n in rose_angles]
            if len(rose_angles) > 36:
                rose_angles = rose_angles[::2]
            rose_compass = compass_objects(
                lb_compass, z, rose_angles, None, graphic.legend_parameters.font)
            orient_lines = [from_linesegment3d(l) for l in lb_orient_lines]
        
            # construct a title from the metadata
            rose_title = text_objects(title_txt, graphic.lower_title_location,
                                      graphic.legend_parameters.text_height,
                                      graphic.legend_parameters.font)
        
            return rose_mesh, orient_lines, rose_compass, rose_legend, rose_title
        
        
        if all_required_inputs(ghenv.Component):
            # set defaults for global variables
            _dir_count_ = 36 if _dir_count_ is None else _dir_count_
            _tilt_angle_ = 0 if _tilt_angle_ is None else _tilt_angle_
            _arrow_scale_ = 1 if _arrow_scale_ is None else _arrow_scale_
            _scale_ = 1 if _scale_ is None else _scale_
            radius = (100 * _scale_) / conversion_to_meters()
            if _center_pt_ is not None:  # process the center point
                center_pt3d = to_point3d(_center_pt_)
                z = center_pt3d.z
            else:
                center_pt3d, z = Point3D(), 0
        
            # compute the intersection matrix if context is specified
            n_vecs = RadiationRose.radial_vectors(_dir_count_, _tilt_angle_)
            dir_vecs = [from_vector3d(vec) for vec in n_vecs]
            int_mtx = None
            if len(context_) != 0 and context_[0] is not None:
                shade_mesh = join_geometry_to_mesh(context_)
                p_vecs = view_sphere.tregenza_sphere_vectors if len(_sky_mtx.data[1]) == 145 \
                    else view_sphere.reinhart_sphere_vectors
                patch_dirs = [from_vector3d(vec) for vec in p_vecs]
                int_mtx, angles = intersect_mesh_rays(
                    shade_mesh, [from_point3d(center_pt3d)] * _dir_count_,
                    patch_dirs, dir_vecs, 1)
        
            # create the RadiationRose object
            rad_rose = RadiationRose(
                _sky_mtx, int_mtx, _dir_count_, _tilt_angle_, legend_par_,
                irradiance_, center_pt3d, radius, _arrow_scale_)
        
            # create the rose visualization
            if not show_comp_:  # only create the total rose mesh
                mesh, orient_lines, compass, legend, title = \
                    translate_rose(*rad_rose.draw(max_rad=max_rad_))
                dir_values = rad_rose.total_values
            else:  # create roses for total, direct and diffuse
                # loop through the 3 radiation types and produce a rose
                mesh, orient_lines, compass, legend, title = [], [], [], [], []
                rad_types = ('total', 'direct', 'diffuse')
                for rose_i in range(3):
                    cent_pt = Point3D(center_pt3d.x + radius * 3 * rose_i,
                                      center_pt3d.y, center_pt3d.z)
                    rose_mesh, rose_lines, rose_compass, rose_legend, rose_title = \
                        translate_rose(*rad_rose.draw(rad_types[rose_i], cent_pt, max_rad_))
                    mesh.append(rose_mesh)
                    compass.extend(rose_compass)
                    orient_lines.extend(rose_lines)
                    legend.extend(rose_legend)
                    title.append(rose_title)
                dir_values = list_to_data_tree(
                    (rad_rose.total_values, rad_rose.direct_values, rad_rose.diffuse_values))
        
            # output the visualization set
            vis_set = [rad_rose, max_rad_, show_comp_]
            vis_set = objectify_output('VisualizationSet Aruments [RadiationRose]', vis_set)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvRadRose)

def unregister():
    bpy.utils.unregister_class(SvRadRose)
