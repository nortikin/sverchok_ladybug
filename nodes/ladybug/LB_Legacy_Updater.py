import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvLegacy(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvLegacy'
    bl_label = 'LB Legacy Updater'
    sv_icon = 'LB_LEGACY'
    sv__update: StringProperty(
        name='_update',
        update=updateNode,
        description='Set to "True" to have this component to search through the current Grasshopper file and drop suggested Ladybug Tools components for every Legacy Ladybug + Honeybee component on the canvas.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_update')
        input_node.prop_name = 'sv__update'
        input_node.tooltip = 'Set to "True" to have this component to search through the current Grasshopper file and drop suggested Ladybug Tools components for every Legacy Ladybug + Honeybee component on the canvas.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Drop suggested Ladybug Tools components into a Grasshopper file for every Legacy Ladybug + Honeybee component on the canvas. - All existing LBT and native Grasshopper components will be left as they are and only the Legacy components will be circled in Red and have the suggested LBT component placed next to them (if applicable). Note that, after this component runs, you must then connect the new LBT components to the others and delete the Legacy components. - Where applicable, each red circle will have a message about how the LBT component differs from the Legacy one or if there may be a more appropirate LBT component in the future. Also note that some Legacy workflows have been heavily refactored since Legacy, meaning a different number of components may be necessary to achieve the same thing (typically fewer in LBT than Legacy, meaning some LEgacy components should be deleted without replacement). -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = []
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_update']
        self.sv_input_types = ['System.Object']
        self.sv_input_defaults = [None]
        self.sv_input_access = ['item']
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

    def process_ladybug(self, _update):

        try:
            from ladybug_tools.versioning.gather import gather_canvas_components
            from ladybug_tools.versioning.legacy import suggest_new_component
            from ladybug_tools.sverchok import all_required_inputs, give_warning
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component) and _update:
            # load all of the Python userobjects and update the versions
            components = gather_canvas_components(ghenv.Component)
            report_init = []
            for comp in components:
                try:
                    report_init.append(suggest_new_component(comp, ghenv.Component))
                except Exception:
                    if hasattr(comp, 'Name'):
                        msg = 'Failed to Update "{}"'.format(comp.Name)
                        print(msg)
                        give_warning(ghenv.Component, msg)
            print(('\n'.join(r for r in report_init if r)))
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvLegacy)

def unregister():
    bpy.utils.unregister_class(SvLegacy)
