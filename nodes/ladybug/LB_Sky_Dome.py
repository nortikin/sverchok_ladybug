import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvSkyDome(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvSkyDome'
    bl_label = 'LB Sky Dome'
    sv_icon = 'LB_SKYDOME'
    sv__sky_mtx: StringProperty(
        name='_sky_mtx',
        update=updateNode,
        description='A Sky Matrix from the "LB Cumulative Sky Matrix" component or the "LB Benefit Sky Matrix" component, which describes the radiation coming from the various patches of the sky.')
    sv__center_pt_: StringProperty(
        name='_center_pt_',
        update=updateNode,
        description='A point for the center of the dome. (Default: (0, 0, 0))')
    sv__scale_: StringProperty(
        name='_scale_',
        update=updateNode,
        description='A number to set the scale of the sky dome. The default is 1, which corresponds to a radius of 100 meters in the current Rhino model\'s unit system.')
    sv_projection_: StringProperty(
        name='projection_',
        update=updateNode,
        description='Optional text for the name of a projection to use from the sky dome hemisphere to the 2D plane. If None, a 3D sky dome will be drawn instead of a 2D one. (Default: None) Choose from the following: * Orthographic * Stereographic')
    sv_irradiance_: StringProperty(
        name='irradiance_',
        update=updateNode,
        description='Boolean to note whether the sky dome should be plotted with units of cumulative Radiation (kWh/m2) [False] or with units of average Irradiance (W/m2) [True]. (Default: False).')
    sv_show_comp_: StringProperty(
        name='show_comp_',
        update=updateNode,
        description='Boolean to indicate whether only one dome with total radiation should be displayed (False) or three domes with the solar radiation components (total, direct, and diffuse) should be shown. (Default: False).')
    sv_legend_par_: StringProperty(
        name='legend_par_',
        update=updateNode,
        description='An optional LegendParameter object to change the display of the sky dome (Default: None).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_sky_mtx')
        input_node.prop_name = 'sv__sky_mtx'
        input_node.tooltip = 'A Sky Matrix from the "LB Cumulative Sky Matrix" component or the "LB Benefit Sky Matrix" component, which describes the radiation coming from the various patches of the sky.'
        input_node = self.inputs.new('SvLBSocket', '_center_pt_')
        input_node.prop_name = 'sv__center_pt_'
        input_node.tooltip = 'A point for the center of the dome. (Default: (0, 0, 0))'
        input_node = self.inputs.new('SvLBSocket', '_scale_')
        input_node.prop_name = 'sv__scale_'
        input_node.tooltip = 'A number to set the scale of the sky dome. The default is 1, which corresponds to a radius of 100 meters in the current Rhino model\'s unit system.'
        input_node = self.inputs.new('SvLBSocket', 'projection_')
        input_node.prop_name = 'sv_projection_'
        input_node.tooltip = 'Optional text for the name of a projection to use from the sky dome hemisphere to the 2D plane. If None, a 3D sky dome will be drawn instead of a 2D one. (Default: None) Choose from the following: * Orthographic * Stereographic'
        input_node = self.inputs.new('SvLBSocket', 'irradiance_')
        input_node.prop_name = 'sv_irradiance_'
        input_node.tooltip = 'Boolean to note whether the sky dome should be plotted with units of cumulative Radiation (kWh/m2) [False] or with units of average Irradiance (W/m2) [True]. (Default: False).'
        input_node = self.inputs.new('SvLBSocket', 'show_comp_')
        input_node.prop_name = 'sv_show_comp_'
        input_node.tooltip = 'Boolean to indicate whether only one dome with total radiation should be displayed (False) or three domes with the solar radiation components (total, direct, and diffuse) should be shown. (Default: False).'
        input_node = self.inputs.new('SvLBSocket', 'legend_par_')
        input_node.prop_name = 'sv_legend_par_'
        input_node.tooltip = 'An optional LegendParameter object to change the display of the sky dome (Default: None).'
        output_node = self.outputs.new('SvLBSocket', 'mesh')
        output_node.tooltip = 'A colored mesh representing the intensity of radiation for each of the sky patches within the sky dome.'
        output_node = self.outputs.new('SvLBSocket', 'compass')
        output_node.tooltip = 'A set of circles, lines and text objects that mark the cardinal directions in relation to the sky dome.'
        output_node = self.outputs.new('SvLBSocket', 'legend')
        output_node.tooltip = 'A legend showing the kWh/m2 or W/m2 values that correspond to the colors of the mesh.'
        output_node = self.outputs.new('SvLBSocket', 'title')
        output_node.tooltip = 'A text object for the title of the sky dome.'
        output_node = self.outputs.new('SvLBSocket', 'patch_vecs')
        output_node.tooltip = 'A list of vectors for each of the patches of the sky dome. All vectors are unit vectors and point from the center towards each of the patches. They can be used to construct visualizations of the rays used to perform radiation analysis.'
        output_node = self.outputs.new('SvLBSocket', 'patch_values')
        output_node.tooltip = 'Radiation values for each of the sky patches in kWh/m2 or W/m2. This will be one list if show_comp_ is "False" and a list of 3 lists (aka. a Data Tree) for total, direct, diffuse if show_comp_ is "True".'
        output_node = self.outputs.new('SvLBSocket', 'mesh_values')
        output_node.tooltip = 'Radiation values for each face of the dome mesh in kWh/m2. This can be used to post-process the radiation data and then regenerate the dome visualization using the mesh output from this component and the "LB Spatial Heatmap" component. Examples of useful post- processing include converting the units to something other than kWh/m2, inverting the +/- sign of radiation values depending on whether radiation is helpful or harmful to building thermal loads, etc. This will be one list if show_comp_ is "False" and a list of 3 lists (aka. a Data Tree) for total, direct, diffuse if show_comp_ is "True".'
        output_node = self.outputs.new('SvLBSocket', 'vis_set')
        output_node.tooltip = 'An object containing VisualizationSet arguments for drawing a detailed version of the Sky Dome in the Rhino scene. This can be connected to the "LB Preview Visualization Set" component to display this version of the Sky Dome in Rhino.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Visualize a sky matrix from the "LB Cumulative Sky Matrix" component as a colored dome, subdivided into patches with a radiation value for each patch. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['mesh', 'compass', 'legend', 'title', 'patch_vecs', 'patch_values', 'mesh_values', 'vis_set']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_sky_mtx', '_center_pt_', '_scale_', 'projection_', 'irradiance_', 'show_comp_', 'legend_par_']
        self.sv_input_types = ['System.Object', 'Point3d', 'double', 'string', 'bool', 'bool', 'System.Object']
        self.sv_input_defaults = [None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _sky_mtx, _center_pt_, _scale_, projection_, irradiance_, show_comp_, legend_par_):

        try:
            from ladybug_geometry.geometry3d.pointvector import Point3D
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug_radiance.visualize.skydome import SkyDome
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_radiance:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import conversion_to_meters
            from ladybug_tools.togeometry import to_point3d
            from ladybug_tools.fromgeometry import from_mesh3d, from_vector3d
            from ladybug_tools.fromobjects import legend_objects, compass_objects
            from ladybug_tools.text import text_objects
            from ladybug_tools.sverchok import all_required_inputs, \
                objectify_output, list_to_data_tree
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        def translate_dome(lb_mesh, lb_compass, graphic, title_txt, values):
            """Translate sky dome geometry into a format suitable for Blender Ladybug.
        
            Args:
                lb_mesh: A ladybug Mesh3D for the dome.
                lb_compass: A ladybug Compass object.
                graphic: A GraphicContainer for the dome.
                title_txt: Text for title of the dome.
                values: A list of radiation values that align with the dome_mesh faces.
        
            Returns:
                dome_mesh: A Blender Ladybug colored mesh for the dome.
                dome_compass: Blender Ladybug objects for the dome compass.
                dome_legend:  Blender Ladybug objects for the dome legend.
                dome_title: A bake-able title for the dome.
                values: A list of radiation values that align with the dome_mesh faces.
            """
            # translate the dome visualization, including legend and compass
            dome_mesh = from_mesh3d(lb_mesh)
            dome_legend = legend_objects(graphic.legend)
            dome_compass = compass_objects(
                lb_compass, z, None, sky_dome.projection, graphic.legend_parameters.font)
        
            # construct a title from the metadata
            dome_title = text_objects(title_txt, graphic.lower_title_location,
                                      graphic.legend_parameters.text_height,
                                      graphic.legend_parameters.font)
        
            return dome_mesh, dome_compass, dome_legend, dome_title, values
        
        
        if all_required_inputs(ghenv.Component):
            # set defaults for global variables
            _scale_ = 1 if _scale_ is None else _scale_
            radius = (100 * _scale_) / conversion_to_meters()
            if _center_pt_ is not None:  # process the center point
                center_pt3d = to_point3d(_center_pt_)
                z = center_pt3d.z
            else:
                center_pt3d, z = Point3D(), 0
        
            # create the SkyDome object
            sky_dome = SkyDome(_sky_mtx, legend_par_, irradiance_,
                               center_pt3d, radius, projection_)
        
            # output patch patch vectors
            patch_vecs = [from_vector3d(vec) for vec in sky_dome.patch_vectors]
        
            # create the dome visualization
            if not show_comp_:  # only create the total dome mesh
                mesh, compass, legend, title, mesh_values = translate_dome(*sky_dome.draw())
                patch_values = sky_dome.total_values
            else:  # create domes for total, direct and diffuse
                # loop through the 3 radiation types and produce a dome
                mesh, compass, legend, title, mesh_values = [], [], [], [], []
                rad_types = ('total', 'direct', 'diffuse')
                for dome_i in range(3):
                    cent_pt = Point3D(center_pt3d.x + radius * 3 * dome_i,
                                      center_pt3d.y, center_pt3d.z)
                    dome_mesh, dome_compass, dome_legend, dome_title, dome_values = \
                        translate_dome(*sky_dome.draw(rad_types[dome_i], cent_pt))
                    mesh.append(dome_mesh)
                    compass.extend(dome_compass)
                    legend.extend(dome_legend)
                    title.append(dome_title)
                    mesh_values.append(dome_values)
                rad_data = (sky_dome.total_values, sky_dome.direct_values, sky_dome.diffuse_values)
                patch_values = list_to_data_tree(rad_data)
                mesh_values = list_to_data_tree(mesh_values)
        
            # output the visualization set
            vis_set = [sky_dome, show_comp_]
            vis_set = objectify_output('VisualizationSet Aruments [SkyDome]', vis_set)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvSkyDome)

def unregister():
    bpy.utils.unregister_class(SvSkyDome)
