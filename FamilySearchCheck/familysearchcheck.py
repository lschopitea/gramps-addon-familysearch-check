
"""FamilySearch Check Tool"""
import os
import pdb
from typing import List, Optional, AnyStr, NoReturn
# from queue import Queue
import logging
import re
# from unicodedata import category

# from gi.repository import Gtk

import gramps.gen.lib
from gramps.gen.plug.menu import BooleanListOption
from gramps.gen.const import GRAMPS_LOCALE as glocale
from gramps.gui.plug import tool, MenuToolOptions
#from gramps.gen.plug.menu import FilterOption, StringOption, BooleanOption
from gramps.gen.plug.menu import StringOption
from gramps.gui.managedwindow import ManagedWindow
# from gramps.gen.simple import SimpleAccess

from genealogy_familysearch import (FamilySearchPopulator, Missing,
    FamilySearchPerson)
from genealogy_gramps import GrampsPopulator, GrampsPerson
# from po.update_po import merge

LOG = logging.getLogger("FSCheck")
LOG.setLevel(logging.DEBUG)
_ = glocale.translation.sgettext


class WorkItem:
    """Work Item to process"""
    def __init__(self, gid: AnyStr, fsid: AnyStr, gen: int = 0):
        """Initializer"""
        self._gid: str = gid
        self._fsid: str = fsid
        self._gen: int = gen

    @property
    def gid(self) -> str:
        """Gramps ID"""
        return self._gid

    @property
    def fsid(self) -> str:
        """FamilySearch ID"""
        return self._fsid

    @property
    def gen(self) -> int:
        """Generation of the work item"""
        return self._gen


