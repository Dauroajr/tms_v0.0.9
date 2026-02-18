def payment_stats(request):
    """
    Context processor para mostrar estatísticas de pagamento na navbar.
    """
    if not request.user.is_authenticated:
        return {}

    if not hasattr(request, "tenant"):
        return {}

    from fleet.models import WorkdayApproval, PaymentOrder

    # Contadores
    pending_approvals = WorkdayApproval.objects.filter(
        tenant=request.tenant, status="pending"
    ).count()

    pending_payments = PaymentOrder.objects.filter(
        tenant=request.tenant, status="pending"
    ).count()

    approved_payments = PaymentOrder.objects.filter(
        tenant=request.tenant, status="approved"
    ).count()

    return {
        "pending_approvals_count": pending_approvals,
        "pending_payments_count": pending_payments,
        "approved_payments_count": approved_payments,
    }
