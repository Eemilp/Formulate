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
from gi.repository import Gio, GObject
from .document import Document

@Gtk.Template(resource_path='/com/github/eemilp/Formulate/window.ui')
class FormulateWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'FormulateWindow'


    header_bar = Gtk.Template.Child("header_bar")
    main_view = Gtk.Template.Child("main_view")

    tabs = Gtk.Template.Child("tabs")
    pages_to_close = None

    # TODO on quit #0.2.0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.connect("close-request", self.close_all)

        quit_action = Gio.SimpleAction(name="quit")
        quit_action.connect("activate", self.close_all)
        self.add_action(quit_action)

        self.tabs.connect("close-page", self.close_tab)

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

    def close_tab(self, tabview, page, next_tabs = None):
        document = page.get_child()
        if document.edited is True:
            dialog = self.close_message_dialog(document.title())
            dialog.choose(self, None, self.close_dialog_response, tabview, page)
        else:
            tabview.close_page_finish(page, True)

            self.close_next_page()
        return True # This is important

    def close_dialog_response(self, dialog, result, tabview, page):
        response = dialog.choose_finish(result)
        if response == "close" or response == "cancel":
            tabview.close_page_finish(page, False)
            self.pages_to_close = None
        if response == "save":
            document = page.get_child()
            self.save(None, document)
            document.connect("file_saved", self.save_before_close_complete, page)
        if response == "discard":
            tabview.close_page_finish(page, True)

            self.close_next_page()

    def save_before_close_complete(self, widget, page):
        self.tabs.close_page_finish(page, True)
        self.close_next_page()

    def close_next_page(self):
        if self.pages_to_close is not None:
            if not self.pages_to_close:
                self.close_all_finish(True)
            else:
                next_page = self.pages_to_close.pop()
                self.tabs.close_page(next_page)


    def close_message_dialog(self, document_name):
        dialog = Adw.AlertDialog.new("Save your work?", document_name + " is not saved")
        dialog.add_response("cancel", "_Cancel")
        dialog.add_response("discard", "_Discard")
        dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.add_response("save", "_Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("cancel")
        return dialog

    def close_all(self, _window = None, _= None):
        pages = [p for p in self.tabs.get_pages()]
        page = pages.pop()
        self.pages_to_close = pages
        self.tabs.close_page(page)
        return True


    def close_all_finish(self, close):
        if close is True:
            self.destroy()


    # Saving, opening, exporting
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
            if document.empty() is True or document.edited is False:
                document.open_file(file)
            else:
                self.add_tab(None, file)

    def save(self, action, document = None):
        if document is None:
            document = self.get_open_document()
        if document.file is None:
            self.save_file_dialog(action, document)
        else:
            # just save the file
            document.save_file(document.file)

    def save_file_dialog(self, action, document = None):
        filter = Gtk.FileFilter()
        filter.add_suffix('fnb')
        native = Gtk.FileDialog()
        native.set_default_filter(filter)
        native.set_initial_name('Document.fnb')
        native.save(self, None, self.on_save_response, document)

    def on_save_response(self, dialog, result, document = None):
        if document is None:
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

