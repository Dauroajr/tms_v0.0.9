from django.shortcuts import render
from django.views.generic import (
    ListView,
    CreateView,
    DeleteView,
    DetailView,
    UpdateView
)

from .mixins import (
    TenantAwareViewMixin,
    TenantAwareDeleteMixin,
    TenantAwareQuerysetMixin,
    TenantRequiredMixin,
)


class TenantAwareListView(TenantAwareViewMixin, ListView):
    """Base ListView that automatically filters by tenant. """

    paginate_by = 20


class TenantAwareDetailView(TenantAwareViewMixin, DetailView):
    pass


class TenantAwareCreateView(TenantAwareViewMixin, CreateView):
    pass


class TenantAwareUpdateView(TenantAwareViewMixin, UpdateView):
    pass


class TenantAwareDeleteView(
    TenantRequiredMixin,
    TenantAwareQuerysetMixin,
    TenantAwareDeleteMixin,  # ← Usa o mixin específico
    DeleteView
):
    pass
