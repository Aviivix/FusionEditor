import gi
import os
import cairo
import math
from operator import itemgetter

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk as gtk
from gi.repository import Pango

class Renderer:
    def __init__(self):
        self.z_order = []
        self.symbols = {
            'Amitie (PPT2) - Root': {
                'Sheet': 'manzai.png',
                'Cut': [6, 6, 6, 6],
                'Position': [200, 200],
                'Pivot': [10, 10],
                'Scale': [1.0, 1.0],
                'Rotation': 2.1,
                'Alpha': 1.0,
                'Red': 0.5,
                'Grn': 0.3,
                'Blu': 1.0,
                'Tint': 0.0,
                'Blend': 'MULTIPLY',
                'Z-Order': 15,
                'Parent': None
            }
        }
    
    def draw(self, ctx):
        # POSITIONAL SHIT
        #  0      1       2     3     4     5      6       7        8        9    10     11    12     13    14     15      16
        # Part, Parent, Piece, Xpos, Ypos, Zpos, Xscale, Yscale, Rotation, Xpiv, Ypiv, Alpha, Color, Tint, Blend, X Off, Y Off
        ctx.save()
        # POSITIONAL SHIT
        #  0      1       2     3     4     5      6       7        8        9    10     11    12     13    14     15      16
        # Part, Parent, Piece, Xpos, Ypos, Zpos, Xscale, Yscale, Rotation, Xpiv, Ypiv, Alpha, Color, Tint, Blend, X Off, Y Off
        coords = self.data_json[self.currentmodel]['Pieces'][p[2]]
        w = coords[2] - coords[0]
        h = coords[3] - coords[1]
        piv = (p[9], -p[10] + h)
        pos = (p[3], -p[4] + 900)
        trans = ((pos[0] - piv[0]) - coords[0], (pos[1] - piv[1]) - coords[1])
        ctx.translate(trans[0], trans[1])
        # Applying inherited motions
        parenting = True
        parent_order = []
        checked_parent = p[1]
        while parenting:
            if checked_parent in self.data_json[self.currentmodel]['Parts']:
                parent_data = list(self.data_json[self.currentmodel]['Parts'][checked_parent])
                parent_data.insert(0, checked_parent)
                parent_order.append(parent_data)
                if parent_data[1] in self.data_json[self.currentmodel]['Parts']:
                    checked_parent = parent_data[1]
                else:
                    parenting = False
            else:
                parenting = False
        parent_order.reverse()
        offset = [0, 0]
        posoffset = [0, 0]
        for parent in parent_order:
            pass
            # do the shit i seriously cant be bothered right now to deal with it

        # Temporarily setting the origin to the pivot to scale and rotate
        ctx.translate(piv[0], piv[1])
        ctx.scale(p[6], p[7])
        radian = p[8] * math.pi / 180
        ctx.rotate(radian)
        ctx.translate(-piv[0], -piv[1])
        ctx.translate(-offset[0], -offset[1])
        # GENERATING THE PIECE
        ctx.rectangle(coords[0], coords[1], w, h)
        ctx.clip()
        ctx.set_source_surface(self.spritesheet_image, 0, 0)
        ctx.paint_with_alpha(p[11])
        r = int(p[12][0:2], 16) / 255
        g = int(p[12][2:4], 16) / 255
        b = int(p[12][4:6], 16) / 255
        blend = p[14].upper()
        # Hey mom can we have a switch statement?
        # we have a switch statement at home
        # Switch statement at home:
        if blend == 'OVER':
            ctx.set_operator(cairo.OPERATOR_OVER)
        elif blend == 'XOR':
            ctx.set_operator(cairo.OPERATOR_XOR)
        elif blend == 'ADD':
            ctx.set_operator(cairo.OPERATOR_ADD)
        elif blend == 'SATURATE':
            ctx.set_operator(cairo.OPERATOR_SATURATE)
        elif blend == 'MULTIPLY':
            ctx.set_operator(cairo.OPERATOR_MULTIPLY)
        elif blend == 'SCREEN':
            ctx.set_operator(cairo.OPERATOR_SCREEN)
        elif blend == 'OVERLAY':
            ctx.set_operator(cairo.OPERATOR_OVERLAY)
        elif blend == 'DARKEN':
            ctx.set_operator(cairo.OPERATOR_DARKEN)
        elif blend == 'LIGHTEN':
            ctx.set_operator(cairo.OPERATOR_LIGHTEN)
        elif blend == 'COLOR DODGE':
            ctx.set_operator(cairo.OPERATOR_COLOR_DODGE)
        elif blend == 'COLOR BURN':
            ctx.set_operator(cairo.OPERATOR_COLOR_BURN)
        elif blend == 'HARD LIGHT':
            ctx.set_operator(cairo.OPERATOR_HARD_LIGHT)
        elif blend == 'SOFT LIGHT':
            ctx.set_operator(cairo.OPERATOR_SOFT_LIGHT)
        elif blend == 'DIFFERENCE':
            ctx.set_operator(cairo.OPERATOR_DIFFERENCE)
        elif blend == 'EXCLUSION':
            ctx.set_operator(cairo.OPERATOR_EXCLUSION)
        ctx.set_source_rgba(r, g, b, p[13])
        ctx.mask_surface(self.spritesheet_image)
        # Undoing the clip
        ctx.restore()
        ctx.save()
        ctx.translate(trans[0], trans[1])
        # Setting canvas settings back up for the next piece.
        ctx.restore()