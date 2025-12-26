import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvAnkleDraft(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvAnkleDraft'
    bl_label = 'LB Ankle Draft'
    sv_icon = 'LB_ANKLEDRAFT'
    sv__full_body_pmv: StringProperty(
        name='_full_body_pmv',
        update=updateNode,
        description='The full-body predicted mean vote (PMV) of the subject. Ankle draft depends on full-body PMV because subjects are more likely to feel uncomfortably cold at their extremities when their whole body is already feeling colder than neutral. The "LB PMV Comfort" component can be used to obatin this input here.')
    sv__draft_velocity: StringProperty(
        name='_draft_velocity',
        update=updateNode,
        description='The velocity of the draft in m/s at ankle level (10cm above the floor).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_full_body_pmv')
        input_node.prop_name = 'sv__full_body_pmv'
        input_node.tooltip = 'The full-body predicted mean vote (PMV) of the subject. Ankle draft depends on full-body PMV because subjects are more likely to feel uncomfortably cold at their extremities when their whole body is already feeling colder than neutral. The "LB PMV Comfort" component can be used to obatin this input here.'
        input_node = self.inputs.new('SvLBSocket', '_draft_velocity')
        input_node.prop_name = 'sv__draft_velocity'
        input_node.tooltip = 'The velocity of the draft in m/s at ankle level (10cm above the floor).'
        output_node = self.outputs.new('SvLBSocket', 'ppd')
        output_node.tooltip = 'The percentage of people dissatisfied (PPD) from cold drafts at ankle level.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate the percentage of people dissatisfied from cold drafts at ankle-level. _ The original tests used to create the model involved blowing cold air on subject\'s ankles at a height of 10 cm off of the ground. The formula was officially incorporated in the ASHRAE 55 standard in 2020 with a recommendation that PPD from ankle draft not exceed 20%. _ For more information on the methods used to create this model see the following: Liu, S., S. Schiavon, A. Kabanshi, W. Nazaroff. 2016. "Predicted percentage of dissatisfied with ankle draft." Accepted Author Manuscript. Indoor Environmental Quality. http://escholarship.org/uc/item/9076254n -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['ppd']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_full_body_pmv', '_draft_velocity']
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

    def process_ladybug(self, _full_body_pmv, _draft_velocity):

        try:
            from ladybug_comfort.local import ankle_draft_ppd
            from ladybug.datacollection import HourlyContinuousCollection
            from ladybug.datatype.fraction import PercentagePeopleDissatisfied
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            ppd = HourlyContinuousCollection.compute_function_aligned(
                ankle_draft_ppd, [_full_body_pmv, _draft_velocity],
                PercentagePeopleDissatisfied(), '%')
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvAnkleDraft)

def unregister():
    bpy.utils.unregister_class(SvAnkleDraft)
