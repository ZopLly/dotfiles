/* Render the actual GTK layout; the only native lock test is in a separate compositor. */
#define module_major_version minimal_major
#define module_minor_version minimal_minor
#define on_window_create minimal_create
#define on_window_destroy minimal_destroy
#include "../gtklock/modules/minimal.c"
#undef module_major_version
#undef module_minor_version
#undef on_window_create
#undef on_window_destroy
#define module_major_version notifications_major
#define module_minor_version notifications_minor
#define on_window_create notifications_create
#define on_window_destroy notifications_destroy
#include "../gtklock/modules/notifications.c"
#undef module_major_version
#undef module_minor_version
#undef on_window_create
#undef on_window_destroy
#define module_major_version layout_major
#define module_minor_version layout_minor
#define on_window_create layout_create
#define on_window_destroy layout_destroy
#include "../gtklock/modules/layout.c"
static void spin(void) {for(int i=0;i<30;i++){while(gtk_events_pending())gtk_main_iteration();g_usleep(10000);}}
static void render_size(int width,int height,const char *path) {
    GtkBuilder *builder=gtk_builder_new();GError *error=NULL;
    g_assert_true(gtk_builder_add_from_file(builder,"gtklock/layout.xml",&error)>0);g_assert_no_error(error);
    struct Window win={0};
    win.window=gtk_offscreen_window_new();gtk_window_set_default_size(GTK_WINDOW(win.window),width,height);gtk_widget_set_size_request(win.window,width,height);
    win.overlay=gtk_overlay_new();gtk_container_add(GTK_CONTAINER(win.window),win.overlay);
#define GET(field,name) win.field=GTK_WIDGET(gtk_builder_get_object(builder,name))
    GET(window_box,"window-box");GET(info_box,"info-box");GET(time_box,"time-box");
    GET(clock_label,"clock-label");GET(date_label,"date-label");GET(body_revealer,"body-revealer");GET(input_field,"input-field");
#undef GET
    gtk_container_add(GTK_CONTAINER(win.overlay),win.window_box);
    gtk_label_set_text(GTK_LABEL(win.clock_label),"21:30");gtk_label_set_text(GTK_LABEL(win.date_label),"Четверг, 22 октября");
    gtk_revealer_set_reveal_child(GTK_REVEALER(win.body_revealer),TRUE);
    g_assert_false(gtk_entry_get_visibility(GTK_ENTRY(win.input_field)));
    layout_create(NULL,&win);minimal_attach(&win);notification_attach(&win);
    gtk_widget_show_all(win.window);spin();
    View *v=g_object_get_data(G_OBJECT(win.window),"minimal-view");
    gtk_label_set_text(GTK_LABEL(v->media),"♫ Вечерний плейлист · пример");gtk_widget_show(v->media);
    gtk_label_set_text(GTK_LABEL(v->battery),"78 % · Заряжается");gtk_widget_show(v->battery);
    GtkWidget *notification=g_object_get_data(G_OBJECT(win.window),"notification-label");
    gtk_label_set_text(GTK_LABEL(notification),"Календарь · пример\nЗавтра: практика в университете\n\nМессенджер · пример\nНовое сообщение\n\nСистема · пример\nБатарея заряжается");gtk_widget_show(notification);spin();
    g_print("%dx%d: media visible=%d mapped=%d h=%d, notifications visible=%d mapped=%d h=%d, battery visible=%d mapped=%d h=%d\n",width,height,
        gtk_widget_get_visible(v->media),gtk_widget_get_mapped(v->media),gtk_widget_get_allocated_height(v->media),
        gtk_widget_get_visible(notification),gtk_widget_get_mapped(notification),gtk_widget_get_allocated_height(notification),
        gtk_widget_get_visible(v->battery),gtk_widget_get_mapped(v->battery),gtk_widget_get_allocated_height(v->battery));
    g_assert_cmpint(gtk_widget_get_allocated_height(v->media),>,16);
    g_assert_cmpint(gtk_widget_get_allocated_height(notification),>,16);
    g_assert_cmpint(gtk_widget_get_allocated_height(v->battery),>,16);
    g_assert_true(gtk_widget_is_drawable(v->media));g_assert_true(gtk_widget_is_drawable(notification));g_assert_true(gtk_widget_is_drawable(v->battery));
    GtkWidget *columns=layout_find(win.window_box,"split-columns");GtkWidget *card=layout_find(win.window_box,"auth-card");
    g_assert_cmpint(gtk_orientable_get_orientation(GTK_ORIENTABLE(columns)),==,width<920?GTK_ORIENTATION_VERTICAL:GTK_ORIENTATION_HORIZONTAL);
    gint clock_x=0,clock_y=0,card_x=0,card_y=0;
    g_assert_true(gtk_widget_translate_coordinates(win.clock_label,win.window_box,0,0,&clock_x,&clock_y));
    g_assert_true(gtk_widget_translate_coordinates(card,win.window_box,0,0,&card_x,&card_y));
    if(width>=920) {
        g_assert_cmpint(clock_x,<,card_x);
        gint right_x=0,right_y=0;g_assert_true(gtk_widget_translate_coordinates(card,columns,0,0,&right_x,&right_y));
        g_assert_cmpint(right_x+gtk_widget_get_allocated_width(card),==,gtk_widget_get_allocated_width(columns));
    } else g_assert_cmpint(clock_y,<,card_y);
    g_assert_cmpint(gtk_widget_get_allocated_width(win.window),==,width);
    g_assert_cmpint(gtk_widget_get_allocated_height(win.window),==,height);
    GdkPixbuf *image=gtk_offscreen_window_get_pixbuf(GTK_OFFSCREEN_WINDOW(win.window));
    g_assert_true(gdk_pixbuf_save(image,path,"png",&error,NULL));g_assert_no_error(error);g_object_unref(image);
    layout_destroy(NULL,&win);minimal_destroy(NULL,&win);notifications_destroy(NULL,&win);gtk_widget_destroy(win.window);g_object_unref(builder);
}
int main(int argc,char **argv) {
    gtk_init(&argc,&argv);
    GtkCssProvider *css=gtk_css_provider_new();GError *error=NULL;
    const char *themes[]={"ancient-odyssey","catppuccin-mocha","gruvbox-dark","tokyo-night",NULL};
    for(int i=0;themes[i];i++) {
        gchar *path=g_strdup_printf("assets/themes/%s/gtklock.css",themes[i]);
        g_assert_true(gtk_css_provider_load_from_path(css,path,&error));g_assert_no_error(error);g_free(path);
    }
    g_assert_true(gtk_css_provider_load_from_path(css,"assets/themes/ancient-odyssey/gtklock.css",&error));g_assert_no_error(error);
    gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),GTK_STYLE_PROVIDER(css),GTK_STYLE_PROVIDER_PRIORITY_USER);
    gchar *cwd=g_get_current_dir();gchar *file=g_build_filename(cwd,"assets/themes/ancient-odyssey/wallpaper.jpg",NULL);
    gchar *uri=g_filename_to_uri(file,NULL,NULL);gchar *background=g_strdup_printf("window { background-image: url(\"%s\"); background-size: cover; background-position: center; }",uri);
    GtkCssProvider *bg=gtk_css_provider_new();gtk_css_provider_load_from_data(bg,background,-1,NULL);
    gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),GTK_STYLE_PROVIDER(bg),GTK_STYLE_PROVIDER_PRIORITY_USER);
    g_free(cwd);g_free(file);g_free(uri);g_free(background);
    render_size(1280,800,"/tmp/niri-lock-split-actual.png");
    render_size(1280,720,"/tmp/niri-lock-split-720.png");
    render_size(760,1000,"/tmp/niri-lock-split-narrow.png");
    g_print("PASS: real GtkBuilder layout, original password field, four palettes, split/compact geometry; no session lock\n");
    return 0;
}
