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
static gboolean layout_apply(gpointer data) {
    struct Window *window=data;
    g_object_set_data(G_OBJECT(window->window),"split-layout-pending",NULL);
    GtkAllocation size;gtk_widget_get_allocation(window->window,&size);
    GtkAllocation *allocation=&size;
    if(size.width<2 || size.height<2)return G_SOURCE_REMOVE;
    GtkWidget *columns=layout_find(window->window_box,"split-columns");
    GtkWidget *footer=layout_find(window->window_box,"lock-footer");
    GtkWidget *card=layout_find(window->window_box,"auth-card");
    if (!columns || !footer || !card) return G_SOURCE_REMOVE;
    gboolean compact=allocation->width<920;
    gboolean short_screen=allocation->height<780;
    gpointer mode=GINT_TO_POINTER((compact?2:1)+(short_screen?4:0));
    if(g_object_get_data(G_OBJECT(window->window),"split-layout-mode")==mode)return G_SOURCE_REMOVE;
    g_object_set_data(G_OBJECT(window->window),"split-layout-mode",mode);
    GtkOrientation orientation=compact?GTK_ORIENTATION_VERTICAL:GTK_ORIENTATION_HORIZONTAL;
    gtk_orientable_set_orientation(GTK_ORIENTABLE(columns),orientation);
    gtk_orientable_set_orientation(GTK_ORIENTABLE(footer),orientation);
    gtk_box_set_spacing(GTK_BOX(columns),compact?20:48);
    gtk_widget_set_halign(card,compact?GTK_ALIGN_CENTER:GTK_ALIGN_END);
    gtk_box_set_child_packing(GTK_BOX(columns),window->info_box,!compact,TRUE,0,GTK_PACK_START);
    gtk_box_set_child_packing(GTK_BOX(columns),card,FALSE,TRUE,0,compact?GTK_PACK_START:GTK_PACK_END);
    gtk_box_set_spacing(GTK_BOX(card),short_screen?12:16);
    GtkStyleContext *context=gtk_widget_get_style_context(window->window_box);
    if(short_screen)gtk_style_context_add_class(context,"short");else gtk_style_context_remove_class(context,"short");
    if(compact)gtk_style_context_add_class(context,"compact");else gtk_style_context_remove_class(context,"compact");
    GtkWidget *spectrum=layout_find(window->window_box,"lock-spectrum");
    if(spectrum)gtk_widget_set_size_request(spectrum,-1,compact?28:40);
    gtk_box_set_spacing(GTK_BOX(footer),compact?16:24);
    gtk_widget_queue_resize(window->window_box);
    return G_SOURCE_REMOVE;
}
static void layout_resize(GtkWidget *widget,GtkAllocation *allocation,gpointer data) {
    (void)widget;struct Window *window=data;
    if(allocation->width<2 || allocation->height<2)return;
    if(g_object_get_data(G_OBJECT(window->window),"split-layout-pending"))return;
    guint id=g_idle_add(layout_apply,window);
    g_object_set_data(G_OBJECT(window->window),"split-layout-pending",GUINT_TO_POINTER(id));
}
void on_window_create(struct GtkLock *lock,struct Window *window) {
    (void)lock;g_signal_connect(window->window,"size-allocate",G_CALLBACK(layout_resize),window);
}
void on_window_destroy(struct GtkLock *lock,struct Window *window) {
    (void)lock;guint id=GPOINTER_TO_UINT(g_object_get_data(G_OBJECT(window->window),"split-layout-pending"));
    if(id)g_source_remove(id);
    g_signal_handlers_disconnect_by_func(window->window,G_CALLBACK(layout_resize),window);
}
