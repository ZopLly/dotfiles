/* gtklock 4: display-only Mako messages. No actions, auth hooks or disk history. */
#include <gio/gio.h>
#include "window-v4.h"
guint module_major_version=4,module_minor_version=0;
struct GtkLock;
static GList *notification_labels;
static GDBusProxy *notification_proxy;
static gboolean notification_started;

static gchar *notification_text(GVariant *items) {
    if (!items || !g_variant_is_of_type(items,G_VARIANT_TYPE("aa{sv}"))) return NULL;
    GString *text=g_string_new(NULL);
    gsize count=MIN(g_variant_n_children(items),3);
    for (gsize i=0;i<count;i++) {
        GVariant *card=g_variant_get_child_value(items,i);
        const gchar *app="",*summary="",*body="";
        g_variant_lookup(card,"app-name","&s",&app);
        g_variant_lookup(card,"summary","&s",&summary);
        g_variant_lookup(card,"body","&s",&body);
        if (i) g_string_append(text,"\n\n");
        g_string_append_printf(text,"%s\n%s\n%s",app,summary,body);
        g_variant_unref(card);
    }
    if (!count) { g_string_free(text,TRUE);return NULL; }
    return g_string_free(text,FALSE);
}
static void notification_render(void) {
    gchar *owner=notification_proxy?g_dbus_proxy_get_name_owner(notification_proxy):NULL;
    GVariant *value=owner?g_dbus_proxy_get_cached_property(notification_proxy,"Notifications"):NULL;
    gchar *text=notification_text(value);
    for (GList *item=notification_labels;item;item=item->next) {
        gtk_label_set_text(GTK_LABEL(item->data),text?text:"");
        gtk_widget_set_visible(item->data,text!=NULL);
    }
    g_free(owner);g_free(text);if(value)g_variant_unref(value);
}
static void notification_changed(GDBusProxy *proxy,GVariant *changed,const gchar *const *invalid,gpointer data) {
    (void)proxy;(void)changed;(void)invalid;(void)data;notification_render();
}
static void notification_owner(GObject *object,GParamSpec *spec,gpointer data) {
    (void)object;(void)spec;(void)data;notification_render();
}
static void notification_ready(GObject *object,GAsyncResult *result,gpointer data) {
    (void)object;(void)data;GError *error=NULL;
    notification_proxy=g_dbus_proxy_new_for_bus_finish(result,&error);g_clear_error(&error);
    if (notification_proxy) {
        g_signal_connect(notification_proxy,"g-properties-changed",G_CALLBACK(notification_changed),NULL);
        g_signal_connect(notification_proxy,"notify::g-name-owner",G_CALLBACK(notification_owner),NULL);
    }
    notification_render();
}
static GtkWidget *notification_attach(struct Window *window) {
    GtkWidget *label=gtk_label_new(NULL);
    gtk_widget_set_name(label,"lock-notifications");
    gtk_widget_set_no_show_all(label,TRUE);gtk_widget_set_can_focus(label,FALSE);
    gtk_label_set_line_wrap(GTK_LABEL(label),TRUE);gtk_label_set_max_width_chars(GTK_LABEL(label),42);
    gtk_label_set_width_chars(GTK_LABEL(label),36);gtk_label_set_lines(GTK_LABEL(label),12);
    gtk_label_set_ellipsize(GTK_LABEL(label),PANGO_ELLIPSIZE_END);gtk_label_set_xalign(GTK_LABEL(label),0);
    gtk_widget_set_halign(label,GTK_ALIGN_END);gtk_widget_set_valign(label,GTK_ALIGN_END);
    GtkWidget *footer=NULL;
    GList *children=gtk_container_get_children(GTK_CONTAINER(window->window_box));
    for(GList *it=children;it;it=it->next)
        if(g_strcmp0(gtk_widget_get_name(it->data),"lock-footer")==0)footer=it->data;
    g_list_free(children);
    if(footer)gtk_box_pack_end(GTK_BOX(footer),label,FALSE,FALSE,0);
    else {
        gtk_widget_set_margin_bottom(label,48);gtk_widget_set_margin_end(label,48);
        gtk_overlay_add_overlay(GTK_OVERLAY(window->overlay),label);
        gtk_overlay_set_overlay_pass_through(GTK_OVERLAY(window->overlay),label,TRUE);
    }
    notification_labels=g_list_prepend(notification_labels,label);
    g_object_set_data(G_OBJECT(window->window),"notification-label",label);
    return label;
}
void on_window_create(struct GtkLock *lock,struct Window *window) {
    (void)lock;notification_attach(window);
    if (!notification_started) {
        notification_started=TRUE;
        g_dbus_proxy_new_for_bus(G_BUS_TYPE_SESSION,G_DBUS_PROXY_FLAGS_DO_NOT_AUTO_START|G_DBUS_PROXY_FLAGS_GET_INVALIDATED_PROPERTIES,
            NULL,"org.freedesktop.Notifications","/fr/emersion/Mako","fr.emersion.Mako",NULL,notification_ready,NULL);
    }
    notification_render();
}
void on_window_destroy(struct GtkLock *lock,struct Window *window) {
    (void)lock;notification_labels=g_list_remove(notification_labels,g_object_get_data(G_OBJECT(window->window),"notification-label"));
}
