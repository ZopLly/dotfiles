/* Test-only geometry after GTK's real session-lock surface is allocated. */
#include "../../gtklock/modules/window-v4.h"
guint module_major_version=4,module_minor_version=0;
struct GtkLock;
static GtkWidget *probe_find(GtkWidget *w,const gchar *name) {
    if(g_strcmp0(gtk_widget_get_name(w),name)==0)return w;
    if(!GTK_IS_CONTAINER(w))return NULL;
    GList *children=gtk_container_get_children(GTK_CONTAINER(w));GtkWidget *found=NULL;
    for(GList *l=children;l && !found;l=l->next)found=probe_find(l->data,name);
    g_list_free(children);return found;
}
static gboolean probe_sample(gpointer data) {
    struct Window *w=data;const gchar *path=g_getenv("GTKLOCK_TEST_GEOMETRY");if(!path)return G_SOURCE_REMOVE;
    GtkWidget *card=probe_find(w->window_box,"auth-card"),*media=probe_find(w->window_box,"minimal-media"),*notifications=probe_find(w->window_box,"lock-notifications");
    if(!card)return G_SOURCE_REMOVE;
    gint x=0,y=0;gtk_widget_translate_coordinates(card,w->window,0,0,&x,&y);
    gchar *json=g_strdup_printf("{\"width\":%d,\"height\":%d,\"card_x\":%d,\"card_width\":%d,\"music_visible\":%s,\"notifications_visible\":%s}",gtk_widget_get_allocated_width(w->window),gtk_widget_get_allocated_height(w->window),x,gtk_widget_get_allocated_width(card),media && gtk_widget_is_drawable(media)?"true":"false",notifications && gtk_widget_is_drawable(notifications)?"true":"false");
    g_file_set_contents(path,json,-1,NULL);g_free(json);return G_SOURCE_REMOVE;
}
void on_window_create(struct GtkLock *lock,struct Window *w) {(void)lock;g_timeout_add(700,probe_sample,w);}
