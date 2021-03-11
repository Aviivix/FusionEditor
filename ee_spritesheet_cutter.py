import json
import gi
import os
import cairo
import shutil
import random
import func

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk


class SheetCutter:
    def __init__(self, builder, window_manager):
        self.number = 1
        self.entity_name = None
        self.data_json = {}
        self.spritesheet_image = None
        self.current_model = None
        self.current_spritesheet = None
        self.list_sheets = []
        self.list_sheetfiles = []
        self.rendered_shapes = []
        self.refreshing_dropdowns = False
        self.window_manager = window_manager

        # Templates
        self.piece_list_box = builder.get_object('ee_notebook_sc_piecelist_listbox')
        self.clear_piece_window()

        # Buttons
        self.button_addnewpiece = builder.get_object('ee_notebook_sc_piecelist_addpiece')
        self.button_addnewsheet = builder.get_object('ee_notebook_sc_piecelist_addsheet')
        self.button_deletesheet = builder.get_object('ee_notebook_sc_piecelist_delsheet')
        self.button_importspritesheetfile = builder.get_object('ee_notebook_sc_canvas_importfile')
        self.switch_corners = builder.get_object('ee_notebook_sc_canvas_cornerswitch')

        # Dropdowns
        self.dropdown_sheetlist = builder.get_object('ee_notebook_sc_piecelist_selectsheet')
        self.dropdown_spritefilelist = builder.get_object('ee_notebook_sc_canvas_fileselector')

        # Fields
        self.field_sheetname = builder.get_object('ee_notebook_sc_piecelist_namesheet')

        # Canvases
        self.rerender = False
        self.spritesheet_canvas = builder.get_object('ee_notebook_sc_canvas')
        self.spritesheet_canvas.connect('draw', self.refresh_sheet)

        # Signals
        self.button_addnewpiece.connect('clicked', self.add_piece, 'New Piece', 0, 0, 0, 0, False, False)
        self.button_addnewsheet.connect('clicked', self.add_sheet)
        self.dropdown_sheetlist.connect('changed', self.switch_model)
        self.dropdown_spritefilelist.connect('changed', self.set_spritesheet)
        self.button_importspritesheetfile.connect('clicked', self.import_spritesheet)
        self.switch_corners.connect('state-set', self.toggle_corners)

        # Sensitivities
        self.button_addnewpiece.set_sensitive(False)
        self.button_addnewsheet.set_sensitive(False)
        self.button_deletesheet.set_sensitive(False)
        self.field_sheetname.set_sensitive(False)
        self.button_importspritesheetfile.set_sensitive(False)
        self.dropdown_spritefilelist.set_sensitive(False)
        self.dropdown_sheetlist.set_sensitive(False)

    def toggle_corners(self, *args):
        self.spritesheet_canvas.queue_draw()

    def refresh_sheet(self, area, context):
        if self.rerender:
            self.clean_sheet(area, context)
            for s in self.rendered_shapes:
                if s['Redraw']:
                    self.draw_shape(context, s['Coords'][0], s['Coords'][1], s['Coords'][2], s['Coords'][3], 255, 0, 0)
        return True

    def add_sheet(self, *args):
        if self.field_sheetname.get_text() != '':
            name = self.field_sheetname.get_text()
            name_taken = True
            taken_pass = False
            count = 2
            while name_taken:
                for sheet in self.list_sheets:
                    if sheet == name:
                        name = name + str(count)
                        count += 1
                        taken_pass = True
                if not taken_pass:
                    name_taken = False
                taken_pass = False
            self.field_sheetname.set_text('')
            # Clear away old sheet stuff
            self.list_sheets.append(name)
            self.dropdown_sheetlist.append_text(name)
            self.dropdown_sheetlist.set_active(len(self.list_sheets) - 1)
            self.rendered_shapes = []

            # Setting new sheet data
            self.current_model = name

            self.switch_model()

    def switch_model(self, *args):
        if self.dropdown_sheetlist.get_active_text() is not None:
            # Clear away old model stuff
            self.clear_piece_window()
            self.rendered_shapes = []
            self.button_addnewpiece.set_sensitive(True)
            self.dropdown_spritefilelist.set_sensitive(True)
            self.button_importspritesheetfile.set_sensitive(True)

            # Setting new model data if it doesn't exist
            self.current_model = self.dropdown_sheetlist.get_active_text()
            try:
                try_value = self.data_json[self.current_model]
            except KeyError:
                self.data_json[self.current_model] = {'Image': self.dropdown_spritefilelist.get_active_text(), 'Default Preset': '', 'Pieces': {'Root': [0, 0, 0, 0]}, 'Parts': {}, 'Presets': {}}

            if self.data_json[self.current_model]['Image'] in self.list_sheetfiles:
                self.dropdown_spritefilelist.set_active(
                    self.list_sheetfiles.index(self.data_json[self.current_model]['Image']))

            self.set_spritesheet()

            for p in self.data_json[self.current_model]['Pieces']:
                coords = self.data_json[self.current_model]['Pieces'][p]
                self.add_piece(False, p, coords[0], coords[1], coords[2], coords[3], True, False)

            self.save_sheet()

    def set_spritesheet(self, *args):
        if self.current_model is not None:
            if self.dropdown_spritefilelist.get_active_text() is not None:
                # INFORMATION
                self.current_spritesheet = self.dropdown_spritefilelist.get_active_text()

                self.data_json[self.current_model]['Image'] = self.current_spritesheet

                self.button_addnewpiece.set_sensitive(True)

                self.spritesheet_image = cairo.ImageSurface.create_from_png('assets/entities/' + self.entity_name + '/' + self.current_spritesheet)
                self.spritesheet_canvas.set_size_request(self.spritesheet_image.get_width(), self.spritesheet_image.get_height())
                self.spritesheet_canvas.queue_resize()
                self.rerender = True
                self.spritesheet_canvas.queue_draw()

    def import_spritesheet(self, *args):
        file_chooser = gtk.FileChooserDialog(title='Select Spritesheet...', buttons=(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL, gtk.STOCK_OPEN, gtk.ResponseType.ACCEPT))
        file_chooser.set_local_only(False)
        file_chooser.set_modal(True)
        file_chooser.connect('response', self.import_response)
        file_chooser.show()

    def import_response(self, widget, response):
        if response in [-6, -4]:
            widget.destroy()
        else:
            file = widget.get_filename()
            shutil.copy(file, 'assets/entities/' + self.entity_name)

            # Refresh sheet file list.
            directories = [x[2] for x in os.walk('assets/entities/' + self.entity_name)]
            directories = directories[0]

            self.list_sheetfiles = []
            for d in directories:
                if d[-4:] == '.png':
                    self.list_sheetfiles.append(d)

            index = len(self.list_sheetfiles) - 1
            self.dropdown_spritefilelist.remove_all()
            for ss in self.list_sheetfiles:
                self.dropdown_spritefilelist.append_text(ss)
            self.dropdown_spritefilelist.set_active(index)

            widget.destroy()

    def add_piece(self, widget, name, cx1, cy1, cx2, cy2, err, dup):
        self.entry = gtk.Builder()
        self.entry.add_from_file('ui/entity_editor_piecelist.glade')
        piece_entry = self.entry.get_object('piecelist_template')

        if dup:
            x1 = int(cx1.get_text())
            y1 = int(cy1.get_text())
            x2 = int(cx2.get_text())
            y2 = int(cy2.get_text())
        else:
            x1 = cx1
            y1 = cy1
            x2 = cx2
            y2 = cy2

        name_taken = True
        taken_pass = False
        count = 2
        new_piece = name
        while name_taken:
            for shape in self.rendered_shapes:
                if shape['Name'] == new_piece:
                    new_piece = new_piece + str(count)
                    count += 1
                    taken_pass = True
            if not taken_pass:
                name_taken = False
            taken_pass = False

        piece_name = self.entry.get_object('piecelist_template_piecename')
        piece_x1 = self.entry.get_object('piecelist_template_coords_x1')
        piece_x2 = self.entry.get_object('piecelist_template_coords_x2')
        piece_y1 = self.entry.get_object('piecelist_template_coords_y1')
        piece_y2 = self.entry.get_object('piecelist_template_coords_y2')
        piece_canvas = self.entry.get_object('piecelist_template_image')
        piece_dup = self.entry.get_object('piecelist_template_dup')

        piece_name.set_text(new_piece)
        piece_x1.set_text(str(x1))
        piece_x2.set_text(str(x2))
        piece_y1.set_text(str(y1))
        piece_y2.set_text(str(y2))

        piece_name.connect('focus-in-event', self.piece_name_input, True)
        piece_name.connect('focus-out-event', self.piece_name_input, False)
        piece_x1.connect('changed', self.piece_coord_input, piece_name, piece_x1, piece_y1, piece_x2, piece_y2, piece_canvas)
        piece_x2.connect('changed', self.piece_coord_input, piece_name, piece_x1, piece_y1, piece_x2, piece_y2, piece_canvas)
        piece_y1.connect('changed', self.piece_coord_input, piece_name, piece_x1, piece_y1, piece_x2, piece_y2, piece_canvas)
        piece_y2.connect('changed', self.piece_coord_input, piece_name, piece_x1, piece_y1, piece_x2, piece_y2, piece_canvas)
        piece_canvas.connect('draw', self.draw_cut_piece, piece_name)
        piece_dup.connect('clicked', self.add_piece, new_piece, piece_x1, piece_y1, piece_x2, piece_y2, False, True)
        piece_canvas.queue_draw()

        highlight_toggle = self.entry.get_object('piecelist_template_highswitch')
        highlight_toggle.connect('state-set', self.highlight_toggle, piece_name)

        self.rendered_shapes.append({'Name': new_piece, "Redraw": True, "Coords": [x1, y1, x2, y2]})

        # Deleting Piece
        piece_delete = self.entry.get_object('piecelist_template_delete')
        piece_delete.connect('clicked', self.delete_piece, piece_entry, piece_name)
        self.piece_list_box.pack_start(piece_entry, False, True, 0)

        self.spritesheet_canvas.queue_draw()

        # Error dialog if necessary
        if err:
            func.dialog(
                'The entity you were trying to load had multiple pieces under the same name.\n\nThese pieces have had their names changed.')
        else:
            self.save_sheet()

    def delete_piece(self, widget, widg, name_widg):
        name = name_widg.get_text()
        index = func.d_index_of(self.rendered_shapes, 'Name', name)
        del self.rendered_shapes[index]
        self.spritesheet_canvas.queue_draw()
        self.piece_list_box.remove(widg)
        self.save_sheet()

    def draw_cut_piece(self, area, ctx, piece_name):
        if self.current_spritesheet is not None:
            piece = piece_name.get_text()
            index = func.d_index_of(self.rendered_shapes, 'Name', piece)
            coords = self.rendered_shapes[index]['Coords']
            if self.window_manager.config.get_config('Theme') == 'Nordic-darker':
                ctx.set_source_rgba(59 / 256, 66 / 256, 82 / 256, 1)
            else:
                ctx.set_source_rgba(230, 230, 230, 1)

            ctx.set_operator(cairo.OPERATOR_SOURCE)
            ctx.paint()
            ctx.set_operator(cairo.OPERATOR_OVER)
            ctx.set_source_rgba(1, 1, 1, 1)

            w = coords[2] - coords[0]
            h = coords[3] - coords[1]
            if w > h:
                if w > 125:
                    scale = 125/w
                else:
                    scale = 1
            else:
                if h > 125:
                    scale = 125/h
                else:
                    scale = 1
            neww = w*scale
            newh = h*scale
            woff = (125-neww)/2
            hoff = (125-newh)/2
            ctx.translate(woff, hoff)
            ctx.rectangle(0, 0, w*scale, h*scale)
            ctx.close_path()
            ctx.scale(scale, scale)
            ctx.clip()
            ctx.set_source_surface(self.spritesheet_image, -coords[0], -coords[1])
            ctx.paint()
        return True

    def clear_piece_window(self):
        for c in self.piece_list_box.get_children():
            self.piece_list_box.remove(c)

    def piece_name_input(self, widget, event, boolean):
        if boolean:
            self.previous_name = widget.get_text()
        else:
            if widget.get_text() != self.previous_name:
                name_taken = True
                taken_pass = False
                new_piece = widget.get_text()

                index = func.d_index_of(self.rendered_shapes, 'Name', self.previous_name)
                self.rendered_shapes[index]['Name'] = '___PLACEHOLDER___'

                while name_taken:
                    for shape in self.rendered_shapes:
                        if shape['Name'] == new_piece:
                            new_piece = new_piece + ' 2'
                            taken_pass = True
                    if not taken_pass:
                        name_taken = False
                    taken_pass = False

                self.rendered_shapes[index]['Name'] = new_piece
                widget.set_text(new_piece)
                self.save_sheet()

    def piece_coord_input(self, widget, name, x1, y1, x2, y2, piece_canvas):
        p_name = name.get_text()
        coords = [x1.get_text(), y1.get_text(), x2.get_text(), y2.get_text()]
        for c in coords:
            try:
                int(c)
            except ValueError:
                coords[coords.index(c)] = 0
            else:
                coords[coords.index(c)] = int(c)
        index = func.d_index_of(self.rendered_shapes, 'Name', p_name)
        self.rendered_shapes[index]['Coords'] = coords
        self.spritesheet_canvas.queue_draw()
        piece_canvas.queue_draw()
        self.save_sheet()

    def highlight_toggle(self, area, widget, name_widget):
        name = name_widget.get_text()
        if not widget:
            self.rendered_shapes[func.d_index_of(self.rendered_shapes, 'Name', name)]['Redraw'] = False
        else:
            self.rendered_shapes[func.d_index_of(self.rendered_shapes, 'Name', name)]['Redraw'] = True

        self.spritesheet_canvas.queue_draw()

    def clean_sheet(self, area, context):
        if self.window_manager.config.get_config('Theme') == 'Nordic-darker':
            context.set_source_rgba(59 / 256, 66 / 256, 82 / 256, 1)
        else:
            context.set_source_rgba(230, 230, 230, 1)

        context.set_operator(cairo.OPERATOR_SOURCE)
        context.paint()
        context.set_operator(cairo.OPERATOR_OVER)

        if self.spritesheet_image is not None:
            context.set_source_rgba(1, 1, 1, 1)
            context.set_source_surface(self.spritesheet_image, 0, 0)

        context.paint()

    def draw_shape(self, context, x1, y1, x2, y2, r, g, b):
        context.set_line_width(1)
        red = float(r) / 255
        green = float(g) / 255
        blue = float(b) / 255
        context.set_source_rgba(red, green, blue, 1)
        # s will be [x1, y1, x2, y2]
        w = x2 - x1
        h = y2 - y1
        context.rectangle(x1, y1, w, h)
        context.stroke()
        if self.switch_corners.get_active():
            context.set_source_rgba(red, green, blue, 0.5)
            context.rectangle(x1, y1, 8, 8)
            context.fill()

    def save_sheet(self):
        pieces = {}
        for p in self.rendered_shapes:
            pieces[p['Name']] = p['Coords']
        self.data_json[self.current_model]['Pieces'] = pieces
        self.data_json[self.current_model]['Image'] = self.current_spritesheet