# class FamilySearchCheck(tool.Tool, ManagedWindow):
class FamilySearchCheck(tool.Tool, ManagedWindow):
    """Check a tree against FamilySearch"""
    # pylint: disable=unused-argument
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, dbstate, user, options_class, name, callback=None):
        LOG.debug("FamilySearchCheck init")
        # self.window = None
        # uistate = user.uistate
        # This inheritance provides the db property
        # This will instantiate options_class and set self.options to the
        # result
        tool.Tool.__init__(self, dbstate, options_class, name)
        # tool.BatchTool.__init__(self, dbstate, user, options_class, name)

        # self.window_name = _('FamilySearch Check Tool')
        # ManagedWindow.__init__(self, user.uistate, [], self.__class__)
        # self.set_window(Gtk.Window(), Gtk.Label(), self.window_name)

        # We need a stack
        self._todo: List = []
        #self._inque: Set = set()
        self._gens: int = 0
        # We are only ever dealing with a single database
        # self._sdb = dbstate
        LOG.debug("Database: %s", self.db)

        # The populators
        self._gpop = None
        self._fspop = None
        # self.show()

        # self.run()
        LOG.debug("FamilySearchCheck init done")

    def find_block(self, idformat: str, start: int, length: int) -> int:
        """Find a block of unused IDs"""
        id: int = start
        block: int = start
        while id - block < length:
            gid: str = idformat % id
            pers = self.db.get_person_from_gramps_id(gid)
            id += 1
            if pers:
                # Reset
                block = id
        return block

    # def init(self):
    #     """Initialize the Tool"""
    #     self.set_text("FamilySearchCheck")

    # @property
    # def sdb(self):
    #     """The database"""
    #     return self._sdb
    #
    # @sdb.setter
    # def sdb(self, value):
    #     """Set the database"""
    #     self._sdb = value

    @property
    def todo(self) -> List:
        """Work remaining"""
        return self._todo

    @property
    def generations(self) -> int:
        """Generations to check"""
        return self._gens

    @generations.setter
    def generations(self, value: int) -> NoReturn:
        self._gens = value

    #@property
    #def inqueue(self) -> Set:
    #    return self._inque

    def add(self, gid, fsid, gen) -> None:
        """Add a work item to the queue"""
        # Put into the queue
        LOG.debug("Adding work item (%s, %s) to queue", gid, fsid)
        self.todo.append(WorkItem(gid, fsid, gen=gen))
        # And the ID into the set
        # gid = self.sdb.gid(primary)
        # self.inqueue.add(gid)

    @staticmethod
    def date(event) -> str:
        date = None
        if event is not Missing and event.date is not Missing:
            date = str(event.date)
        else:
            date = "Missing"
        return date

    def process(self):
        """Process a single work item"""
        # Pull an item off the work queue
        item: WorkItem = self.todo.pop()
        LOG.debug("Generation: %d", item.gen)

        # We check every data item that we have access to
        fsid: str = item.fsid
        gid: str = item.gid

        fspers = self._fspop.person(fsid=fsid)
        gpers = self._gpop.person(gid=gid)

        cmp = fspers % gpers
        LOG.debug("Person comparison: %s", cmp)

        fsmthr: FamilySearchPerson = fspers.mother
        gmthr: GrampsPerson = gpers.mother
        create = "YES"
        if not fsmthr and not gmthr:
            LOG.info("No mother information")
        elif not fsmthr:
            LOG.info("Mother \"%s\" not in FamilySearch",
                     gmthr.name.value if gmthr.name else "Missing")
        elif not gmthr:
            LOG.info("Mother \"%s\" not in Gramps", fsmthr.name.value)
            # We want to confirm Person creation
            if create == "YES":
                # We have the data we want in the FamilySearch mother
                # Give the ID as blank so a new person is added to the
                # database
                gmthr = self._gpop.person(gid="", other=fsmthr)
                # We add the internet path that connects the Gramps Person with
                # the FamilySearch ID
                gmthr.add_url(fsmthr.id_url())
                # And we add the new Person as the mother
                gpers.mother = gmthr
                LOG.debug("Mother: (%s, %s)", gmthr.id, fsmthr.id)
                if item.gen + 1 > self.generations:
                    LOG.debug("Generation limit reached for mother")
                else:
                    self.add(str(gmthr.id), str(fsmthr.id), item.gen + 1)
        else:
            LOG.debug("Mother retrieved")
            LOG.debug("Name: Gramps: %s, FS: %s",
                      gmthr.name.value if gmthr else "Missing",
                      fsmthr.name.value if fsmthr else "Missing")
            LOG.debug("Sex: Gramps: %s, FS: %s", gmthr.sex, fsmthr.sex)
            LOG.debug("Born: Gramps: %s, FS: %s",
                       FamilySearchCheck.date(gmthr.born),
                      FamilySearchCheck.date(fsmthr.born))
            cmp = fsmthr % gmthr
            LOG.debug("Mother comparison: %s", cmp)
            if item.gen + 1 > self.generations:
                LOG.debug("Generation limit reached for mother")
            elif cmp.similarity > .6 and cmp.confidence > .8:
                self.add(str(gmthr.id), str(fsmthr.id), item.gen + 1)
            else:
                LOG.info("Mother records too different, tree abandoned")

        fsfthr: FamilySearchPerson = fspers.father
        gfthr: GrampsPerson = gpers.father
        if not fsfthr and not gfthr:
            LOG.info("No father information")
        elif not fsfthr:
            LOG.info("Father \"%s\" not in FamilySearch", gfthr.name.value)
        elif not gfthr:
            LOG.info("Father \"%s\" not in Gramps", fsfthr.name.value)
            # We want to confirm Person creation
            if create == "YES":
                # We have the data we want in the FamilySearch father
                # Give the ID as blank so a new person is added to the
                # database
                gfthr = self._gpop.person(gid="", other=fsfthr)
                # We add the internet path that connects the Gramps Person with
                # the FamilySearch ID
                gfthr.add_url(fsfthr.id_url())
                # And we add the new Person as the father
                gpers.father = gfthr
                # And make a new work item
                LOG.debug("Father: (%s, %s)", gfthr.id, fsfthr.id)
                if item.gen + 1 > self.generations:
                    LOG.debug("Generation limit reached for father")
                else:
                    self.add(str(gfthr.id), str(fsfthr.id), item.gen + 1)
        else:
            LOG.debug("Father retrieved")
            LOG.debug("Name: Gramps: %s, FS: %s",
                      gfthr.name.value, fsfthr.name.value)
            LOG.debug("Sex: Gramps: %s, FS: %s", gfthr.sex, fsfthr.sex)
            LOG.debug("Born: Gramps: %s, FS: %s",
                      FamilySearchCheck.date(gfthr.born),
                      FamilySearchCheck.date(fsfthr.born))
            cmp = fsfthr % gfthr
            LOG.debug("Father comparison: %s", cmp)
            if item.gen + 1 > self.generations:
                LOG.debug("Generation limit reached for father")
            elif cmp.similarity > .6 and cmp.confidence > .8:
                self.add(str(gfthr.id), str(fsfthr.id), item.gen + 1)
            else:
                LOG.info("Father records too different, tree abandoned")

        # Cleanup
        #self.inqueue.discard(gid)

    # def run(self, database):
    # def run(self):
    def run_tool(self):
        """Check against the FamilySearch database"""
        # How far up the tree to go
        # ascend: int = 4

        # We need to grab the number of generations to process from the options
        #gens = options_class.menu.get_option_by_name('generations')
        self.generations = 2
        LOG.info("Processing %d generations", self.generations)

        # Get the merge option from the options
        pdb.set_trace()
        merge_menu = self.options.menu.get_option_by_name('merge')
        self.merge: List[str] = merge_menu.get_selected()
        LOG.debug("Merge option: %s", self.merge[0])

        # Find the starting point of a block of unused IDs large enough to
        # accommodate the number of potential additions
        idform: str = "I%05d"
        block: int = self.find_block(idform, 10000, pow(2, self.generations + 1))
        LOG.info("Block found at %s", idform % block)

        # Nomenclature:
        #   Person is a GRAMPS entity
        #   Individual is a unique genetic organism
        #   An Individual may be represented by multiple Persons
        # Given a pair of Persons we want to do a recursive merge, i.e. follow
        # the Families and the Persons there to see if there is correspondence.
        # We place any merge candidates in a list and recurse over each
        # Simple access functions
        # self.sdb = SimpleAccess(database)

        # Get the default person
        # Need to get this from the options
        gid = None
        defpers: gramps.gen.lib.Person = self.db.get_default_person()
        if defpers is None:
            LOG.debug("Could not get default person")
            # gid = "I1000"
            gid = "I0000"
            defpers = self.db.get_person_from_gramps_id(gid)
        # gid = defpers.get_handle()
        gid = defpers.gramps_id
        gname: gramps.gen.lib.Name = defpers.primary_name
        LOG.debug("Default person primary name: %s, %s",
                  gname.get_surname(), gname.get_first_name())
        fsid: Optional[AnyStr] = None
        # We would like to find the FamilySearch ID in the URLs
        # The URL can be to the tree or the details
        # https://www.familysearch.org/en/tree/person/<id>
        # https://www.familysearch.org/en/tree/person/details/<id>
        LOG.debug("Default person URLs: %s", defpers.urls)
        if defpers.urls is not None and len(defpers.urls) > 0:
            p = re.compile(r"""https://www\.familysearch\.org/en/tree/person(/details)?/(.+)$""")
            for url in defpers.urls:
                url: AnyStr
                # LOG.debug("URL: %s", url.path)
                m = p.match(url.path)
                if m:
                    LOG.debug("ID match: %s", m.group(2))
                    fsid = m.group(2)

        # If we didn't find it, then we can go to the old style of looking in
        # the citations
        if not fsid:
            LOG.debug("Default person citation list: %s", defpers.citation_list)
        # If still nothing then we needed to have it from the options
        if not fsid:
            LOG.error("FamilySearch ID not supplied and not available in Person")
            return
        # Add the starting point of the processing
        self.add(gid, fsid, gen=0)

        # Set up the populators
        self._gpop = GrampsPopulator(self.db)
        # And add the index block to the Gramps populator
        self._gpop.index.set(block - 1)
        # For FamilySearch access we get the credentials from the environment
        user: str = os.environ['FAMILYSEARCH_USER']
        password: str = os.environ['FAMILYSEARCH_PASS']
        self._fspop = FamilySearchPopulator(user, password)
        # pdb.set_trace()

        # Iterate until all the work items have been processed
        pdb.set_trace()
        while self.todo:
            self.process()
        LOG.debug("Processing done")

    # def merge(self, sdb, primary, secondary):
    #     pass


