import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvMeshSelector(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvMeshSelector'
    bl_label = 'LB Mesh Threshold Selector'
    sv_icon = 'LB_MESHSELECTOR'
    sv__values: StringProperty(
        name='_values',
        update=updateNode,
        description='A list of numbers that correspond to either the number of faces or vertices of the _mesh.')
    sv__mesh: StringProperty(
        name='_mesh',
        update=updateNode,
        description='The mesh from which a sub-region will be selected. This is typically a colored mesh output from a study.')
    sv__operator_: StringProperty(
        name='_operator_',
        update=updateNode,
        description='A text string representing an operator for the the conditional statement.  The default is greater than (>).  This must be an operator in python and examples include the following: * > - Greater Than * < - Less Than * >= - Greater or Equal * <= - Less or Equal * == - Equals * != - Does not Equal')
    sv__pct_threshold_: StringProperty(
        name='_pct_threshold_',
        update=updateNode,
        description='A number between 0 and 100 that represents the percentage of the mesh faces or vertices to be included in the resulting sub_mesh. (Default: 25%).')
    sv_abs_threshold_: StringProperty(
        name='abs_threshold_',
        update=updateNode,
        description='An optional number that represents the absolute threshold above which a given mesh face or vertex is included in the resulting sub_mesh. An input here will override the percent threshold input above.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_values')
        input_node.prop_name = 'sv__values'
        input_node.tooltip = 'A list of numbers that correspond to either the number of faces or vertices of the _mesh.'
        input_node = self.inputs.new('SvLBSocket', '_mesh')
        input_node.prop_name = 'sv__mesh'
        input_node.tooltip = 'The mesh from which a sub-region will be selected. This is typically a colored mesh output from a study.'
        input_node = self.inputs.new('SvLBSocket', '_operator_')
        input_node.prop_name = 'sv__operator_'
        input_node.tooltip = 'A text string representing an operator for the the conditional statement.  The default is greater than (>).  This must be an operator in python and examples include the following: * > - Greater Than * < - Less Than * >= - Greater or Equal * <= - Less or Equal * == - Equals * != - Does not Equal'
        input_node = self.inputs.new('SvLBSocket', '_pct_threshold_')
        input_node.prop_name = 'sv__pct_threshold_'
        input_node.tooltip = 'A number between 0 and 100 that represents the percentage of the mesh faces or vertices to be included in the resulting sub_mesh. (Default: 25%).'
        input_node = self.inputs.new('SvLBSocket', 'abs_threshold_')
        input_node.prop_name = 'sv_abs_threshold_'
        input_node.tooltip = 'An optional number that represents the absolute threshold above which a given mesh face or vertex is included in the resulting sub_mesh. An input here will override the percent threshold input above.'
        output_node = self.outputs.new('SvLBSocket', 'total_value')
        output_node.tooltip = 'The sum of each value that meets the criteria multiplied by the corresponding mesh face area. This can generally be used to understand how much value is captured according to the conditional critera. For example, if the input _mesh is a radiation study, this is equal to the total radiation falling on the sub_mesh. This may or may not be meaningful depending on the units of the connected _values. This output will always be zero for cases where values correspond to mesh vertices and not faces.'
        output_node = self.outputs.new('SvLBSocket', 'total_area')
        output_node.tooltip = 'The area of the sub_mesh that meets the criteria.'
        output_node = self.outputs.new('SvLBSocket', 'sub_mesh')
        output_node.tooltip = 'A new mesh with the faces or vertices removed to reveal just the portion that satisfies the conditional criteria. By default, this is hidden to that just the outline appears in the geometry preview.'
        output_node = self.outputs.new('SvLBSocket', 'outline')
        output_node.tooltip = 'A set of lines outlining the portion of the mesh that is above the threshold.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Select a sub-region of a mesh using aligned values and conditional criteria. _ This has multiple uses and can be applied to any study that outputs a list of results that are aligned with a mesh. For example, quantifying the daylit area from a daylight analysis, selecting the portion of a roof with enough solar radiation for photovoltaic panels, etc. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['total_value', 'total_area', 'sub_mesh', 'outline']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_values', '_mesh', '_operator_', '_pct_threshold_', 'abs_threshold_']
        self.sv_input_types = ['double', 'Mesh', 'string', 'double', 'double']
        self.sv_input_defaults = [None, None, None, None, None]
        self.sv_input_access = ['list', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _values, _mesh, _operator_, _pct_threshold_, abs_threshold_):

        try:
            from ladybug_tools.togeometry import to_mesh3d
            from ladybug_tools.fromgeometry import from_mesh3d_to_outline
            from ladybug_tools.sverchok import all_required_inputs, hide_output
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # check the input values and provide defaults
            lb_mesh = to_mesh3d(_mesh)
            val_count = len(_values)
            face_match = val_count == len(lb_mesh.faces)
            assert face_match or val_count == len(lb_mesh.vertices), \
                'Number of _values ({}) must match the number of mesh faces ({}) or ' \
                'the number of mesh vertices ({}).'.format(
                    val_count, len(lb_mesh.faces), len(lb_mesh.faces))
            fract_thresh = 0.25 if _pct_threshold_ is None else _pct_threshold_ / 100
            operator = '>' if _operator_ is None else _operator_.strip()
            if operator in ('==', '!='):
                assert abs_threshold_ is not None, 'An abs_threshold_ must be ' \
                    'specified to use the "{}" operator.'.format(operator)
        
            # get a list of boolean values that meet the conditional criteria
            if abs_threshold_ is not None:
                statement = '{} ' + operator + str(abs_threshold_)
                pattern = []
                for val in _values:
                    pattern.append(eval(statement.format(val), {}))
            else:
                pattern = [False] * val_count
                target_count = int(fract_thresh * (val_count))
                face_i_sort = [x for (y, x) in sorted(zip(_values, list(range(val_count))))]
                rel_values = list(reversed(face_i_sort)) if '>' in operator else face_i_sort
                for cnt in rel_values[:target_count]:
                    pattern[cnt] = True
        
            # remove the faces or vertices from the mesh and compute the outputs
            total_value, total_area = 0, 0
            try:
                sub_mesh_lb, vf_pattern = lb_mesh.remove_faces(pattern) if face_match else \
                    lb_mesh.remove_vertices(pattern)
                if face_match:
                    for incl, val, area in zip(pattern, _values, lb_mesh.face_areas):
                        if incl:
                            total_area += area
                            total_value += val * area
                else:
                    total_area = sub_mesh_lb.area
                # convert everything to Blender Ladybug geometry
                sub_mesh, outline = from_mesh3d_to_outline(sub_mesh_lb)
                hide_output(ghenv.Component, 3)
            except AssertionError as e:
                if not 'Mesh must have at least one face' in str(e):
                    raise AssertionError(e)

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvMeshSelector)

def unregister():
    bpy.utils.unregister_class(SvMeshSelector)
