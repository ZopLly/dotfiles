#include "../../gtklock/modules/keyboard.c"
int main(int argc,char **argv) {
    gtk_init(&argc,&argv);
    GtkWidget *label=gtk_label_new(NULL);g_object_ref_sink(label);keyboard_labels=g_list_prepend(NULL,label);
    keyboard_render();g_assert_cmpstr(gtk_label_get_text(GTK_LABEL(label)),==,"—");
    g_assert_true(keyboard_apply_json("{\"KeyboardLayoutsChanged\":{\"keyboard_layouts\":{\"names\":[\"English (US)\",\"Russian\"],\"current_idx\":0}}}"));
    g_assert_cmpstr(gtk_label_get_text(GTK_LABEL(label)),==,"EN");
    g_assert_true(keyboard_apply_json("{\"KeyboardLayoutSwitched\":{\"idx\":1}}"));
    g_assert_cmpstr(gtk_label_get_text(GTK_LABEL(label)),==,"RU");
    const gchar *bad[]={"{}","invalid","{\"KeyboardLayoutSwitched\":{\"idx\":99}}","{\"KeyboardLayoutSwitched\":{\"idx\":-1}}","{\"KeyboardLayoutSwitched\":{\"idx\":\"0\"}}","{\"KeyboardLayoutsChanged\":{\"keyboard_layouts\":{\"names\":[],\"current_idx\":0}}}",NULL};
    for(guint i=0;bad[i];i++){g_assert_false(keyboard_apply_json(bad[i]));g_assert_cmpstr(gtk_label_get_text(GTK_LABEL(label)),==,"RU");}
    keyboard_known=FALSE;keyboard_render();g_assert_cmpstr(gtk_label_get_text(GTK_LABEL(label)),==,"—");
    if(argc>1 && g_str_equal(argv[1],"--stream")) {
        keyboard_start();gint64 deadline=g_get_monotonic_time()+3000000;gboolean saw_en=FALSE,saw_ru=FALSE;
        while(g_get_monotonic_time()<deadline && !saw_ru) {
            while(g_main_context_iteration(NULL,FALSE));
            if(g_str_equal(gtk_label_get_text(GTK_LABEL(label)),"EN"))saw_en=TRUE;
            if(saw_en && g_str_equal(gtk_label_get_text(GTK_LABEL(label)),"RU"))saw_ru=TRUE;
            g_usleep(10000);
        }
        g_assert_true(saw_en);g_assert_true(saw_ru);keyboard_stop();
        for(guint i=0;i<30;i++){while(g_main_context_iteration(NULL,FALSE));g_usleep(10000);}
        g_assert_null(keyboard_process);g_assert_null(keyboard_input);g_assert_cmpuint(keyboard_retry,==,0);
    }
    g_list_free(keyboard_labels);keyboard_labels=NULL;g_strfreev(keyboard_names);keyboard_names=NULL;g_object_unref(label);
    g_print("PASS: layout initialization, EN/RU switching, invalid data rejected, unavailable state; no keyboard or password events read\n");
    return 0;
}
