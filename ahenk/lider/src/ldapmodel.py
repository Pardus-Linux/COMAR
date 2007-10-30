#
# Copyright (C) 2007, TUBITAK/UEKAE
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. Please read the COPYING file.
#

import ldaputil
import ldapview

i18n = lambda x: x

class ComputerInfoModel(ldaputil.LdapClass):
    name_field = "cn"
    object_label = i18n("Computer")
    entries = (
        ("memory", "pardusMemoryCapacity", int, i18n("Memory"), ldapview.numberWidget, "*", {}),
        ("services", "pardusServices", list, i18n("Services"), ldapview.listWidget, "*", {"items": [i18n("Service")]}),
    )


class ComputerPolicyModel(ldaputil.LdapClass):
    name_field = "cn"
    object_label = i18n("Policy")
    objectClass = ["top", "device", "pardusComputer", "pisiPolicy", "comarUserPolicy", "comarServicePolicy"]
    entries = (
        # pisiPolicy
        ("pisi_mode", "pisiAutoUpdateMode", str, i18n("Update Mode"), ldapview.comboWidget, i18n("PISI"), {"options": [("off", i18n("Off")), ("security", i18n("Security Only")), ("full", i18n("Full"))], "default": "off"}),
        ("pisi_interval", "pisiAutoUpdateInterval", int, i18n("Interval"), ldapview.timerWidget, i18n("PISI"), {}),
        ("pisi_zone", "pisiAutoUpdateZone", str, i18n("Update Between"), ldapview.timeIntervalWidget, i18n("PISI"), {}),
        ("pisi_repos", "pisiRepositories", str, i18n("Repositories"), ldapview.listWidget, i18n("PISI"), {"items": [i18n("Repo Name"), i18n("URL")], "seperator": "|", "items_seperator": ","}),
        ("pisi_wanted", "pisiWantedPackage", list, i18n("Wanted Packages"), ldapview.listWidget, i18n("PISI"), {"items": [i18n("Package")]}),
        ("pisi_unwanted", "pisiUnwantedPackage", list, i18n("Unwanted Packages"), ldapview.listWidget, i18n("PISI"), {"items": [i18n("Package")]}),
        # comarServicePolicy
        ("service_start", "comarServiceStart", list, i18n("Wanted Services"), ldapview.listWidget, i18n("Services"), {"items": [i18n("Service")]}),
        ("service_stop", "comarServiceStop", list, i18n("Unwanted Services"), ldapview.listWidget, i18n("Services"), {"items": [i18n("Service")]}),
        # comarUserPolicy
        ("user_source", "comarUserSourceMode", str, i18n("User Source"), ldapview.comboWidget, i18n("COMAR"), {"options": [("local", i18n("Local")), ("ldap", i18n("LDAP"))], "default": "local"}),
        ("user_scope", "comarUserLdapSearchScope", str, i18n("Search Scope"), ldapview.comboWidget, i18n("COMAR"), {"options": [("base", i18n("Base")), ("onelevel", i18n("One Level")), ("subtree", i18n("Subtree"))], "default": "subtree"}),
        ("user_uri", "comarUserLdapURI", str, i18n("Database URI"), ldapview.textWidget, i18n("COMAR"), {"urlencode": True}),
        ("user_base", "comarUserLdapBase", str, i18n("Base DN"), ldapview.textWidget, i18n("COMAR"), {}),
        ("user_filter", "comarUserLdapFilter", str, i18n("User Filter"), ldapview.textWidget, i18n("COMAR"), {}),
    )


class UnitPolicyModel(ComputerPolicyModel):
    name_field = "ou"
    object_label = i18n("Policy")
    objectClass = ["top", "organizationalUnit", "pisiPolicy", "comarUserPolicy", "comarServicePolicy"]

class DirectoryModel(ldaputil.LdapClass):
    name_field = "dc"
    object_label = i18n("Directory")
    objectClass = ["dcObject", "organization"]
    entries = (
        ("label", "o", str, i18n("Label"), ldapview.textWidget, "*", {"multi": False, "required": True}),
        ("description", "description", str, i18n("Description"), ldapview.textWidget, "*", {}),
    )

class ComputerModel(ldaputil.LdapClass):
    name_field = "cn"
    object_label = i18n("Computer")
    objectClass = ["top", "device", "pardusComputer", "pisiPolicy", "comarUserPolicy", "comarServicePolicy"]
    entries = (
        ("description", "description", str, i18n("Description"), ldapview.textWidget, "*", {}),
        #("password", "userPassword", str, i18n("Password"), ldapview.textWidget, "*", {"password": True}),
        ("unit", "ou", str, i18n("Member of"), ldapview.textWidget, "*", {}),
    )

class UnitModel(ldaputil.LdapClass):
    name_field = "ou"
    object_label = i18n("Unit")
    objectClass = ["top", "organizationalUnit", "pisiPolicy", "comarUserPolicy", "comarServicePolicy"]
    entries = (
        ("description", "description", str, i18n("Description"), ldapview.textWidget, "*", {}),
    )

class UserModel(ldaputil.LdapClass):
    name_field = "uid"
    object_label = i18n("User")
    objectClass = ["top", "account", "posixAccount", "shadowAccount"]
    entries = (
        ("label", "cn", str, i18n("Real Name"), ldapview.textWidget, "*", {"multi": False, "required": True}),
        ("password", "userPassword", str, i18n("Password"), ldapview.textWidget, "*", {"password": True}),
        ("shell", "loginShell", str, i18n("Shell"), ldapview.textWidget, "*", {"required": True}),
        ("home", "homeDirectory", str, i18n("Home"), ldapview.textWidget, "*", {"multi": False, "required": True}),
        ("uid", "uidNumber", int, i18n("User ID"), ldapview.numberWidget, "*", {"multi": False, "required": True}),
        ("gid", "gidNumber", int, i18n("Group ID"), ldapview.numberWidget, "*", {"multi": False, "required": True}),
    )

class GroupModel(ldaputil.LdapClass):
    name_field = "cn"
    object_label = i18n("Group")
    objectClass = ["top", "posixGroup"]
    entries = (
        ("gid", "gidNumber", int, i18n("Group ID"), ldapview.numberWidget, "*", {"multi": False, "required": True}),
        ("members", "memberUid", list, i18n("Members"), ldapview.listWidget, "*", {"items": [i18n("Username")]}),
    )
