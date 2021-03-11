# import player
import random
import entity_editor
import scene_editor
import func
import json
import gi
import time

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk
from gi.repository import GLib


class Main:
    def __init__(self):
        # Loading the splash text JSON file
        with open('ui/splash.json') as s:
            self.splash = json.load(s)
            self.splash_text = self.splash[random.randint(0, len(self.splash) - 1)]
            if self.splash_text == 'Brace for impact! We\'re going to crash':
                self.splash_text = self.splash[random.randint(0, len(self.splash) - 1)]
            if self.splash_text == 'Brace for impact! We\'re going to crash':
                self.splash_text = self.splash[random.randint(0, len(self.splash) - 1)]
            self.splash_finished = False
            self.splash_counter = -10

        # Initialize splash_finished
        self.splash_finished = False

        # Set glade file and set up builder
        self.glade_file = 'ui/main.glade'
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.glade_file)

        # Set up the window manager instance
        self.window_manager = func.WindowManager()
        self.window_manager.add_window('launcher', self.builder)

        # Object definitions
        self.splash_label = self.builder.get_object('launcher_mainbox_titlebox_subtitle')

        # Editor windows initialization
        self.entityeditor = entity_editor.EntityEditor()
        self.sceneeditor = scene_editor.SceneEditor()

        # Main Window
        self.window = self.builder.get_object('launcher_window')
        self.window.connect('delete-event', gtk.main_quit)
        self.window.connect('focus-in-event', self.type_splash)

        # Dark/Light Mode Switcher
        self.theme_button = self.builder.get_object('launcher_mainbox_theme_button')
        self.theme_button.connect('clicked', self.window_manager.toggle_theme)

        # Editor Buttons
        self.entity_editor_button = self.builder.get_object('launcher_mainbox_selectbox_edit_entitiesbutton')
        self.entity_editor_button.connect('clicked', self.open_window, 'ee', self.window_manager, self.entityeditor)
        self.scene_editor_button = self.builder.get_object('launcher_mainbox_selectbox_edit_scenebutton')
        self.scene_editor_button.connect('clicked', self.open_window, 'se', self.window_manager, self.sceneeditor)

        self.window.show()
        self.window_manager.load_theme()

        GLib.timeout_add(50, self.type_splash)

        gtk.main()

    def type_splash(self, *args):
        if self.splash_counter >= 0:
            self.splash_label.set_text(self.splash_text[0:self.splash_counter])
            if self.splash_text[0:self.splash_counter] == self.splash_text:
                if self.splash_text == 'Brace for impact! We\'re going to crash':
                    while True:
                        pass
                else:
                    return False
            else:
                self.splash_counter += 1
                return True
        else:
            self.splash_counter += 1
            return True

    def open_window(self, widget, window_name, window_manager, window_class):
        if window_name not in window_manager.windows:
            window_class.display(window_manager)
        else:
            print('Window already open!')


if __name__ == '__main__':
    main = Main()
