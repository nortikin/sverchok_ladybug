import bpy
import ladybug_tools.helper
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat

ghenv = ladybug_tools.helper.ghenv

class SvCaptureView(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvCaptureView'
    bl_label = 'LB Capture View'
    sv_icon = 'LB_CAPTUREVIEW'
    sv__file_name: StringProperty(
        name='_file_name',
        update=updateNode,
        description='The file name, which the image will be saved as. Note that, for animations, each saved image should have a different name. Otherwise, the previous image will be overwritten by each successive image. Unique names for each animation frame can be achieved by using the animating slider to generate the file name.')
    sv__folder_: StringProperty(
        name='_folder_',
        update=updateNode,
        description='The folder into which the image file will be written. This should be a complete path to the folder. If None, the images will be written to one of the following default locations: - Windows - C:/Users/[USERNAME]/ladybug_tools/resources/captured_views/ Mac - /Users/[USERNAME]/ladybug_tools/resources/captured_views/')
    sv_viewport_: StringProperty(
        name='viewport_',
        update=updateNode,
        description='Text for the Rhino viewport name which will be captured. This can also be a list of viewports in which case multiple views will be captured. If None, the default will be the active viewport (the last viewport in which you navigated). Acceptable inputs include: - Perspective Top Bottom Left Right Front Back any view name that has been saved within the Rhino file')
    sv_width_: StringProperty(
        name='width_',
        update=updateNode,
        description='Integer for the width of the image to be captured in pixels. If None, the default is the width of the Rhino viewport currently on the screen.')
    sv_height_: StringProperty(
        name='height_',
        update=updateNode,
        description='Integer for the height of the image to be captured in pixels. If None, the default is the height of the Rhino viewport currently on the screen.')
    sv_mode_: StringProperty(
        name='mode_',
        update=updateNode,
        description='Text for the display mode of the viewport to be captured.If None, the default will be the display mode of the active viewport (the last viewport in which you navigated). Acceptable inputs include: - Wireframe Shaded Rendered Ghosted X-Ray Technical Artistic Pen')
    sv_transparent_: StringProperty(
        name='transparent_',
        update=updateNode,
        description='Boolean to note whether the captured .png file should have a transparent background. If None or False, the image will have the Rhino viewport background color.')
    sv__capture: StringProperty(
        name='_capture',
        update=updateNode,
        description='Set to "True" to capture the image of the Rhino viewport.')

    def sv_init(self, context):
        self.width *= 1.3
        input_node = self.inputs.new('SvLBSocket', '_file_name')
        input_node.prop_name = 'sv__file_name'
        input_node.tooltip = 'The file name, which the image will be saved as. Note that, for animations, each saved image should have a different name. Otherwise, the previous image will be overwritten by each successive image. Unique names for each animation frame can be achieved by using the animating slider to generate the file name.'
        input_node = self.inputs.new('SvLBSocket', '_folder_')
        input_node.prop_name = 'sv__folder_'
        input_node.tooltip = 'The folder into which the image file will be written. This should be a complete path to the folder. If None, the images will be written to one of the following default locations: - Windows - C:/Users/[USERNAME]/ladybug_tools/resources/captured_views/ Mac - /Users/[USERNAME]/ladybug_tools/resources/captured_views/'
        input_node = self.inputs.new('SvLBSocket', 'viewport_')
        input_node.prop_name = 'sv_viewport_'
        input_node.tooltip = 'Text for the Rhino viewport name which will be captured. This can also be a list of viewports in which case multiple views will be captured. If None, the default will be the active viewport (the last viewport in which you navigated). Acceptable inputs include: - Perspective Top Bottom Left Right Front Back any view name that has been saved within the Rhino file'
        input_node = self.inputs.new('SvLBSocket', 'width_')
        input_node.prop_name = 'sv_width_'
        input_node.tooltip = 'Integer for the width of the image to be captured in pixels. If None, the default is the width of the Rhino viewport currently on the screen.'
        input_node = self.inputs.new('SvLBSocket', 'height_')
        input_node.prop_name = 'sv_height_'
        input_node.tooltip = 'Integer for the height of the image to be captured in pixels. If None, the default is the height of the Rhino viewport currently on the screen.'
        input_node = self.inputs.new('SvLBSocket', 'mode_')
        input_node.prop_name = 'sv_mode_'
        input_node.tooltip = 'Text for the display mode of the viewport to be captured.If None, the default will be the display mode of the active viewport (the last viewport in which you navigated). Acceptable inputs include: - Wireframe Shaded Rendered Ghosted X-Ray Technical Artistic Pen'
        input_node = self.inputs.new('SvLBSocket', 'transparent_')
        input_node.prop_name = 'sv_transparent_'
        input_node.tooltip = 'Boolean to note whether the captured .png file should have a transparent background. If None or False, the image will have the Rhino viewport background color.'
        input_node = self.inputs.new('SvLBSocket', '_capture')
        input_node.prop_name = 'sv__capture'
        input_node.tooltip = 'Set to "True" to capture the image of the Rhino viewport.'
        output_node = self.outputs.new('SvLBSocket', 'Output')
        output_node.tooltip = 'The file path of the image taken with this component.'

    def draw_buttons(self, context, layout):
        op = layout.operator('node.sv_lb_socket_name', text='', icon='QUESTION', emboss=False).tooltip = 'Capture views of the Rhino scene and save them to your hard drive as as a .png files. _ This is particularly useful when creating animations and one needs to automate the capturing of views. Note that images will likely have a Rhino world axes icon in the lower left of the image unless you go to Options > Grid > and uncheck "Show world axes icon". -'

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        self.sv_output_names = ['Output']
        for name in self.sv_output_names:
            setattr(self, '{}_out'.format(name), [])
        self.sv_input_names = ['_file_name', '_folder_', 'viewport_', 'width_', 'height_', 'mode_', 'transparent_', '_capture']
        self.sv_input_types = ['string', 'string', 'string', 'int', 'int', 'string', 'bool', 'bool']
        self.sv_input_defaults = [None, None, None, None, None, None, None, None]
        self.sv_input_access = ['item', 'item', 'list', 'item', 'item', 'item', 'item', 'item']
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

    def process_ladybug(self, _file_name, _folder_, viewport_, width_, height_, mode_, transparent_, _capture):

        import os
        
        try:
            from ladybug.futil import preparedir
            from ladybug.config import folders
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug:\n\t{}'.format(e))
        
        try:
            from honeybee.config import folders
            default_folder = os.path.join(folders.default_simulation_folder, 'captured_views')
        except:
            home_folder = os.getenv('HOME') or os.path.expanduser('~')
            default_folder = os.path.join(home_folder, 'captured_views')
        
        try:
            from ladybug_tools.sverchok import all_required_inputs, bring_to_front
            from ladybug_tools.viewport import viewport_by_name, capture_view
        except ImportError as e:
            raise ImportError('\nFailed to import ladybug_tools:\n\t{}'.format(e))
        
        
        if all_required_inputs(ghenv.Component) and _capture:
            # ensure the component runs last on the canvas
            bring_to_front(ghenv.Component)
        
            # prepare the folder
            folder = _folder_ if _folder_ is not None else default_folder
            preparedir(folder, remove_content=False)
        
            # get the viewport objects
            vp_names = viewport_ if len(viewport_) != 0 else [None]
            viewports = [viewport_by_name(vp) for vp in vp_names]
        
            # save the viewports to images
            for i, view_p in enumerate(viewports):
                f_name = _file_name if len(viewports) == 1 else \
                    '{}_{}'.format(_file_name, vp_names[i])
                file_p = os.path.join(folder, f_name)
                fp = capture_view(view_p, file_p, width_, height_, mode_, transparent_)
                print(fp)
        

        for name in self.sv_output_names:
            if name in locals():
                getattr(self, '{}_out'.format(name)).append([locals()[name]])


def register():
    bpy.utils.register_class(SvCaptureView)

def unregister():
    bpy.utils.unregister_class(SvCaptureView)
