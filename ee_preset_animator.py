import json
import gi
import os
import shutil
import cairo
import random
import func
import math
import ease
from operator import itemgetter

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk
from gi.repository import GLib


# noinspection PyUnresolvedReferences,PyArgumentList
class PresetAnimator:
    def __init__(self, builder, window_manager):
        self.entity_name = None
        self.data_json = {}
        self.window_manager = window_manager
        self.spritesheet_image = None
        self.bg_image = None
        self.current_sheet = None
        self.current_spritesheet = None
        self.current_model = None
        self.current_preset = None
        self.current_part = None
        self.current_modifier = None
        self.current_frame = 0
        self.part_data = {}
        self.part_entries = []
        self.window = None

        # Easing Dict
        self.eases = {
            'instant': None,
            'linear': ease.linear,
            'quad in': ease.quad_in,
            'quad out': ease.quad_out,
            'quad': ease.quad,
            'cub in': ease.cub_in,
            'cub out': ease.cub_out,
            'cub': ease.cub,
            'quart in': ease.quart_in,
            'quart out': ease.quart_out,
            'quart': ease.quart,
            'quint in': ease.quint_in,
            'quint out': ease.quint_out,
            'quint': ease.quint,
            'sine in': ease.sine_in,
            'sine out': ease.sine_out,
            'sine': ease.sine,
            'circ in': ease.circ_in,
            'circ out': ease.circ_out,
            'circ': ease.circ,
            'exp in': ease.exp_in,
            'exp out': ease.exp_out,
            'exp': ease.exp,
            'elast in': ease.elast_in,
            'elast out': ease.elast_out,
            'elast': ease.elast,
            'back in': ease.back_in,
            'back out': ease.back_out,
            'back': ease.back,
            'bounce in': ease.bounce_in,
            'bounce out': ease.bounce_out,
            'bounce': ease.bounce
        }

        # Blend Dict
        self.blends = {
            'OVER': cairo.OPERATOR_OVER,
            'XOR': cairo.OPERATOR_XOR,
            'ADD': cairo.OPERATOR_ADD,
            'SATURATE': cairo.OPERATOR_SATURATE,
            'MULTIPLY': cairo.OPERATOR_MULTIPLY,
            'SCREEN': cairo.OPERATOR_SCREEN,
            'OVERLAY': cairo.OPERATOR_OVERLAY,
            'DARKEN': cairo.OPERATOR_DARKEN,
            'LIGHTEN': cairo.OPERATOR_LIGHTEN,
            'COLOR DODGE': cairo.OPERATOR_COLOR_DODGE,
            'COLOR BURN': cairo.OPERATOR_COLOR_BURN,
            'HARD LIGHT': cairo.OPERATOR_HARD_LIGHT,
            'SOFT LIGHT': cairo.OPERATOR_SOFT_LIGHT,
            'DIFFERENCE': cairo.OPERATOR_DIFFERENCE,
            'EXCLUSION': cairo.OPERATOR_EXCLUSION
        }

        self.cols = [
            'Part',
            'Parent',
            'Piece',
            'Position',
            'Order',
            'Scale',
            'Angle',
            'Pivot',
            'Alpha',
            'RGB',
            'Tint',
            'Blend'
        ]
        self.modifiers = [
            'Part',
            'Parent',
            'Piece',
            'X Pos',
            'Y Pos',
            'Z Order',
            'X Scale',
            'Y Scale',
            'Angle',
            'X Pivot',
            'Y Pivot',
            'Alpha',
            'Red',
            'Green',
            'Blue',
            'Tint',
            'Blend'
        ]
        self.modcols = [
            'Modifier',
            'Length',
            'Loop'
        ]
        self.animation_sheet_cols = [
            'Keyframe',
            'Frame',
            'New Value',
            'Motion Style'
        ]
        self.part_analogies = {
            'Parent': 0,
            'Piece': 1,
            'X Pos': 2,
            'Y Pos': 3,
            'Z Order': 4,
            'X Scale': 5,
            'Y Scale': 6,
            'Angle': 7,
            'X Pivot': 8,
            'Y Pivot': 9,
            'Alpha': 10,
            'Red': 11,
            'Green': 11,
            'Blue': 11,
            'Tint': 12,
            'Blend': 13
        }

        self.part_listmodel = gtk.ListStore(str, str, str, str, str, str, str, str, str, str, str, str)
        self.modifier_listmodel = gtk.ListStore(str, int, int)
        self.animation_sheet_listmodel = gtk.ListStore(int, int, str, str)

        # Trees
        self.part_tree = builder.get_object('ee_notebook_pa_viewbox_part_tree')
        self.mod_tree = builder.get_object('ee_notebook_pa_viewbox_mod_tree')
        self.animation_sheet_tree = builder.get_object('ee_notebook_pa_viewbox_animation_sheet')
        self.part_tree.set_model(self.part_listmodel)
        self.part_tree.columns_autosize()
        self.part_tree.connect('row-activated', self.switch_part)
        self.mod_tree.set_model(self.modifier_listmodel)
        self.mod_tree.columns_autosize()
        self.mod_tree.connect('row-activated', self.switch_mod)
        self.animation_sheet_tree.set_model(self.animation_sheet_listmodel)
        self.animation_sheet_tree.columns_autosize()
        self.animation_sheet_tree.connect('row-activated', self.mod_frame_selected)

        for i, column in enumerate(self.cols):
            cell = gtk.CellRendererText()
            col = gtk.TreeViewColumn(column, cell, text=i)
            col.set_expand(True)
            self.part_tree.append_column(col)

        for i, column in enumerate(self.modcols):
            cell = gtk.CellRendererText()
            col = gtk.TreeViewColumn(column, cell, text=i)
            col.set_expand(True)
            self.mod_tree.append_column(col)

        for i, column in enumerate(self.animation_sheet_cols):
            cell = gtk.CellRendererText()
            col = gtk.TreeViewColumn(column, cell, text=i)
            col.set_expand(True)
            self.animation_sheet_tree.append_column(col)

        self.dropdown_modellist = builder.get_object('ee_notebook_pa_viewbox_modelselector')
        self.dropdown_presetlist = builder.get_object('ee_notebook_pa_viewbox_presetselector')
        self.dropdown_modellist.connect('changed', self.switch_model)
        self.dropdown_presetlist.connect('changed', self.switch_preset)

        self.box_toggle = builder.get_object('ee_notebook_pa_viewbox_boxtoggle')
        self.box_toggle.connect('state-set', self.queue_redraw)
        self.panel_toggle = builder.get_object('ee_notebook_pa_viewbox_panelswitch')
        self.panel_toggle.connect('state-set', self.switch_panels)
        self.switch_trueview = builder.get_object('ee_notebook_pa_viewbox_truescale')
        self.switch_trueview.connect('state-set', self.true_view)

        self.mainview = builder.get_object('ee_notebook_pa_mainview')
        self.prop_panel = builder.get_object('ee_notebook_pa_mainview_panel')
        self.panel_text = builder.get_object('ee_notebook_pa_viewbox_panellabel')
        self.previewframe = builder.get_object('ee_notebook_pa_mainview_preview')

        # Keyframe Properties Menu
        self.motion_dropdown = builder.get_object('ee_notebook_pa_viewbox_keyprop_motion')
        for m in self.eases:
            self.motion_dropdown.append_text(m)
        self.motion_dropdown.set_sensitive(False)
        self.entry_keyframe = builder.get_object('ee_notebook_pa_viewbox_keyprop_frame')
        self.entry_keyvalue = builder.get_object('ee_notebook_pa_viewbox_keyprop_value')
        self.button_keycreate = builder.get_object('ee_notebook_pa_viewbox_keyprop_new')
        self.button_keysave = builder.get_object('ee_notebook_pa_viewbox_keyprop_save')
        self.button_keycopy = builder.get_object('ee_notebook_pa_viewbox_keyprop_copy')
        self.button_keypaste = builder.get_object('ee_notebook_pa_viewbox_keyprop_paste')
        self.button_keydelete = builder.get_object('ee_notebook_pa_viewbox_keyprop_delete')
        self.button_keycreate.connect('clicked', self.key_create)
        self.button_keysave.connect('clicked', self.key_edit)
        self.button_keycreate.set_sensitive(False)
        self.button_keysave.set_sensitive(False)
        self.button_keydelete.set_sensitive(False)
        self.button_keycopy.set_sensitive(False)
        self.button_keypaste.set_sensitive(False)

        # Modifier controls
        self.button_modcopy = builder.get_object('ee_notebook_pa_control_copymod')
        self.button_modpaste = builder.get_object('ee_notebook_pa_control_pastemod')
        self.button_modclear = builder.get_object('ee_notebook_pa_control_clearmod')
        self.button_partcopy = builder.get_object('ee_notebook_pa_control_copypart')
        self.button_partpaste = builder.get_object('ee_notebook_pa_control_pastepart')
        self.button_partclear = builder.get_object('ee_notebook_pa_control_clearpart')
        self.button_modcopy.connect('clicked', self.mod_copy)
        self.button_modpaste.connect('clicked', self.mod_paste)
        self.button_modclear.connect('clicked', self.mod_clear)
        self.button_partcopy.connect('clicked', self.part_copy)
        self.button_partpaste.connect('clicked', self.part_paste)
        self.button_partclear.connect('clicked', self.part_clear)
        self.button_modpaste.set_sensitive(False)
        self.button_partpaste.set_sensitive(False)

        # Animation Control
        self.button_controlprev = builder.get_object('ee_notebook_pa_control_prev')
        self.play_toggle = builder.get_object('ee_notebook_pa_control_play')
        self.button_controlnext = builder.get_object('ee_notebook_pa_control_next')
        self.button_controljump = builder.get_object('ee_notebook_pa_control_jump')
        self.entry_controlframe = builder.get_object('ee_notebook_pa_control_frameinput')

        self.play_toggle.connect('toggled', self.pause_play)
        self.button_controlnext.connect('clicked', self.go_to, 'next_frame')
        self.button_controlprev.connect('clicked', self.go_to, 'prev_frame')
        self.button_controljump.connect('clicked', self.go_to, 'spec_frame')

        # FUcking cairo canvas
        self.canvas = builder.get_object('ee_notebook_pa_previewcanvas')
        self.canvas.connect('draw', self.refresh_canvas)
        self.dropdown_backgrounds = builder.get_object('ee_notebook_pa_viewbox_bgselector')
        self.dropdown_backgrounds.connect('changed', self.bg_set)

        # Refresh Backgrounds
        self.list_backgrounds = [x[0] for x in os.walk('assets/backgrounds')]
        del self.list_backgrounds[0]

        self.dropdown_backgrounds.remove_all()
        for d in self.list_backgrounds:
            self.dropdown_backgrounds.append_text(d.rsplit('\\', 1)[-1])
        self.dropdown_backgrounds.set_active(0)

    def key_edit(self, *args):
        sel = self.animation_sheet_tree.get_selection()
        sel = sel.get_selected()
        index = sel[0].get_value(sel[1], 0)
        if self.current_modifier not in self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part]:
            self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier] = {'Data': {}, 'Frames': []}
            self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier]['Data']['Loop Point'] = -1
        if self.entry_keyframe.get_text() != '':
            frame = int(self.entry_keyframe.get_text())
        else:
            frame = 0
        if self.entry_keyvalue.get_text() != '':
            if self.current_modifier in ['X Pos', 'Y Pos', 'Z Order', 'Angle', 'X Pivot', 'Y Pivot']:
                value = int(self.entry_keyvalue.get_text())
            elif self.current_modifier in ['X Scale', 'Y Scale', 'Alpha', 'Tint']:
                value = float(self.entry_keyvalue.get_text())
            else:
                value = str(self.entry_keyvalue.get_text())
        else:
            value = self.data_json[self.current_model]['Parts'][self.current_part][self.part_analogies[self.current_modifier]]
        if self.motion_dropdown.get_active_text() in self.eases:
            motion = self.motion_dropdown.get_active_text()
        else:
            motion = 'linear'
        self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier]['Frames'][index] = {'Frame': frame, 'Modifier': value, 'Motion': motion}
        self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier]['Frames'] = sorted(self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier]['Frames'], key=itemgetter('Frame'))
        self.switch_mod()

    def key_create(self, *args):
        if self.current_modifier not in self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part]:
            self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier] = {'Data': {}, 'Frames': []}
            self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier]['Data']['Loop Point'] = -1
        if self.entry_keyframe.get_text() != '':
            frame = int(self.entry_keyframe.get_text())
        else:
            frame = 0
        if self.entry_keyvalue.get_text() != '':
            if self.current_modifier in ['X Pos', 'Y Pos', 'Z Order', 'Angle', 'X Pivot', 'Y Pivot']:
                value = int(self.entry_keyvalue.get_text())
            elif self.current_modifier in ['X Scale', 'Y Scale', 'Alpha', 'Tint']:
                value = float(self.entry_keyvalue.get_text())
            else:
                value = str(self.entry_keyvalue.get_text())
        else:
            value = self.data_json[self.current_model]['Parts'][self.current_part][self.part_analogies[self.current_modifier]]
        print(self.motion_dropdown.get_active_text())
        if self.motion_dropdown.get_active_text() in self.eases:
            motion = self.motion_dropdown.get_active_text()
        else:
            motion = 'linear'
        self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier]['Frames'].append({'Frame': frame, 'Modifier': value, 'Motion': motion})
        self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier]['Frames'] = sorted(self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier]['Frames'], key=itemgetter('Frame'))
        self.switch_mod()

    def part_copy(self, *args):
        self.button_partpaste.set_sensitive(True)
        self.stored_part = self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part]

    def part_paste(self, *args):
        self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part] = self.stored_part
        self.switch_part()
        self.switch_mod()

    def part_clear(self, *args):
        self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part] = {}
        self.switch_part()
        self.switch_mod()

    def mod_copy(self, *args):
        self.button_modpaste.set_sensitive(True)
        self.stored_modifier = {
            'Mod': self.current_modifier,
            'Data': self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier]
        }

    def mod_paste(self, *args):
        if self.current_modifier == self.stored_modifier['Mod']:
            self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier] = self.stored_modifier['Data']
            self.switch_mod()

    def mod_clear(self, *args):
        self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier] = {}
        self.switch_mod()

    def go_to(self, widget, go_to):
        if go_to == 'next_frame':
            self.current_frame += 1
            self.canvas.queue_draw()
        elif go_to == 'prev_frame':
            self.current_frame -= 1
            self.canvas.queue_draw()
        elif go_to == 'spec_frame':
            if self.entry_controlframe is not None:
                try:
                    int(self.entry_controlframe.get_text())
                except ValueError:
                    pass
                else:
                    self.current_frame = int(self.entry_controlframe.get_text())
                    self.canvas.queue_draw()

    def true_view(self, *args):
        if self.switch_trueview.get_active():
            self.previewframe.set_size_request(1600, 900)
        else:
            self.previewframe.set_size_request(-1, -1)
        self.canvas.queue_draw()

    def switch_panels(self, *args):
        if self.panel_toggle.get_active():
            self.mainview.reorder_child(self.prop_panel, 1)
            self.panel_text.set_text('Panel on Right')
        else:
            self.mainview.reorder_child(self.prop_panel, 0)
            self.panel_text.set_text('Panel on Left')

    def pause_play(self, *args):
        self.current_frame = 0
        if self.play_toggle.get_active():
            GLib.timeout_add(16.666, self.play)

    def play(self):
        self.current_frame += 1
        self.canvas.queue_draw()
        if self.play_toggle.get_active():
            return True
        else:
            self.current_frame = 0
            self.canvas.queue_draw()
            return False

    def queue_redraw(self, *args):
        self.canvas.queue_draw()

    def mod_frame_selected(self, *args):
        sel = self.animation_sheet_tree.get_selection()
        sel = sel.get_selected()
        self.button_keysave.set_sensitive(True)
        self.button_keydelete.set_sensitive(True)
        self.button_keycopy.set_sensitive(True)
        self.entry_keyframe.set_text(str(sel[0].get_value(sel[1], 1)))
        self.entry_keyvalue.set_text(str(sel[0].get_value(sel[1], 2)))
        for e, name in enumerate(self.eases):
            if name == sel[0].get_value(sel[1], 3):
                self.motion_dropdown.set_active(e)

    def switch_mod(self, *args):
        sel = self.mod_tree.get_selection()
        sel = sel.get_selected()
        self.current_modifier = sel[0].get_value(sel[1], 0)
        self.animation_sheet_listmodel.clear()
        if self.current_part in self.data_json[self.current_model]['Presets'][self.current_preset]:
            if self.current_modifier in self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part]:
                for index, f in enumerate(self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][self.current_modifier]['Frames']):
                    self.animation_sheet_listmodel.append([index, f['Frame'], str(f['Modifier']), f['Motion']])
        self.button_keysave.set_sensitive(False)
        self.button_keydelete.set_sensitive(False)
        self.button_keycopy.set_sensitive(False)
        self.button_keycreate.set_sensitive(True)
        self.button_keypaste.set_sensitive(True)
        self.motion_dropdown.set_sensitive(True)
    
    def switch_part(self, *args):
        sel = self.part_tree.get_selection()
        sel = sel.get_selected()
        self.current_part = sel[0].get_value(sel[1], 0)
        self.modifier_listmodel.clear()
        if self.current_part in self.data_json[self.current_model]['Presets'][self.current_preset]:
            for m in self.modifiers:
                if m in self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part]:
                    self.modifier_listmodel.append([m, self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][m]['Frames'][-1]['Frame'], self.data_json[self.current_model]['Presets'][self.current_preset][self.current_part][m]['Data']['Loop Point']])
                else:
                    self.modifier_listmodel.append([m, 0, -1])
        else:
            for m in self.modifiers:
                self.modifier_listmodel.append([m, 0, -1])
        self.motion_dropdown.set_sensitive(False)

    def switch_preset(self, *args):
        if self.dropdown_presetlist.get_active_text() is not None:
            self.current_preset = self.dropdown_presetlist.get_active_text()

            self.part_listmodel.clear()
            self.part_data = {}
            for o in self.data_json[self.current_model]['Parts']:
                data = list(self.data_json[self.current_model]['Parts'][o])
                data.insert(0, o)
                if data[2] in self.data_json[self.current_model]['Pieces']:
                    coords = self.data_json[self.current_model]['Pieces'][data[2]]
                else:
                    coords = [0, 0, 0, 0]

                self.part_data[o] = {
                    'Parent': {
                        'Value': data[1],
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'Piece': {
                        'Value': coords,
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'X Pos': {
                        'Value': data[3],
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'Y Pos': {
                        'Value': -data[4],
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'X Pivot': {
                        'Value': data[9],
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'Y Pivot': {
                        'Value': -data[10],
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'Rotation': {
                        'Value': data[8],
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'X Scale': {
                        'Value': data[6],
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'Y Scale': {
                        'Value': data[7],
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'Alpha': {
                        'Value': data[11],
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'Red': {
                        'Value': int(data[12][0:2], 16) / 255,
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'Green': {
                        'Value': int(data[12][2:4], 16) / 255,
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'Blue': {
                        'Value': int(data[12][4:6], 16) / 255,
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'Tint': {
                        'Value': data[13],
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'Blend': {
                        'Value': data[14],
                        'Index': 0,
                        'Loop Point': -1
                    },
                    'Z Order': {
                        'Value': data[5],
                        'Index': 0,
                        'Loop Point': -1
                    }
                }
                self.part_listmodel.append([o, str(data[1]), str(data[2]), str(data[3]) + ', ' + str(data[4]), str(data[5]), str(data[6]) + ', ' + str(data[7]), str(data[8]), str([data[9], data[10]]), str(data[11]), str(self.part_data[o]['Red']['Value']) + ', ' + str(self.part_data[o]['Green']['Value']) + ', ' + str(self.part_data[o]['Blue']['Value']), str(data[13]), str(data[14])])
            self.canvas.queue_draw()

    def switch_model(self, *args):
        if self.dropdown_modellist.get_active_text() is not None:

            self.current_model = self.dropdown_modellist.get_active_text()

            self.dropdown_presetlist.remove_all()
            if len(self.data_json[self.current_model]['Presets']) != 0:
                for preset in self.data_json[self.current_model]['Presets']:
                    self.dropdown_presetlist.append_text(preset)
                self.dropdown_presetlist.set_active(0)

            # Canvas shit
            self.current_spritesheet = self.data_json[self.current_model]['Image']
            self.spritesheet_image = cairo.ImageSurface.create_from_png('assets/entities/' + self.entity_name + '/' + self.current_spritesheet)
            self.switch_preset()

    def refresh_canvas(self, area, context):
        self.clean_canvas(area, context)
        return True

    def frame_adjust(self, part):
        # Check frame data for current preset.
        if self.current_preset is not None:
            if part in self.data_json[self.current_model]['Presets'][self.current_preset]:
                for m in self.data_json[self.current_model]['Presets'][self.current_preset][part]:

                    # Shorter variable for part info
                    part_info = self.data_json[self.current_model]['Presets'][self.current_preset][part][m]

                    if part_info['Data']['Loop Point'] < 0:
                        # If the thing isn't looping and we're past the end of the loop we can just ignore everything
                        if self.current_frame > part_info['Frames'][-1]['Frame']:
                            return
                        # Else just set frame in here
                        else:
                            frame = self.current_frame
                    # Checking if we're past the last frame in the animation on a loop
                    elif self.current_frame > part_info['Frames'][-1]['Frame']:
                        frame = self.current_frame % (part_info['Frames'][-1]['Frame'] + 1 - part_info['Frames'][part_info['Data']['Loop Point']]['Frame'])
                    # Otherwise just do normal modulo operations (this is probably omittable)
                    else:
                        frame = self.current_frame % (part_info['Frames'][-1]['Frame'] + 1)

                    # Set the index
                    index = None
                    for n, framedata in enumerate(part_info['Frames']):
                        if frame >= framedata['Frame']:
                            index = n
                        else:
                            break
                    if index is None:
                        index = -1

                    # Determine next index
                    if part_info['Frames'][index]['Frame'] == part_info['Frames'][-1]['Frame']:
                        nextindex = part_info['Data']['Loop Point']
                    else:
                        nextindex = index + 1

                    # Applying modifiers to the parts
                    # String modifiers should always be instant.
                    if m in ['Piece']:
                        self.part_data[part]['Piece']['Value'] = self.data_json[self.current_model]['Pieces'][part_info['Frames'][index]['Modifier']]
                    else:
                        if nextindex == 0:
                            s = 1
                        else:
                            s = part_info['Frames'][nextindex]['Frame'] - part_info['Frames'][index]['Frame']
                        f = frame - part_info['Frames'][index]['Frame']
                        pr = f/s
                        c = part_info['Frames'][nextindex]['Motion'].lower()
                        n = part_info['Frames'][nextindex]['Modifier']
                        o = part_info['Frames'][index]['Modifier']
                        # s - span, f - Frame, pr - Progress, o - old value, n - new value, c - motion

                        value = (n-o) * self.eases[c](pr) + o
                        self.part_data[part][m]['Value'] = value
                        if m in ['X Scale', 'Y Scale']:
                            if value == 0:
                                self.part_data[part][m]['Value'] = 0.00000001


    def clean_canvas(self, area, context):
        context.set_source_rgba(0, 0, 0, 1)
        if self.window.get_focus() != self.entry_controlframe:
            self.entry_controlframe.set_text(str(self.current_frame))
        if self.dropdown_backgrounds.get_active_text() is not None:
            if not self.switch_trueview.get_active():
                extents = context.clip_extents()
                xscale = extents[2] / 1600
                yscale = extents[3] / 900
                # Revise this to assemble a background spritesheet
                context.scale(xscale, yscale)
            else:
                context.clip_extents()
            context.set_source_surface(self.bg_image, 0, 0)
            context.paint()
            context.set_operator(cairo.OPERATOR_OVER)
            if self.current_preset is not None:
                if self.spritesheet_image is not None:
                    # Determine render order and parenting data
                    # Just so I don't get confused later, PART DATA JSON SHIT
                    # 0 Parent, 1 Piece, 2 XPos, 3 YPos, 4 ZPos, 5 XScale, 6 YScale, 7 Rotation, 8 XPiv, 9 YPiv, 10 Alpha, 11 HEX, 12 Tint, 13 Blend
                    part_zlist = []
                    for n in self.data_json[self.current_model]['Parts']:
                        self.frame_adjust(n)
                        part_zlist.append([n, self.part_data[n]['Z Order']['Value']])
                    z_order = sorted(part_zlist, key=itemgetter(1))
                    # Render the shit
                    for p in z_order:
                        self.draw_part(context, p[0])

    def draw_part(self, context, part):
        # 0      1       2             3          4       5       6          7       8     9      10         11        12
        # Name | Image | PieceCoords | Position | Pivot | Scale | Rotation | Alpha | RGB | Tint | Operator | Z Order | Parent
        context.save()
        p = self.part_data[part]
        w = p['Piece']['Value'][2] - p['Piece']['Value'][0]
        h = p['Piece']['Value'][3] - p['Piece']['Value'][1]
        # Self Values
        pos = [p['X Pos']['Value'], p['Y Pos']['Value']]
        piv = [p['X Pivot']['Value'], p['Y Pivot']['Value'] + h]
        scale = [p['X Scale']['Value'], p['Y Scale']['Value']]
        rotation = p['Rotation']['Value']*math.pi/180
        alpha = p['Alpha']['Value']
        rgb = [p['Red']['Value'], p['Green']['Value'], p['Blue']['Value']]
        tint = p['Tint']['Value']
        operator = p['Blend']['Value']
        # Apply inheritance
        parents = []
        checking = p['Parent']['Value']
        rooting = True
        if p['Parent']['Value'] in self.data_json[self.current_model]['Parts']:
            while rooting:
                n = self.part_data[checking]
                parent_coords = n['Piece']['Value']
                parents.insert(0, n)
                if n['Parent']['Value'] in self.data_json[self.current_model]['Parts']:
                    checking = n['Parent']['Value']
                else:
                    rooting = False
        context.translate(0, 900)
        for i in parents:
            context.translate(i['X Pos']['Value'], i['Y Pos']['Value'])
            context.scale(i['X Scale']['Value'], i['Y Scale']['Value'])
            context.rotate(i['Rotation']['Value']*math.pi/180)
            context.translate(-i['X Pivot']['Value'], -i['Y Pivot']['Value'])
            alpha = alpha * i['Alpha']['Value']
        context.translate(pos[0], pos[1])
        context.scale(scale[0], scale[1])
        context.rotate(rotation)
        context.translate(-piv[0] - p['Piece']['Value'][0], -piv[1] - p['Piece']['Value'][1])

        # Set clipping boundaries and draw the piece
        context.rectangle(p['Piece']['Value'][0], p['Piece']['Value'][1], w, h)
        context.save()
        context.clip()
        context.set_source_surface(self.spritesheet_image, 0, 0)
        context.paint_with_alpha(alpha)
        context.set_operator(self.blends[operator])
        context.set_source_rgba(rgb[0], rgb[1], rgb[2], tint)
        context.mask_surface(self.spritesheet_image)
        context.restore()
        # Drawing bounding box, if needed.
        # Add:  or (self.radio_box_sel.get_active() and getting current selection)
        if self.box_toggle.get_active():
            context.rectangle(p['Piece']['Value'][0], p['Piece']['Value'][1], w, h)
            context.set_line_width(3)
            context.set_source_rgba(255, 0, 0, 1)
            context.stroke()
            context.fill()
            context.arc(p['Piece']['Value'][0] + piv[0], p['Piece']['Value'][1] + piv[1], 10, 0.0, 2 * math.pi)
            context.set_line_width(3)
            context.set_source_rgba(255, 0, 0, 1)
            context.fill()
        # Setting canvas settings back up for the following piece.
        context.restore()

    def bg_set(self, *args):
        if self.dropdown_backgrounds.get_active_text() is not None:
            # Revise this to assemble a background spritesheet.
            self.bg_image = cairo.ImageSurface.create_from_png('assets/backgrounds/' + self.dropdown_backgrounds.get_active_text() + '/main.png')
            self.canvas.queue_draw()
