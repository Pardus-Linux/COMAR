#
# Copyright (C) 2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

import copy

from qt import *
from kdeui import *
from kdecore import *

from utility import *
from dialogs import *
import domain

import ldap


class Browser(KListView):
    """Domain browser"""
    
    def __init__(self, parent, window):
        KListView.__init__(self, parent)
        self.addColumn("")
        self.header().hide()
        self.setRootIsDecorated(True)
        self.window = window
        
        self.menu_domain = QPopupMenu(self)
        self.menu_domain.insertItem(getIconSet("folder", KIcon.Small), i18n("&New Directory"), self.slotNewDirectory)
        self.menu_domain.insertSeparator()
        self.menu_domain.insertItem(getIconSet("remove", KIcon.Small), i18n("&Remove"), self.slotRemove)
        self.menu_domain.insertSeparator()
        self.menu_domain.insertItem(getIconSet("configure", KIcon.Small), i18n("&Configure"), self.slotConfigure)
        
        self.menu_directory = QPopupMenu(self)
        self.menu_directory.insertItem(getIconSet("folder", KIcon.Small), i18n("&New Directory"), self.slotNewDirectory)
        self.menu_directory.insertSeparator()
        self.menu_directory.insertItem(getIconSet("remove", KIcon.Small), i18n("&Remove"), self.slotRemoveDirectory)
        self.menu_directory.insertSeparator()
        self.menu_directory.insertItem(getIconSet("reload", KIcon.Small), i18n("&Refresh"), self.slotRefresh)
        self.menu_directory.insertSeparator()
        self.menu_directory.insertItem(getIconSet("configure", KIcon.Small), i18n("&Properties"), self.slotDirectoryProperties)
        
        self.connect(self, SIGNAL("contextMenuRequested(QListViewItem*, const QPoint &, int)"), self.slotPopup)
        self.connect(self, SIGNAL("expanded(QListViewItem*)"), self.slotExpand)
        self.connect(self, SIGNAL("collapsed(QListViewItem*)"), self.slotCollapse)
        self.connect(self, SIGNAL("selectionChanged()"), self.slotNodeChanged)
        
        self.initDomains()
    
    def initDomains(self):
        dc = self.window.dc
        for connection in dc.connections:
            label = connection.label
            dn = connection.base_dn
            BrowserItem(self, self.window, dn, None, connection)
    
    def slotPopup(self, item, point, button):
        if item:
            if isinstance(item.parent(), BrowserItem):
                self.menu_directory.exec_loop(point)
            else:
                self.menu_domain.exec_loop(point)
    
    def slotConfigure(self):
        item = self.selectedItem()
        dd = DomainDialog(self, item.connection)
        if dd.exec_loop():
            try:
                item.reloadObject()
            except ldap.LDAPError:
                item.disableDomain()
            if item.connection.isModified():
                dc = self.window.dc
    
    def slotDirectoryProperties(self):
        item = self.selectedItem()
        connection = item.connection
        model_old = copy.deepcopy(item.model)
        od = ObjectDialog(self.window, item.dn, item.model)
        if od.exec_loop():
            model_new = od.model
            try:
                connection.modify(od.dn, model_old.toEntry(exclude=["name"]), model_new.toEntry(exclude=["name"]))
            except ldap.LDAPError, e:
                if e.__class__ in domain.LDAPCritical:
                    item.disableDomain()
                else:
                    self.window.showError(e.args[0]["info"])
            else:
                item.parent().collapseNodes()
                item.parent().expandNodes()
    
    def slotNewDirectory(self):
        item = self.selectedItem()
        connection = item.connection
        od = ObjectDialog(self.window, item.dn, domain.DirectoryModel())
        if od.exec_loop():
            try:
                connection.add(od.dn, od.model.toEntry())
            except ldap.LDAPError, e:
                if e.__class__ in domain.LDAPCritical:
                    item.disableDomain()
                else:
                    self.window.showError(e.args[0]["info"])
            else:
                if item.isOpen():
                    item.collapseNodes()
                item.expandNodes()
    
    def slotRemoveDirectory(self):
        item = self.selectedItem()
        confirm = self.window.doubleConfirm(i18n("Remove directory?"), i18n("Are you sure you want to remove '%1' ?").arg(item.text(0)), i18n("This is not undoable. Are you sure you want to continue?"))
        if confirm:
            try:
                item.connection.delete(item.dn)
            except ldap.LDAPError, e:
                if e.__class__ in domain.LDAPCritical:
                    item.disableDomain()
                else:
                    self.window.showError(e.args[0]["info"])
            else:
                item.parent().collapseNodes()
                item.parent().expandNodes()
    
    def slotRemove(self):
        item = self.selectedItem()
        confirm = self.window.confirm(i18n("Remove domain?"), i18n("Are you sure you want to remove '%1' ?").arg(item.text(0)))
        if confirm:
            item.disableDomain()
            dc = self.window.dc
            dc.removeConnection(item.connection)
            self.takeItem(item)
    
    def slotRefresh(self):
        self.showObjects()
    
    def slotExpand(self, item):
        item.expandNodes()
    
    def slotCollapse(self, item):
        item.collapseNodes()
    
    def slotNodeChanged(self):
        self.showObjects()
    
    def showObjects(self):
        object_len = 0
        show_tab = None
        
        objects = [
            (self.window.computers, "pardusComputer", domain.ComputerModel, domain.ComputerPolicyModel, "krdc", i18n("Computers (%1)")),
            (self.window.units, "organizationalUnit", domain.UnitModel, domain.UnitPolicyModel, "server", i18n("Units (%1)")),
            (self.window.users, "posixAccount", domain.UserModel, None, "user", i18n("Users (%1)")),
            (self.window.groups, "posixGroup", domain.GroupModel, None, "kontact_contacts", i18n("Groups (%1)")),
        ]
        
        for objectWidget, objectClass, objectModel, objectPolicy, icon, label in objects:
            objectWidget.clear()
            item = self.selectedItem()
            if item and isinstance(item.parent(), BrowserItem):
                try:
                    result = item.connection.search(item.dn, ldap.SCOPE_ONELEVEL, "objectClass=%s" % objectClass)
                except ldap.LDAPError, e:
                    if e.__class__ in domain.LDAPCritical:
                        self.disableDomain()
                    else:
                        self.window.showError(e.args[0]["info"])
                else:
                    for dn, attrs in result:
                        model = objectModel(attrs)
                        policy = None
                        if objectPolicy:
                            policy = objectPolicy(attrs)
                        ObjectListItem(objectWidget, self.window, dn, model, policy, icon)
                    self.window.tab.setTabLabel(objectWidget, label.arg(len(result)))
                if len(result) > object_len:
                    show_tab = objectWidget
                    object_len = len(result)
        
        self.window.tab.showPage(show_tab)


