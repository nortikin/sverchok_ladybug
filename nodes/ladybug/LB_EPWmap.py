import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvEPWMap(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvEPWMap'
    bl_label = 'LB EPWmap'
    sv_icon = 'LB_EPWMAP'
    sv__epw_map: StringProperty(
        name='_epw_map',
        update=updateNode,
        description='Set to "True" to open EPWmap in a supported browser.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_epw_map')
        input_node.prop_name = 'sv__epw_map'
        input_node.tooltip = 'Set to "True" to open EPWmap in a supported browser.'
        output_node = self.outputs.new('SvLBSocket', 'Output')
        output_node.tooltip = '...'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Open EPWmap in a web browser. -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['Output']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_epw_map']
        self.sv_input_types = ['bool']
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

    def process_ladybug(self, _epw_map):

        # import core Python dependencies
        import webbrowser as wb
        import os
        
        try:  # import ladybug_tools dependencies
            from ladybug_tools.sverchok import all_required_inputs
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        # dictonary of accetable browsers and their default file paths.
        acceptable_browsers = [
            ['chrome', 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'],
            ['chrome', 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'],
            ['firefox', 'C:\\Program Files\\Mozilla Firefox\\firefox.exe'],
            ['chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'] # MacOS
        ]
        
        # URL to epwmap.
        url = 'http://www.ladybug.tools/epwmap/'
        
        
        # function for opening a browser page on Mac
        def mac_open(url):
            os.system("open \"\" " + url)
        
        
        if all_required_inputs(ghenv.Component) and _epw_map is True:
            broswer_found = False
            for browser in acceptable_browsers:
                browser_path = browser[1]
                if broswer_found == False and os.path.isfile(browser_path) == True:
                    broswer_found = True
                    wb.register(browser[0],  None, wb.BackgroundBrowser(browser_path), 1)
                    try:
                        wb.get(browser[0]).open(url, 2, True)
                        print('Opening epwmap.')
                    except ValueError:
                        mac_open(url)
            if broswer_found == False:
                print(
                    'An accepable broswer was not found on your machine.\n'
                    'The default browser will be used but epwmap may not display '
                    'correctly there.'
                )
                try:
                    wb.open(url, 2, True)
                except ValueError:
                    mac_open(url)
        else:
            print('Set _epw_map to True.')

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvEPWMap)

def unregister():
    bpy.utils.unregister_class(SvEPWMap)
