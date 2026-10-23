/* GTK widget test only; never acquires a session lock or touches PAM. */
#include "../gtklock/modules/notifications.c"
int main(int argc,char **argv) {
    gtk_init(&argc,&argv);
    GtkWidget *label=gtk_label_new(NULL);
    GVariantBuilder list,card;
    g_variant_builder_init(&list,G_VARIANT_TYPE("aa{sv}"));
    for (int i=0;i<4;i++) {
        g_variant_builder_init(&card,G_VARIANT_TYPE_VARDICT);
        g_variant_builder_add(&card,"{sv}","app-name",g_variant_new_string("Niri Test"));
        g_variant_builder_add(&card,"{sv}","summary",g_variant_new_string("Synthetic <title>"));
        g_variant_builder_add(&card,"{sv}","body",g_variant_new_string("<b>Body</b>"));
        g_variant_builder_add_value(&list,g_variant_builder_end(&card));
    }
    GVariant *value=g_variant_ref_sink(g_variant_builder_end(&list));
    gchar *text=notification_text(value);
    gtk_label_set_text(GTK_LABEL(label),text);
    g_assert_nonnull(strstr(gtk_label_get_text(GTK_LABEL(label)),"<b>Body</b>"));
    gchar **pieces=g_strsplit(text,"Synthetic",-1);
    g_assert_cmpuint(g_strv_length(pieces),==,4);g_strfreev(pieces);
    g_assert_false(gtk_label_get_use_markup(GTK_LABEL(label)));
    g_free(text);g_variant_unref(value);gtk_widget_destroy(label);
    g_assert_null(notification_text(NULL));
    g_print("PASS: three read-only cards, plain text, missing service hidden; no session lock\n");
    return 0;
}
