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

static int is_authorized;

static void check_authorization_cb(PolkitAuthority *authority, GAsyncResult *res, GMainLoop *loop)
{
    GError *error;
    PolkitAuthorizationResult *result;

    error = NULL;

    /* A PolKitAuthorizationResult or NULL if error is set. Free with g_object_free() */
    log_info("finish the async auth.\n");
    result = polkit_authority_check_authorization_finish(authority, res, &error);
    if (error != NULL)
    {
        log_error("Error checking authorization: %s\n", error->message);
        g_error_free(error);
    }
    else
        /* Set global result */
        is_authorized = polkit_authorization_result_get_is_authorized(result);

    log_info("quitting loop, is authorized: %d\n", is_authorized);
    /*g_object_free(result);*/
    g_main_loop_quit(loop);
    log_info("callback returns.\n");
}


//! Check if sender is allowed to call method
int
policy_check(const char *sender, const char *action_id, int *result)
{
    /*!
     *
     * @sender Bus name of the sender
     * @result polkit result
     * @return 0 on success, 1 on error
     */

    /* polkit-1 stuff */
    PolkitAuthority *pk_authority;
    PolkitSubject *pk_subject;
    GMainLoop *loop;

    g_type_init();
    /*g_thread_init(NULL);*/

    /*int uid = -1;*/
    is_authorized = 0;

    /* FIXME: Could not find out how to get uid for sender */
    /*uid = dbus_bus_get_unix_user(conn, sender, &err);*/

    /* Always authorized
    if (uid == 0 && (result=1))
        return 0;
    */

    /* Create loop */
    loop = g_main_loop_new(NULL, FALSE);

    /* Get authority */
    log_info("Creating authority.\n");
    pk_authority = polkit_authority_get();

    /* Create PolkitSubject */
    log_info("Creating subject from: %s\n", sender);
    pk_subject = polkit_system_bus_name_new((const gchar*) sender);

    /* Asynchronously check for authorization */
    log_info("async check authorization.\n");
    polkit_authority_check_authorization(pk_authority,
                                         pk_subject,
                                         action_id,
                                         NULL, /* PolkitDetails */
                                         POLKIT_CHECK_AUTHORIZATION_FLAGS_ALLOW_USER_INTERACTION, /* FIXME */
                                         NULL, /* cancellable */
                                         (GAsyncReadyCallback) check_authorization_cb,
                                         loop);

    log_info("running loop.\n");
    g_main_loop_run(loop);
    g_object_unref(pk_authority);
    g_object_unref(pk_subject);
    g_main_loop_unref(loop);

    /* Set result */
    *result = is_authorized;
    log_info("returning 0 with result: %d\n", *result);

    return 0;
}
