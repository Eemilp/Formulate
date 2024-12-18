# textbox.py
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
from gi.repository import Gtk, Gdk

@Gtk.Template(resource_path='/com/github/eemilp/Formulate/textbox.ui')
class TextBox(Adw.Bin):
    __gtype_name__ = 'TextBox'

    textview = Gtk.Template.Child("textview")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        controller = Gtk.EventControllerKey.new()
        controller.connect("key-pressed", self.on_keypress)
        self.textview.add_controller(controller)

    def on_keypress(self, controller, keyval, keycode, modifiers):
        if modifiers & (Gdk.ModifierType.SHIFT_MASK | Gdk.ModifierType.CONTROL_MASK):
            if keyval == Gdk.KEY_Return:
                #TODO this is ugly although it works
                controller.forward(self.get_parent().get_parent().get_parent())
                return True
        return False

