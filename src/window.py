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
    main_view = Gtk.Template.Child("main_view")

    tabs = Gtk.Template.Child("tabs")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Saving and loading actions
        open_action = Gio.SimpleAction(name="open")
        open_action.connect("activate", self.open_file_dialog)
        self.add_action(open_action)

        save_action = Gio.SimpleAction(name="save")
        save_action.connect("activate", self.save)
        self.add_action(save_action)

        save_as_action = Gio.SimpleAction(name="save-as")
        save_as_action.connect("activate", self.save_file_dialog)
        self.add_action(save_as_action)

        export_action = Gio.SimpleAction(name="export")
        export_action.connect("activate", self.export_dialog)
        self.add_action(export_action)

        new_action = Gio.SimpleAction(name="new")
        new_action.connect("activate", self.add_tab)
        self.add_action(new_action)

        # add initial tab
        self.add_tab()

    def add_tab(self, from_widget = None, from_file = None):
        document = Document()
        document.connect("file_opened", self.update_tab_labels)
        document.connect("file_saved", self.update_tab_labels)
        page = self.tabs.append(document)
        if from_file is not None:
            document.open_file(from_file)
        else:
            page.set_title(document.title())
        self.tabs.set_selected_page(page)

    def update_tab_labels(self, _):
        pages = [p for p in self.tabs.get_pages()]
        for page in pages:
            title = page.get_child().title()
            page.set_title(title)

    def get_open_document(self):
        return self.tabs.get_selected_page().get_child()


    def open_file_dialog(self, action, _):
        filter = Gtk.FileFilter()
        filter.add_suffix('fnb')
        native = Gtk.FileDialog()
        native.set_default_filter(filter)
        native.open(self, None, self.on_open_response)

    def on_open_response(self, dialog, result):
        document = self.get_open_document()
        file = dialog.open_finish(result)
        if file is not None:
            if document.empty() is True:
                document.open_file(file)
            else:
                self.add_tab(None, file)

    def save(self, action, _):
        document = self.get_open_document()
        if document.file is None:
            self.save_file_dialog(action, None)
        else:
            # just save the file
            self.get_open_document().save_file(document.file)

    def save_file_dialog(self, action, _):
        filter = Gtk.FileFilter()
        filter.add_suffix('fnb')
        native = Gtk.FileDialog()
        native.set_default_filter(filter)
        native.set_initial_name('Document.fnb')
        native.save(self, None, self.on_save_response)

    def on_save_response(self, dialog, result):
        document = self.get_open_document()
        file = dialog.save_finish(result)
        if file is not None:
            document.save_file(file)


    def export_dialog(self, action, _):
        native = Gtk.FileDialog()
        native.set_initial_name('Document.tex')
        native.save(self, None, self.on_export_response)

    def on_export_response(self, dialog, result):
        file = dialog.save_finish(result)
        if file is not None:
            self.get_open_document().export_file(file)

