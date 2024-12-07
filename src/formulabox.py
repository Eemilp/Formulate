# formulabox.py
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
# GNU General Public License for more details./home/eemil/Projects/qalcpad/src/window.py
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>./home/eemil/Projects/qalcpad/src/window.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw
from gi.repository import Gtk
from .formula import Editor
# for parsing latex into an expression
import lark.exceptions
from . import parser

@Gtk.Template(resource_path='/com/github/eemilp/Formulate/formulabox.ui')
class FormulaBox(Gtk.Box):
    __gtype_name__ = 'FormulaBox'

    viewport = Gtk.Template.Child("editor_viewport")
    editor_label = Gtk.Template.Child("editor_text")

    def __init__(self, latex_expr = None, **kwargs):
        super().__init__(**kwargs)
        # print(type(self.viewport))
        # print(type(self.editor_label))
        elements = None
        if latex_expr != None:
            try:
                elements = parser.from_latex(latex_expr)
            except lark.exceptions.LarkError:
                return

        editor = Editor(elements)
        self.viewport.set_child(editor)
        # editor.connect("calculate", self.on_formula_updated, editor)

    def get_expression(self):
        return self.viewport.get_child().expr.to_str()

    def update_label(self, next_label):
        # if there is an = sign, use an arrow for more beautiful notation
        if('=' in self.viewport.get_child().expr.to_str()):
            formatted_label = "<span font='Latin Modern Math 20'>→ " + next_label + "</span>"
            self.editor_label.set_label(formatted_label)
        else:
            formatted_label = "<span font='Latin Modern Math 20'>= " + next_label + "</span>"
            self.editor_label.set_label(formatted_label)

    def get_label(self):
        return self.editor_label.get_label()[34:][:-7]
