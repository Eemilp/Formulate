# converter.py
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

from .data import GREEK_LETTERS

def create_tex_source(md_source):
    # The main reason why this is necessary is that the formula editor uses
    # unicode symbols internally. These get converted into the latex repr
    # + other necessary things
    for textual, unicode_char in GREEK_LETTERS.items():
        tex_repr = '\\' + textual + ' '
        md_source = md_source.replace(unicode_char, tex_repr)

    # replacements on qalc outputs
    # TODO replace sub and superscripts
    md_source = md_source.replace('·', '\\cdot ')
    md_source = md_source.replace('−', '-')
    md_source = md_source.replace('→', '\\rightarrow')

    preample = '''% Generated by Formulate
\\documentclass{article}
\\usepackage{amsmath}
\\begin{document}
'''
    return preample + md_source + '\n\\end{document}'
