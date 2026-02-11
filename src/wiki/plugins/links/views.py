from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.generic import View
from wiki import models
from wiki.core.utils import object_to_json_response
from wiki.decorators import get_article


class QueryUrlPath(View):
    def _prime_cached_ancestors(self, urlpaths):
        urlpaths = list(urlpaths)
        if not urlpaths:
            return urlpaths

        ancestor_filter = Q()
        for node in urlpaths:
            ancestor_filter |= Q(
                tree_id=node.tree_id, lft__lte=node.lft, rght__gte=node.rght
            )

        ancestors = (
            models.URLPath.objects.filter(ancestor_filter)
            .select_related_common()
            .order_by("tree_id", "lft")
        )

        targets_by_id = {node.id: node for node in urlpaths}
        current_tree = None
        stack = []
        for node in ancestors:
            if node.tree_id != current_tree:
                current_tree = node.tree_id
                stack = []
            while stack and stack[-1].rght < node.lft:
                stack.pop()
            if node.id in targets_by_id:
                targets_by_id[node.id].cached_ancestors = list(stack)
            stack.append(node)

        return urlpaths

    @method_decorator(get_article(can_read=True))
    def dispatch(self, request, article, *args, **kwargs):
        max_num = kwargs.pop("max_num", 20)
        query = request.GET.get("query", None)

        matches = []

        if query:
            matches = (
                models.URLPath.objects.can_read(request.user)
                .active()
                .filter(
                    article__current_revision__title__contains=query,
                    article__current_revision__deleted=False,
                )
            )
            matches = list(matches.select_related_common()[:max_num])
            self._prime_cached_ancestors(matches)
            matches = [
                "[{title:s}](wiki:{url:s})".format(
                    title=m.article.current_revision.title,
                    url="/" + m.path.strip("/"),
                )
                for m in matches
            ]

        return object_to_json_response(matches)
