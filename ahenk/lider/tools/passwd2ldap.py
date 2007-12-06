#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

import ldap
import ldap.modlist

SUCCESS, FAIL = xrange(2)


def saltedSHA(password):
    import base64
    import sha
    import random
    
    chars = "".join([chr(x) for x in xrange(33, 91)])
    salt = "".join([random.choice(chars) for x in xrange(10)])
    ctx = sha.new(password)
    ctx.update(salt)
    hash = "{SSHA}" + base64.b64encode(ctx.digest() + salt)
    return hash


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
        ldap_server = sys.argv[1]
        ldap_user = sys.argv[2]
        ldap_password = sys.argv[3]
        ldap_base_users = sys.argv[4]
        ldap_base_groups = sys.argv[5]
        ldap_default_pw = sys.argv[6]
    except KeyboardInterrupt:
        print
        print "Cancelled"
        return FAIL
    except (IndexError, ValueError,):
        print "Usage:"
        print "%s serverURI userDN userPW usersDN groupsDN defaultUserPW" % sys.argv[0]
        print
        print "Example:"
        print "%s 127.0.0.1 cn=admin,dc=domain,dc=com qwerty dc=users,dc=domain,dc=com dc=groups,dc=domain,dc=com 1q2w3e4r5t6y" % sys.argv[0]
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
            failed_groups.append(attrs["cn"][0])
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
        if dn in users and users[dn]["uidNumber"][0] >= 1000:
            users[dn]["userPassword"] = [saltedSHA(ldap_default_pw)]
    
    print "Importing users..."
    for dn, attrs in users.iteritems():
        attrs = tidy_modlist(attrs)
        try:
            conn.add_s(dn, ldap.modlist.addModlist(attrs))
        except ldap.LDAPError, e:
            print "[ER] %s (%s)" % (attrs["uid"][0], e.args[0]["desc"])
            failed_users.append(attrs["uid"][0])
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
