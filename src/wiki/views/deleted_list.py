from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from wiki import models


class DeletedListView(TemplateView):
    template_name = "wiki/deleted_list.html"

    def dispatch(self, request, *args, **kwargs):
        # Let logged in super users continue
        if not request.user.is_superuser:
            return redirect("wiki:root")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs["deleted_articles"] = (
            models.Article.objects.select_related("current_revision")
            .prefetch_related("urlpath_set")
            .filter(current_revision__deleted=True)
        )
        return super().get_context_data(**kwargs)
