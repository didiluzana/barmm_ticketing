from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """
    Prevent users marked with must_change_password=True
    from accessing the application until they change
    their password.

    The password-change and logout pages remain accessible.
    Django admin is also allowed so a superuser is not
    accidentally locked out of /admin/.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        user = getattr(
            request,
            "user",
            None,
        )

        if (
            user
            and user.is_authenticated
            and getattr(
                user,
                "must_change_password",
                False,
            )
        ):

            change_password_url = reverse(
                "change_password"
            )

            allowed_paths = [
                change_password_url,
                reverse("logout"),
            ]

            # Allow Django admin.
            # This avoids accidentally locking
            # the administrator out.
            if request.path.startswith("/admin/"):
                return self.get_response(request)

            if request.path not in allowed_paths:
                return redirect(
                    change_password_url
                )

        return self.get_response(request)
