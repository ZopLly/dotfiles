/* Isolated GTK test harness. Not a locker; never installed or used for locking. */
#include "../../gtklock/modules/minimal.c"
static GVariant *metadata(const gchar *title,const gchar *artist) {
    GVariantBuilder b;g_variant_builder_init(&b,G_VARIANT_TYPE_VARDICT);
    if(title)g_variant_builder_add(&b,"{sv}","xesam:title",g_variant_new_string(title));
    const gchar *artists[]={artist,NULL};if(artist)g_variant_builder_add(&b,"{sv}","xesam:artist",g_variant_new_strv(artists,-1));
    return g_variant_builder_end(&b);
}
int main(int argc,char **argv) {
    gtk_init(&argc,&argv);
    GDBusProxy *p=g_object_new(G_TYPE_DBUS_PROXY,NULL);
    g_dbus_proxy_set_cached_property(p,"PlaybackStatus",g_variant_new_string("Playing"));
    g_dbus_proxy_set_cached_property(p,"Metadata",metadata("Odyssey","Homer"));
    gchar *text=track_text(p);g_assert_cmpstr(text,==,"СЕЙЧАС ИГРАЕТ\n\n♪ Odyssey — Homer");g_free(text);
    const gchar *off[]={"Paused","Stopped","Unknown",NULL};
    for(int i=0;off[i];i++){g_dbus_proxy_set_cached_property(p,"PlaybackStatus",g_variant_new_string(off[i]));g_assert_null(track_text(p));}
    g_dbus_proxy_set_cached_property(p,"PlaybackStatus",g_variant_new_string("Playing"));
    g_dbus_proxy_set_cached_property(p,"Metadata",metadata("   ",NULL));g_assert_null(track_text(p));
    g_dbus_proxy_set_cached_property(p,"Metadata",metadata(NULL,NULL));g_assert_null(track_text(p));
    g_dbus_proxy_set_cached_property(p,"Metadata",g_variant_new_string("invalid"));g_assert_null(track_text(p));
    g_dbus_proxy_set_cached_property(p,"PlaybackStatus",g_variant_new_int32(1));g_assert_null(track_text(p));
    g_dbus_proxy_set_cached_property(p,"PlaybackStatus",g_variant_new_string("Playing"));
    g_dbus_proxy_set_cached_property(p,"Metadata",metadata(NULL,NULL));
    GtkBuilder *builder=gtk_builder_new();GError *error=NULL;
    g_assert(gtk_builder_add_from_file(builder,"gtklock/layout.xml",&error));g_assert_no_error(error);
    const gchar *ids[]={"window-box","input-field","clock-label","date-label","body-revealer","message-box","unlock-button",NULL};
    for(int i=0;ids[i];i++)g_assert_nonnull(gtk_builder_get_object(builder,ids[i]));
    const gchar *themes[]={"ancient-odyssey","catppuccin-mocha","gruvbox-dark","tokyo-night",NULL};
    for(int i=0;themes[i];i++){
        GtkCssProvider *css=gtk_css_provider_new();gchar *path=g_strdup_printf("assets/themes/%s/gtklock.css",themes[i]);
        g_assert(gtk_css_provider_load_from_path(css,path,&error));g_assert_no_error(error);g_free(path);g_object_unref(css);
    }
    View v={.media=label("minimal-media"),.battery=label("minimal-battery")};views=g_list_append(NULL,&v);
    players=g_hash_table_new_full(g_str_hash,g_str_equal,g_free,g_object_unref);g_hash_table_insert(players,g_strdup("test"),p);
    render();g_assert(gtk_widget_get_visible(v.media));
    g_assert_nonnull(strstr(gtk_label_get_text(GTK_LABEL(v.media)),"Ничего не играет"));
    g_dbus_proxy_set_cached_property(p,"Metadata",metadata("Odyssey","Homer"));render();g_assert(gtk_widget_get_visible(v.media));
    g_dbus_proxy_set_cached_property(p,"PlaybackStatus",g_variant_new_string("Paused"));render();g_assert(gtk_widget_get_visible(v.media));
    g_assert_nonnull(strstr(gtk_label_get_text(GTK_LABEL(v.media)),"Ничего не играет"));
    gtk_widget_show_all(v.media);g_assert(gtk_widget_get_visible(v.media));
    g_assert_nonnull(strstr(gtk_label_get_text(GTK_LABEL(v.media)),"Ничего не играет"));
    g_hash_table_remove_all(players);render();g_assert(gtk_widget_get_visible(v.media));
    g_assert_nonnull(strstr(gtk_label_get_text(GTK_LABEL(v.media)),"Ничего не играет"));
    if (argc > 1) {
        GtkWidget *window=gtk_offscreen_window_new();gtk_window_set_default_size(GTK_WINDOW(window),1280,800);
        GtkWidget *overlay=gtk_overlay_new();gtk_container_add(GTK_CONTAINER(window),overlay);
        GtkWidget *box=GTK_WIDGET(gtk_builder_get_object(builder,"window-box"));gtk_container_add(GTK_CONTAINER(overlay),box);
        gtk_label_set_text(GTK_LABEL(gtk_builder_get_object(builder,"clock-label")),"21:48");
        gtk_label_set_text(GTK_LABEL(gtk_builder_get_object(builder,"date-label")),"Tuesday, 13 October");
        gtk_revealer_set_reveal_child(GTK_REVEALER(gtk_builder_get_object(builder,"body-revealer")),TRUE);
        gtk_box_pack_end(GTK_BOX(box),v.media,FALSE,FALSE,0);
        gtk_overlay_add_overlay(GTK_OVERLAY(overlay),v.battery);gtk_widget_set_halign(v.battery,GTK_ALIGN_CENTER);gtk_widget_set_valign(v.battery,GTK_ALIGN_END);gtk_widget_set_margin_bottom(v.battery,28);
        GtkCssProvider *css=gtk_css_provider_new();gtk_css_provider_load_from_path(css,"assets/themes/ancient-odyssey/gtklock.css",NULL);
        gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),GTK_STYLE_PROVIDER(css),GTK_STYLE_PROVIDER_PRIORITY_USER);
        GtkCssProvider *bg=gtk_css_provider_new();gtk_css_provider_load_from_data(bg,"window { background-image: url('file:///tmp/lockscreen-minimal-blur.jpg'); background-size: cover; background-position: center; }",-1,NULL);
        gtk_style_context_add_provider_for_screen(gdk_screen_get_default(),GTK_STYLE_PROVIDER(bg),GTK_STYLE_PROVIDER_PRIORITY_USER);
        gtk_widget_show_all(window);gtk_label_set_text(GTK_LABEL(v.battery),"78% · Charging");gtk_widget_show(v.battery);
        for(int i=0;i<2;i++) {
            gtk_label_set_text(GTK_LABEL(v.media),"♪ The Odyssey — Ancient Shores");gtk_widget_set_visible(v.media,i==1);
            for(int n=0;n<20;n++){while(gtk_events_pending())gtk_main_iteration();g_usleep(10000);}
            GdkPixbuf *shot=gtk_offscreen_window_get_pixbuf(GTK_OFFSCREEN_WINDOW(window));
            gdk_pixbuf_save(shot,i ? "/tmp/lockscreen-minimal-playing.png" : "/tmp/lockscreen-minimal-paused.png","png",NULL,NULL);g_object_unref(shot);
        }
    }
    g_print("PASS: Playing-only valid metadata, persistent empty state on paused/stopped/missing player; XML IDs and all four theme CSS.\n");
    return 0;
}
