import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvBenefitMatrix(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvBenefitMatrix'
    bl_label = 'LB Benefit Sky Matrix'
    sv_icon = 'LB_BENEFITMATRIX'
    sv_north_: StringProperty(
        name='north_',
        update=updateNode,
        description='A number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. 90 is West and 270 is East. This can also be Vector for the direction to North. (Default: 0)')
    sv__location: StringProperty(
        name='_location',
        update=updateNode,
        description='A ladybug Location that has been output from the "LB Import EPW" component or the "LB Construct Location" component.')
    sv__temperature: StringProperty(
        name='_temperature',
        update=updateNode,
        description='An annual hourly DataCollection of temperature, which will be used to establish whether radiation is desired or not for each time step.')
    sv__bal_temp_: StringProperty(
        name='_bal_temp_',
        update=updateNode,
        description='The temperature in Celsius between which radiation switches from being a benefit to a harm. Typical residential buildings have balance temperatures as high as 18C and commercial buildings tend to have lower values around 12C. (Default 15C).')
    sv__bal_offset_: StringProperty(
        name='_bal_offset_',
        update=updateNode,
        description='The temperature offset from the balance temperature in Celsius where radiation is neither harmful nor helpful. (Default: 2).')
    sv__direct_rad: StringProperty(
        name='_direct_rad',
        update=updateNode,
        description='An annual hourly DataCollection of Direct Normal Radiation such as that which is output from the "LB Import EPW" component or the "LB Import STAT" component.')
    sv__diffuse_rad: StringProperty(
        name='_diffuse_rad',
        update=updateNode,
        description='An annual hourly DataCollection of Diffuse Horizontal Radiation such as that which is output from the "LB Import EPW" component or the "LB Import STAT" component.')
    sv__hoys_: StringProperty(
        name='_hoys_',
        update=updateNode,
        description='A number or list of numbers between 0 and 8760 that respresent the hour(s) of the year for which to generate the sky matrix. The "LB Calculate HOY" component can output this number given a month, day and hour. The "LB Analysis Period" component can output a list of HOYs within a certain hour or date range. By default, the matrix will be for the entire year.')
    sv_high_density_: StringProperty(
        name='high_density_',
        update=updateNode,
        description='A Boolean to indicate whether the higher-density Reinhart sky matrix should be generated (True), which has roughly 4 times the sky patches as the (default) original Tregenza sky (False). Note that, while the Reinhart sky has a higher resolution and is more accurate, it will result in considerably longer calculation time for incident radiation studies. The difference in sky resolution can be observed with the "LB Sky Dome" component. (Default: False).')
    sv__ground_ref_: StringProperty(
        name='_ground_ref_',
        update=updateNode,
        description='A number between 0 and 1 to note the average ground reflectance that is associated with the sky matrix. (Default: 0.2).')
    sv__folder_: StringProperty(
        name='_folder_',
        update=updateNode,
        description='The folder in which the Radiance commands are executed to produce the sky matrix. If None, it will be written to Ladybug\'s default EPW folder.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', 'north_')
        input_node.prop_name = 'sv_north_'
        input_node.tooltip = 'A number between -360 and 360 for the counterclockwise difference between the North and the positive Y-axis in degrees. 90 is West and 270 is East. This can also be Vector for the direction to North. (Default: 0)'
        input_node = self.inputs.new('SvLBSocket', '_location')
        input_node.prop_name = 'sv__location'
        input_node.tooltip = 'A ladybug Location that has been output from the "LB Import EPW" component or the "LB Construct Location" component.'
        input_node = self.inputs.new('SvLBSocket', '_temperature')
        input_node.prop_name = 'sv__temperature'
        input_node.tooltip = 'An annual hourly DataCollection of temperature, which will be used to establish whether radiation is desired or not for each time step.'
        input_node = self.inputs.new('SvLBSocket', '_bal_temp_')
        input_node.prop_name = 'sv__bal_temp_'
        input_node.tooltip = 'The temperature in Celsius between which radiation switches from being a benefit to a harm. Typical residential buildings have balance temperatures as high as 18C and commercial buildings tend to have lower values around 12C. (Default 15C).'
        input_node = self.inputs.new('SvLBSocket', '_bal_offset_')
        input_node.prop_name = 'sv__bal_offset_'
        input_node.tooltip = 'The temperature offset from the balance temperature in Celsius where radiation is neither harmful nor helpful. (Default: 2).'
        input_node = self.inputs.new('SvLBSocket', '_direct_rad')
        input_node.prop_name = 'sv__direct_rad'
        input_node.tooltip = 'An annual hourly DataCollection of Direct Normal Radiation such as that which is output from the "LB Import EPW" component or the "LB Import STAT" component.'
        input_node = self.inputs.new('SvLBSocket', '_diffuse_rad')
        input_node.prop_name = 'sv__diffuse_rad'
        input_node.tooltip = 'An annual hourly DataCollection of Diffuse Horizontal Radiation such as that which is output from the "LB Import EPW" component or the "LB Import STAT" component.'
        input_node = self.inputs.new('SvLBSocket', '_hoys_')
        input_node.prop_name = 'sv__hoys_'
        input_node.tooltip = 'A number or list of numbers between 0 and 8760 that respresent the hour(s) of the year for which to generate the sky matrix. The "LB Calculate HOY" component can output this number given a month, day and hour. The "LB Analysis Period" component can output a list of HOYs within a certain hour or date range. By default, the matrix will be for the entire year.'
        input_node = self.inputs.new('SvLBSocket', 'high_density_')
        input_node.prop_name = 'sv_high_density_'
        input_node.tooltip = 'A Boolean to indicate whether the higher-density Reinhart sky matrix should be generated (True), which has roughly 4 times the sky patches as the (default) original Tregenza sky (False). Note that, while the Reinhart sky has a higher resolution and is more accurate, it will result in considerably longer calculation time for incident radiation studies. The difference in sky resolution can be observed with the "LB Sky Dome" component. (Default: False).'
        input_node = self.inputs.new('SvLBSocket', '_ground_ref_')
        input_node.prop_name = 'sv__ground_ref_'
        input_node.tooltip = 'A number between 0 and 1 to note the average ground reflectance that is associated with the sky matrix. (Default: 0.2).'
        input_node = self.inputs.new('SvLBSocket', '_folder_')
        input_node.prop_name = 'sv__folder_'
        input_node.tooltip = 'The folder in which the Radiance commands are executed to produce the sky matrix. If None, it will be written to Ladybug\'s default EPW folder.'
        output_node = self.outputs.new('SvLBSocket', 'sky_mtx')
        output_node.tooltip = 'A sky matrix object containing the radiation benefit/harm coming from each patch of the sky. This can be used for a radiation study, a radition rose, or a sky dome visualization. It can also be deconstructed into its individual values with the "LB Deconstruct Matrix" component.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Get a matrix representing the benefit/harm of radiation based on temperature data. _ When this sky matrix is used in radiation studies or to produce radiation graphics, positive values represent helpful wintertime sun energy that can offset heating loads during cold temperatures while negative values represent harmful summertime sun energy that can increase cooling loads during hot temperatures. _ Radiation benefit skies are particularly helpful for evaluating building massing and facade designs in terms of passive solar heat gain vs. cooling energy increase. _ This component uses Radiance\'s gendaymtx function to calculate the radiation for each patch of the sky. Gendaymtx is written by Ian Ashdown and Greg Ward. Morere information can be found in Radiance manual at: http://www.radiance-online.org/learning/documentation/manual-pages/pdfs/gendaymtx.pdf -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['sky_mtx']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['north_', '_location', '_temperature', '_bal_temp_', '_bal_offset_', '_direct_rad', '_diffuse_rad', '_hoys_', 'high_density_', '_ground_ref_', '_folder_']
        self.sv_input_types = ['System.Object', 'System.Object', 'System.Object', 'double', 'double', 'System.Object', 'System.Object', 'double', 'bool', 'double', 'string']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'item', 'item', 'item', 'item', 'item', 'list', 'item', 'item', 'item']
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

    def process_ladybug(self, north_, _location, _temperature, _bal_temp_, _bal_offset_, _direct_rad, _diffuse_rad, _hoys_, high_density_, _ground_ref_, _folder_):

        import math
        
        try:
            from ladybug_geometry.geometry2d.pointvector import Vector2D
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))
        
        try:
            from ladybug_radiance.skymatrix import SkyMatrix
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from ladybug_tools.togeometry import to_vector2d
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        try:
            from lbt_recipes.version import check_radiance_date
        except ImportError as e:
            raise ImportError('\nFailed to import honeybee_radiance:\n\t{}'.format(e))
        
        # check the istalled Radiance date and get the path to the gemdaymtx executable
        check_radiance_date()
        
        
        if all_required_inputs(ghenv.Component):
            # process and set defaults for all of the global inputs
            _bal_temp_ = 15 if _bal_temp_ is None else _bal_temp_
            _bal_offset_ = 2 if _bal_offset_ is None else _bal_offset_
            if north_ is not None:  # process the north_
                try:
                    north_ = math.degrees(
                        to_vector2d(north_).angle_clockwise(Vector2D(0, 1)))
                except AttributeError:  # north angle instead of vector
                    north_ = float(north_)
            else:
                north_ = 0
            ground_r = 0.2 if _ground_ref_ is None else _ground_ref_
        
            # create the sky matrix object
            sky_mtx = SkyMatrix.from_components_benefit(
                _location, _direct_rad, _diffuse_rad, _temperature, _bal_temp_, _bal_offset_,
                _hoys_, north_, high_density_, ground_r)
            if _folder_:
                sky_mtx.folder = _folder_
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvBenefitMatrix)

def unregister():
    bpy.utils.unregister_class(SvBenefitMatrix)
