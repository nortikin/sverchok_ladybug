import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvRadAsymm(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvRadAsymm'
    bl_label = 'LB Radiant Asymmetry'
    sv_icon = 'LB_RADASYMM'
    sv__radiant_diff: StringProperty(
        name='_radiant_diff',
        update=updateNode,
        description='A number for the the radiant temperature difference between two sides of the same plane where an occupant is located [C]. This can also be a data collection representing the radiant temperature difference over time [C].')
    sv__asymmetry_type: StringProperty(
        name='_asymmetry_type',
        update=updateNode,
        description='Text or an integer that representing the type of radiant asymmetry being evaluated. Occupants are more sensitive to warm ceilings and cool walls than cool ceilings and warm walls. Choose from the following options. _ * 0 = WarmCeiling * 1 = CoolWall * 2 = CoolCeiling * 3 = WarmWall')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_radiant_diff')
        input_node.prop_name = 'sv__radiant_diff'
        input_node.tooltip = 'A number for the the radiant temperature difference between two sides of the same plane where an occupant is located [C]. This can also be a data collection representing the radiant temperature difference over time [C].'
        input_node = self.inputs.new('SvLBSocket', '_asymmetry_type')
        input_node.prop_name = 'sv__asymmetry_type'
        input_node.tooltip = 'Text or an integer that representing the type of radiant asymmetry being evaluated. Occupants are more sensitive to warm ceilings and cool walls than cool ceilings and warm walls. Choose from the following options. _ * 0 = WarmCeiling * 1 = CoolWall * 2 = CoolCeiling * 3 = WarmWall'
        output_node = self.outputs.new('SvLBSocket', 'ppd')
        output_node.tooltip = 'The percentage of people dissatisfied (PPD) for the input radiant asymmetry.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate the percentage of people dissatisfied from radiant asymmetry. _ The comfort functions used here come from Figure 5.2.4.1 of ASHRAE 55 2010. Note that, if the resulting input results in a PPD beyond what is included in this Figure, the maximum PPD will simply be returned. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['ppd']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_radiant_diff', '_asymmetry_type']
        self.sv_input_types = ['System.Object', 'string']
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

    def process_ladybug(self, _radiant_diff, _asymmetry_type):

        try:
            from ladybug_comfort.local import radiant_asymmetry_ppd
            from ladybug.datacollection import HourlyContinuousCollection
            from ladybug.datatype.fraction import PercentagePeopleDissatisfied
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        ASYMMETRY_TYPES = {
            '0': 0,
            '1': 1,
            '2': 2,
            '3': 3,
            'WarmCeiling': 0,
            'CoolWall': 1,
            'CoolCeiling': 2,
            'WarmWall': 3
        }
        
        
        
        if all_required_inputs(ghenv.Component):
            ppd = HourlyContinuousCollection.compute_function_aligned(
                radiant_asymmetry_ppd, [_radiant_diff, ASYMMETRY_TYPES[_asymmetry_type]],
                PercentagePeopleDissatisfied(), '%')
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvRadAsymm)

def unregister():
    bpy.utils.unregister_class(SvRadAsymm)
