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
    MATH = 0
    TEXT = 1
    COMPUTATION = 2

@Gtk.Template(resource_path='/com/github/eemilp/Formulate/cell.ui')
class Cell(Adw.Bin):
    __gtype_name__ = 'Cell'
    __gsignals__ = {
        'add_cell_below': (GObject.SignalFlags.RUN_LAST, None, (int,)),
        'remove_cell': (GObject.SignalFlags.RUN_LAST, None, ()),
        'calculate' : (GObject.SignalFlags.RUN_LAST, None, ()),
        'edit' : (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    cell_centerbox = Gtk.Template.Child("cell_centerbox")
    remove_cell_button = Gtk.Template.Child("remove_cell")
    add_cell_button = Gtk.Template.Child("add_cell")
    run_cell_button = Gtk.Template.Child("run_cell")
    clear_cell_button = Gtk.Template.Child("clear_cell")

    right_revealer = Gtk.Template.Child("right_revealer")
    left_revealer = Gtk.Template.Child("left_revealer")

    cell_type = None

    def __init__(self, cell_type, data=None, **kwargs):
        add_shortcut_to_action(self, "<Ctrl>t", "cell.add_text")
        add_shortcut_to_action(self, "<Ctrl>m", "cell.add_math")
        add_shortcut_to_action(self, "<Shift>Return", "cell.add_and_run")
        add_shortcut_to_action(self, "<Ctrl>Return", "cell.run")
        add_shortcut_to_action(self, "<Ctrl>BackSpace", "cell.clear")
        super().__init__(**kwargs)
        self.create_editor(cell_type, data)

        add_math_action = Gio.SimpleAction(
            name="add_math",
        )
        add_math_action.connect("activate", self.add_cell_or_change_type, CellType.MATH)
        add_text_action = Gio.SimpleAction(
            name="add_text",
        )
        add_text_action.connect("activate", self.add_cell_or_change_type, CellType.TEXT)
        run_action = Gio.SimpleAction(
            name="run"
        )
        run_action.connect("activate", self.run_calculation)
        add_and_run_action = Gio.SimpleAction(
            name="add_and_run"
        )
        add_and_run_action.connect("activate", self.add_and_run)
        clear_action = Gio.SimpleAction(
            name="clear"
        )
        clear_action.connect("activate", self.clear_calculation)

        cell_menu_group = Gio.SimpleActionGroup()
        cell_menu_group.add_action(add_math_action)
        cell_menu_group.add_action(add_text_action)
        cell_menu_group.add_action(run_action)
        cell_menu_group.add_action(add_and_run_action)
        cell_menu_group.add_action(clear_action)
        self.insert_action_group("cell", cell_menu_group)

        self.remove_cell_button.connect("clicked", self.remove_cell_button_clicked)
        self.add_cell_button.connect("clicked", self.add_cell_button_clicked, CellType.MATH)
        self.run_cell_button.connect("clicked", lambda *_: self.run_calculation())
        self.clear_cell_button.connect("clicked", self.clear_calculation)

        focus_controller = Gtk.EventControllerFocus.new()
        focus_controller.connect("enter", self.on_focus_enter)
        focus_controller.connect("leave", self.on_focus_leave)
        self.add_controller(focus_controller)

    def create_editor(self, cell_type, data = None):
        self.cell_type = cell_type
        if cell_type == CellType.MATH or cell_type == CellType.COMPUTATION:
            # add one formulabox for now
            formulabox = FormulaBox(data)
            self.cell_centerbox.set_center_widget(formulabox)

            formulabox.viewport.get_child().connect("edit", self.on_edit)
            formulabox.viewport.get_child().connect("newline", self.add_cell, CellType.MATH)

        elif cell_type == CellType.TEXT:
            # text editor implemented in an TextView
            textbox = TextBox()
            self.cell_centerbox.set_center_widget(textbox)

            buffer = textbox.textview.get_buffer()
            buffer.connect("changed", self.on_edit)

            if data != None:
                buffer.set_text(data, -1)
        else:
            return None

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

    def run_calculation(self, widget = None, _ = None):
        if self.cell_type != CellType.TEXT:
            self.cell_type = CellType.COMPUTATION
            self.emit("calculate")

    def on_focus_enter(self, widget, _ = None):
        self.right_revealer.set_reveal_child(True)
        self.left_revealer.set_reveal_child(True)
    def on_focus_leave(self, widget, _ = None):
        self.right_revealer.set_reveal_child(False)
        self.left_revealer.set_reveal_child(False)
        if self.cell_type == CellType.COMPUTATION:
            self.emit("calculate")

    def on_edit(self, _ = None):
        if self.get_cell_content() == "":
            self.add_cell_button.set_icon_name("text-math-change-symbolic")
        else:
            self.add_cell_button.set_icon_name("list-add-symbolic")
        self.emit("edit")

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

    def add_and_run(self, widget, _):
        self.emit("add_cell_below", int(CellType.MATH))
        if self.cell_type != CellType.TEXT:
            self.run_calculation()

    def clear_calculation(self, widget, _ = None):
        if self.cell_type != CellType.TEXT:
           self.update_result(None)
           self.cell_type = CellType.MATH
           self.emit("calculate")

    # Essentially passing through button signals
    def add_cell_button_clicked(self, widget, _ = None, data=CellType.MATH):
        if self.get_cell_content() == "":
            self.add_cell_button.popup()
        else:
            self.add_cell(widget, _, data)

    def add_cell_or_change_type(self, widget, _ = None, data=CellType.MATH):
        if self.get_cell_content() == "":
            self.cell_centerbox.set_center_widget(None)
            self.create_editor(data)
            self.get_editor().grab_focus()
        else:
            self.add_cell(widget, _, data)

    def add_cell(self, widget, _ = None, data=CellType.MATH):
        self.emit("add_cell_below", int(data))

    def remove_cell_button_clicked(self, widget):
        self.emit("remove_cell")
