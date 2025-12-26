import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvRTrad(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvRTrad'
    bl_label = 'LB Real Time Incident Radiation'
    sv_icon = 'LB_RTRAD'
    sv__int_mtx: StringProperty(
        name='_int_mtx',
        update=updateNode,
        description='A Geometry/Sky Intersection Matrix from the "LB Incident Radiation"  component. This matrix contains the relationship between each point of the analyzed geometry and each patch of the sky.')
    sv__sky_mtx: StringProperty(
        name='_sky_mtx',
        update=updateNode,
        description='A Sky Matrix from the "LB Cumulative Sky Matrix" component, which describes the radiation coming from the various patches of the sky. The "LB Sky Dome" component can be used to visualize any sky matrix.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_int_mtx')
        input_node.prop_name = 'sv__int_mtx'
        input_node.tooltip = 'A Geometry/Sky Intersection Matrix from the "LB Incident Radiation"  component. This matrix contains the relationship between each point of the analyzed geometry and each patch of the sky.'
        input_node = self.inputs.new('SvLBSocket', '_sky_mtx')
        input_node.prop_name = 'sv__sky_mtx'
        input_node.tooltip = 'A Sky Matrix from the "LB Cumulative Sky Matrix" component, which describes the radiation coming from the various patches of the sky. The "LB Sky Dome" component can be used to visualize any sky matrix.'
        output_node = self.outputs.new('SvLBSocket', 'results')
        output_node.tooltip = 'A list of numbers that aligns with the points of the original analysis performed with the "LB Incident Radiation"  component. Each number indicates the cumulative incident radiation received by each of the points from the sky matrix in kWh/m2. To visualize these radiation values in the Rhino scene, connect these values to the "LB Spatial Heatmap" component along with the mesh output from the original analysis with the "LB Incident Radiation"  component.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Compute Incident Radiation values for any sky matrix in real time using the Geometry/Sky intersection matrix produced by the "LB Incident Radiation" component. _ Using this component enables one to scroll through radiation on an hour-by-hour or month-by-month basis in a manner that is an order of magnitude faster than running each sky matrix through the "LB Incident Radiation" component. _ The speed of this component is thanks to the fact that the Geometry/Sky intersection matrix contains the relationship between the geometry and each patch of the sky. So computing new radiation values is as simple as multiplying the sky matrix by the intersection matrix. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['results']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_int_mtx', '_sky_mtx']
        self.sv_input_types = ['System.Object', 'System.Object']
        self.sv_input_defaults = [None, None]
        self.sv_input_access = ['item', 'item']
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

    def process_ladybug(self, _int_mtx, _sky_mtx):

        
        try:  # python 2
            from itertools import izip as zip
        except ImportError:  # python 3
            pass
        
        try:
            from ladybug_tools.sverchok import all_required_inputs, de_objectify_output
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # deconstruct the matrices and get the total radiation from each patch
            int_mtx = de_objectify_output(_int_mtx)
            sky_mtx = de_objectify_output(_sky_mtx)
            total_sky_rad = [dirr + difr for dirr, difr in zip(sky_mtx[1], sky_mtx[2])]
            ground_rad = [(sum(total_sky_rad) / len(total_sky_rad)) * sky_mtx[0][1]] * len(total_sky_rad)
            all_rad = total_sky_rad + ground_rad 
        
            # compute the results
            results = []
            for pt_rel in int_mtx:
                results.append(sum(r * w for r, w in zip(pt_rel, all_rad)))
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvRTrad)

def unregister():
    bpy.utils.unregister_class(SvRTrad)
