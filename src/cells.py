# cells.py
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
from gi.repository import Gtk, Gdk
from gi.repository import GObject, Gio, GLib
from .formula import Editor
from .utils import add_shortcut_to_action
from enum import IntEnum

# different types of cells
class CellType(IntEnum):
    MATH = 1
    TEXT = 2
    COMPUTATION = 3

# Abstarct type to hold signals and common behavior for each cell
class Cell(Gtk.ListBoxRow):
    __gtype_name__ = 'Cell'
    __gsignals__ = {
        'add_cell_below': (GObject.SignalFlags.RUN_LAST, None, (int,)),
        'remove_cell': (GObject.SignalFlags.RUN_LAST, None, ()),
        'edit' : (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self, **kwargs):
        add_shortcut_to_action(self, "<Ctrl>t", "cell.add_text")
        add_shortcut_to_action(self, "<Ctrl>m", "cell.add_math")
        super().__init__(**kwargs)

        # Actions
        self.add_math_action = Gio.SimpleAction(
            name="add_math",
        )
        self.add_math_action.connect("activate", self.on_add_math)
        self.add_text_action = Gio.SimpleAction(
            name="add_text",
        )
        self.add_text_action.connect("activate", self.on_add_text)

        self.cell_action_group = Gio.SimpleActionGroup()
        self.cell_action_group.add_action(self.add_math_action)
        self.cell_action_group.add_action(self.add_text_action)
        self.insert_action_group("cell", self.cell_action_group)

    def on_edit(self, _):
        self.emit("edit")

    def on_add_math(self, widget, _ = None):
        self.emit("add_cell_below", int(CellType.MATH))

    def on_add_text(self, widget = None, _ = None):
        self.emit("add_cell_below", int(CellType.TEXT))

    def remove(self, widget = None, _ = None):
        self.emit("remove_cell")

# Helper function to create cells based on data and CellType
def create_cell(cell_type, content = None):
    if cell_type == CellType.MATH:
        return MathCell(content)
    if cell_type == CellType.COMPUTATION:
        return MathCell(content, True)
    if cell_type == CellType.TEXT:
        return TextCell(content)
    else:
        print("Oh no!")
        return None

@Gtk.Template(resource_path='/com/github/eemilp/Formulate/mathcell.ui')
class MathCell(Cell):
    __gtype_name__ = 'MathCell'
    __gsignals__ = {
        'calculate' : (GObject.SignalFlags.RUN_LAST, None, ()),
        'clear' : (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    viewport = Gtk.Template.Child("editor_viewport")
    result_label = Gtk.Template.Child("result_text")
    revealer = Gtk.Template.Child("long_text_revealer")
    calculate_button_revealer = Gtk.Template.Child("calculate_button_revealer")
    long_label = Gtk.Template.Child("long_text")
    calculate_button = Gtk.Template.Child("calculate_button")

    computation = False

    def __init__(self, data = None, is_computation = False, **kwargs):
        add_shortcut_to_action(self, "<Ctrl>Return", "cell.run")
        add_shortcut_to_action(self, "<Shift>Return", "cell.add_and_run")
        add_shortcut_to_action(self, "<Ctrl>BackSpace", "cell.clear")
        super().__init__(**kwargs)

        # Add actions
        self.run_action = Gio.SimpleAction(
            name="run"
        )
        self.run_action.connect("activate", self.on_calculate)
        self.add_and_run_action = Gio.SimpleAction(
            name="add_and_run"
        )
        self.add_and_run_action.connect("activate", self.on_add_and_run)
        self.clear_action = Gio.SimpleAction(
            name="clear"
        )
        self.clear_action.connect("activate", self.clear)

        self.cell_action_group.add_action(self.run_action)
        self.cell_action_group.add_action(self.add_and_run_action)
        self.cell_action_group.add_action(self.clear_action)
        self.insert_action_group("cell", self.cell_action_group)

        # Init cell
        self.computation = is_computation

        elements = None #TODO loading
        self.editor = Editor(elements)
        self.editor.connect("edit", self.on_edit)
        self.editor.connect("newline", self.on_add_math)
        self.editor.connect("delete", self.remove)
        self.viewport.set_child(self.editor)

        # Focus controller
        self.focus_controller = Gtk.EventControllerFocus.new()
        self.focus_controller.connect("enter", self.on_focus_enter)
        self.focus_controller.connect("leave", self.on_focus_leave)
        self.add_controller(self.focus_controller)

        # Button and revealer
        self.calculate_button.connect("clicked",self.on_calculate_button_clicked)
        if self.computation:
            self.set_button_clear()
        else:
            self.set_button_calculate()

    def set_button_clear(self):
        self.calculate_button.set_icon_name("edit-clear-symbolic")
    def set_button_calculate(self):
        self.calculate_button.set_icon_name("media-playback-start")
    def on_calculate_button_clicked(self, widget):
        if self.computation:
            self.clear(self.calculate_button)
        else:
            self.on_calculate(self.calculate_button)

    def get_type(self):
        if self.computation:
            return CellType.COMPUTATION
        else:
            return CellType.MATH

    def get_expression(self):
        if self.computation:
            return self.editor.expr.to_str()
        else:
            return None

    def get_latex(self):
        return self.editor.expr.to_latex() + self.result_label.get_label()
    def get_content(self):
        # JSON
        expression = self.editor.expr
        expr_dict = expression.dump()
        return expr_dict

    def get_editor(self):
        return self.editor

    def update_result(self, result):
        # self.result_label.set_selectable(True)
        # if there is an = sign, use an arrow for more beautiful notation
        if result is None:
            self.result_label.set_label("")
        elif('=' in self.viewport.get_child().expr.to_str()):
            formatted_label = "<span font='Latin Modern Math 18'>→ " + result + "</span>"
            self.result_label.set_label(formatted_label)
        else:
            formatted_label = "<span font='Latin Modern Math 18'>= " + result + "</span>"
            self.result_label.set_label(formatted_label)

    def update_interpretation(self, interp):
        if interp is None:
            self.long_label.set_label("")
        else:
            self.long_label.set_label(interp)

    def on_add_and_run(self, widget, _ = None):
        self.on_calculate(None)
        self.on_add_math(None)

    def on_calculate(self, widget, _ = None):
        self.computation = True
        self.revealer.set_reveal_child(True)
        self.set_button_clear()
        self.emit("calculate")

    def clear(self, widget, _ = None):
        self.computation = False
        self.revealer.set_reveal_child(False)
        self.update_result(None)
        self.set_button_calculate()
        self.emit("calculate")

    def on_focus_enter(self, widget, _ = None):
        self.calculate_button_revealer.set_reveal_child(True)
        if self.computation:
            self.revealer.set_reveal_child(True)
    def on_focus_leave(self, widget, _ = None):
        self.calculate_button_revealer.set_reveal_child(False)
        if self.computation:
            self.revealer.set_reveal_child(False)
            self.emit("calculate")



@Gtk.Template(resource_path='/com/github/eemilp/Formulate/textcell.ui')
class TextCell(Cell):
    __gtype_name__ = 'TextCell'
    __gsignals__ = {
        'calculate' : (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    editor = Gtk.Template.Child("textview")

    def __init__(self, data = None, **kwargs):
        add_shortcut_to_action(self, "<Shift>Return", "cell.add_math")
        super().__init__(**kwargs)

        # TODO load files

        self.editor.connect("backspace", self.on_backspace)
        self.editor.connect("move-cursor", self.on_move_cursor)
        self.buffer = self.editor.get_buffer()
        self.buffer.connect("changed", self.on_edit)

    def get_type(self):
        return CellType.TEXT

    def get_latex(self):
        # Essentially copied from gnome documentation:
        buffer = self.editor.get_buffer()
        # Retrieve the iterator at the start of the buffer
        start = buffer.get_start_iter()
        # Retrieve the iterator at the end of the buffer
        end = buffer.get_end_iter()
        # Retrieve all the visible text between the two bounds
        text = buffer.get_text(start, end, False)
        return text
    def get_content(self):
        # Just returns the content of the cell. Same as latex
        return self.get_latex()

    def on_backspace(self, widget, _ = None):
        if self.buffer.get_char_count() == 0:
            self.remove()

    def on_move_cursor(self, textview, step, count, extend_selection):
        pass

    def get_editor(self):
        return self.editor