class BrowserItem(QListViewItem):
    """Domain tree element.
       Requires a parent node object, window object and DN for the node.
       Non-root nodes require a label, root nodes require a connection object."""
    
    def __init__(self, parent, window, dn, model, connection=None):
        self.window = window
        self.dn = dn
        self.model = model
        if connection:
            self.connection = connection
        else:
            self.connection = parent.connection
        self.label = ""
        if self.model:
            self.label = unicode(model.fields["label"])
        QListViewItem.__init__(self, parent, self.label)
        self.setExpandable(True)
        self.initObject()
    
    def initObject(self):
        """Initialize domain object. Gets label from domain server, if it's a root node."""
        if isinstance(self.parent(), BrowserItem):
            self.setState("node_close")
        else:
            try:
                self.connection.bind()
            except ldap.LDAPError, e:
                self.disableDomain()
                return
            try:
                results = self.connection.search(self.dn, ldap.SCOPE_BASE, "objectClass=organization")
                dn, attrs = results[0]
                label = unicode(attrs["o"][0])
                self.setText(0, label)
            except ldap.LDAPError, e:
                if e.__class__ in domain.LDAPCritical:
                    self.disableDomain()
                else:
                    self.window.showError(e.args[0]["info"])
            else:
                self.setState("active")
    
    def reloadObject(self):
        """Reset connection and initialize domain object again."""
        self.connection.unbind()
        self.connection.bind()
        self.initObject()
    
    def getRootNode(self):
        """Find root node."""
        item = self
        while True:
            if not isinstance(item.parent(), BrowserItem):
                return item
            item = item.parent()
    
    def disableDomain(self):
        """Disable domain tree. Used when connection errors occur."""
        self.connection.unbind()
        root = self.getRootNode()
        root.setState("error")
        root.clearNodes()
        root.setOpen(False)
    
    def setState(self, state):
        """Set state of a node. (root: [active, error], others: [node_open, node_close]"""
        self.state = state
        if state == "active":
            self.setPixmap(0, getIcon("connect_established.png", KIcon.Small))
        #elif state == "passive":
        #    self.setPixmap(0, getIcon("connect_creating.png", KIcon.Small))
        elif state == "error":
            self.setPixmap(0, getIcon("connect_no.png", KIcon.Small))
        elif state == "node_open":
            self.setPixmap(0, getIcon("folder_open.png", KIcon.Small))
        elif state == "node_close":
            self.setPixmap(0, getIcon("folder.png", KIcon.Small))
    
    def getChildren(self):
        """Give sub-organizations. Returns False on error"""
        try:
            return self.connection.search(self.dn, ldap.SCOPE_ONELEVEL, "objectClass=organization")
        except ldap.LDAPError, e:
            desc = e.args[0]["info"]
            if not self.firstChild():
                self.setOpen(False)
            if e.__class__ in domain.LDAPCritical:
                self.disableDomain()
            else:
                self.window.showError(e.args[0]["info"])
            return False
    
    def expandNodes(self):
        if isinstance(self.parent(), BrowserItem):
            self.setState("node_open")
            self.setOpen(True)
        else:
            try:
                self.reloadObject()
            except ldap.LDAPError, e:
                if not self.firstChild():
                    self.setOpen(False)
                if e.__class__ in domain.LDAPCritical:
                    self.disableDomain()
                else:
                    self.window.showError(e.args[0]["info"])
                return
        
        organizations = self.getChildren()
        if organizations == False:
            if not self.firstChild():
                self.setOpen(False)
        else:
            self.clearNodes()
            for organization in organizations:
                dn, attrs = organization
                model = domain.DirectoryModel(attrs)
                BrowserItem(self, self.window, dn, model)
            
            if not len(organizations):
                self.setOpen(False)
    
    def clearNodes(self):
        kid = self.firstChild()
        while kid:
            tmp = kid.nextSibling()
            self.takeItem(kid)
            kid = tmp
    
    def collapseNodes(self):
        if isinstance(self.parent(), BrowserItem):
            self.setState("node_close")


