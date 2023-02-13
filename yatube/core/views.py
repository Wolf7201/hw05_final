from django.shortcuts import render


def page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def forbidden(request, exception):
    return render(request, 'core/403.html', {'path': request.path}, status=403)
