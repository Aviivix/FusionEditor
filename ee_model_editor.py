import json
import gi
import os
import shutil
import cairo
import random
import func
import math
from operator import itemgetter

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk
from gi.repository import Pango


# noinspection PyUnresolvedReferences
class ModelEditor:
    def __init__(self, builder, window_manager):
        self.entity_name = None
        self.data_json = {}
        self.current_sheet = None
        self.current_spritesheet = None
        self.window_manager = window_manager
        self.spritesheet_image = None

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

        # Buttons
        self.button_add_part = builder.get_object('ee_notebook_me_control_addpart')
        self.button_dup_part = builder.get_object('ee_notebook_me_control_duppart')
        self.button_del_part = builder.get_object('ee_notebook_me_control_delpart')
        self.button_child_part = builder.get_object('ee_notebook_me_control_addchild')
        self.button_autopivot = builder.get_object('ee_notebook_me_vis_autopiv_apply')
        self.switch_framemirror = builder.get_object('ee_notebook_me_vis_mirror')
        self.switch_trueview = builder.get_object('ee_notebook_me_vis_truescale')

        # Button Signals
        self.button_add_part.connect('clicked', self.add_part, 'add')
        self.button_dup_part.connect('clicked', self.add_part, 'dup')
        self.button_del_part.connect('clicked', self.delete_part)
        self.switch_framemirror.connect('state-set', self.queue_canvas)
        self.switch_trueview.connect('state-set', self.queue_canvas)

        # Default Sensitivities
        self.button_add_part.set_sensitive(False)
        self.button_dup_part.set_sensitive(False)
        self.button_del_part.set_sensitive(False)
        self.button_child_part.set_sensitive(False)

        # Radio Buttons
        self.radio_box_none = builder.get_object('ee_notebook_me_vis_boxes_none')
        self.radio_box_sel = builder.get_object('ee_notebook_me_vis_boxes_sel')
        self.radio_box_all = builder.get_object('ee_notebook_me_vis_boxes_all')
        self.radio_piv_none = builder.get_object('ee_notebook_me_vis_pivots_none')
        self.radio_piv_sel = builder.get_object('ee_notebook_me_vis_pivots_sel')
        self.radio_piv_all = builder.get_object('ee_notebook_me_vis_pivots_all')
        self.radio_box_none.connect('toggled', self.queue_canvas)
        self.radio_box_sel.connect('toggled', self.queue_canvas)
        self.radio_box_all.connect('toggled', self.queue_canvas)
        self.radio_piv_none.connect('toggled', self.queue_canvas)
        self.radio_piv_sel.connect('toggled', self.queue_canvas)
        self.radio_piv_all.connect('toggled', self.queue_canvas)

        # Dropdown
        self.dropdown_modellist = builder.get_object('ee_notebook_me_modellist')
        self.dropdown_modellist.connect('changed', self.switch_model)

        # Part List Box
        self.part_tree = builder.get_object('ee_notebook_me_tree')
        self.piece_tree = builder.get_object('ee_notebook_me_piecetree')

        # FUcking cairo canvas
        self.previewframe = builder.get_object('ee_notebook_me_previewframe')
        self.canvas = builder.get_object('ee_notebook_me_previewcanvas')
        self.canvas.connect('draw', self.refresh_canvas)
        self.dropdown_backgrounds = builder.get_object('ee_notebook_me_bglist')
        self.dropdown_backgrounds.connect('changed', self.bg_set)

        # Refresh Backgrounds
        self.list_backgrounds = [x[0] for x in os.walk('assets/backgrounds')]
        del self.list_backgrounds[0]

        self.dropdown_backgrounds.remove_all()
        for d in self.list_backgrounds:
            self.dropdown_backgrounds.append_text(d.rsplit('\\', 1)[-1])
        self.dropdown_backgrounds.set_active(0)

        # ListStore for Models
        self.pieces_cols = [
            'Piece',
            'Width',
            'Height'
        ]

        # ListStore Initialization
        self.cols = [
            'Part',
            'Parent',
            'Piece',
            'X Pos',
            'Y Pos',
            'Z Order',
            'X Scale',
            'Y Scale',
            'Rotation',
            'X Pivot',
            'Y Pivot',
            'Alpha',
            'Color',
            'Tint',
            'Blend'
        ]
        self.part_entries = []
        self.piece_entries = []

        self.piece_listmodel = gtk.ListStore(str, int, int)
        self.part_listmodel = gtk.ListStore(str, str, str, int, int, int, float, float, int, int, int, float, str, float, str)

        self.piece_tree.set_model(self.piece_listmodel)
        self.piece_tree.columns_autosize()
        self.part_tree.set_model(self.part_listmodel)
        self.part_tree.columns_autosize()

        for i, column in enumerate(self.cols):
            cell = gtk.CellRendererText()
            cell.props.editable_set = True
            cell.props.editable = True
            cell.connect('edited', self.edited, self.cols.index(column), column)
            col = gtk.TreeViewColumn(column, cell, text=i)
            col.set_expand(True)
            self.part_tree.append_column(col)

        for i, column in enumerate(self.pieces_cols):
            cell = gtk.CellRendererText()
            col = gtk.TreeViewColumn(column, cell, text=i)
            col.set_expand(True)
            self.piece_tree.append_column(col)

        self.part_tree.get_selection().connect('changed', self.selected)
        self.button_autopivot.connect('clicked', self.auto_pivot)

    def auto_pivot(self, *args):
        sel = self.part_tree.get_selection()
        sel = sel.get_selected()
        print(sel)

    def edited(self, widget, path, new_text, col, colname):
        sel = self.part_tree.get_selection()
        sel = sel.get_selected()
        name = sel[0].get_value(sel[1], 0)
        abort = False
        if colname in ['X Pos', 'Y Pos', 'Z Order', 'Rotation', 'X Pivot', 'Y Pivot']:
            try:
                int(new_text)
            except ValueError:
                text = 0
            else:
                text = int(new_text)
            self.part_listmodel[path][col] = text
        elif colname in ['X Scale', 'Y Scale', 'Alpha', 'Tint']:
            try:
                float(new_text)
            except ValueError:
                text = 0
            else:
                text = float(new_text)
            self.part_listmodel[path][col] = text
        elif colname == 'Piece':
            text = new_text
            if text in self.data_json[self.currentmodel]['Pieces']:
                self.part_listmodel[path][col] = text
            else:
                abort = True
        elif colname == 'Parent':
            text = new_text
            if text in self.data_json[self.currentmodel]['Parts']:
                self.part_listmodel[path][col] = text
            else:
                text = 'None'
                self.part_listmodel[path][col] = text
        elif colname == 'Blend':
            text = new_text.upper()
            if text in ['OVER', 'XOR', 'ADD', 'SATURATE', 'MULTIPLY', 'SCREEN', 'OVERLAY', 'DARKEN', 'LIGHTEN', 'COLOR DODGE', 'COLOR BURN', 'HARD LIGHT', 'SOFT LIGHT', 'DIFFERENCE', 'EXCLUSION']:
                self.part_listmodel[path][col] = text
            else:
                abort = True
        else:
            text = new_text
            self.part_listmodel[path][col] = text

        if not abort:
            sel2 = self.part_tree.get_selection()
            sel2 = sel2.get_selected()
            values = list(sel[0].get(sel2[1], 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14))

            self.part_entries[int(path)] = list(sel[0].get(sel[1], 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14))

            if colname == 'Part':
                del self.data_json[self.currentmodel]['Parts'][name]
                self.data_json[self.currentmodel]['Parts'][text] = list(values)
            else:
                self.data_json[self.currentmodel]['Parts'][name] = list(values)
                curname = name
        self.canvas.queue_draw()

    def selected(self, *args):
        self.button_dup_part.set_sensitive(True)
        self.button_del_part.set_sensitive(True)

    def add_part(self, widget, sourcetype):
        if sourcetype == 'add':
            name_taken = True
            taken_pass = False
            count = 2
            new_part = 'New Part'
            while name_taken:
                for part in self.data_json[self.currentmodel]['Parts']:
                    if part == new_part:
                        new_part = new_part + str(count)
                        count += 1
                        taken_pass = True
                if not taken_pass:
                    name_taken = False
                taken_pass = False

            self.part_entries.append([new_part, 'None', '', 0, 0, 0, 1, 1, 0, 0, 0, 1, 'FFFFFF', 0, 'MULTIPLY'])
            self.part_listmodel.append(self.part_entries[-1])
            self.data_json[self.currentmodel]['Parts'][new_part] = ['None', '', 0, 0, 0, 1, 1, 0, 0, 0, 1, 'FFFFFF', 0, 'MULTIPLY']
        elif sourcetype == 'dup':
            sel = self.part_tree.get_selection()
            sel = sel.get_selected()
            name = sel[0].get_value(sel[1], 0)
            name_taken = True
            taken_pass = False
            count = 2
            while name_taken:
                for part in self.data_json[self.currentmodel]['Parts']:
                    if part == name:
                        name = name + str(count)
                        count += 1
                        taken_pass = True
                if not taken_pass:
                    name_taken = False
                taken_pass = False
            values = list(sel[0].get(sel[1], 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14))
            self.data_json[self.currentmodel]['Parts'][name] = values
            self.part_entries.append(values)
            self.part_listmodel.append(self.part_entries[-1])
        self.canvas.queue_draw()

    def delete_part(self, widget):
        sel = self.part_tree.get_selection()
        sel = sel.get_selected()
        name = sel[0].get_value(sel[1], 0)
        self.part_entries.remove(list(sel[0].get(sel[1], 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)))
        self.part_listmodel.remove(sel[1])
        del self.data_json[self.currentmodel]['Parts'][name]

    def switch_model(self, *args):
        if self.dropdown_modellist.get_active_text() is not None:
            self.button_add_part.set_sensitive(True)

            self.piece_listmodel.clear()
            self.currentmodel = self.dropdown_modellist.get_active_text()
            for p in self.data_json[self.currentmodel]['Pieces']:
                self.add_piece(p, self.data_json[self.currentmodel]['Pieces'][p])

            # Canvas shit
            self.current_spritesheet = self.data_json[self.currentmodel]['Image']
            self.spritesheet_image = cairo.ImageSurface.create_from_png('assets/entities/' + self.entity_name + '/' + self.current_spritesheet)

            self.part_listmodel.clear()
            self.part_entries = []
            for o in self.data_json[self.currentmodel]['Parts']:
                part_data = list(self.data_json[self.currentmodel]['Parts'][o])
                self.part_entries.append(part_data)
                part_data.insert(0, o)
                if part_data[2] in self.data_json[self.currentmodel]['Pieces']:
                    coords = self.data_json[self.currentmodel]['Pieces'][part_data[2]]
                else:
                    coords = [0, 0, 0, 0]
                self.part_listmodel.append(self.part_entries[-1])

            self.canvas.queue_draw()

    def add_piece(self, name, coords):
        w = coords[2] - coords[0]
        h = coords[3] - coords[1]
        self.piece_listmodel.append([name, w, h])

    def queue_canvas(self, *args):
        if self.switch_trueview.get_active():
            self.previewframe.set_size_request(1600, 900)
        else:
            self.previewframe.set_size_request(-1, -1)
        self.canvas.queue_draw()

    def refresh_canvas(self, area, context):
        self.clean_canvas(area, context)
        return True

    def clean_canvas(self, area, context):
        context.set_source_rgba(0, 0, 0, 1)
        if self.dropdown_backgrounds.get_active_text() is not None:
            if not self.switch_trueview.get_active():
                extents = context.clip_extents()
                xscale = extents[2] / 1600
                yscale = extents[3] / 900
                # Revise this to assemble a background spritesheet
                context.scale(xscale, yscale)
            context.set_source_surface(self.bg_image, 0, 0)
            context.paint()
            context.set_operator(cairo.OPERATOR_OVER)
            if self.switch_framemirror.get_active():
                context.translate(1600, 0)
                context.scale(-1, 1)
            if self.spritesheet_image is not None:
                # Determine render order and parenting data
                part_zlist = []
                for n in self.data_json[self.currentmodel]['Parts']:
                    nl = list(self.data_json[self.currentmodel]['Parts'][n])
                    nl.insert(0, n)
                    if nl[2] in self.data_json[self.currentmodel]['Pieces']:
                        nc = self.data_json[self.currentmodel]['Pieces'][nl[2]]
                    else:
                        nc = [0, 0, 0, 0]
                    part_zlist.append([n, self.current_spritesheet, nc, [nl[3], -nl[4]], [nl[9], -nl[10]], [nl[6], nl[7]], nl[8], nl[11], [int(nl[12][0:2], 16) / 255, int(nl[12][2:4], 16) / 255, int(nl[12][4:6], 16) / 255], nl[13], self.blends[nl[14]], nl[5], nl[1]])
                z_order = sorted(part_zlist, key=itemgetter(11))
                # Render the shit
                for p in z_order:
                    self.draw_part(context, p)


    def draw_part(self, context, p):
        # 0      1       2             3          4       5       6          7       8     9      10         11        12
        # Name | Image | PieceCoords | Position | Pivot | Scale | Rotation | Alpha | RGB | Tint | Operator | Z Order | Parent
        context.save()
        w = p[2][2] - p[2][0]
        h = p[2][3] - p[2][1]
        # Self Values
        pos = p[3]
        piv = [ p[4][0], p[4][1] + h ]
        scale = p[5]
        rotation = p[6]*math.pi/180
        alpha = p[7]
        rgb = p[8]
        tint = p[9]
        operator = p[10]
        # Apply inheritance
        parents = []
        checking = p[12]
        rooting = True
        if p[12] in self.data_json[self.currentmodel]['Parts']:
            while rooting:
                n = self.data_json[self.currentmodel]['Parts'][checking]
                parent_coords = self.data_json[self.currentmodel]['Pieces'][n[1]]
                parents.insert(0, [parent_coords, [n[2], -n[3]], [n[8], -n[9]], [n[5], n[6]], n[7], n[10]])
                if n[0] in self.data_json[self.currentmodel]['Parts']:
                    checking = n[0]
                else:
                    rooting = False
        context.translate(0, 900)
        for i in parents:
            context.translate(i[1][0], i[1][1])
            context.scale(i[3][0], i[3][1])
            context.rotate(i[4]*math.pi/180)
            context.translate(-i[2][0], -i[2][1])
            alpha = alpha * i[5]
        context.translate(pos[0], pos[1])
        context.scale(scale[0], scale[1])
        context.rotate(rotation)
        context.translate(-piv[0] - p[2][0], -piv[1] - p[2][1])

        # Set clipping boundaries and draw the piece
        context.rectangle(p[2][0], p[2][1], w, h)
        context.save()
        context.clip()
        context.set_source_surface(self.spritesheet_image, 0, 0)
        context.paint_with_alpha(alpha)
        context.set_operator(operator)
        context.set_source_rgba(rgb[0], rgb[1], rgb[2], tint)
        context.mask_surface(self.spritesheet_image)
        context.restore()

        # Drawing bounding box, if needed.
        # Add:  or (self.radio_box_sel.get_active() and getting current selection)
        if self.radio_box_all.get_active():
            context.rectangle(p[2][0], p[2][1], w, h)
            context.set_line_width(3)
            context.set_source_rgba(255, 0, 0, 1)
            context.stroke()
            context.fill()

        # Drawing pivots, if needed.
        # Add:  or (self.radio_box_sel.get_active() and getting current selection)
        if self.radio_piv_all.get_active():
            context.arc(p[2][0] + piv[0], p[2][1] + piv[1], 10, 0.0, 2 * math.pi)
            context.set_line_width(3)
            context.set_source_rgba(255, 0, 0, 1)
            context.fill()
        # Setting canvas settings back up for the next piece.
        context.restore()

    def bg_set(self, *args):
        if self.dropdown_backgrounds.get_active_text() is not None:
            # Revise this to assemble a background spritesheet.
            self.bg_image = cairo.ImageSurface.create_from_png('assets/backgrounds/' + self.dropdown_backgrounds.get_active_text() + '/main.png')
            self.canvas.queue_draw()
