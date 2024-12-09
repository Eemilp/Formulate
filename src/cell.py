# cell.py
#
# Copyright 2024 Eemil Praks
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw
from gi.repository import Gtk
from gi.repository import GObject, Gio, GLib
# from .formula import Editor
from .formulabox import FormulaBox
from .textbox import TextBox
from .utils import add_shortcut_to_action
from enum import IntEnum

# different types of cells
class CellType(IntEnum):
    MATH = 1
    TEXT = 2
    COMPUTATION = 3

@Gtk.Template(resource_path='/com/github/eemilp/Formulate/cell.ui')
class Cell(Adw.Bin):
    __gtype_name__ = 'Cell'
    __gsignals__ = {
        'add_cell_below': (GObject.SignalFlags.RUN_LAST, None, (int,)),
        'remove_cell': (GObject.SignalFlags.RUN_LAST, None, ()),
        'calculate' : (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    cell_centerbox = Gtk.Template.Child("cell_centerbox")
    remove_cell_button = Gtk.Template.Child("remove_cell")
    add_cell_button = Gtk.Template.Child("add_cell")

    cell_type = None

    def __init__(self, cell_type, data=None, **kwargs):
        add_shortcut_to_action(self, "<Ctrl>t", "add.text")
        add_shortcut_to_action(self, "<Ctrl>m", "add.math")
        super().__init__(**kwargs)
        self.cell_type = cell_type
        if cell_type == CellType.MATH or cell_type == CellType.COMPUTATION:
            # add one formulabox for now
            formulabox = FormulaBox(data)
            self.cell_centerbox.set_center_widget(formulabox)

            # hook up the signal for calculation
            formulabox.viewport.get_child().connect("calculate", self.run_calculation)

        elif cell_type == CellType.TEXT:
            # text editor implemented in an TextView
            textbox = TextBox()

            if data != None:
                buffer = textbox.textview.get_buffer()
                buffer.set_text(data, -1)

            self.cell_centerbox.set_center_widget(textbox)
            pass
        else:
            print("Oh no!")

        add_math_action = Gio.SimpleAction(
            name="math",
        )
        add_math_action.connect("activate", self.add_cell_button_clicked, CellType.MATH)
        add_text_action = Gio.SimpleAction(
            name="text",
        )
        add_text_action.connect("activate", self.add_cell_button_clicked, CellType.TEXT)

        add_menu_group = Gio.SimpleActionGroup()
        add_menu_group.add_action(add_math_action)
        add_menu_group.add_action(add_text_action)
        self.insert_action_group("add", add_menu_group)

        self.remove_cell_button.connect("clicked", self.remove_cell_button_clicked)
        self.add_cell_button.connect("clicked", self.add_cell_button_clicked, CellType.MATH)


    # Functions to abstract away getting and updating math expressions
    def get_expression(self):
        if self.cell_type == CellType.COMPUTATION:
            return self.cell_centerbox.get_center_widget().get_expression()
        else:
            return None
    def update_result(self, result):
        if self.cell_type == CellType.COMPUTATION:
            self.cell_centerbox.get_center_widget().update_label(result)
    def get_result(self):
        if self.cell_type == CellType.COMPUTATION:
            return self.cell_centerbox.get_center_widget().get_label()
        else:
            return ""

    def run_calculation(self, _ = None):
        self.cell_type = CellType.COMPUTATION
        self.emit("calculate")

    def get_editor(self):
        if self.cell_type == CellType.MATH or self.cell_type == CellType.COMPUTATION:
            return self.cell_centerbox.get_center_widget().viewport.get_child()
        else:
            return self.cell_centerbox.get_center_widget().get_child()

    def get_cell_content(self):
        if self.cell_type == CellType.MATH or self.cell_type == CellType.COMPUTATION:
            expr = self.cell_centerbox.get_center_widget().viewport.get_child().expr
            return expr.to_latex()
        if self.cell_type == CellType.TEXT:
            # Essentially copied from gnome documentation:
            buffer = self.cell_centerbox.get_center_widget().textview.get_buffer()
            # Retrieve the iterator at the start of the buffer
            start = buffer.get_start_iter()
            # Retrieve the iterator at the end of the buffer
            end = buffer.get_end_iter()
            # Retrieve all the visible text between the two bounds
            text = buffer.get_text(start, end, False)
            return text
        else:
            print("Oh no!")
            return "";

    # Essentially passing through button signals
    def add_cell_button_clicked(self, widget, _, data=CellType.MATH):
        self.emit("add_cell_below", int(data))
    def remove_cell_button_clicked(self, widget):
        self.emit("remove_cell")

    def set_deletability(self, deletable):
        self.remove_cell_button.set_sensitive(deletable)
