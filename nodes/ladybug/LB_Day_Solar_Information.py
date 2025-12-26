import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvDayInfo(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvDayInfo'
    bl_label = 'LB Day Solar Information'
    sv_icon = 'LB_DAYINFO'
    sv__location: StringProperty(
        name='_location',
        update=updateNode,
        description='A ladybug Location that has been output from the "LB Import EPW" component or the "LB Construct Location" component.')
    sv__doy: StringProperty(
        name='_doy',
        update=updateNode,
        description='An integer for the day of the year for which solar information is be computed. The "LB Calculate HOY" component can be used to compute the day of the year from month and day inputs.')
    sv__depression_: StringProperty(
        name='_depression_',
        update=updateNode,
        description='An angle in degrees indicating the additional period before/after the edge of the sun has passed the horizon where the sun is still considered up. Setting this value to 0 will compute sunrise/sunset as the time when the edge of the sun begins to touch the horizon. Setting it to the angular diameter of the sun (0.5334) will compute sunrise/sunset as the time when the sun just finishes passing the horizon (actual physical sunset). Setting it to 0.833 will compute the apparent sunrise/sunset, accounting for atmospheric refraction. Setting this to 6 will compute sunrise/sunset as the beginning/end of civil twilight. Setting this to 12 will compute sunrise/sunset as the beginning/end of nautical twilight. Setting this to 18 will compute sunrise/sunset as the beginning/end of astronomical twilight. (Default: 0.5334 for the physical sunset).')
    sv_solar_time_: StringProperty(
        name='solar_time_',
        update=updateNode,
        description='A boolean to indicate if the output datetimes for sunrise, noon and sunset should be in solar time as opposed to the time zone of the location. (Default: False).')
    sv_dl_saving_: StringProperty(
        name='dl_saving_',
        update=updateNode,
        description='An optional analysis period for daylight saving time. This will be used to adjust the output times by an hour when applicable. If unspecified, no daylight saving time will be used')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_location')
        input_node.prop_name = 'sv__location'
        input_node.tooltip = 'A ladybug Location that has been output from the "LB Import EPW" component or the "LB Construct Location" component.'
        input_node = self.inputs.new('SvLBSocket', '_doy')
        input_node.prop_name = 'sv__doy'
        input_node.tooltip = 'An integer for the day of the year for which solar information is be computed. The "LB Calculate HOY" component can be used to compute the day of the year from month and day inputs.'
        input_node = self.inputs.new('SvLBSocket', '_depression_')
        input_node.prop_name = 'sv__depression_'
        input_node.tooltip = 'An angle in degrees indicating the additional period before/after the edge of the sun has passed the horizon where the sun is still considered up. Setting this value to 0 will compute sunrise/sunset as the time when the edge of the sun begins to touch the horizon. Setting it to the angular diameter of the sun (0.5334) will compute sunrise/sunset as the time when the sun just finishes passing the horizon (actual physical sunset). Setting it to 0.833 will compute the apparent sunrise/sunset, accounting for atmospheric refraction. Setting this to 6 will compute sunrise/sunset as the beginning/end of civil twilight. Setting this to 12 will compute sunrise/sunset as the beginning/end of nautical twilight. Setting this to 18 will compute sunrise/sunset as the beginning/end of astronomical twilight. (Default: 0.5334 for the physical sunset).'
        input_node = self.inputs.new('SvLBSocket', 'solar_time_')
        input_node.prop_name = 'sv_solar_time_'
        input_node.tooltip = 'A boolean to indicate if the output datetimes for sunrise, noon and sunset should be in solar time as opposed to the time zone of the location. (Default: False).'
        input_node = self.inputs.new('SvLBSocket', 'dl_saving_')
        input_node.prop_name = 'sv_dl_saving_'
        input_node.tooltip = 'An optional analysis period for daylight saving time. This will be used to adjust the output times by an hour when applicable. If unspecified, no daylight saving time will be used'
        output_node = self.outputs.new('SvLBSocket', 'sunrise')
        output_node.tooltip = 'The time of sunrise expressed as HH:MM where hours range from 0 to 23. Note that this may be None if there is no sunrise or sunset on the specified day. (eg. at the north pole on the winter solstice).'
        output_node = self.outputs.new('SvLBSocket', 'sunset')
        output_node.tooltip = 'The time of sunset expressed as HH:MM where hours range from 0 to 23. Note that this may be None if there is no sunrise or sunset on the specified day. (eg. at the north pole on the winter solstice).'
        output_node = self.outputs.new('SvLBSocket', 'solar_noon')
        output_node.tooltip = 'The time of solar noon when the sun is at its highest point in the sky, expressed as HH:MM.'
        output_node = self.outputs.new('SvLBSocket', 'noon_alt')
        output_node.tooltip = 'The altitude of the sun at solar noon in degrees. This is the maximum altitude that will be expereinced on the input day.'
        output_node = self.outputs.new('SvLBSocket', 'day_length')
        output_node.tooltip = 'The length of the input day in hours.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Compute solar infomation about a day of the year at a particular location. This includes the time of sunrise, sunset, solar noon, and the length of the day in hours. _ Note that these times are intended to represent a typical year and they will often vary by a few minutes depending on where in the leap year cycle a given year falls. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['sunrise', 'sunset', 'solar_noon', 'noon_alt', 'day_length']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_location', '_doy', '_depression_', 'solar_time_', 'dl_saving_']
        self.sv_input_types = ['System.Object', 'int', 'double', 'bool', 'System.Object']
        self.sv_input_defaults = [None, None, None, None, None]
        self.sv_input_access = ['item', 'list', 'item', 'item', 'item']
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

    def process_ladybug(self, _location, _doy, _depression_, solar_time_, dl_saving_):

        try:
            from ladybug.sunpath import Sunpath
            from ladybug.dt import Date
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component):
            # set default values
            solar_time_ = False if solar_time_ is None else solar_time_  # process solar time
            _depression_ = 0.5334 if _depression_ is None else _depression_
        
            # initialize sunpath based on location
            sp = Sunpath.from_location(_location, 0, dl_saving_)
        
            # for each day of the year, compute the information
            sunrise, sunset, solar_noon, noon_alt, day_length = [], [], [], [], []
            for doy in _doy:
                doy_date = Date.from_doy(doy)
                solar_info = sp.calculate_sunrise_sunset(
                    doy_date.month, doy_date.day, _depression_, solar_time_)
                print(solar_info)
                sr, sn, ss = solar_info['sunrise'], solar_info['noon'], solar_info['sunset']
                solar_noon.append(sn.time)
                noon_alt.append(sp.calculate_sun_from_date_time(sn).altitude)
                if sr is not None:
                    sunrise.append(sr.time)
                else:
                    sunrise.append(None)
                if ss is not None:
                    sunset.append(ss.time)
                    day_length.append((ss - sr).total_seconds() / 3600)
                else:
                    sunset.append(None)
                    day_length.append(None)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvDayInfo)

def unregister():
    bpy.utils.unregister_class(SvDayInfo)
