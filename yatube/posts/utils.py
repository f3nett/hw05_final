from django.conf import settings
from django.core.paginator import Paginator


def get_paginator(request, queryset, posts_count=settings.POSTS_COUNT):
    """Пагинатор"""
    paginator = Paginator(queryset, posts_count)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
