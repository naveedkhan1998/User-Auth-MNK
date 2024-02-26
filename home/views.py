# views.py
from django.contrib.staticfiles.views import serve
from django.views.generic import TemplateView
from backend.settings import BASE_DIR

class StaticFilesListView(TemplateView):
    template_name = str(BASE_DIR) + "/home/templates/static_files_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data you may need
        return context

def serve_static(request, path, insecure=True, **kwargs):
    return serve(request, path, insecure=insecure, **kwargs)
