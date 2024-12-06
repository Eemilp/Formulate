#qalculator.py
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
from subprocess import run, Popen, PIPE

class Qalculator(object):

    process = None

    def __init__(self,):
        # qalc_terse = lambda e: run(['qalc', '-t', e], capture_output=True).stdout.decode('UTF-8').strip()
        pass

    def qalculate(self, expr):
        #return run(['qalc' ,'-t -f', '<(printf "' + expr, '")'], shell = True, capture_output=True).stdout.decode('UTF-8').strip()
        self.process = Popen(['qalc', '-t', '-f', '-'],
        stdin=PIPE,             # Connect to stdin
        stdout=PIPE,            # Connect to stdout
        #stderr=PIPE,            # Connect to stderr (optional)
        text=True                          # Treat input and output as text strings (Python 3.6+)
        )
        ret, err = self.process.communicate(expr + '\nquit', 1)
        return ret


