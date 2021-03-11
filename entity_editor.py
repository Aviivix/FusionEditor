import json
import gi
import os
import cairo
import shutil
import random
import func
import ee_spritesheet_cutter as sc
import ee_model_editor as me
import ee_preset_animator as pa

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk


# noinspection PyUnresolvedReferences,PyAttributeOutsideInit
class EntityEditor:
    def __init__(self):
        self.number = 1
        self.entity_name = None
        self.refreshing_dropdowns = False

    def display(self, window_manager):
        glade_file = 'ui/entity_editor.glade'
        self.builder = gtk.Builder()
        self.builder.add_from_file(glade_file)

        self.window = self.builder.get_object('entity_editor_window')
        self.window.connect('delete-event', self.destroy, window_manager)

        # Dark/Light Mode Switcher
        self.theme_button = self.builder.get_object('ee_mainbox_theme_button')
        self.theme_button.connect('clicked', window_manager.toggle_theme)

        # Tabs
        self.cutter = sc.SheetCutter(self.builder, window_manager)
        self.modeler = me.ModelEditor(self.builder, window_manager)
        self.animator = pa.PresetAnimator(self.builder, window_manager)

        # Passing window to animator
        self.animator.window = self.window

        # List of entities
        self.list_entities = [x[0] for x in os.walk('assets/entities')]
        del self.list_entities[0]

        self.dropdown_entitylist = self.builder.get_object('ee_header_entitycurrent_selector')
        for d in self.list_entities:
            self.dropdown_entitylist.append_text(d.rsplit('\\', 1)[-1])
        self.dropdown_entitylist.set_active(0)

        # Entity Stuff
        self.button_saveentity = self.builder.get_object('ee_header_entitycurrent_savebutton')
        self.button_loadentity = self.builder.get_object('ee_header_entitycurrent_loadbutton')
        self.button_renameentity = self.builder.get_object('ee_header_entitycurrent_renamebutton')
        self.button_createnewentity = self.builder.get_object('ee_header_entitycurrent_newbutton')
        self.button_openfolder = self.builder.get_object('ee_header_entitycurrent_openfolder')
        self.field_entityrename = self.builder.get_object('ee_header_entitycurrent_renamebox')

        self.status_bar = self.builder.get_object('ee_status_bar')

        self.button_openfolder.connect('clicked', self.open_folder)
        self.button_createnewentity.connect('clicked', self.create_entity)
        self.button_loadentity.connect('clicked', self.load_entity)
        self.button_saveentity.connect('clicked', self.save_entity)
        self.window.connect('focus-in-event', self.dropdown_refresh)
        self.window.connect('focus-out-event', self.focus_out)

        self.button_openfolder.set_sensitive(False)
        self.button_saveentity.set_sensitive(False)

        # Window manager shit and finishing up
        window_manager.add_window('ee', self.builder)
        self.window.show()
        window_manager.load_theme()

    def focus_out(self, *args):
        self.animator.play_toggle.set_active(False)

    def dropdown_refresh(self, *args):
        self.refreshing_dropdowns = True
        self.cutter.refreshing_dropdowns = True

        # Refresh Entities
        self.list_entities = [x[0] for x in os.walk('assets/entities')]
        del self.list_entities[0]

        index = self.dropdown_entitylist.get_active()
        self.dropdown_entitylist.remove_all()
        for d in self.list_entities:
            self.dropdown_entitylist.append_text(d.rsplit('\\', 1)[-1])
        self.dropdown_entitylist.set_active(index)

        # Refresh Backgrounds
        self.list_backgrounds = [x[0] for x in os.walk('assets/backgrounds')]
        del self.list_backgrounds[0]

        index = self.modeler.dropdown_backgrounds.get_active()
        self.modeler.dropdown_backgrounds.remove_all()
        for d in self.list_backgrounds:
            self.modeler.dropdown_backgrounds.append_text(d.rsplit('\\', 1)[-1])
        self.modeler.dropdown_backgrounds.set_active(index)

        index = self.animator.dropdown_backgrounds.get_active()
        self.animator.dropdown_backgrounds.remove_all()
        for d in self.list_backgrounds:
            self.animator.dropdown_backgrounds.append_text(d.rsplit('\\', 1)[-1])
        self.animator.dropdown_backgrounds.set_active(index)

        # If there's an active entity...
        if self.entity_name is not None:
            # Spritesheet Cutter Stuff
            # Refresh sheet file list.
            directories = [x[2] for x in os.walk('assets/entities/' + self.entity_name)]
            directories = directories[0]

            self.cutter.list_sheetfiles = []
            for d in directories:
                if d[-4:] == '.png':
                    self.cutter.list_sheetfiles.append(d)

            index = self.cutter.dropdown_spritefilelist.get_active()
            self.cutter.dropdown_spritefilelist.remove_all()
            for ss in self.cutter.list_sheetfiles:
                self.cutter.dropdown_spritefilelist.append_text(ss)
            self.cutter.dropdown_spritefilelist.set_active(index)

            # Model Editor stuff
            index = self.modeler.dropdown_modellist.get_active()
            self.modeler.dropdown_modellist.remove_all()
            for m in self.data_json:
                self.modeler.dropdown_modellist.append_text(m)
            self.modeler.dropdown_modellist.set_active(index)

            # Animator stuff
            index = self.animator.dropdown_modellist.get_active()
            self.animator.dropdown_modellist.remove_all()
            for m in self.data_json:
                self.animator.dropdown_modellist.append_text(m)
            self.animator.dropdown_modellist.set_active(index)

    def create_entity(self, *args):
        if self.field_entityrename.get_text() != '':
            name = self.field_entityrename.get_text()
            name_taken = True
            taken_pass = False
            count = 2
            while name_taken:
                for entity in self.list_entities:
                    if entity == name:
                        name = name + '(' + str(count) + ')'
                        count += 1
                        taken_pass = True
                if not taken_pass:
                    name_taken = False
                taken_pass = False
            self.field_entityrename.set_text('')
            self.entity_name = name
            os.mkdir('assets/entities/' + self.entity_name)
            self.list_entities.append(name)
            self.dropdown_entitylist.append_text(name)
            self.dropdown_entitylist.set_active(self.list_entities.index(name))
            self.load_entity()

    def load_entity(self, *args):
        # Top Interactives
        self.button_saveentity.set_sensitive(True)
        self.button_openfolder.set_sensitive(True)

        # Subclass Interactives
        self.cutter.button_addnewsheet.set_sensitive(True)
        self.cutter.button_deletesheet.set_sensitive(True)
        self.cutter.field_sheetname.set_sensitive(True)
        self.cutter.dropdown_sheetlist.set_sensitive(True)
        self.cutter.button_addnewpiece.set_sensitive(False)
        self.cutter.dropdown_spritefilelist.set_sensitive(False)
        self.cutter.button_importspritesheetfile.set_sensitive(False)

        # Subclass Clearance
        self.cutter.dropdown_sheetlist.remove_all()
        self.cutter.dropdown_spritefilelist.remove_all()
        self.cutter.clear_piece_window()
        self.modeler.dropdown_modellist.remove_all()
        self.animator.dropdown_modellist.remove_all()

        # Subclass Lists
        self.cutter.list_sheets = []
        self.cutter.list_sheetfiles = []
        self.cutter.rendered_shapes = []
        self.modeler.part_entries = []
        self.modeler.piece_entries = []

        # Subclass Initializations
        self.cutter.spritesheet_image = None
        self.cutter.current_spritesheet = None
        self.cutter.current_sheet = None
        self.modeler.spritesheet_image = None
        self.modeler.current_spritesheet = None
        self.modeler.current_sheet = None
        self.animator.spritesheet_image = None
        self.animator.current_spritesheet = None
        self.animator.current_sheet = None

        # Load new entity data
        self.entity_name = self.dropdown_entitylist.get_active_text()

        directories = [x[2] for x in os.walk('assets/entities/' + self.entity_name)]
        directories = directories[0]
        json_exists = False
        for d in directories:
            if d[-4:] == '.png':
                self.cutter.list_sheetfiles.append(d)
            elif d == 'data.json':
                json_exists = True

        if json_exists:
            with open('assets/entities/' + self.entity_name + '/data.json', 'r') as c:
                self.data_json = json.load(c)
        else:
            default_data = {}
            with open('assets/entities/' + self.entity_name + '/data.json', 'w') as c:
                json.dump(default_data, c)
                self.data_json = default_data

        # Pass data to tabs
        self.cutter.entity_name = self.entity_name
        self.cutter.data_json = self.data_json

        self.modeler.entity_name = self.entity_name
        self.modeler.data_json = self.data_json

        self.animator.entity_name = self.entity_name
        self.animator.data_json = self.data_json

        # Cutter Post-Loading Updates
        # Putting the PNG list into the cutter dropdown
        for ss in self.cutter.list_sheetfiles:
            self.cutter.dropdown_spritefilelist.append_text(ss)
        self.cutter.dropdown_spritefilelist.set_active(0)

        # Convert Sheets keys into Sheet select dropdown.
        for s in self.data_json:
            self.cutter.list_sheets.append(s)
            self.cutter.dropdown_sheetlist.append_text(s)
            self.modeler.dropdown_modellist.append_text(s)
            self.animator.dropdown_modellist.append_text(s)

        # Check how many keys there are in the Sprite Sheets key
        if len(self.cutter.list_sheets) != 0:
            # Default the active one to the first
            self.cutter.dropdown_sheetlist.set_active(0)
            self.modeler.dropdown_modellist.set_active(0)
            self.animator.dropdown_modellist.set_active(0)
            self.cutter.current_model = self.cutter.dropdown_sheetlist.get_active_text()
            self.cutter.switch_model()

    def save_entity(self, *args):
        with open('assets/entities/' + self.entity_name + '/data.json', 'w') as c:
            json.dump(self.data_json, c, indent=4)
        self.status_bar.set_text('Saved.')

    def open_folder(self, *args):
        pass

    def destroy(self, widget, event_data, window_manager):
        window_manager.close_window('ee')
