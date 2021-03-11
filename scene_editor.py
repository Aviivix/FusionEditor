import json
import gi
import os
import func

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk


class SceneEditor:
    def __init__(self):
        pass

    def get_builder(self):
        return self.builder

    def display(self, window_manager):
        glade_file = 'ui/scene_editor.glade'
        self.builder = gtk.Builder()
        self.builder.add_from_file(glade_file)

        self.window = self.builder.get_object('scene_editor_window')
        self.window.connect('delete-event', self.destroy, window_manager)

        # Dark/Light Mode Switcher
        self.theme_button = self.builder.get_object('se_mainbox_theme_button')
        self.theme_button.connect('clicked', window_manager.toggle_theme)

        self.advanced_switch = self.builder.get_object('se_mainbox_editor_main_advswitch')
        self.advanced_switch.connect('state-set', self.advanced_toggle)

        window_manager.add_window('se', self.builder)
        self.window.show()
        window_manager.load_theme()

    def advanced_toggle(self, widget, *args):
        book = self.builder.get_object('se_editor_editmodes')
        achap = self.builder.get_object('se_editor_adv_story')
        schap = self.builder.get_object('se_editor_sim_story')
        direction = widget.get_active()
        if direction:
            achap.set_current_page(schap.get_current_page())
            book.set_current_page(1)
        else:
            schap.set_current_page(achap.get_current_page())
            book.set_current_page(0)

    def destroy(self, widget, event_data, window_manager):
        window_manager.close_window('se')
