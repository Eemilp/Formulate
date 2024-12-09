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

    # calculator object
    qalc = Qalculator()

    # Cells in
    cells = Gtk.Template.Child("cells")
    toast_overlay = Gtk.Template.Child("toast_overlay")

    cell_history = deque()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # add an empty cell
        self.append_cell()
        for c in self.cells:
            c.set_deletability(False)

    def remove_cell(self, cell):
        # Move this Box to BoxList and add position tracking to do the undo action
        # undo toast
        toast = Adw.Toast.new("Deleted cell")
        toast.set_button_label("Undo")
        toast.set_priority(1) #high prio
        toast.connect("dismissed", self.dismissed_undo_toast)
        toast.connect("button_clicked", self.toast_undo)

        self.toast_overlay.add_toast(toast)

        pos = [c for c in self.cells].index(cell)

        self.cells.remove(cell)
        self.cell_history.append({'pos':pos, 'cell':cell})

        # if computation we need to recompute to not have internal state
        if cell.cell_type == CellType.COMPUTATION:
            self.run_calculation()

        #Juggling deletability so that only cell cannot be deleted
        if len([0 for c in self.cells]) == 1:
            for c in self.cells:
                c.set_deletability(False)

    def toast_undo(self, _ = None):
        cell = self.cell_history[-1]['cell']
        pos = self.cell_history[-1]['pos']

        #all this to get the cell before the position or None
        cells = [None]
        cells.extend([c for c in self.cells])
        cell_before = cells[pos]
        self.cells.insert_child_after(cell, cell_before)

        if len(cells) == 2: # if there was only one cell left
            cells[1].set_deletability(True)

        # if computation we need to recompute to not have internal state
        if cell.cell_type == CellType.COMPUTATION:
            self.run_calculation()



    def dismissed_undo_toast(self, _ = None):
        self.cell_history.pop()


    def add_cell_after(self, old_cell, cell_type):
        #Juggling deletability so that only cell cannot be deleted
        if len([0 for c in self.cells]) == 1:
            for c in self.cells:
                c.set_deletability(True)

        new_cell = Cell(cell_type)

        # connect the signals to cell controls
        cell_editor = new_cell.get_editor()

        new_cell.connect("calculate", self.run_calculation)

        new_cell.connect("add_cell_below", self.add_cell_after)
        new_cell.connect("remove_cell", self.remove_cell)

        # insert new cell and move focus to it
        self.cells.insert_child_after(new_cell, old_cell)
        cell_editor.grab_focus()

    # Ugly but needed for adding the initial cell
    def append_cell(self, cell_type = CellType.TEXT, cell_data = None):
        #Juggling deletability so that only cell cannot be deleted
        if len([0 for c in self.cells]) == 1:
            for c in self.cells:
                c.set_deletability(True)

        new_cell = Cell(cell_type, cell_data)
        cell_editor = new_cell.get_editor()

        # connect the calculate signal to run the notebook
        new_cell.connect("calculate", self.run_calculation)

        new_cell.connect("add_cell_below", self.add_cell_after)
        new_cell.connect("remove_cell", self.remove_cell)

        #Insert cell, grab focus
        self.cells.append(new_cell)
        cell_editor.grab_focus()

    def run_calculation(self, _widget = None):
        computed_cells = [c for c in self.cells if c.cell_type == CellType.COMPUTATION]

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
        cell_data = [dict(type=c.cell_type, content=c.get_cell_content()) for c in self.cells]
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
        contents = file.load_contents_finish(result)
        if not contents[0]:
            path = file.peek_path()
            print(f"Unable to open {path}: {contents[1]}")

        decoded = contents[1].decode('utf-8')
        data = json.loads(decoded)

        # TODO check version

        cell_data = data['cells']

        # remove current document and add new document
        for c in [c for c in self.cells]: # Wow this is stupid
            self.cells.remove(c)
        for d in cell_data:
            self.append_cell(d['type'], d['content'])

        #Juggling deletability so that only cell cannot be deleted
        if len([0 for c in self.cells]) == 1:
            for c in self.cells:
                c.set_deletability(False)


        self.run_calculation()


    def export_file(self, file, type = 'md'):

        def get_md(c):
            if c.cell_type == CellType.MATH:
                return '$$\n' + c.get_cell_content() + '\n$$'
            elif c.cell_type == CellType.COMPUTATION:
                return '$$\n' + c.get_cell_content() + ' ' + c.get_result() + '\n$$'
            else:
                return c.get_cell_content()

        lines = [get_md(c) for c in self.cells]
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

