/* Optional display-only gtklock 4 module. Never reads the password or authenticates. */
#include <gio/gio.h>
#include "window-v4.h"
guint module_major_version = 4, module_minor_version = 0;
struct GtkLock;
typedef struct { GtkWidget *media, *battery; } View;
static GList *views;
static GHashTable *players;
static GDBusProxy *battery;
static GDBusConnection *session;
static gboolean started;

static gchar *track_text(GDBusProxy *proxy) {
    GVariant *status = g_dbus_proxy_get_cached_property(proxy, "PlaybackStatus");
    gboolean playing = status && g_variant_is_of_type(status, G_VARIANT_TYPE_STRING) && g_str_equal(g_variant_get_string(status, NULL), "Playing");
    if (status) g_variant_unref(status);
    if (!playing) return NULL;
    GVariant *metadata = g_dbus_proxy_get_cached_property(proxy, "Metadata");
    if (!metadata) return NULL;
    if (!g_variant_is_of_type(metadata, G_VARIANT_TYPE_VARDICT)) { g_variant_unref(metadata); return NULL; }
    const gchar *title = NULL;
    g_variant_lookup(metadata, "xesam:title", "&s", &title);
    if (!title || !g_utf8_validate(title, -1, NULL)) { g_variant_unref(metadata); return NULL; }
    gchar *clean = g_strdup(title); g_strstrip(clean);
    if (!*clean) { g_free(clean); g_variant_unref(metadata); return NULL; }
    GVariant *artists = g_variant_lookup_value(metadata, "xesam:artist", G_VARIANT_TYPE_STRING_ARRAY);
    gchar *artist = NULL;
    if (artists && g_variant_n_children(artists)) g_variant_get_child(artists, 0, "s", &artist);
    gchar *text = artist && *artist ? g_strdup_printf("♪ %s — %s", clean, artist) : g_strdup_printf("♪ %s", clean);
    g_free(clean); g_free(artist); if (artists) g_variant_unref(artists); g_variant_unref(metadata);
    return text;
}
static void render(void) {
    gchar *music = NULL;
    if (players) {
        GHashTableIter it; gpointer value;
        g_hash_table_iter_init(&it, players);
        while (g_hash_table_iter_next(&it, NULL, &value)) if ((music = track_text(value))) break;
    }
    gchar *power = NULL;
    if (battery) {
        GVariant *present = g_dbus_proxy_get_cached_property(battery, "IsPresent");
        GVariant *percent = g_dbus_proxy_get_cached_property(battery, "Percentage");
        GVariant *state = g_dbus_proxy_get_cached_property(battery, "State");
        if (present && percent && state && g_variant_is_of_type(present,G_VARIANT_TYPE_BOOLEAN) && g_variant_is_of_type(percent,G_VARIANT_TYPE_DOUBLE) && g_variant_is_of_type(state,G_VARIANT_TYPE_UINT32) && g_variant_get_boolean(present)) {
            guint s = g_variant_get_uint32(state); double p = g_variant_get_double(percent);
            if (p >= 0 && p <= 100) power = g_strdup_printf("%.0f%% · %s", p, s == 1 ? "Charging" : s == 4 ? "Full" : s == 2 ? "On battery" : "Battery");
        }
        if (present) g_variant_unref(present);
        if (percent) g_variant_unref(percent);
        if (state) g_variant_unref(state);
    }
    for (GList *l=views;l;l=l->next) {
        View *v=l->data;
        gtk_label_set_text(GTK_LABEL(v->media),music ? music : ""); gtk_widget_set_visible(v->media,music != NULL);
        gtk_label_set_text(GTK_LABEL(v->battery),power ? power : ""); gtk_widget_set_visible(v->battery,power != NULL);
    }
    g_free(music); g_free(power);
}
static void changed(GDBusProxy *p, GVariant *v, const gchar *const *invalid, gpointer data) {
    (void)p;(void)v;(void)invalid;(void)data;render();
}
static void player_ready(GObject *obj,GAsyncResult *result,gpointer data) {
    (void)obj; gchar *name=data;GError *error=NULL;
    GDBusProxy *p=g_dbus_proxy_new_finish(result,&error);
    gchar *owner = p ? g_dbus_proxy_get_name_owner(p) : NULL;
    if (p && owner) {
        g_hash_table_replace(players,g_strdup(name),p);
        g_signal_connect(p,"g-properties-changed",G_CALLBACK(changed),NULL);
    } else if(p) g_object_unref(p);
    g_free(owner);g_clear_error(&error);g_free(name);render();
}
static void add_player(const gchar *name) {
    if (!g_str_has_prefix(name,"org.mpris.MediaPlayer2.") || g_hash_table_contains(players,name)) return;
    g_dbus_proxy_new(session,G_DBUS_PROXY_FLAGS_DO_NOT_AUTO_START,NULL,name,"/org/mpris/MediaPlayer2","org.mpris.MediaPlayer2.Player",NULL,player_ready,g_strdup(name));
}
static void owner_changed(GDBusConnection *c,const gchar *sender,const gchar *path,const gchar *iface,const gchar *signal,GVariant *params,gpointer data) {
    (void)c;(void)sender;(void)path;(void)iface;(void)signal;(void)data;
    const gchar *name,*old,*owner;g_variant_get(params,"(&s&s&s)",&name,&old,&owner);
    if (!g_str_has_prefix(name,"org.mpris.MediaPlayer2.")) return;
    g_hash_table_remove(players,name);if (*owner) add_player(name);render();
}
static void names_ready(GObject *obj,GAsyncResult *result,gpointer data) {
    (void)data;GError *error=NULL;GVariant *reply=g_dbus_connection_call_finish(G_DBUS_CONNECTION(obj),result,&error);
    if (reply) { gchar **names=NULL;g_variant_get(reply,"(^as)",&names);for(guint i=0;names[i];i++)add_player(names[i]);g_strfreev(names);g_variant_unref(reply); }
    g_clear_error(&error);
}
static void bus_ready(GObject *obj,GAsyncResult *result,gpointer data) {
    (void)obj;(void)data;GError *error=NULL;session=g_bus_get_finish(result,&error);g_clear_error(&error);if(!session)return;
    g_dbus_connection_signal_subscribe(session,"org.freedesktop.DBus","org.freedesktop.DBus","NameOwnerChanged","/org/freedesktop/DBus",NULL,G_DBUS_SIGNAL_FLAGS_NONE,owner_changed,NULL,NULL);
    g_dbus_connection_call(session,"org.freedesktop.DBus","/org/freedesktop/DBus","org.freedesktop.DBus","ListNames",NULL,G_VARIANT_TYPE("(as)"),G_DBUS_CALL_FLAGS_NONE,2000,NULL,names_ready,NULL);
}
static void battery_ready(GObject *obj,GAsyncResult *result,gpointer data) {
    (void)obj;(void)data;GError *error=NULL;battery=g_dbus_proxy_new_for_bus_finish(result,&error);g_clear_error(&error);
    if(battery)g_signal_connect(battery,"g-properties-changed",G_CALLBACK(changed),NULL);
    render();
}
static GtkWidget *label(const gchar *name) {
    GtkWidget *w=gtk_label_new(NULL);gtk_widget_set_name(w,name);gtk_widget_set_no_show_all(w,TRUE);
    gtk_label_set_ellipsize(GTK_LABEL(w),PANGO_ELLIPSIZE_END);gtk_label_set_max_width_chars(GTK_LABEL(w),40);
    gtk_widget_set_can_focus(w,FALSE);return w;
}
static View *minimal_attach(struct Window *win) {
    View *v=g_new0(View,1);v->media=label("minimal-media");v->battery=label("minimal-battery");
    GtkWidget *footer=NULL;
    GList *children=gtk_container_get_children(GTK_CONTAINER(win->window_box));
    for(GList *it=children;it;it=it->next)
        if(g_strcmp0(gtk_widget_get_name(it->data),"lock-footer")==0)footer=it->data;
    g_list_free(children);
    gtk_widget_set_halign(v->media,GTK_ALIGN_START);gtk_widget_set_valign(v->media,GTK_ALIGN_END);
    gtk_box_pack_start(GTK_BOX(footer?footer:win->window_box),v->media,TRUE,TRUE,0);
    gtk_widget_set_halign(v->battery,GTK_ALIGN_END);gtk_widget_set_valign(v->battery,GTK_ALIGN_START);gtk_widget_set_margin_top(v->battery,24);gtk_widget_set_margin_end(v->battery,48);
    gtk_overlay_add_overlay(GTK_OVERLAY(win->overlay),v->battery);
    g_object_set_data(G_OBJECT(win->window),"minimal-view",v);views=g_list_prepend(views,v);
    return v;
}
void on_window_create(struct GtkLock *lock,struct Window *win) {
    (void)lock;minimal_attach(win);
    if(!started){started=TRUE;players=g_hash_table_new_full(g_str_hash,g_str_equal,g_free,g_object_unref);g_bus_get(G_BUS_TYPE_SESSION,NULL,bus_ready,NULL);
        g_dbus_proxy_new_for_bus(G_BUS_TYPE_SYSTEM,G_DBUS_PROXY_FLAGS_DO_NOT_AUTO_START,NULL,"org.freedesktop.UPower","/org/freedesktop/UPower/devices/DisplayDevice","org.freedesktop.UPower.Device",NULL,battery_ready,NULL);}
    render();
}
void on_window_destroy(struct GtkLock *lock,struct Window *win) {
    (void)lock;View *v=g_object_get_data(G_OBJECT(win->window),"minimal-view");views=g_list_remove(views,v);g_free(v);
}
