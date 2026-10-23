/* Display-only responsive composition; never reads input or auth state. */
#include "window-v4.h"
guint module_major_version=4,module_minor_version=0;
struct GtkLock;
static GtkWidget *layout_find(GtkWidget *widget,const gchar *name) {
    if (g_strcmp0(gtk_widget_get_name(widget),name)==0) return widget;
    if (!GTK_IS_CONTAINER(widget)) return NULL;
    GList *children=gtk_container_get_children(GTK_CONTAINER(widget));GtkWidget *found=NULL;
    for (GList *it=children;it && !found;it=it->next) found=layout_find(it->data,name);
    g_list_free(children);return found;
}
static void layout_resize(GtkWidget *widget,GtkAllocation *allocation,gpointer data) {
    (void)widget;struct Window *window=data;
    GtkWidget *columns=layout_find(window->window_box,"split-columns");
    GtkWidget *footer=layout_find(window->window_box,"lock-footer");
    GtkWidget *card=layout_find(window->window_box,"auth-card");
    if (!columns || !footer || !card) return;
    gboolean compact=allocation->width<920;
    gpointer mode=GINT_TO_POINTER(compact?2:1);
    if(g_object_get_data(G_OBJECT(window->window),"split-layout-mode")==mode)return;
    g_object_set_data(G_OBJECT(window->window),"split-layout-mode",mode);
    GtkOrientation orientation=compact?GTK_ORIENTATION_VERTICAL:GTK_ORIENTATION_HORIZONTAL;
    gtk_orientable_set_orientation(GTK_ORIENTABLE(columns),orientation);
    gtk_orientable_set_orientation(GTK_ORIENTABLE(footer),orientation);
    gtk_box_set_spacing(GTK_BOX(columns),compact?20:48);
    gtk_widget_set_halign(card,compact?GTK_ALIGN_CENTER:GTK_ALIGN_END);
    gtk_box_set_child_packing(GTK_BOX(columns),window->info_box,!compact,TRUE,0,GTK_PACK_START);
    gtk_box_set_child_packing(GTK_BOX(columns),card,FALSE,TRUE,0,compact?GTK_PACK_START:GTK_PACK_END);
    GtkStyleContext *context=gtk_widget_get_style_context(window->window_box);
    if(compact)gtk_style_context_add_class(context,"compact");else gtk_style_context_remove_class(context,"compact");
}
void on_window_create(struct GtkLock *lock,struct Window *window) {
    (void)lock;g_signal_connect(window->window,"size-allocate",G_CALLBACK(layout_resize),window);
}
void on_window_destroy(struct GtkLock *lock,struct Window *window) {
    (void)lock;g_signal_handlers_disconnect_by_func(window->window,G_CALLBACK(layout_resize),window);
}
