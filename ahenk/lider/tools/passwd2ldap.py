#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

import ldap
import ldap.modlist

SUCCESS, FAIL = xrange(2)


def tidy_modlist(_attrs):
    attrs = {}
    for key, values in _attrs.iteritems():
        if values != [""]:
            attrs[key] = values
    return attrs


def main():
    if os.getuid() != 0:
        print "Must be run as root."
        return SUCCESS
    
    try:
        ldap_server = raw_input("Server: ")
        ldap_user = raw_input("User: ")
        ldap_password = raw_input("Password: ")
        ldap_base_users = raw_input("Users DN: ")
        ldap_base_groups = raw_input("Groups DN: ")
    except KeyboardInterrupt:
        print
        print "Cancelled"
        return FAIL
    
    try:
        conn = ldap.open(ldap_server)
        conn.simple_bind_s(ldap_user, ldap_password)
    except ldap.LDAPError, e:
        print e.args[0]["desc"]
        return FAIL
    
    failed_users = []
    failed_groups = []
    
    print "Importing groups..."
    for line in file("/etc/group"):
        line = line.strip()
        groupname, label, gid, users = line.split(":")
        dn = "cn=%s,%s" % (groupname, ldap_base_groups)
        attrs = {
            "objectClass": ["top", "posixGroup"],
            "gidNumber": [gid],
            "cn": [groupname],
            "memberUid": users.split(","),
        }
        attrs = tidy_modlist(attrs)
        try:
            conn.add_s(dn, ldap.modlist.addModlist(attrs))
        except ldap.LDAPError, e:
            print "[ER] %s (%s)" % (attrs["cn"][0], e.args[0]["desc"])
            failed_groups.append(groupname)
        else:
            print "[OK] %s" % attrs["cn"][0]
    
    if failed_groups:
        print
        print "These groups could not be imported:"
        print "  " + "\n  ".join(failed_groups)
    else:
        print "All groups imported to LDAP"
    
    print
    
    users = {}
    for line in file("/etc/passwd"):
        line = line.strip()
        username, password, uid, gid, realname, home, shell = line.split(":")
        dn = "uid=%s,%s" % (username, ldap_base_users)
        users[dn] = {
            "objectClass": ["top", "account", "posixAccount"],
            "uidNumber": [uid],
            "gidNumber": [gid],
            "uid": [username],
            "loginShell": [shell],
            "homeDirectory": [home],
            "cn": [realname],
            "userPassword": [],
        }
    
    for line in file("/etc/shadow"):
        line = line.strip()
        username, password, other = line.split(":", 2)
        dn = "uid=%s,%s" % (username, ldap_base_users)
        if dn in users:
            users[dn]["userPassword"] = [password]
    
    print "Importing users..."
    for dn, attrs in users.iteritems():
        attrs = tidy_modlist(attrs)
        try:
            conn.add_s(dn, ldap.modlist.addModlist(attrs))
        except ldap.LDAPError, e:
            print "[ER] %s (%s)" % (attrs["uid"][0], e.args[0]["desc"])
            failed_users.append(username)
        else:
            print "[OK] %s" % attrs["uid"][0]
    
    if failed_users:
        print
        print "These users could not be imported:"
        print "  " + "\n  ".join(failed_users)
    else:
        print "All users imported to LDAP"
    
    return SUCCESS


if __name__ == "__main__":
    sys.exit(main())