class ObjectList(KListView):
    def __init__(self, parent, window, object_type):
        KListView.__init__(self, parent)
        self.addColumn(i18n("Name"))
        self.addColumn(i18n("Description"))
        #self.header().hide()
        self.setResizeMode(KListView.LastColumn)
        self.setRootIsDecorated(False)
        self.setSelectionMode(QListView.Extended)
        self.window = window
        self.type = object_type
        
        self.menu_item = QPopupMenu(self)
        self.id_menu = [
            self.menu_item.insertItem(getIconSet("filenew", KIcon.Small), i18n("&New"), self.slotNewItem),
            self.menu_item.insertSeparator(),
            self.menu_item.insertItem(getIconSet("remove", KIcon.Small), i18n("&Remove"), self.slotRemove),
            self.menu_item.insertSeparator(),
            self.menu_item.insertItem(getIconSet("services", KIcon.Small), i18n("&Policy"), self.slotPolicy),
            self.menu_item.insertItem(getIconSet("configure", KIcon.Small), i18n("&Configuration"), self.slotProperties),
        ]
        
        self.connect(self, SIGNAL("contextMenuRequested(QListViewItem*, const QPoint&, int)"), self.slotPopup)
    
    def slotPopup(self, item, point, col):
        browser = self.window.browser
        selected = browser.selectedItem()
        if not selected or not isinstance(selected.parent(), BrowserItem):
            return
        for i in self.id_menu:
            self.menu_item.setItemVisible(i, True)
        items = self.selectedItems()
        if len(items):
            if len(items) > 1 and not items[0].model.allow_multiple_edit:
                for i in self.id_menu[3:]:
                    self.menu_item.setItemVisible(i, False)
        else:
            for i in self.id_menu[1:]:
                self.menu_item.setItemVisible(i, False)
        if not items[0].policy:
            for i in self.id_menu[4:5]:
                self.menu_item.setItemVisible(i, False)
        self.menu_item.exec_loop(point)
    
    def slotNewItem(self):
        browser = self.window.browser
        item = browser.selectedItem()
        connection = item.connection
        dn = item.dn
        if self.type == "computer":
            model = domain.ComputerModel()
        elif self.type == "unit":
            model = domain.UnitModel()
        elif self.type == "user":
            model = domain.UserModel()
        elif self.type == "group":
            model = domain.GroupModel()
        od = ObjectDialog(self.window, dn, model)
        if od.exec_loop():
            try:
                connection.add(od.dn, od.model.toEntry(append=True))
            except ldap.LDAPError, e:
                if e.__class__ in domain.LDAPCritical:
                    item.disableDomain()
                else:
                    self.window.showError(e.args[0]["info"])
            else:
                browser.showObjects()
    
    def slotProperties(self):
        browser = self.window.browser
        connection = browser.selectedItem().connection
        items = self.selectedItems()
        item = items[0]
        if len(items) > 1 and item.model.allow_multiple_edit:
            multiple = True
            od = ObjectDialog(self.window, item.dn, item.model.__class__(), multiple=True)
        else:
            multiple = False
            model_old = copy.deepcopy(item.model)
            od = ObjectDialog(self.window, item.dn, item.model)
        if od.exec_loop():
            model_new = od.model
            try:
                # Modify attributes
                if multiple:
                    for item in items:
                        connection.modify(item.dn, item.model.toEntry(exclude=["name"]), model_new.toEntry(exclude=["name"], append=True))
                else:
                    connection.modify(od.dn, model_old.toEntry(exclude=["name"]), model_new.toEntry(exclude=["name"], append=True))
                    # Rename
                    if model_new.fields["name"] != model_old.fields["name"]:
                        new_name = od.objectName()
                        connection.rename(item.dn, new_name)
            except ldap.LDAPError, e:
                if e.__class__ in domain.LDAPCritical:
                    item.disableDomain()
                else:
                    self.window.showError(e.args[0]["info"])
            else:
                browser.showObjects()
    
    def slotPolicy(self):
        browser = self.window.browser
        connection = browser.selectedItem().connection
        items = self.selectedItems()
        item = items[0]
        if not item.policy:
            return
        if len(items) > 1 and item.policy.allow_multiple_edit:
            multiple = True
            od = ObjectDialog(self.window, item.dn, item.policy.__class__(), multiple=True)
        else:
            multiple = False
            model_old = copy.deepcopy(item.policy)
            od = ObjectDialog(self.window, item.dn, item.policy)
        if od.exec_loop():
            model_new = od.model
            try:
                if multiple:
                    for item in items:
                        connection.modify(item.dn, item.policy.toEntry(exclude=["name"]), model_new.toEntry(exclude=["name"], append=True))
                else:
                    connection.modify(od.dn, model_old.toEntry(exclude=["name"]), model_new.toEntry(exclude=["name"], append=True))
            except ldap.LDAPError, e:
                if e.__class__ in domain.LDAPCritical:
                    item.disableDomain()
                else:
                    self.window.showError(e.args[0]["info"])
    
    def slotRemove(self):
        browser = self.window.browser
        items = self.selectedItems()
        if len(items) == 1:
            label = items[0].text(0)
            confirm = self.window.doubleConfirm(i18n("Remove object?"), i18n("Are you sure you want to remove '%1' ?").arg(label), i18n("This is not undoable. Are you sure you want to continue?"))
        elif len(items) < 10:
            labels = [" - %s" % item.text(0) for item in items]
            labels = "\n".join(labels)
            confirm = self.window.doubleConfirm(i18n("Remove objects?"), i18n("Are you sure you want to remove these objects?\n%1").arg(labels), i18n("This is not undoable. Are you sure you want to continue?"))
        else:
            count = len(items)
            confirm = self.window.doubleConfirm(i18n("Remove objects?"), i18n("Are you sure you want to remove %1 objects?").arg(count), i18n("This is not undoable. Are you sure you want to continue?"))
        if confirm:
            connection = browser.selectedItem().connection
            failed = []
            for item in items:
                try:
                    connection.delete(item.dn)
                except ldap.LDAPError, e:
                    if e.__class__ in domain.LDAPCritical:
                        item.disableDomain()
                        return
                    else:
                        failed.append((item, e.args[0]["info"]))
            if len(failed):
                failed = [" - %s (%s)" % (item.label, message) for item, message in failed]
                failed = "\n".join(failed)
                self.window.showWarning(i18n("Unable to delete these objects:\n%1").arg(failed))
            else:
                count = len(items)
                self.window.showInfo(i18n("Removed %1 objects.").arg(count))
                browser.showObjects()


class ObjectListItem(KListViewItem):
    def __init__(self, parent, window, dn, model, policy, icon):
        self.window = window
        self.dn = dn
        self.model = model
        self.policy = policy
        if "label" in model.fields:
            label = unicode(model.fields["label"])
        else:
            label = model.fields["name"]
        if "description" in model.fields:
            description = unicode(model.fields["description"])
        else:
            description = ""
        KListViewItem.__init__(self, parent, label)
        self.setPixmap(0, getIcon(icon, KIcon.Small))
        self.setText(0, label)
        self.setText(1, description)
