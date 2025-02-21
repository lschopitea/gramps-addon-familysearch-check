#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2025 Lou Sanchez-Chopitea
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
if __name__ == "__main__":
    from gramps.gen.plug._pluginreg import *
    from gramps.gen.const import GRAMPS_LOCALE as glocale
    _ = glocale.translation.gettext

"""
GRAMPS registration file
"""

register(TOOL,
         id='family_search_check',
         name=_("FamilySearch Check tool"),
         description=_("Checks tree against FamilySearch."),
         version='0.0.1',
         gramps_target_version="6.0",
         status=EXPERIMENTAL,
         fname='familysearchcheck.py',
         authors=["Lou Sanchez-Chopitea"],
         authors_email=["lou.sanchezchopitea@gmail.com"],
         category=TOOL_DBPROC,
         toolclass='FamilySearchCheck',
         optionclass='FamilySearchCheckOptions',
         # tool_modes=[TOOL_MODE_GUI],
         help_url="https://github.com/lschopitea/gramps-addon-familysearch-check/tree/main/FamilySearchCheck",
         )
