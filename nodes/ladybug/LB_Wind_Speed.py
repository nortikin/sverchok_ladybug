import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvWindSpeed(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvWindSpeed'
    bl_label = 'LB Wind Speed'
    sv_icon = 'LB_WINDSPEED'
    sv__met_wind_vel: StringProperty(
        name='_met_wind_vel',
        update=updateNode,
        description='A data collection of meteorological wind speed measured at the _met_height_ with the _met_terrian [m/s]. Typically, this comes from the "LB Import EPW" component. This can also be a number for the meteorological wind speed in m/s.')
    sv__height_: StringProperty(
        name='_height_',
        update=updateNode,
        description='The height above the ground to be evaluated in meters. (Default: 1 meter, which is suitable for most thermal comfort models like PET and SET.).')
    sv__terrain_: StringProperty(
        name='_terrain_',
        update=updateNode,
        description='Text string that sets the terrain class associated with the output air_speed. This can also be an integer that codes for the terrain. (Default: city). Must be one the following. _ 0 = city - 50% of buildings above 21m over a distance of at least 2000m upwind. 1 = suburban - suburbs, wooded areas. 2 = country - open, with scattered objects generally less than 10m high. 3 = water - flat areas downwind of a large water body (max 500m inland).')
    sv__met_height_: StringProperty(
        name='_met_height_',
        update=updateNode,
        description='A number for the height above the ground at which the meteorological wind speed is measured in meters. (Default: 10 meters, which is the standard used by most airports and EPW files).')
    sv__met_terrain_: StringProperty(
        name='_met_terrain_',
        update=updateNode,
        description='Text string that sets the terrain class associated with the meteorological wind speed. This can also be an integer that codes for the terrain. (Default: country, which is typical of most airports where wind measurements are taken). Must be one the following. _ 0 = city - 50% of buildings above 21m over a distance of at least 2000m upwind. 1 = suburban - suburbs, wooded areas. 2 = country - open, with scattered objects generally less than 10m high. 3 = water - flat areas downwind of a large water body (max 500m inland).')
    sv_log_law_: StringProperty(
        name='log_law_',
        update=updateNode,
        description='A boolean to note whether the wind profile should use a logarithmic law to determine wind speeds instead of the default power law, which is used by EnergyPlus. (Default: False).')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_met_wind_vel')
        input_node.prop_name = 'sv__met_wind_vel'
        input_node.tooltip = 'A data collection of meteorological wind speed measured at the _met_height_ with the _met_terrian [m/s]. Typically, this comes from the "LB Import EPW" component. This can also be a number for the meteorological wind speed in m/s.'
        input_node = self.inputs.new('SvLBSocket', '_height_')
        input_node.prop_name = 'sv__height_'
        input_node.tooltip = 'The height above the ground to be evaluated in meters. (Default: 1 meter, which is suitable for most thermal comfort models like PET and SET.).'
        input_node = self.inputs.new('SvLBSocket', '_terrain_')
        input_node.prop_name = 'sv__terrain_'
        input_node.tooltip = 'Text string that sets the terrain class associated with the output air_speed. This can also be an integer that codes for the terrain. (Default: city). Must be one the following. _ 0 = city - 50% of buildings above 21m over a distance of at least 2000m upwind. 1 = suburban - suburbs, wooded areas. 2 = country - open, with scattered objects generally less than 10m high. 3 = water - flat areas downwind of a large water body (max 500m inland).'
        input_node = self.inputs.new('SvLBSocket', '_met_height_')
        input_node.prop_name = 'sv__met_height_'
        input_node.tooltip = 'A number for the height above the ground at which the meteorological wind speed is measured in meters. (Default: 10 meters, which is the standard used by most airports and EPW files).'
        input_node = self.inputs.new('SvLBSocket', '_met_terrain_')
        input_node.prop_name = 'sv__met_terrain_'
        input_node.tooltip = 'Text string that sets the terrain class associated with the meteorological wind speed. This can also be an integer that codes for the terrain. (Default: country, which is typical of most airports where wind measurements are taken). Must be one the following. _ 0 = city - 50% of buildings above 21m over a distance of at least 2000m upwind. 1 = suburban - suburbs, wooded areas. 2 = country - open, with scattered objects generally less than 10m high. 3 = water - flat areas downwind of a large water body (max 500m inland).'
        input_node = self.inputs.new('SvLBSocket', 'log_law_')
        input_node.prop_name = 'sv_log_law_'
        input_node.tooltip = 'A boolean to note whether the wind profile should use a logarithmic law to determine wind speeds instead of the default power law, which is used by EnergyPlus. (Default: False).'
        output_node = self.outputs.new('SvLBSocket', 'air_speed')
        output_node.tooltip = 'A data collection or single value for the air speed at the input _height_ above the ground for the input _terrain_. This can be plugged into thermal comfort models like PET or SET/PMV. Alternatively, by connecting the wind data to the "LB Wind rose" component, a wind rose for the input _terrain_ and _height_ above the ground can be produced.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Calculate wind speed at a specific height above the ground for a given terrain type. _ By default, the component will calculate wind speed at a height of 1 meter, which is suitable for most thermal comfort models like PET and SET. Alternatively, by hooking up the output wind data to the "LB Wind rose" component, a wind rose for any terrain or at height above the ground can be produced. _ This component uses the same wind profile function as used by the "LB Wind Profile" component. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['air_speed']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_met_wind_vel', '_height_', '_terrain_', '_met_height_', '_met_terrain_', 'log_law_']
        self.sv_input_types = ['System.Object', 'System.Object', 'string', 'double', 'string', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _met_wind_vel, _height_, _terrain_, _met_height_, _met_terrain_, log_law_):

        try:
            from ladybug.datacollection import BaseCollection
            from ladybug.windprofile import WindProfile
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        # dictionary to map integers to terrain types
        TERRAIN_TYPES = {
            '0': 'city',
            '1': 'suburban',
            '2': 'country',
            '3': 'water',
            'city': 'city',
            'suburban': 'suburban',
            'country': 'country',
            'water': 'water'
        }
        
        
        if all_required_inputs(ghenv.Component):
            # set default values
            _height_ = 1 if _height_ is None else _height_
            _terrain_ = 'city' if _terrain_ is None else TERRAIN_TYPES[_terrain_.lower()]
            _met_height_ = 10 if _met_height_ is None else _met_height_
            _met_terrain_ = 'country' if _met_terrain_ is None \
                else TERRAIN_TYPES[_met_terrain_.lower()]
            log_law_ = False if log_law_ is None else log_law_
        
            # create the wind profile object and extract the air speeds
            profile = WindProfile(_terrain_, _met_terrain_, _met_height_, log_law_)
            if isinstance(_met_wind_vel, BaseCollection):
                air_speed = profile.calculate_wind_data(_met_wind_vel, _height_)
            else:  # assume that it is a single number
                _met_wind_vel = float(_met_wind_vel)
                air_speed = profile.calculate_wind(_met_wind_vel, _height_)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvWindSpeed)

def unregister():
    bpy.utils.unregister_class(SvWindSpeed)
