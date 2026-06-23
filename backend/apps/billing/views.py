from __future__ import annotations

import logging

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import analytics, entitlements, services
from .gateways import SUPPORTED_GATEWAYS, GatewayError, WebhookVerificationError
from .models import Coupon, Invoice, Payment, Plan, Subscription
from .serializers import (
    CancelRequestSerializer,
    CouponSerializer,
    InvoiceSerializer,
    PaymentSerializer,
    PlanSerializer,
    RefundRequestSerializer,
    SubscribeRequestSerializer,
    SubscriptionSerializer,
)

log = logging.getLogger("apps.billing")


class IsBillingAdmin(BasePermission):
    message = "Billing administration is restricted to platform admins."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_staff or getattr(user, "role", "") == "ADMIN")
        )


class PlanListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        plans = Plan.objects.filter(is_active=True, is_public=True)
        return Response(PlanSerializer(plans, many=True).data)


class CurrentSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sub = entitlements.active_subscription(request.user)
        return Response(
            {
                "subscription": SubscriptionSerializer(sub).data if sub else None,
                "entitlements": entitlements.snapshot(request.user),
            }
        )


class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubscribeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        plan = data["plan"]

        if data.get("institution_id"):
            return self._subscribe_institution(request, data, plan)

        try:
            result = services.subscribe(
                request.user,
                plan,
                gateway=data["gateway"],
                coupon_code=data.get("coupon_code", ""),
                start_trial=data.get("start_trial", True),
                success_url=data.get("success_url", ""),
                cancel_url=data.get("cancel_url", ""),
            )
        except GatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        if result.subscription.coupon_id:
            services.redeem_coupon(result.subscription.coupon)
        return self._serialize_result(result)

    def _subscribe_institution(self, request, data, plan):
        from apps.institutions.models import Institution
        from apps.institutions.permissions import _is_inst_admin

        institution = get_object_or_404(Institution, id=data["institution_id"])
        if not _is_inst_admin(request.user, institution.id):
            raise PermissionDenied("Only an institution admin can purchase a plan.")
        result = services.subscribe_institution(
            institution=institution,
            plan=plan,
            seats=data.get("seats", 1),
            gateway=data["gateway"],
            coupon_code=data.get("coupon_code", ""),
            billing_email=data.get("billing_email", ""),
            purchased_by=request.user,
            success_url=data.get("success_url", ""),
            cancel_url=data.get("cancel_url", ""),
        )
        return self._serialize_result(result)

    @staticmethod
    def _serialize_result(result):
        payload = {
            "status": result.subscription.status,
            "requires_payment": result.requires_payment,
            "checkout_url": result.checkout_url,
            "checkout_payload": result.checkout_payload,
        }
        if result.invoice:
            payload["invoice"] = InvoiceSerializer(result.invoice).data
        return Response(payload, status=status.HTTP_201_CREATED)


class CancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CancelRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sub = entitlements.active_subscription(request.user) or (
            Subscription.objects.filter(user=request.user).order_by("-created_at").first()
        )
        if sub is None:
            return Response({"detail": "No subscription to cancel."}, status=status.HTTP_404_NOT_FOUND)
        services.cancel_subscription(sub, at_period_end=serializer.validated_data["at_period_end"])
        sub.refresh_from_db()
        return Response(SubscriptionSerializer(sub).data)


class WebhookView(APIView):
    """Signature-authenticated; no session/JWT auth (gateways aren't users)."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request, gateway=None):
        name = (gateway or request.query_params.get("gateway") or "").upper()
        if name not in SUPPORTED_GATEWAYS:
            return Response({"detail": "Unknown gateway."}, status=status.HTTP_400_BAD_REQUEST)
        headers = {k: v for k, v in request.headers.items()}
        try:
            result = services.handle_webhook(name, request.body, headers)
        except WebhookVerificationError as exc:
            log.warning("Rejected %s webhook: %s", name, exc)
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except GatewayError as exc:
            log.warning("Gateway error on %s webhook: %s", name, exc)
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(result)


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Invoice.objects.filter(user=self.request.user)
            .prefetch_related("payments")
            .order_by("-created_at")
        )


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by("-created_at")


class ValidateCouponView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        code = (request.query_params.get("code") or "").strip()
        plan_slug = request.query_params.get("plan")
        coupon = Coupon.objects.filter(code=code).first()
        plan = Plan.objects.filter(slug=plan_slug).first() if plan_slug else None
        if not coupon or not coupon.is_valid(plan):
            return Response({"valid": False})
        preview = None
        if plan:
            q = services.quote(plan, coupon)
            preview = {
                "subtotal": str(q.subtotal),
                "discount": str(q.discount),
                "total": str(q.total),
                "currency": q.currency,
            }
        return Response({"valid": True, "coupon": CouponSerializer(coupon).data, "preview": preview})


class RefundView(APIView):
    permission_classes = [IsAuthenticated, IsBillingAdmin]

    def post(self, request):
        serializer = RefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payment = get_object_or_404(Payment, id=data["payment_id"])
        try:
            services.refund_payment(
                payment,
                amount=data.get("amount"),
                also_cancel=data.get("cancel_subscription", False),
            )
        except GatewayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        payment.refresh_from_db()
        return Response(PaymentSerializer(payment).data)


class RevenueAnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsBillingAdmin]

    def get(self, request):
        return Response(analytics.overview())