class FamilySearchCheckOptions(MenuToolOptions):
    """Option class for event description editor."""

    def __init__(self, name, person_id=None, dbstate=None):
        # name is the id from the gpr
        LOG.debug("FamilySearchCheckOptions init")
        # add_menu_options is called here
        MenuToolOptions.__init__(self, name, person_id, dbstate)
        pdb.set_trace()
        LOG.debug("FamilySearchCheckOptions init done")

    def add_menu_options(self, menu):
        """Menu options."""
        LOG.debug("Adding options")
        # menu.filter_list = CustomFilters.get_filters("Event")
        # all_filter = GenericFilterFactory("Event")()
        # all_filter.set_name(_("All Events"))
        # all_filter.add_rule(rules.event.AllEvents([]))
        # all_filter_in_list = False
        # for fltr in menu.filter_list:
        #     if fltr.get_name() == all_filter.get_name():
        #         all_filter_in_list = True
        # if not all_filter_in_list:
        #     menu.filter_list.insert(0, all_filter)
        #
        # events = FilterOption(_("Events"), 0)
        # menu.add_option(_("Option"), "events", events)
        # events.set_filters(menu.filter_list)
        #
        #find = StringOption(_("Find"), "")
        #menu.add_option(_("Option"), "find", find)

        category_name = "Tool Options"
        merge = BooleanListOption("Merge options")
        merge.add_button("Always", False)
        merge.add_button("Confirm", False)
        merge.add_button("Never", True)
        menu.add_option(category_name, "merge", merge)

        # replace = StringOption(_("Replace"), "")
        # menu.add_option(_("Option"), "replace", replace)
        #
        # keep_old = BooleanOption(_("Replace substring only"), False)
        # keep_old.set_help(_("If True only the substring will be replaced, "
        #                     "otherwise the whole description will be deleted "
        #                     "and replaced by the new one."))
        # menu.add_option(_("Option"), "keep_old", keep_old)
        #
        # regex = BooleanOption(_("Allow regex"), False)
        # regex.set_help(_("Allow regular expressions."))
        # menu.add_option(_("Option"), "regex", regex)
        LOG.debug("Adding options done")

# class FamilySearchCheckOptions(tool.ToolOptions):
#     """
#     Defines options and provides handling interface.
#     """
#     def __init__(self, name, person_id=None):
#         LOG.debug("Options init")
#         tool.ToolOptions.__init__(self, name, person_id)
#
#         # Options specific for this report
#         self.options_dict = {
#             'name'   : 2,
#             'password' : 2,
#         }
#         self.options_help = {
#             'name'   : ("=num",
#                            "Name to login to website",
#                            "?string?"),
#             'password' : ("=num",
#                            "Password to log in to website",
#                            "Integer number")
#             }
