import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvToStep(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvToStep'
    bl_label = 'LB Convert to Timestep'
    sv_icon = 'LB_TOSTEP'
    sv__data: StringProperty(
        name='_data',
        update=updateNode,
        description='A Ladybug Hourly DataCollection object.  This can be either continuous or discontinuous.')
    sv__timestep_: StringProperty(
        name='_timestep_',
        update=updateNode,
        description='The timestep to which the data will be converted. If this is higher than the input _data timestep, values will be linerarly interpolated to the new timestep.  If it is lower, values that do not fit the timestep will be removed from the DataCollection. (Defaut: 1)')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_data')
        input_node.prop_name = 'sv__data'
        input_node.tooltip = 'A Ladybug Hourly DataCollection object.  This can be either continuous or discontinuous.'
        input_node = self.inputs.new('SvLBSocket', '_timestep_')
        input_node.prop_name = 'sv__timestep_'
        input_node.tooltip = 'The timestep to which the data will be converted. If this is higher than the input _data timestep, values will be linerarly interpolated to the new timestep.  If it is lower, values that do not fit the timestep will be removed from the DataCollection. (Defaut: 1)'
        output_node = self.outputs.new('SvLBSocket', 'data')
        output_node.tooltip = 'A Continuous DataCollection at the input _timestep_.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Convert a hourly Ladybug data collection to a continuous collection at a specific timestep. _ This will be done either through linear interpolation or by culling out values that do not fit the timestep.  It can also be used to convert a discontinous data collection to a continuous one by linearly interpolating over holes in the data set. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['data']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_data', '_timestep_']
        self.sv_input_types = ['System.Object', 'int']
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

    def process_ladybug(self, _data, _timestep_):

        try:
            from ladybug.datacollection import HourlyDiscontinuousCollection, \
                HourlyContinuousCollection
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # check the inputs
            assert isinstance(_data, HourlyDiscontinuousCollection), \
                ' Connected _data is not a Hourly Data Collection. Got{}'.format(type(_data))
            if _timestep_ is not None:
                valid_timesteps = _data.header.analysis_period.VALIDTIMESTEPS
                assert _timestep_ in valid_timesteps, ' Connected _timestep_ is not a'\
                    ' hourly timestep.\n Got {}. Choose from: {}'.format(
                    _timestep_, sorted(valid_timesteps.keys()))
        
            # if the data is not continuous, interpolate over holes.
            if not isinstance(_data, HourlyContinuousCollection):
                if _data.validated_a_period is False:
                    _data = data.validate_analysis_period
                _data = _data.interpolate_holes()
        
            # convert the data to the timestep
            if _timestep_ and _timestep_ != _data.header.analysis_period.timestep:
                if _timestep_ < _data.header.analysis_period.timestep:
                    data = _data.cull_to_timestep(_timestep_)
                else:
                    data = _data.interpolate_to_timestep(_timestep_)
            else:
                data = _data

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvToStep)

def unregister():
    bpy.utils.unregister_class(SvToStep)
