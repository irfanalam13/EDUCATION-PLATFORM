from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CancelView,
    CurrentSubscriptionView,
    InvoiceViewSet,
    PaymentViewSet,
    PlanListView,
    RefundView,
    RevenueAnalyticsView,
    SubscribeView,
    ValidateCouponView,
    WebhookView,
)

router = DefaultRouter()
router.register("invoices", InvoiceViewSet, basename="billing-invoices")
router.register("payments", PaymentViewSet, basename="billing-payments")

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="billing-plans"),
    path("subscription/", CurrentSubscriptionView.as_view(), name="billing-subscription"),
    path("subscribe/", SubscribeView.as_view(), name="billing-subscribe"),
    path("cancel/", CancelView.as_view(), name="billing-cancel"),
    path("coupon/validate/", ValidateCouponView.as_view(), name="billing-coupon-validate"),
    path("refund/", RefundView.as_view(), name="billing-refund"),
    path("analytics/revenue/", RevenueAnalyticsView.as_view(), name="billing-revenue"),
    path("webhook/", WebhookView.as_view(), name="billing-webhook-generic"),
    path("webhook/<str:gateway>/", WebhookView.as_view(), name="billing-webhook"),
    path("", include(router.urls)),
]
