import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvSyMask(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvSyMask'
    bl_label = 'LB Sky Mask'
    sv_icon = 'LB_SYMASK'
    sv_context_: StringProperty(
        name='context_',
        update=updateNode,
        description='Rhino Breps and/or Rhino Meshes representing context geometry that can block the sky to the center of the sky mask.')
    sv_orientation_: StringProperty(
        name='orientation_',
        update=updateNode,
        description='A number between 0 and 360 that sets the direction of a vertically- oriented surface for which the sky view will be visualized and computed. Alternatively, this input can be the words "north", "east", "south" or "west." An input here will result in the output of an orient_mask, which blocks the portion of the sky that is not visible from a vertical surface with this orientation. Furthermore, all of the view-related outputs will be computed for a surface with the specified orientation (overriding any plane input for the _center_).')
    sv_overhang_proj_: StringProperty(
        name='overhang_proj_',
        update=updateNode,
        description='A number between 0 and 90 that sets the angle between the _center_ and the edge of an imagined horizontal overhang projecting past the point. Note that this option is only available when there is an input for orientation_ above. An input here will result in the output of a strategy_mask, which blocks the portion of the sky taken up by an overhang with the input projection angle.')
    sv_left_fin_proj_: StringProperty(
        name='left_fin_proj_',
        update=updateNode,
        description='A number between 0 and 180 that sets the angle between the _center_ and the edge of an imagined vertical fin projecting past the left side of the point. Note that this option is only available when there is an input for orientation_ above. An input here will result in the output of a strategy_mask, which blocks the portion of the sky taken up by a vertical fin with the input projection angle.')
    sv_right_fin_proj_: StringProperty(
        name='right_fin_proj_',
        update=updateNode,
        description='A number between 0 and 180 that sets the angle between the _center_ and the edge of an imagined vertical fin projecting past the right side of the point. Note that this option is only available when there is an input for orientation_ above. An input here will result in the output of a strategy_mask, which blocks the portion of the sky taken up by a vertical fin with the input projection angle.')
    sv__density_: StringProperty(
        name='_density_',
        update=updateNode,
        description='An integer that is greater than or equal to 1, which to sets the number of times that the sky patches are split. Higher numbers input here will ensure a greater accuracy but will also take longer to run. A value of 3 should result in sky view factors with less than 1% error from the true value. (Default: 1).')
    sv__center_: StringProperty(
        name='_center_',
        update=updateNode,
        description='A point or plane for which the visible portion of the sky will be evaluated. If a point is input here, the view-related outputs will be indiferent to orientation and the sky_view outut will technically be Sky Exposure (or the fraction of the sky hemisphere that is visible from the point). If a plane is input here (or an orientation_ is connected), the view-related outputs will be sensitive to orientation and the sky_view output will be true Sky View (or the fraction of the sky visible from a surface in a plane). If no value is input here, the center will be a point (Sky Exposure) at the Rhino origin (0, 0, 0).')
    sv__scale_: StringProperty(
        name='_scale_',
        update=updateNode,
        description='A number to set the scale of the sky mask. The default is 1, which corresponds to a radius of 100 meters in the current Rhino model\'s unit system.')
    sv_projection_: StringProperty(
        name='projection_',
        update=updateNode,
        description='Optional text for the name of a projection to use from the sky dome hemisphere to the 2D plane. If None, a 3D dome will be drawn instead of a 2D one. Choose from the following: * Orthographic * Stereographic')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', 'context_')
        input_node.prop_name = 'sv_context_'
        input_node.tooltip = 'Rhino Breps and/or Rhino Meshes representing context geometry that can block the sky to the center of the sky mask.'
        input_node = self.inputs.new('SvLBSocket', 'orientation_')
        input_node.prop_name = 'sv_orientation_'
        input_node.tooltip = 'A number between 0 and 360 that sets the direction of a vertically- oriented surface for which the sky view will be visualized and computed. Alternatively, this input can be the words "north", "east", "south" or "west." An input here will result in the output of an orient_mask, which blocks the portion of the sky that is not visible from a vertical surface with this orientation. Furthermore, all of the view-related outputs will be computed for a surface with the specified orientation (overriding any plane input for the _center_).'
        input_node = self.inputs.new('SvLBSocket', 'overhang_proj_')
        input_node.prop_name = 'sv_overhang_proj_'
        input_node.tooltip = 'A number between 0 and 90 that sets the angle between the _center_ and the edge of an imagined horizontal overhang projecting past the point. Note that this option is only available when there is an input for orientation_ above. An input here will result in the output of a strategy_mask, which blocks the portion of the sky taken up by an overhang with the input projection angle.'
        input_node = self.inputs.new('SvLBSocket', 'left_fin_proj_')
        input_node.prop_name = 'sv_left_fin_proj_'
        input_node.tooltip = 'A number between 0 and 180 that sets the angle between the _center_ and the edge of an imagined vertical fin projecting past the left side of the point. Note that this option is only available when there is an input for orientation_ above. An input here will result in the output of a strategy_mask, which blocks the portion of the sky taken up by a vertical fin with the input projection angle.'
        input_node = self.inputs.new('SvLBSocket', 'right_fin_proj_')
        input_node.prop_name = 'sv_right_fin_proj_'
        input_node.tooltip = 'A number between 0 and 180 that sets the angle between the _center_ and the edge of an imagined vertical fin projecting past the right side of the point. Note that this option is only available when there is an input for orientation_ above. An input here will result in the output of a strategy_mask, which blocks the portion of the sky taken up by a vertical fin with the input projection angle.'
        input_node = self.inputs.new('SvLBSocket', '_density_')
        input_node.prop_name = 'sv__density_'
        input_node.tooltip = 'An integer that is greater than or equal to 1, which to sets the number of times that the sky patches are split. Higher numbers input here will ensure a greater accuracy but will also take longer to run. A value of 3 should result in sky view factors with less than 1% error from the true value. (Default: 1).'
        input_node = self.inputs.new('SvLBSocket', '_center_')
        input_node.prop_name = 'sv__center_'
        input_node.tooltip = 'A point or plane for which the visible portion of the sky will be evaluated. If a point is input here, the view-related outputs will be indiferent to orientation and the sky_view outut will technically be Sky Exposure (or the fraction of the sky hemisphere that is visible from the point). If a plane is input here (or an orientation_ is connected), the view-related outputs will be sensitive to orientation and the sky_view output will be true Sky View (or the fraction of the sky visible from a surface in a plane). If no value is input here, the center will be a point (Sky Exposure) at the Rhino origin (0, 0, 0).'
        input_node = self.inputs.new('SvLBSocket', '_scale_')
        input_node.prop_name = 'sv__scale_'
        input_node.tooltip = 'A number to set the scale of the sky mask. The default is 1, which corresponds to a radius of 100 meters in the current Rhino model\'s unit system.'
        input_node = self.inputs.new('SvLBSocket', 'projection_')
        input_node.prop_name = 'sv_projection_'
        input_node.tooltip = 'Optional text for the name of a projection to use from the sky dome hemisphere to the 2D plane. If None, a 3D dome will be drawn instead of a 2D one. Choose from the following: * Orthographic * Stereographic'
        output_node = self.outputs.new('SvLBSocket', 'context_mask')
        output_node.tooltip = 'A mesh for the portion of the sky dome masked by the context_ geometry.'
        output_node = self.outputs.new('SvLBSocket', 'orient_mask')
        output_node.tooltip = 'A mesh for the portion of the sky dome that is not visible from a surface is facing a given orientation.'
        output_node = self.outputs.new('SvLBSocket', 'strategy_mask')
        output_node.tooltip = 'A mesh of the portion of the sky dome masked by the overhang, left fin, and right fin projections.'
        output_node = self.outputs.new('SvLBSocket', 'sky_mask')
        output_node.tooltip = 'A mesh of the portion of the sky dome visible by the _center_ through the strategies and context_ geometry.'
        output_node = self.outputs.new('SvLBSocket', 'context_view')
        output_node.tooltip = 'The percentage of the sky dome masked by the context_ geometry.'
        output_node = self.outputs.new('SvLBSocket', 'orient_view')
        output_node.tooltip = 'The percentage of the sky dome that is not visible from a surface is facing a given orientation.'
        output_node = self.outputs.new('SvLBSocket', 'strategy_view')
        output_node.tooltip = 'The percentage of the sky dome viewed by the overhang, left fin, and right fin projections.'
        output_node = self.outputs.new('SvLBSocket', 'sky_view')
        output_node.tooltip = 'The percentage of the sky dome visible by the _center_ through the strategies and context_ geometry.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Visualize the portion of the sky dome that is masked by context geometry or shading strategies around a given point. _ Separate meshs will be generated for the portions of the sky dome that are masked vs visible. The percentage of the sky that is masked by the context geometry and is visible will also be computed. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['context_mask', 'orient_mask', 'strategy_mask', 'sky_mask', 'context_view', 'orient_view', 'strategy_view', 'sky_view']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['context_', 'orientation_', 'overhang_proj_', 'left_fin_proj_', 'right_fin_proj_', '_density_', '_center_', '_scale_', 'projection_']
        self.sv_input_types = ['GeometryBase', 'string', 'double', 'double', 'double', 'int', 'System.Object', 'double', 'string']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['list', 'item', 'item', 'item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, context_, orientation_, overhang_proj_, left_fin_proj_, right_fin_proj_, _density_, _center_, _scale_, projection_):

        import math
        
        try:
            from ladybug_geometry.geometry2d.pointvector import Point2D
            from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
            from ladybug_geometry.geometry3d.mesh import Mesh3D
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug.viewsphere import view_sphere
            from ladybug.compass import Compass
            from ladybug.color import Color
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import conversion_to_meters
            from ladybug_tools.togeometry import to_point3d, to_plane
            from ladybug_tools.fromgeometry import from_mesh3d, from_point3d, from_vector3d
            from ladybug_tools.intersect import join_geometry_to_mesh, intersect_mesh_rays
            from ladybug_tools.sverchok import turn_off_old_tag
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        turn_off_old_tag(ghenv.Component)
        
        
        def apply_mask_to_sky(sky_pattern, mask_pattern):
            """Apply a pattern of a mask to a pattern of visible sky."""
            for i, val in enumerate(mask_pattern):
                if val:
                    sky_pattern[i] = False
        
        
        def apply_mask_to_base_mask(base_pattern, mask_pattern, ignore_pattern):
            """Apply a pattern of a mask to a base pattern with the option to ignore elements."""
            for i, (val, ig_val) in enumerate(zip(mask_pattern, ignore_pattern)):
                if val and not ig_val:
                    base_pattern[i] = True
        
        
        def mask_mesh_from_pattern(base_mask, mask_pattern, color):
            """Get a Blender Ladybug mesh of a mask from a pattern aligned to the faces of a base mesh."""
            try:
                mask_mesh = base_mask.remove_faces_only(mask_pattern)
            except AssertionError:  # all mesh faces have been removed
                return None
            mask_mesh.colors = [color] * len(mask_mesh.faces)
            return from_mesh3d(mask_mesh)
        
        
        
        # process the inputs and set defaults for global variables
        _scale_ = 1 if _scale_ is None else _scale_
        radius = (100 * _scale_) / conversion_to_meters()
        if _center_ is not None:  # process the center point into a Point2D
            try:  # assume that it is a point
                center_pt3d, direction = to_point3d(_center_), None
            except AttributeError:
                plane, is_orient = to_plane(_center_), True
                center_pt3d, direction = plane.o, plane.n
        else:
            center_pt3d, direction = Point3D(), None
        az_count, alt_count = 72, 18
        if _density_:
            az_count = az_count * _density_
            alt_count = alt_count * _density_
        if orientation_ is not None:  # process the orientation to a number
            ori_dict = {'north': 0, 'east': 90, 'south': 180, 'west': 270}
            try:  # first check if it's text for the direction
                orientation_ = ori_dict[orientation_.lower()]
            except KeyError:  # it's a number for the orientation
                orientation_ = float(orientation_)
            direction = Vector3D(0, 1, 0).rotate_xy(-math.radians(orientation_))
        
        
        # create the dome mesh of the sky and position/project it correctly
        sky_mask, view_vecs = view_sphere.dome_radial_patches(az_count, alt_count)
        sky_mask = sky_mask.scale(radius)
        if center_pt3d != Point3D():
            m_vec = Vector3D(center_pt3d.x, center_pt3d.y, center_pt3d.z)
            sky_mask = sky_mask.move(m_vec)
        if projection_ is not None:
            if projection_.title() == 'Orthographic':
                pts = (Compass.point3d_to_orthographic(pt) for pt in sky_mask.vertices)
            elif projection_.title() == 'Stereographic':
                pts = (Compass.point3d_to_stereographic(pt, radius, center_pt3d)
                       for pt in sky_mask.vertices)
            else:
                raise ValueError(
                    'Projection type "{}" is not recognized.'.format(projection_))
            pts3d = tuple(Point3D(pt.x, pt.y, center_pt3d.z) for pt in pts)
            sky_mask = Mesh3D(pts3d, sky_mask.faces)
        sky_pattern = [True] * len(view_vecs)  # pattern to be adjusted by the various masks
        
        
        # account for the orientation and any of the projection strategies
        orient_pattern, strategy_pattern = None, None
        if direction is not None:
            orient_pattern, dir_angles = view_sphere.orientation_pattern(direction, view_vecs)
            apply_mask_to_sky(sky_pattern, orient_pattern)
            if overhang_proj_ or left_fin_proj_ or right_fin_proj_:
                strategy_pattern = [False] * len(view_vecs)
                if overhang_proj_:
                    over_pattern = view_sphere.overhang_pattern(direction, overhang_proj_, view_vecs)
                    apply_mask_to_base_mask(strategy_pattern, over_pattern, orient_pattern)
                    apply_mask_to_sky(sky_pattern, over_pattern)
                if left_fin_proj_ or right_fin_proj_:
                    f_pattern = view_sphere.fin_pattern(direction, left_fin_proj_, right_fin_proj_, view_vecs)
                    apply_mask_to_base_mask(strategy_pattern, f_pattern, orient_pattern)
                    apply_mask_to_sky(sky_pattern, f_pattern)
        
        
        # account for any input context
        context_pattern = None
        if len(context_) != 0:
            shade_mesh = join_geometry_to_mesh(context_)  # mesh the context
            points = [from_point3d(center_pt3d)]
            view_vecs = [from_vector3d(pt) for pt in view_vecs]
            int_matrix, angles = intersect_mesh_rays(shade_mesh, points, view_vecs)
            context_pattern = [val == 0 for val in int_matrix[0]]
            apply_mask_to_sky(sky_pattern, context_pattern)
        
        
        # get the weights for each patch to be used in view factor calculation
        weights = view_sphere.dome_radial_patch_weights(az_count, alt_count)
        if direction is not None:
            weights = [wgt * abs(math.cos(ang)) * 2 for wgt, ang in zip(weights, dir_angles)]
        
        
        # create meshes for the masks and compute any necessary view factors
        gray, black = Color(230, 230, 230), Color(0, 0, 0)
        context_view, orient_view, strategy_view = 0, 0, 0
        if context_pattern is not None:
            context_mask = mask_mesh_from_pattern(sky_mask, context_pattern, black)
            context_view = sum(wgt for wgt, is_viz in zip(weights, context_pattern) if is_viz)
        if orient_pattern is not None:
            orient_mask = mask_mesh_from_pattern(sky_mask, orient_pattern, black)
            orient_view = sum(wgt for wgt, is_viz in zip(weights, orient_pattern) if is_viz)
        if strategy_pattern is not None:
            strategy_mask = mask_mesh_from_pattern(sky_mask, strategy_pattern, black)
            strategy_view = sum(wgt for wgt, is_viz in zip(weights, strategy_pattern) if is_viz)
        sky_mask = mask_mesh_from_pattern(sky_mask, sky_pattern, gray)
        sky_view = sum(wgt for wgt, is_viz in zip(weights, sky_pattern) if is_viz)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvSyMask)

def unregister():
    bpy.utils.unregister_class(SvSyMask)
