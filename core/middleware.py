
from django.utils.deprecation import MiddlewareMixin
from .user_context import set_user

class CurrentUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # AuthenticationMiddleware já rodou antes; request.user existe
        set_user(getattr(request, "user", None))

    def process_response(self, request, response):
        set_user(None)
        return response
