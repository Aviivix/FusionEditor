import json
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk


class WindowManager:
    def __init__(self):
        self.windows = {}
        self.config = Config()

    def config_refresh(self):
        self.config = Config()

    def add_window(self, name, builder):
        self.windows[name] = builder

    def close_window(self, name):
        del self.windows[name]

    def load_theme(self):
        self.config_refresh()
        theme = self.config.get_config('Theme')
        for w in self.windows:
            if w == 'se':
                if theme == 'Nordic-darker':
                    target = self.windows[w].get_object(w + '_mainbox_theme_image')
                    target.set_from_file('ui/night.ico')
                    target = self.windows[w].get_object(w + '_mainbox_help_image')
                    target.set_from_file('ui/darkq.ico')
                else:
                    target = self.windows[w].get_object(w + '_mainbox_theme_image')
                    target.set_from_file('ui/day.ico')
                    target = self.windows[w].get_object(w + '_mainbox_help_image')
                    target.set_from_file('ui/lightq.ico')
            else:
                if theme == 'Nordic-darker':
                    target = self.windows[w].get_object(w + '_mainbox_theme_image')
                    target.set_from_file('ui/night.ico')
                else:
                    target = self.windows[w].get_object(w + '_mainbox_theme_image')
                    target.set_from_file('ui/day.ico')
        gtk_settings = gtk.Settings.get_default()
        gtk_settings.set_property("gtk-theme-name", theme)

    def toggle_theme(self, widget):
        self.config_refresh()
        try:
            if self.config.get_config('Theme') == 'Nordic-darker':
                self.config.edit_config('Theme', 'Sweet')
                self.load_theme()
            else:
                self.config.edit_config('Theme', 'Nordic-darker')
                self.load_theme()
        except KeyError:
            self.config.edit_config('Theme', 'Nordic-darker')
            self.load_theme()


class ConsoleLog:
    def __init__(self):
        self.log = []
        self.print = []
        pass

    def add_log(self, source, log_type, text):
        self.log.append('[' + source + '] [' + log_type + ']: ' + text)

    def json_load(self, source, json_dict):
        # [Source][JSON Loaded]: {}
        self.add_log(source, 'JSON Load', 'JSON file loaded: ' + str(json_dict))

    def djson_update(self, source, key, value, cause):
        self.add_log(source, 'DJ Update', 'Key \'' + key + '\' changed to \'' + value + '\' by ' + cause)
        if 'update_djs' in self.print:
            print(self.log[-1])


class Config():
    def __init__(self):
        with open('config.json', 'r') as j:
            default_data = {
                'Theme': 'Nordic-darker'
            }
            try:
                self.data = json.load(j)
            except:
                with open('config.json', 'c') as c:
                    json.dump(default_data, c)
                    self.data = default_data

    def edit_config(self, key, value):
        self.__init__()
        self.data[key] = value
        with open('config.json', 'w') as j:
            json.dump(self.data, j)

    def get_config(self, key):
        self.__init__()
        return self.data[key]


def d_index_of(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return -1


def dialog(text):
    builder = gtk.Builder()
    builder.add_from_file('ui/dialog.glade')
    dialog = builder.get_object('text')
    dialog.set_text(text)
    window = builder.get_object('window')
    button = builder.get_object('ok_button')
    button.connect('clicked', error_close, window)

def error_close(widget, window):
    window.close_window()