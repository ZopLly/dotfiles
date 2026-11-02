/* Shared CAVA worker, owned only while music plays. No microphone input. */
#include <json-glib/json-glib.h>
#include <signal.h>
static GList *spectrum_areas;
static gdouble spectrum_levels[20];
static GSubprocess *spectrum_process;
static GDataInputStream *spectrum_input;
static GCancellable *spectrum_cancel;
static void spectrum_stop(void);
static void spectrum_redraw(void){for(GList *l=spectrum_areas;l;l=l->next)gtk_widget_queue_draw(l->data);}
static gboolean spectrum_frame(const gchar *line) {
    JsonParser *p=json_parser_new();gboolean ok=FALSE;
    if(!json_parser_load_from_data(p,line,-1,NULL))goto done;
    JsonNode *root=json_parser_get_root(p);if(!JSON_NODE_HOLDS_ARRAY(root))goto done;
    JsonArray *a=json_node_get_array(root);if(json_array_get_length(a)!=20)goto done;
    gdouble next[20];
    for(guint i=0;i<20;i++) {
        JsonNode *n=json_array_get_element(a,i);GType t=json_node_get_value_type(n);
        if(!JSON_NODE_HOLDS_VALUE(n) || (t!=G_TYPE_INT64 && t!=G_TYPE_DOUBLE))goto done;
        next[i]=json_node_get_double(n);if(!(next[i]>=0 && next[i]<=1))goto done;
    }
    memcpy(spectrum_levels,next,sizeof(next));spectrum_redraw();ok=TRUE;
done:g_object_unref(p);return ok;
}
static gboolean spectrum_draw(GtkWidget *widget,cairo_t *cr,gpointer data) {
    (void)data;GdkRGBA color={0.5,0.7,0.8,1};
    gtk_style_context_lookup_color(gtk_widget_get_style_context(widget),"lock_accent",&color);
    gdouble width=gtk_widget_get_allocated_width(widget),height=gtk_widget_get_allocated_height(widget);
    gdouble cell=width/20.0;
    cairo_set_source_rgba(cr,color.red,color.green,color.blue,0.9);
    for(guint i=0;i<20;i++) {
        gdouble h=MAX(2.0,spectrum_levels[i]*(height-2));
        cairo_rectangle(cr,i*cell+1,height-h,MAX(1.0,cell-4),h);
    }
    cairo_fill(cr);return FALSE;
}
static void spectrum_reaped(GObject *object,GAsyncResult *result,gpointer data) {
    (void)data;g_subprocess_wait_finish(G_SUBPROCESS(object),result,NULL);
}
static void spectrum_read(GObject *object,GAsyncResult *result,gpointer data) {
    (void)data;GError *error=NULL;gsize size=0;
    gchar *line=g_data_input_stream_read_line_finish(G_DATA_INPUT_STREAM(object),result,&size,&error);
    if(G_DATA_INPUT_STREAM(object)!=spectrum_input){g_free(line);g_clear_error(&error);return;}
    if(!line || error){g_free(line);g_clear_error(&error);spectrum_stop();return;}
    if(size<2048)spectrum_frame(line);
    g_free(line);g_data_input_stream_read_line_async(spectrum_input,G_PRIORITY_DEFAULT,spectrum_cancel,spectrum_read,NULL);
}
static void spectrum_stop(void) {
    if(spectrum_cancel)g_cancellable_cancel(spectrum_cancel);
    g_clear_object(&spectrum_input);g_clear_object(&spectrum_cancel);
    if(spectrum_process) {
        /* Graceful shutdown lets the Python worker terminate and reap its CAVA. */
        g_subprocess_send_signal(spectrum_process,SIGTERM);
        g_subprocess_wait_async(spectrum_process,NULL,spectrum_reaped,NULL);
        g_clear_object(&spectrum_process);
    }
    memset(spectrum_levels,0,sizeof(spectrum_levels));spectrum_redraw();
}
static void spectrum_sync(gboolean playing) {
    if(!playing || !spectrum_areas){spectrum_stop();return;}
    if(spectrum_process)return;
    const gchar *root=g_getenv("NIRI_LOCK_ROOT");
    gchar *worker=root && g_path_is_absolute(root)?g_build_filename(root,"quickshell/cava_stream.py",NULL):g_build_filename(g_get_user_config_dir(),"quickshell/cava_stream.py",NULL);
    if(!g_file_test(worker,G_FILE_TEST_IS_REGULAR)){g_free(worker);return;}
    spectrum_process=g_subprocess_new(G_SUBPROCESS_FLAGS_STDOUT_PIPE|G_SUBPROCESS_FLAGS_STDERR_SILENCE,NULL,"python3",worker,"--json",NULL);g_free(worker);
    if(!spectrum_process)return;
    spectrum_cancel=g_cancellable_new();spectrum_input=g_data_input_stream_new(g_subprocess_get_stdout_pipe(spectrum_process));
    g_data_input_stream_read_line_async(spectrum_input,G_PRIORITY_DEFAULT,spectrum_cancel,spectrum_read,NULL);
}
static GtkWidget *spectrum_attach(void) {
    GtkWidget *area=gtk_drawing_area_new();gtk_widget_set_name(area,"lock-spectrum");
    gtk_widget_set_size_request(area,-1,40);gtk_widget_set_can_focus(area,FALSE);
    gtk_widget_set_no_show_all(area,TRUE);g_signal_connect(area,"draw",G_CALLBACK(spectrum_draw),NULL);
    spectrum_areas=g_list_prepend(spectrum_areas,area);return area;
}
static void spectrum_detach(GtkWidget *area) {
    spectrum_areas=g_list_remove(spectrum_areas,area);if(!spectrum_areas)spectrum_stop();
}
