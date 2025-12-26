import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvHumanToSky(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvHumanToSky'
    bl_label = 'LB Human to Sky Relation'
    sv_icon = 'LB_HUMANTOSKY'
    sv_north_: StringProperty(
        name='north_',
        update=updateNode,
        description='A number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. 90 is West and 270 is East. This can also be Vector for the direction to North. (Default: 0)')
    sv__location: StringProperty(
        name='_location',
        update=updateNode,
        description='A ladybug Location that has been output from the "LB Import EPW" component, the "LB Import Location" component, or the "LB Construct Location" component. This will be used to compute hourly sun positions for the fract_body_exp.')
    sv__position: StringProperty(
        name='_position',
        update=updateNode,
        description='A point for the position of the human subject in the Rhino scene. This is used to understand where a person is in relationship to the _context. The point input here should be at the feet of the human a series of points will be generated above. This can also be a list of points, which will result in several outputs.')
    sv__context: StringProperty(
        name='_context',
        update=updateNode,
        description='Rhino Breps and/or Rhino Meshes representing context geometry that can block the human subject\'s direct sun and view to the sky.')
    sv__pt_count_: StringProperty(
        name='_pt_count_',
        update=updateNode,
        description='A positive integer for the number of points used to represent the human subject geometry. Points are evenly distributed over the _height_ and are used to compute fracitonal values for the fract_body_exp in the case that only some of the points can see the sun. When context shade around the subject is large or coarse, using a single point is likely to return similar results as using several points. However, this number should be increased when context is detailed and has the potential to shade only part of the human subject at a given time. (Default: 1).')
    sv__height_: StringProperty(
        name='_height_',
        update=updateNode,
        description='A number for the the height of the human subject in the current Rhino Model units. (Default: 1.8 m in the equivalent Rhino Model units; roughly the average height of a standing adult).')
    sv__cpu_count_: StringProperty(
        name='_cpu_count_',
        update=updateNode,
        description='An integer to set the number of CPUs used in the execution of the intersection calculation. If unspecified, it will automatically default to one less than the number of CPUs currently available on the machine or 1 if only one processor is available.')
    sv__run: StringProperty(
        name='_run',
        update=updateNode,
        description='Set to "True" to run the component and compute the human/sky relationship. If set to "False" but all other required inputs are specified, this component will output points showing the human subject.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', 'north_')
        input_node.prop_name = 'sv_north_'
        input_node.tooltip = 'A number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. 90 is West and 270 is East. This can also be Vector for the direction to North. (Default: 0)'
        input_node = self.inputs.new('SvLBSocket', '_location')
        input_node.prop_name = 'sv__location'
        input_node.tooltip = 'A ladybug Location that has been output from the "LB Import EPW" component, the "LB Import Location" component, or the "LB Construct Location" component. This will be used to compute hourly sun positions for the fract_body_exp.'
        input_node = self.inputs.new('SvLBSocket', '_position')
        input_node.prop_name = 'sv__position'
        input_node.tooltip = 'A point for the position of the human subject in the Rhino scene. This is used to understand where a person is in relationship to the _context. The point input here should be at the feet of the human a series of points will be generated above. This can also be a list of points, which will result in several outputs.'
        input_node = self.inputs.new('SvLBSocket', '_context')
        input_node.prop_name = 'sv__context'
        input_node.tooltip = 'Rhino Breps and/or Rhino Meshes representing context geometry that can block the human subject\'s direct sun and view to the sky.'
        input_node = self.inputs.new('SvLBSocket', '_pt_count_')
        input_node.prop_name = 'sv__pt_count_'
        input_node.tooltip = 'A positive integer for the number of points used to represent the human subject geometry. Points are evenly distributed over the _height_ and are used to compute fracitonal values for the fract_body_exp in the case that only some of the points can see the sun. When context shade around the subject is large or coarse, using a single point is likely to return similar results as using several points. However, this number should be increased when context is detailed and has the potential to shade only part of the human subject at a given time. (Default: 1).'
        input_node = self.inputs.new('SvLBSocket', '_height_')
        input_node.prop_name = 'sv__height_'
        input_node.tooltip = 'A number for the the height of the human subject in the current Rhino Model units. (Default: 1.8 m in the equivalent Rhino Model units; roughly the average height of a standing adult).'
        input_node = self.inputs.new('SvLBSocket', '_cpu_count_')
        input_node.prop_name = 'sv__cpu_count_'
        input_node.tooltip = 'An integer to set the number of CPUs used in the execution of the intersection calculation. If unspecified, it will automatically default to one less than the number of CPUs currently available on the machine or 1 if only one processor is available.'
        input_node = self.inputs.new('SvLBSocket', '_run')
        input_node.prop_name = 'sv__run'
        input_node.tooltip = 'Set to "True" to run the component and compute the human/sky relationship. If set to "False" but all other required inputs are specified, this component will output points showing the human subject.'
        output_node = self.outputs.new('SvLBSocket', 'human_points')
        output_node.tooltip = 'The points used to represent the human subject in the calculation of the fraction of the body exposed to sun. Note that these are generated even when _run is set to "False".'
        output_node = self.outputs.new('SvLBSocket', 'human_line')
        output_node.tooltip = 'Line representing the height of the human subject. Note that this is generated even when _run is set to "False".'
        output_node = self.outputs.new('SvLBSocket', 'fract_body_exp')
        output_node.tooltip = 'A data collection for the fraction of the body exposed to direct sunlight at each hour of the year. This can be plugged into the "Solar MRT" components in order to account for context shading in the computation of MRT.'
        output_node = self.outputs.new('SvLBSocket', 'sky_exposure')
        output_node.tooltip = 'A single number between 0 and 1 for the fraction of the sky vault in human subject’s view. This can be plugged into the "Solar MRT" components in order to account for context shading in the computation of MRT.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate parameters for the relationship between human geometry and the sky given the position of a human subject and context geometry surrounding this position. _ The outputs of this component can be plugged into either the "LB Outdoor Solar MRT" or the "LB Indoor Solar MRT" in order to account for context shading around a human subject in these MRT calculations. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['human_points', 'human_line', 'fract_body_exp', 'sky_exposure']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['north_', '_location', '_position', '_context', '_pt_count_', '_height_', '_cpu_count_', '_run']
        self.sv_input_types = ['System.Object', 'System.Object', 'Point3d', 'GeometryBase', 'int', 'double', 'int', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'list', 'list', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, north_, _location, _position, _context, _pt_count_, _height_, _cpu_count_, _run):

        import math
        
        try:
            from ladybug_geometry.geometry2d.pointvector import Vector2D
            from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
            from ladybug_geometry.geometry3d.line import LineSegment3D
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug.sunpath import Sunpath
            from ladybug.viewsphere import view_sphere
            from ladybug.datacollection import HourlyContinuousCollection
            from ladybug.header import Header
            from ladybug.analysisperiod import AnalysisPeriod
            from ladybug.datatype.fraction import Fraction
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.config import conversion_to_meters
            from ladybug_tools.togeometry import to_point3d, to_vector2d
            from ladybug_tools.fromgeometry import from_point3d, from_vector3d, \
                from_linesegment3d
            from ladybug_tools.intersect import join_geometry_to_mesh, intersect_mesh_rays
            from ladybug_tools.sverchok import all_required_inputs, list_to_data_tree, \
                recommended_processor_count
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        def human_height_points(position, height, pt_count):
            """Get a list of points and a line representing the human geometry.
        
            Args:
                position: Blender Ladybug point for the position of the human.
                height: Number for the height of the human.
                pt_count: Integer for the number of points representing the human.
        
            Returns:
                 A tuple with human points as first element and human line as second.
                 Both geomtries are Blender Ladybug geometries.
            """
            lb_feet_pt = to_point3d(position).move(Vector3D(0, 0, height / 100))
            lb_hum_line = LineSegment3D(lb_feet_pt, Vector3D(0, 0, height))
            lb_pts = [lb_hum_line.midpoint] if pt_count == 1 else \
                lb_hum_line.subdivide_evenly(pt_count - 1)
            if len(lb_pts) == pt_count - 1:  # sometimes tolerance kills the last point
                lb_pts.append(lb_feet_pt.move(Vector3D(0, 0, height)))
            h_points = [from_point3d(pt) for pt in lb_pts]
            return h_points, from_linesegment3d(lb_hum_line)
        
        
        def fract_exposed_from_mtx(person_sun_int_matrix, day_pattern):
            """Get a Data Collection of fraction exposed values from an intersection matrix.
        
            Args:
                person_sun_int_matrix: An intersection matrix of 0s and 1s for the points
                    of a single person.
                day_pattern: A list of 8760 booleans indicating whether the sun is
                    up (True) or down (Fasle).
        
            Returns:
                 A data collection for the fraction of body exposed.
             """
            pt_count = len(person_sun_int_matrix)
            fract_per_sun = [sum(pt_int_ar) / pt_count for pt_int_ar in zip(*person_sun_int_matrix)]
            fract_exp_vals = []
            per_sun_i = 0
            for is_sun in day_pattern:
                if is_sun:
                    fract_exp_vals.append(fract_per_sun[per_sun_i])
                    per_sun_i += 1
                else:
                    fract_exp_vals.append(0)
            meta_dat = {'type': 'Fraction of Body Exposed to Direct Sun'}
            fract_exp_head = Header(Fraction(), 'fraction', AnalysisPeriod(), meta_dat)
            return HourlyContinuousCollection(fract_exp_head, fract_exp_vals)
        
        
        def sky_exposure_from_mtx(person_sky_int_matrix, patch_weights):
            """Get a the sky exposure from an intersection matrix.
        
            Args:
                person_sky_int_matrix: An intersection matrix of 0s and 1s for the
                    points of a person intersected with the 145 tregenza patches.
                patch_weights: A list of 145 weights to be applies to the patches.
        
            Returns:
                 A value for the sky exposure of the person.
             """
            pt_count = len(person_sky_int_matrix)
            sky_exp_per_pt = [sum((r * w) / 145 for r, w in zip(int_list, patch_wghts))
                              for int_list in person_sky_int_matrix]
            return sum(sky_exp_per_pt) / pt_count
        
        
        if all_required_inputs(ghenv.Component):
            # process the north input if specified
            if north_ is not None:  # process the north_
                try:
                    north_ = math.degrees(to_vector2d(north_).angle_clockwise(Vector2D(0, 1)))
                except AttributeError:  # north angle instead of vector
                    north_ = float(north_)
            else:
                north_ = 0
        
            # set the default point count, height, and cpu_count if unspecified
            _pt_count_ = _pt_count_ if _pt_count_ is not None else 1
            _height_ = _height_ if _height_ is not None else 1.8 / conversion_to_meters()
            workers = _cpu_count_ if _cpu_count_ is not None else recommended_processor_count()
        
            # create the points representing the human geometry
            human_points = []
            human_line = []
            for pos in _position:
                hpts, hlin = human_height_points(pos, _height_, _pt_count_)
                human_points.extend(hpts)
                human_line.append(hlin)
        
            if _run:
                # mesh the context for the intersection calculation
                shade_mesh = join_geometry_to_mesh(_context)
        
                # generate the sun vectors for each sun-up hour of the year
                sp = Sunpath.from_location(_location, north_)
                sun_vecs = []
                day_pattern = []
                for hoy in range(8760):
                    sun = sp.calculate_sun_from_hoy(hoy)
                    day_pattern.append(sun.is_during_day)
                    if sun.is_during_day:
                        sun_vecs.append(from_vector3d(sun.sun_vector_reversed))
        
                # intersect the sun vectors with the context and compute fraction exposed
                sun_int_matrix, angles = intersect_mesh_rays(
                    shade_mesh, human_points, sun_vecs, cpu_count=workers)
                fract_body_exp = []
                for i in range(0, len(human_points), _pt_count_):
                    fract_body_exp.append(
                        fract_exposed_from_mtx(sun_int_matrix[i:i + _pt_count_], day_pattern))
        
                # generate the vectors and weights for sky exposure
                sky_vecs = [from_vector3d(vec) for vec in view_sphere.tregenza_dome_vectors]
                patch_wghts = view_sphere.dome_patch_weights(1)
        
                # compute the sky exposure
                sky_int_matrix, angles = intersect_mesh_rays(
                    shade_mesh, human_points, sky_vecs, cpu_count=workers)
                sky_exposure = []
                for i in range(0, len(human_points), _pt_count_):
                    sky_exposure.append(
                        sky_exposure_from_mtx(sky_int_matrix[i:i + _pt_count_], patch_wghts))
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvHumanToSky)

def unregister():
    bpy.utils.unregister_class(SvHumanToSky)
