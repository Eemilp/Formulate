# window.py
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
from gi.repository import Gio
from .document import Document

@Gtk.Template(resource_path='/com/github/eemilp/Formulate/window.ui')
class FormulateWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'FormulateWindow'


    header_bar = Gtk.Template.Child("header_bar")
    scrolled_window = Gtk.Template.Child("scrolled_window")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # add a new document
        new_document = Document()
        self.scrolled_window.set_child(new_document)

        # Saving and loading actions
        open_action = Gio.SimpleAction(name="open")
        open_action.connect("activate", self.open_file_dialog)
        self.add_action(open_action)

        save_action = Gio.SimpleAction(name="save-as")
        save_action.connect("activate", self.save_file_dialog)
        self.add_action(save_action)

        export_action = Gio.SimpleAction(name="export")
        export_action.connect("activate", self.export_dialog)
        self.add_action(export_action)


    def open_file_dialog(self, action, _):
        filter = Gtk.FileFilter()
        filter.add_suffix('fnb')
        native = Gtk.FileDialog()
        native.set_default_filter(filter)
        native.open(self, None, self.on_open_response)

    def on_open_response(self, dialog, result):
        file = dialog.open_finish(result)
        if file is not None:
            self.scrolled_window.get_child().get_child().open_file(file)

    def save_file_dialog(self, action, _):
        filter = Gtk.FileFilter()
        filter.add_suffix('fnb')
        native = Gtk.FileDialog()
        native.set_default_filter(filter)
        native.set_initial_name('Document.fnb')
        native.save(self, None, self.on_save_response)

    def on_save_response(self, dialog, result):
        file = dialog.save_finish(result)
        if file is not None:
            self.scrolled_window.get_child().get_child().save_file(file)


    def export_dialog(self, action, _):
        native = Gtk.FileDialog()
        native.save(self, None, self.on_export_response)

    def on_export_response(self, dialog, result):
        file = dialog.save_finish(result)
        if file is not None:
            self.scrolled_window.get_child().get_child().export_file(file)

