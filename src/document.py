# document.py
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
from gi.repository import Gio, GLib
from .formulabox import FormulaBox
from .qalculator import Qalculator
from .cell import Cell, CellType
from .converter import *
import json # for saving and loading
from collections import deque

@Gtk.Template(resource_path='/com/github/eemilp/Formulate/document.ui')
class Document(Gtk.Box):
    __gtype_name__ = 'Document'

    qalc = Qalculator()

    cells = Gtk.Template.Child("cells")
    toast_overlay = Gtk.Template.Child("toast_overlay")

    cell_history = deque()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        #constructing the status page
        empty_notebook_page = Adw.StatusPage.new()
        empty_notebook_page.set_title("Empty Notebook")
        empty_notebook_page.set_description("Add cell")
        add_math_button = Gtk.Button.new_with_label("Math")
        add_text_button = Gtk.Button.new_with_label("Text")
        add_math_button.connect("clicked", self.add_cell, CellType.MATH)
        add_text_button.connect("clicked", self.add_cell, CellType.TEXT)
        button_box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 5)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.append(add_math_button)
        button_box.append(add_text_button)
        empty_notebook_page.set_child(button_box)
        self.cells.set_placeholder(empty_notebook_page)

        self.cells.connect("row-activated", self.row_selected)


        add_math_button.grab_focus()

        # add an empty cell
        # self.append_cell()

    def remove_cell(self, cell):
        # undo toast
        toast = Adw.Toast.new("Deleted cell")
        toast.set_button_label("Undo")
        toast.set_priority(1) #high prio
        toast.connect("dismissed", self.dismissed_undo_toast)
        toast.connect("button_clicked", self.toast_undo)

        self.toast_overlay.add_toast(toast)

        pos = cell.get_parent().get_index()

        self.cells.remove(cell.get_parent())
        self.cell_history.append({'pos':pos, 'cell':cell})

        # if computation we need to recompute to not have internal state
        if cell.cell_type == CellType.COMPUTATION:
            self.run_calculation()

    def toast_undo(self, _ = None):
        cell = self.cell_history[-1]['cell']
        pos = self.cell_history[-1]['pos']

        self.cells.insert(cell, pos)

        # if computation we need to recompute to not have internal state
        if cell.cell_type == CellType.COMPUTATION:
            self.run_calculation()

    def dismissed_undo_toast(self, _ = None):
        self.cell_history.pop()

    def add_cell(self, pos=None, cell_type = CellType.TEXT, cell_data = None):
        new_cell = Cell(cell_type, cell_data)
        new_cell.connect("calculate", self.run_calculation)
        new_cell.connect("add_cell_below", self.add_cell)
        new_cell.connect("remove_cell", self.remove_cell)

        cell_editor = new_cell.get_editor()

        if type(pos) is Cell:
            index = pos.get_parent().get_index() + 1
            self.cells.insert(new_cell, index)
        else:
            self.cells.append(new_cell)

        row = new_cell.get_parent()

        cell_editor.grab_focus()

    def row_selected(self, _, row):
        editor = row.get_child().get_editor()
        row.get_child().get_editor().grab_focus()


    def run_calculation(self, _widget = None):
        cells = [c.get_child() for c in self.cells][:-1] #Due to last element being status page
        computed_cells = [c for c in cells if c.cell_type == CellType.COMPUTATION]

        # get all expressions in the document
        expressions = [c.get_expression() for c in computed_cells]

        # Empty rows get discarded by qalc -> empty rows replaced by zero
        expressions = ['0' if e == '' else e for e in expressions]

        # calculate the results
        result_string = self.qalc.qalculate('\n'.join(expressions))
        results = result_string.split('\n') #! note last element empty

        # update labels
        for (c, r) in zip(computed_cells, results):
            c.update_result(r)

    def save_file(self, file):
        # TODO version information
        cells = [c.get_child() for c in self.cells][:-1] #Due to last element being status page
        cell_data = [dict(type=c.cell_type, content=c.get_cell_content()) for c in cells]
        data = dict(version="0.1.0", cells=cell_data)
        data_str = json.dumps(data)
        bytes = GLib.Bytes.new(data_str.encode('utf-8'))

        # Start the asynchronous operation to save the data into the file
        file.replace_contents_bytes_async(bytes,
                                          None,
                                          False,
                                          Gio.FileCreateFlags.NONE,
                                          None,
                                          self.save_file_complete)

    def save_file_complete(self, file, result):
        res = file.replace_contents_finish(result)
        info = file.query_info("standard::display-name",
                           Gio.FileQueryInfoFlags.NONE)
        if info:
           display_name = info.get_attribute_string("standard::display-name")
        else:
            display_name = file.get_basename()

        toast = Adw.Toast.new("Saved " + display_name)
        if not res:
            toast = Adw.Toast.new(f"Unable to save {display_name}")

        self.toast_overlay.add_toast(toast)

    def open_file(self, file):
        file.load_contents_async(None, self.open_file_complete)

    def open_file_complete(self, file, result):
        # TODO error handling
        contents = file.load_contents_finish(result)
        if not contents[0]:
            path = file.peek_path()
            print(f"Unable to open {path}: {contents[1]}")

        decoded = contents[1].decode('utf-8')
        data = json.loads(decoded)

        # TODO check version

        cell_data = data['cells']

        # remove current document and add new document
        # for c in [c for c in self.cells]: # jWow this is stupid
            # self.cells.remove(c)
        for d in cell_data:
            self.add_cell(None, d['type'], d['content'])

        self.run_calculation()

    def export_file(self, file, type = 'md'):
        cells = [c.get_child() for c in self.cells][:-1] #Due to Empty last element

        def get_md(c):
            if c.cell_type == CellType.MATH:
                return '$$\n' + c.get_cell_content() + '\n$$'
            elif c.cell_type == CellType.COMPUTATION:
                return '$$\n' + c.get_cell_content() + ' ' + c.get_result() + '\n$$'
            else:
                return c.get_cell_content()

        lines = [get_md(c) for c in cells]
        data_str = '\n'.join(lines)

        # TODO pdf conversion
        data_str = create_tex_source(data_str)

        bytes = GLib.Bytes.new(data_str.encode('utf-8'))

        # Start the asynchronous operation to save the data into the file
        file.replace_contents_bytes_async(bytes,
                                          None,
                                          False,
                                          Gio.FileCreateFlags.NONE,
                                          None,
                                          self.export_complete)

    def export_complete(self, file, result):
        res = file.replace_contents_finish(result)
        info = file.query_info("standard::display-name",
                           Gio.FileQueryInfoFlags.NONE)
        if info:
           display_name = info.get_attribute_string("standard::display-name")
        else:
            display_name = file.get_basename()
        if not res:
            print(f"Unable to save {display_name}")

