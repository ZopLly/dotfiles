#include <gtk/gtk.h>
#include "../../gtklock/modules/spectrum.h"
int main(int argc,char **argv) {
    gtk_init(&argc,&argv);GtkWidget *area=spectrum_attach();g_object_ref_sink(area);
    GtkWidget *window=gtk_offscreen_window_new();gtk_container_add(GTK_CONTAINER(window),area);
    gtk_widget_set_size_request(window,320,48);gtk_widget_show_all(window);gtk_widget_show(area);
    g_assert_true(spectrum_frame("[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1,0.9,0.8,0.7,0.6,0.5,0.4,0.3,0.2,0.1,0]"));
    g_assert_false(spectrum_frame("[1,2]"));g_assert_false(spectrum_frame("invalid"));
    spectrum_sync(TRUE);g_assert_nonnull(spectrum_process);
    const gchar *pidfile=g_getenv("SPECTRUM_TEST_WORKER_PID");g_assert_nonnull(pidfile);
    g_file_set_contents(pidfile,g_subprocess_get_identifier(spectrum_process),-1,NULL);
    gint64 deadline=g_get_monotonic_time()+3000000;gboolean got_frame=FALSE;
    while(g_get_monotonic_time()<deadline && !got_frame) {
        while(g_main_context_iteration(NULL,FALSE));
        if(spectrum_levels[0]==0.25)got_frame=TRUE;
        g_usleep(10000);
    }
    g_assert_true(got_frame);spectrum_sync(FALSE);
    for(guint i=0;i<100;i++){while(g_main_context_iteration(NULL,FALSE));g_usleep(10000);}
    g_assert_null(spectrum_process);g_assert_null(spectrum_input);
    spectrum_detach(area);gtk_widget_destroy(window);g_object_unref(area);
    g_print("PASS: validated spectrum frames, real worker output, stop on pause, drawing and shutdown\n");return 0;
}
