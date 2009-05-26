/*
 *
 * Copyright (c) 2005-2009, TUBITAK/UEKAE
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 *
 */

#include "log.h"
#include "policy.h"

//! Check if sender is allowed to call method
int
policy_check(const char *sender, const char *action, PolKitResult *result)
{
    /*!
     *
     * @sender Bus name of the sender
     * @result PK result
     * @return 0 on success, 1 on error
     */

    DBusConnection *conn;
    DBusError err;
    PolKitContext *polkit_ctx;
    PolKitCaller *polkit_clr;
    PolKitAction *polkit_act;
    PolKitError *perr;
    int uid = -1;

    *result = (PolKitResult) POLKIT_RESULT_NO;

    dbus_error_init(&err);

    conn = dbus_bus_get_private(DBUS_BUS_SYSTEM, &err);
    if (dbus_error_is_set(&err)) {
        log_error("Unable to open connection to query PolicyKit: %s\n", err.message);
        dbus_error_free(&err);
        return -1;
    }

    // If UID is 0, don't query PolicyKit
    uid = dbus_bus_get_unix_user(conn, sender, &err);
    if (dbus_error_is_set(&err)) {
        log_error("Unable to get caller UID: %s\n", err.message);
        dbus_error_free(&err);
        return -1;
    }
    if (uid == 0) {
        *result = (PolKitResult) POLKIT_RESULT_YES;
        return 0;
    }

    polkit_ctx = polkit_context_new();
    if (!polkit_context_init(polkit_ctx, &perr)) {
        log_error("Unable to initialize PK context: %s\n", polkit_error_get_error_message(perr));
        polkit_error_free(perr);
        return -1;
    }

    polkit_clr = polkit_caller_new_from_dbus_name(conn, sender, &err);
    if (dbus_error_is_set(&err)) {
        log_error("Unable to get caller info: %s\n", err.message);
        dbus_error_free(&err);
        return -1;
    }

    if (!polkit_action_validate_id(action)) {
        log_error("Unable to query PolicyKit, action is not valid: %s\n", action);
        return -1;
    }

    polkit_act = polkit_action_new();
    polkit_action_set_action_id(polkit_act, action);

    *result = polkit_context_is_caller_authorized(polkit_ctx, polkit_act, polkit_clr, FALSE, &perr);

    return 0;
}
