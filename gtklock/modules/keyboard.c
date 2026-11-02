/* Display-only Niri layout events. Never observes keys, password or auth state. */
#include <gio/gio.h>
#include <json-glib/json-glib.h>
#include "window-v4.h"
guint module_major_version=4,module_minor_version=0;
struct GtkLock;
static GList *keyboard_labels;
static gchar **keyboard_names;
static guint keyboard_index;
static gboolean keyboard_known;
static GSubprocess *keyboard_process;
static GDataInputStream *keyboard_input;
static GCancellable *keyboard_cancel;
static guint keyboard_retry;
static void keyboard_start(void);
static void keyboard_stop(void);

static void keyboard_render(void) {
    const gchar *full=keyboard_known && keyboard_names ? keyboard_names[keyboard_index] : NULL;
    const gchar *short_name=full;
    if(full && g_str_has_prefix(full,"English"))short_name="EN";
    else if(full && g_str_has_prefix(full,"Russian"))short_name="RU";
    gchar *limited=short_name?g_utf8_substring(short_name,0,MIN(g_utf8_strlen(short_name,-1),12)):g_strdup("—");
    for(GList *l=keyboard_labels;l;l=l->next) {
        gtk_label_set_text(GTK_LABEL(l->data),limited);
        gtk_widget_set_tooltip_text(l->data,full?full:"Раскладка временно недоступна");
    }
    g_free(limited);
}
static gboolean keyboard_integer(JsonObject *obj,const gchar *key,guint *result) {
    JsonNode *n=json_object_get_member(obj,key);
    if(!n || !JSON_NODE_HOLDS_VALUE(n) || json_node_get_value_type(n)!=G_TYPE_INT64)return FALSE;
    gint64 v=json_node_get_int(n);if(v<0 || v>31)return FALSE;
    *result=(guint)v;return TRUE;
}
static gboolean keyboard_apply_json(const gchar *line) {
    JsonParser *parser=json_parser_new();gboolean ok=FALSE;
    if(!json_parser_load_from_data(parser,line,-1,NULL))goto done;
    JsonNode *root=json_parser_get_root(parser);if(!JSON_NODE_HOLDS_OBJECT(root))goto done;
    JsonObject *event=json_node_get_object(root);
    JsonNode *node=json_object_get_member(event,"KeyboardLayoutsChanged");
    if(node && JSON_NODE_HOLDS_OBJECT(node)) {
        JsonObject *changed=json_node_get_object(node);
        node=json_object_get_member(changed,"keyboard_layouts");
        if(!node || !JSON_NODE_HOLDS_OBJECT(node))goto done;
        JsonObject *layouts=json_node_get_object(node);guint idx;
        node=json_object_get_member(layouts,"names");
        if(!node || !JSON_NODE_HOLDS_ARRAY(node) || !keyboard_integer(layouts,"current_idx",&idx))goto done;
        JsonArray *a=json_node_get_array(node);guint count=json_array_get_length(a);
        if(!count || count>32 || idx>=count)goto done;
        gchar **names=g_new0(gchar *,count+1);
        for(guint i=0;i<count;i++) {
            JsonNode *value=json_array_get_element(a,i);
            if(!JSON_NODE_HOLDS_VALUE(value) || json_node_get_value_type(value)!=G_TYPE_STRING) {g_strfreev(names);goto done;}
            const gchar *s=json_node_get_string(value);
            if(!s || !*s || strlen(s)>256 || !g_utf8_validate(s,-1,NULL)) {g_strfreev(names);goto done;}
            names[i]=g_strdup(s);
        }
        g_strfreev(keyboard_names);keyboard_names=names;keyboard_index=idx;keyboard_known=TRUE;ok=TRUE;
    } else {
        node=json_object_get_member(event,"KeyboardLayoutSwitched");guint idx;
        if(!node || !JSON_NODE_HOLDS_OBJECT(node) || !keyboard_integer(json_node_get_object(node),"idx",&idx))goto done;
        if(!keyboard_names || idx>=g_strv_length(keyboard_names))goto done;
        keyboard_index=idx;keyboard_known=TRUE;ok=TRUE;
    }
    if(ok)keyboard_render();
done:
    g_object_unref(parser);return ok;
}
static void keyboard_reaped(GObject *object,GAsyncResult *result,gpointer data) {
    (void)data;g_subprocess_wait_finish(G_SUBPROCESS(object),result,NULL);
}
static gboolean keyboard_restart(gpointer data) {
    (void)data;keyboard_retry=0;if(keyboard_labels)keyboard_start();return G_SOURCE_REMOVE;
}
static void keyboard_read(GObject *object,GAsyncResult *result,gpointer data) {
    (void)data;GDataInputStream *input=G_DATA_INPUT_STREAM(object);GError *error=NULL;gsize length=0;
    gchar *line=g_data_input_stream_read_line_finish(input,result,&length,&error);
    if(input!=keyboard_input) {g_free(line);g_clear_error(&error);return;}
    if(!line || error) {
        g_free(line);g_clear_error(&error);keyboard_stop();keyboard_known=FALSE;keyboard_render();
        if(keyboard_labels)keyboard_retry=g_timeout_add(1500,keyboard_restart,NULL);
        return;
    }
    /* Other Niri events are discarded. Nothing from the stream is persisted. */
    if(length<65536 && (strstr(line,"KeyboardLayoutsChanged") || strstr(line,"KeyboardLayoutSwitched")))keyboard_apply_json(line);
    g_free(line);
    g_data_input_stream_read_line_async(input,G_PRIORITY_DEFAULT,keyboard_cancel,keyboard_read,NULL);
}
static void keyboard_stop(void) {
    if(keyboard_retry){g_source_remove(keyboard_retry);keyboard_retry=0;}
    if(keyboard_cancel)g_cancellable_cancel(keyboard_cancel);
    g_clear_object(&keyboard_input);g_clear_object(&keyboard_cancel);
    if(keyboard_process) {
        g_subprocess_force_exit(keyboard_process);
        g_subprocess_wait_async(keyboard_process,NULL,keyboard_reaped,NULL);
        g_clear_object(&keyboard_process);
    }
}
static void keyboard_start(void) {
    if(keyboard_process || !keyboard_labels)return;
    GError *error=NULL;
    keyboard_process=g_subprocess_new(G_SUBPROCESS_FLAGS_STDOUT_PIPE|G_SUBPROCESS_FLAGS_STDERR_SILENCE,&error,"niri","msg","-j","event-stream",NULL);
    g_clear_error(&error);
    if(!keyboard_process){keyboard_known=FALSE;keyboard_render();keyboard_retry=g_timeout_add(1500,keyboard_restart,NULL);return;}
    keyboard_cancel=g_cancellable_new();
    keyboard_input=g_data_input_stream_new(g_subprocess_get_stdout_pipe(keyboard_process));
    g_data_input_stream_read_line_async(keyboard_input,G_PRIORITY_DEFAULT,keyboard_cancel,keyboard_read,NULL);
}
static GtkWidget *keyboard_find(GtkWidget *widget) {
    if(g_strcmp0(gtk_widget_get_name(widget),"lock-layout")==0)return widget;
    if(!GTK_IS_CONTAINER(widget))return NULL;
    GList *children=gtk_container_get_children(GTK_CONTAINER(widget));GtkWidget *found=NULL;
    for(GList *l=children;l && !found;l=l->next)found=keyboard_find(l->data);
    g_list_free(children);return found;
}
void on_window_create(struct GtkLock *lock,struct Window *window) {
    (void)lock;GtkWidget *label=keyboard_find(window->window_box);if(!GTK_IS_LABEL(label))return;
    keyboard_labels=g_list_prepend(keyboard_labels,label);
    g_object_set_data(G_OBJECT(window->window),"keyboard-label",label);keyboard_render();keyboard_start();
}
void on_window_destroy(struct GtkLock *lock,struct Window *window) {
    (void)lock;keyboard_labels=g_list_remove(keyboard_labels,g_object_get_data(G_OBJECT(window->window),"keyboard-label"));
    if(!keyboard_labels){keyboard_stop();g_clear_pointer(&keyboard_names,g_strfreev);keyboard_known=FALSE;}
}
