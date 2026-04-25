from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import random
import uuid

from database import db

ORDER_STATUS_FLOW = [
    "order_placed",
    "payment_confirmed",
    "processing",
    "shipped",
    "out_for_delivery",
    "delivered",
]

ORDER_STATUS_LABELS = {
    "order_placed": "Order Placed",
    "payment_confirmed": "Payment Confirmed",
    "processing": "Processing",
    "shipped": "Shipped",
    "out_for_delivery": "Out for Delivery",
    "delivered": "Delivered",
    "payment_failed": "Payment Failed",
}

ORDER_EVENT_MAP = {
    "order_placed": "order_created",
    "payment_confirmed": "payment_confirmed",
    "processing": "order_processing",
    "shipped": "order_shipped",
    "out_for_delivery": "order_out_for_delivery",
    "delivered": "order_delivered",
    "payment_failed": "payment_failed",
}

PAYMENT_SCENARIO_TIMINGS = {
    "success": {
        "payment_updates": [("success", 10)],
        "order_updates": [
            ("payment_confirmed", 10),
            ("processing", 20),
            ("shipped", 40),
            ("out_for_delivery", 70),
            ("delivered", 100),
        ],
    },
    "pending": {
        "payment_updates": [("pending", 5), ("success", 25)],
        "order_updates": [
            ("payment_confirmed", 25),
            ("processing", 35),
            ("shipped", 55),
            ("out_for_delivery", 85),
            ("delivered", 115),
        ],
    },
    "failed": {
        "payment_updates": [("failed", 10)],
        "order_updates": [("payment_failed", 10)],
    },
}

STATUS_CHAIN_DELAYS = {
    "order_placed": [("payment_confirmed", 10), ("processing", 20), ("shipped", 40), ("out_for_delivery", 70), ("delivered", 100)],
    "payment_confirmed": [("processing", 10), ("shipped", 30), ("out_for_delivery", 60), ("delivered", 90)],
    "processing": [("shipped", 20), ("out_for_delivery", 50), ("delivered", 80)],
    "shipped": [("out_for_delivery", 30), ("delivered", 60)],
    "out_for_delivery": [("delivered", 30)],
    "delivered": [],
    "payment_failed": [],
}

NOTIFICATION_TEMPLATE_MAP = {
    "order_created": "order_confirmation",
    "payment_confirmed": "payment_status",
    "payment_failed": "payment_status",
    "order_shipped": "shipping_update",
    "order_out_for_delivery": "out_for_delivery",
    "order_delivered": "delivery_complete",
}

CALL_SCENARIO_TONES = {
    "cart_abandonment": "persuasive",
    "product_interest": "informative",
    "order_update": "professional",
    "post_delivery_followup": "friendly",
}


def utc_now() -> datetime:
    return datetime.utcnow().replace(microsecond=0)


def to_iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat()


def parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if not value:
        return utc_now()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return utc_now()
    return utc_now()


class CommerceSimulationService:
    def __init__(self):
        self._database = db

    @property
    def mongo(self):
        return self._database.db

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    def _build_order_timeline_entry(
        self,
        status: str,
        description: str,
        source: str = "system",
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        timestamp = created_at or utc_now()
        return {
            "status": status,
            "label": ORDER_STATUS_LABELS.get(status, status.replace("_", " ").title()),
            "description": description,
            "source": source,
            "metadata": metadata or {},
            "created_at": to_iso(timestamp),
        }

    def _build_payment_timeline_entry(
        self,
        status: str,
        description: str,
        source: str = "system",
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        timestamp = created_at or utc_now()
        return {
            "status": status,
            "description": description,
            "source": source,
            "metadata": metadata or {},
            "created_at": to_iso(timestamp),
        }

    def _build_scheduled_transitions(self, scenario: str, created_at: datetime) -> List[Dict[str, Any]]:
        config = PAYMENT_SCENARIO_TIMINGS.get(scenario, PAYMENT_SCENARIO_TIMINGS["success"])
        return [
            {
                "transition_id": self._new_id("ordtr"),
                "target_status": status,
                "due_at": to_iso(created_at + timedelta(seconds=offset)),
                "processed_at": None,
            }
            for status, offset in config["order_updates"]
        ]

    def _build_payment_updates(self, scenario: str, created_at: datetime) -> List[Dict[str, Any]]:
        config = PAYMENT_SCENARIO_TIMINGS.get(scenario, PAYMENT_SCENARIO_TIMINGS["success"])
        return [
            {
                "update_id": self._new_id("payup"),
                "target_status": status,
                "due_at": to_iso(created_at + timedelta(seconds=offset)),
                "processed_at": None,
            }
            for status, offset in config["payment_updates"]
        ]

    def _build_tracking_number(self, order_number: str) -> str:
        suffix = order_number.replace("ORD-", "")
        return f"SIM-{suffix[:4]}-{random.randint(100000, 999999)}"

    def _resolve_checkout_items(self, user_id: str, request_items: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        cart_items = db.get_user_cart(user_id)
        if cart_items:
            resolved = []
            request_lookup = {
                f"{item.get('product_id')}::{item.get('size', '')}::{item.get('color', '')}": item
                for item in (request_items or [])
            }
            for item in cart_items:
                fallback = request_lookup.get(
                    f"{item.get('product_id')}::{item.get('size', '')}::{item.get('color', '')}"
                ) or next(
                    (
                        request_item
                        for request_item in (request_items or [])
                        if str(request_item.get("product_id")) == str(item.get("product_id"))
                    ),
                    None,
                )
                resolved.append(
                    {
                        "product_id": item["product_id"],
                        "product_name": item["product"]["product_name"],
                        "quantity": item["quantity"],
                        "price": item["product"]["price"],
                        "size": item.get("size") or (fallback or {}).get("size"),
                        "color": item.get("color") or (fallback or {}).get("color"),
                    }
                )
            return resolved

        resolved_items: List[Dict[str, Any]] = []
        for item in request_items or []:
            try:
                product_id = int(item.get("product_id"))
            except (TypeError, ValueError):
                continue
            product = db.get_product(product_id)
            if not product:
                continue
            resolved_items.append(
                {
                    "product_id": product_id,
                    "product_name": item.get("product_name") or product.get("product_name"),
                    "quantity": int(item.get("quantity", 1)),
                    "price": float(item.get("price", product.get("price", 0))),
                    "size": item.get("size"),
                    "color": item.get("color"),
                }
            )
        return resolved_items

    def _calculate_totals(self, items: List[Dict[str, Any]]) -> Dict[str, float]:
        subtotal = round(sum(float(item["price"]) * int(item["quantity"]) for item in items), 2)
        tax_amount = round(subtotal * 0.08, 2)
        shipping_amount = 0 if subtotal >= 100 else 9.99
        discount_amount = 0.0
        final_amount = round(subtotal + tax_amount + shipping_amount - discount_amount, 2)
        return {
            "total_amount": subtotal,
            "tax_amount": tax_amount,
            "shipping_amount": shipping_amount,
            "discount_amount": discount_amount,
            "final_amount": final_amount,
        }

    def _build_event(
        self,
        event_type: str,
        user_id: Optional[str],
        payload: Optional[Dict[str, Any]] = None,
        order_number: Optional[str] = None,
        payment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = utc_now()
        return {
            "event_id": self._new_id("evt"),
            "event_type": event_type,
            "user_id": user_id,
            "order_number": order_number,
            "payment_id": payment_id,
            "payload": payload or {},
            "created_at": to_iso(now),
        }

    def _emit_event(
        self,
        event_type: str,
        user_id: Optional[str],
        payload: Optional[Dict[str, Any]] = None,
        order_number: Optional[str] = None,
        payment_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        event = self._build_event(event_type, user_id, payload, order_number, payment_id)
        self.mongo.commerce_events.insert_one(event)
        self._dispatch_event_side_effects(event)
        return event

    def _notification_message(self, event_type: str, order: Optional[Dict[str, Any]], payment: Optional[Dict[str, Any]]) -> str:
        order_number = (order or {}).get("order_number", "your order")
        if event_type == "order_created":
            return f"Your order {order_number} has been placed successfully. We will keep you posted on every milestone."
        if event_type == "payment_confirmed":
            amount = (payment or {}).get("amount", (order or {}).get("final_amount", 0))
            return f"Payment for {order_number} is confirmed. Amount charged: ${amount:.2f}."
        if event_type == "payment_failed":
            return f"Payment for {order_number} did not go through. You can retry from your account."
        if event_type == "order_shipped":
            tracking = ((order or {}).get("fulfillment") or {}).get("tracking_number") or (order or {}).get("tracking_number")
            return f"Your order {order_number} has shipped. Tracking number: {tracking or 'will be assigned soon'}."
        if event_type == "order_out_for_delivery":
            return f"Your order {order_number} is out for delivery today."
        if event_type == "order_delivered":
            return f"Your order {order_number} has been delivered. We hope you love it."
        return f"Update for {order_number}: {event_type.replace('_', ' ').title()}."

    def _build_call_script(
        self,
        scenario: str,
        user: Optional[Dict[str, Any]] = None,
        order: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        first_name = (user or {}).get("first_name") or "there"
        order_number = (order or {}).get("order_number", "your order")
        product_name = (metadata or {}).get("product_name", "the item you viewed")
        if scenario == "cart_abandonment":
            return (
                f"Hi {first_name}, this is ABFRL support. We noticed you left items in your cart. "
                "If you have any questions about fit, delivery, or payment, I can help and make checkout easier."
            )
        if scenario == "product_interest":
            return (
                f"Hi {first_name}, this is a quick ABFRL follow-up about {product_name}. "
                "I can share fabric details, sizing help, and delivery timelines if that would help you decide."
            )
        if scenario == "order_update":
            status = (metadata or {}).get("status", (order or {}).get("order_status", "updated"))
            return (
                f"Hi {first_name}, this is an update on {order_number}. "
                f"Your order is now {status.replace('_', ' ')}. Let us know if you need delivery assistance."
            )
        return (
            f"Hi {first_name}, this is ABFRL checking in after delivery of {order_number}. "
            "We'd love to hear how everything went and if there is anything we can improve."
        )

    def _create_notification(
        self,
        user_id: str,
        order_number: Optional[str],
        template_key: str,
        message: str,
        dedupe_key: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if self.mongo.notifications.find_one({"dedupe_key": dedupe_key}):
            return None
        now = utc_now()
        notification = {
            "notification_id": self._new_id("ntf"),
            "user_id": user_id,
            "order_number": order_number,
            "channel": "whatsapp",
            "provider": "openclaw",
            "mode": "simulated",
            "template_key": template_key,
            "message": message,
            "status": "simulated_sent",
            "dedupe_key": dedupe_key,
            "metadata": metadata or {},
            "created_at": to_iso(now),
            "sent_at": to_iso(now),
        }
        self.mongo.notifications.insert_one(notification)
        return notification

    def _create_call_workflow(
        self,
        user_id: str,
        scenario: str,
        script: str,
        dedupe_key: str,
        order_number: Optional[str] = None,
        scheduled_for: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if self.mongo.call_workflows.find_one({"dedupe_key": dedupe_key}):
            return None

        now = utc_now()
        workflow = {
            "call_workflow_id": self._new_id("call"),
            "user_id": user_id,
            "order_number": order_number,
            "scenario": scenario,
            "tone": CALL_SCENARIO_TONES.get(scenario, "professional"),
            "status": "scheduled" if scheduled_for and scheduled_for > now else "ready",
            "script": script,
            "summary": "",
            "transcript": [],
            "dedupe_key": dedupe_key,
            "metadata": metadata or {},
            "scheduled_for": to_iso(scheduled_for or now),
            "created_at": to_iso(now),
            "updated_at": to_iso(now),
        }
        self.mongo.call_workflows.insert_one(workflow)
        return workflow

    def _dispatch_event_side_effects(self, event: Dict[str, Any]) -> None:
        user_id = event.get("user_id")
        if not user_id:
            return

        user = db.get_user_flexible(user_id)
        order = self.get_order(event.get("order_number")) if event.get("order_number") else None
        payment = self.get_payment(event.get("payment_id")) if event.get("payment_id") else None
        event_type = event.get("event_type")

        whatsapp = (user or {}).get("whatsapp_connection") or {}
        if whatsapp.get("status") == "connected" and whatsapp.get("opt_in", True):
            template_key = NOTIFICATION_TEMPLATE_MAP.get(event_type)
            if template_key:
                self._create_notification(
                    user_id=user_id,
                    order_number=event.get("order_number"),
                    template_key=template_key,
                    message=self._notification_message(event_type, order, payment),
                    dedupe_key=f"{event.get('event_id')}:{template_key}",
                    metadata={"event_type": event_type},
                )

        if event_type in {"order_shipped", "order_out_for_delivery"}:
            self._create_call_workflow(
                user_id=user_id,
                scenario="order_update",
                script=self._build_call_script(
                    "order_update",
                    user=user,
                    order=order,
                    metadata={"status": order.get("order_status") if order else event_type},
                ),
                dedupe_key=f"{event.get('event_id')}:order_update",
                order_number=event.get("order_number"),
                metadata={"trigger_event": event_type},
            )

        if event_type == "order_delivered":
            self._create_call_workflow(
                user_id=user_id,
                scenario="post_delivery_followup",
                script=self._build_call_script("post_delivery_followup", user=user, order=order),
                dedupe_key=f"{event.get('event_id')}:post_delivery_followup",
                order_number=event.get("order_number"),
                scheduled_for=utc_now() + timedelta(hours=24),
                metadata={"trigger_event": event_type},
            )

    def get_order(self, order_number: str) -> Optional[Dict[str, Any]]:
        order = self.mongo.orders.find_one({"order_number": order_number})
        if not order:
            return None
        payments = list(self.mongo.payments.find({"order_number": order_number}).sort("created_at", 1))
        order["payments"] = payments
        if "timeline" not in order:
            order["timeline"] = []
        return order

    def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        return self.mongo.payments.find_one({"payment_id": payment_id})

    def list_user_orders(self, user_id: str) -> List[Dict[str, Any]]:
        orders = list(self.mongo.orders.find({"user_id": user_id}).sort("created_at", -1))
        for order in orders:
            order["payments"] = list(self.mongo.payments.find({"order_number": order["order_number"]}).sort("created_at", 1))
        return orders

    def list_admin_orders(self) -> List[Dict[str, Any]]:
        orders = list(self.mongo.orders.find().sort("created_at", -1).limit(100))
        for order in orders:
            order_number = order.get("order_number")
            order["payments"] = list(self.mongo.payments.find({"order_number": order_number}).sort("created_at", 1))
            order["notifications"] = list(self.mongo.notifications.find({"order_number": order_number}).sort("created_at", -1).limit(10))
            order["call_workflows"] = list(self.mongo.call_workflows.find({"order_number": order_number}).sort("created_at", -1).limit(10))
        return orders

    def create_checkout(
        self,
        user_id: str,
        shipping_address: str,
        billing_address: str,
        payment_method: str,
        payment_scenario: str = "success",
        items: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        created_at = utc_now()
        resolved_items = self._resolve_checkout_items(user_id, items)
        if not resolved_items:
            raise ValueError("Cart is empty")

        totals = self._calculate_totals(resolved_items)
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        payment_id = self._new_id("pay")
        user = db.get_user_flexible(user_id)
        order_doc = {
            "order_number": order_number,
            "user_id": user_id,
            "items": resolved_items,
            "shipping_address": shipping_address,
            "billing_address": billing_address,
            "payment_method": payment_method,
            "payment_status": "initiated",
            "latest_payment_id": payment_id,
            "order_status": "order_placed",
            "status": "order_placed",
            "timeline": [
                self._build_order_timeline_entry(
                    "order_placed",
                    "Order received and queued for payment simulation.",
                    source="checkout",
                    created_at=created_at,
                )
            ],
            "scheduled_transitions": self._build_scheduled_transitions(payment_scenario, created_at),
            "simulation": {
                "auto_progress": True,
                "payment_scenario": payment_scenario,
                "created_at": to_iso(created_at),
            },
            "fulfillment": {
                "carrier": "SimShip",
                "tracking_number": None,
                "delivery_eta": None,
            },
            "customer_snapshot": {
                "name": f"{(user or {}).get('first_name', '')} {(user or {}).get('last_name', '')}".strip(),
                "phone": (user or {}).get("phone"),
                "email": (user or {}).get("email"),
            },
            "created_at": to_iso(created_at),
            "updated_at": to_iso(created_at),
            **totals,
        }
        payment_doc = {
            "payment_id": payment_id,
            "order_number": order_number,
            "user_id": user_id,
            "amount": totals["final_amount"],
            "method": payment_method,
            "scenario": payment_scenario,
            "status": "initiated",
            "attempt_number": 1,
            "timeline": [
                self._build_payment_timeline_entry(
                    "initiated",
                    "Payment simulation started.",
                    source="checkout",
                    created_at=created_at,
                )
            ],
            "scheduled_updates": self._build_payment_updates(payment_scenario, created_at),
            "created_at": to_iso(created_at),
            "updated_at": to_iso(created_at),
        }

        self.mongo.orders.insert_one(order_doc)
        self.mongo.payments.insert_one(payment_doc)
        db.clear_user_cart(user_id)
        self.record_user_activity(
            user_id,
            "checkout_started",
            {
                "order_number": order_number,
                "payment_scenario": payment_scenario,
                "payment_method": payment_method,
            },
        )
        self._emit_event("order_created", user_id, {"payment_scenario": payment_scenario}, order_number=order_number)
        self._emit_event("payment_initiated", user_id, {"method": payment_method}, order_number=order_number, payment_id=payment_id)
        return self.get_order(order_number) or order_doc

    def _update_payment_status(self, payment: Dict[str, Any], status: str, source: str = "worker") -> Dict[str, Any]:
        now = utc_now()
        update_fields = {
            "status": status,
            "updated_at": to_iso(now),
        }
        timeline_entry = self._build_payment_timeline_entry(
            status,
            f"Payment moved to {status}.",
            source=source,
            created_at=now,
        )
        self.mongo.payments.update_one(
            {"payment_id": payment["payment_id"]},
            {
                "$set": update_fields,
                "$push": {"timeline": timeline_entry},
            },
        )
        updated = self.get_payment(payment["payment_id"]) or {**payment, **update_fields}
        return updated

    def _update_order_status(
        self,
        order: Dict[str, Any],
        status: str,
        source: str = "worker",
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = utc_now()
        update_fields: Dict[str, Any] = {
            "order_status": status,
            "status": status,
            "updated_at": to_iso(now),
        }
        if status == "shipped":
            tracking_number = ((order.get("fulfillment") or {}).get("tracking_number")) or self._build_tracking_number(order["order_number"])
            update_fields["fulfillment"] = {
                **(order.get("fulfillment") or {}),
                "carrier": "SimShip",
                "tracking_number": tracking_number,
                "delivery_eta": to_iso(now + timedelta(minutes=2)),
            }
            update_fields["tracking_number"] = tracking_number
        elif status == "out_for_delivery":
            update_fields["fulfillment"] = {
                **(order.get("fulfillment") or {}),
                "carrier": (order.get("fulfillment") or {}).get("carrier", "SimShip"),
                "tracking_number": (order.get("fulfillment") or {}).get("tracking_number") or order.get("tracking_number"),
                "delivery_eta": to_iso(now + timedelta(minutes=1)),
            }
        elif status == "delivered":
            update_fields["fulfillment"] = {
                **(order.get("fulfillment") or {}),
                "delivered_at": to_iso(now),
            }

        timeline_entry = self._build_order_timeline_entry(
            status,
            note or f"Order status changed to {ORDER_STATUS_LABELS.get(status, status)}.",
            source=source,
            created_at=now,
        )
        self.mongo.orders.update_one(
            {"order_number": order["order_number"]},
            {
                "$set": update_fields,
                "$push": {"timeline": timeline_entry},
            },
        )
        updated = self.get_order(order["order_number"]) or {**order, **update_fields}
        return updated

    def _mark_payment_update_processed(self, payment_id: str, update_id: str) -> None:
        self.mongo.payments.update_one(
            {"payment_id": payment_id, "scheduled_updates.update_id": update_id},
            {"$set": {"scheduled_updates.$.processed_at": to_iso(utc_now())}},
        )

    def _mark_order_transition_processed(self, order_number: str, transition_id: str) -> None:
        self.mongo.orders.update_one(
            {"order_number": order_number, "scheduled_transitions.transition_id": transition_id},
            {"$set": {"scheduled_transitions.$.processed_at": to_iso(utc_now())}},
        )

    def process_due_simulations(self) -> None:
        self._process_due_payment_updates()
        self._process_due_order_transitions()
        self._process_cart_abandonment_calls()
        self._activate_due_call_workflows()

    def _process_due_payment_updates(self) -> None:
        now = utc_now()
        payments = list(self.mongo.payments.find({"scheduled_updates.processed_at": None}))
        for payment in payments:
            for update in sorted(payment.get("scheduled_updates", []), key=lambda item: item.get("due_at", "")):
                if update.get("processed_at"):
                    continue
                if parse_dt(update.get("due_at")) > now:
                    continue
                updated_payment = self._update_payment_status(payment, update["target_status"])
                self._mark_payment_update_processed(payment["payment_id"], update["update_id"])
                self.mongo.orders.update_one(
                    {"order_number": payment["order_number"]},
                    {"$set": {"payment_status": update["target_status"], "updated_at": to_iso(now)}},
                )
                event_type = "payment_confirmed" if update["target_status"] == "success" else f"payment_{update['target_status']}"
                self._emit_event(
                    event_type,
                    payment["user_id"],
                    {"status": update["target_status"]},
                    order_number=payment["order_number"],
                    payment_id=payment["payment_id"],
                )
                payment = updated_payment

    def _process_due_order_transitions(self) -> None:
        now = utc_now()
        orders = list(self.mongo.orders.find({"scheduled_transitions.processed_at": None}))
        for order in orders:
            for transition in sorted(order.get("scheduled_transitions", []), key=lambda item: item.get("due_at", "")):
                if transition.get("processed_at"):
                    continue
                if parse_dt(transition.get("due_at")) > now:
                    continue
                updated_order = self._update_order_status(
                    order,
                    transition["target_status"],
                    note=f"Simulation advanced the order to {ORDER_STATUS_LABELS.get(transition['target_status'], transition['target_status'])}.",
                )
                self._mark_order_transition_processed(order["order_number"], transition["transition_id"])
                if transition["target_status"] == "payment_confirmed":
                    self.mongo.orders.update_one(
                        {"order_number": order["order_number"]},
                        {"$set": {"payment_status": "success", "updated_at": to_iso(now)}},
                    )
                if transition["target_status"] == "payment_failed":
                    self.mongo.orders.update_one(
                        {"order_number": order["order_number"]},
                        {"$set": {"payment_status": "failed", "updated_at": to_iso(now)}},
                    )
                event_type = ORDER_EVENT_MAP.get(transition["target_status"])
                if event_type:
                    self._emit_event(
                        event_type,
                        order["user_id"],
                        {"status": transition["target_status"]},
                        order_number=order["order_number"],
                        payment_id=order.get("latest_payment_id"),
                    )
                order = updated_order

    def _product_interest_trigger(self, user_id: str, product_id: int) -> None:
        since = to_iso(utc_now() - timedelta(hours=24))
        views = list(
            self.mongo.user_activity.find(
                {
                    "user_id": user_id,
                    "activity_type": "product_view",
                    "product_id": product_id,
                    "created_at": {"$gte": since},
                }
            )
        )
        if len(views) < 3:
            return

        cart_items = db.get_user_cart(user_id)
        if any(item.get("product_id") == product_id for item in cart_items):
            return

        recent_orders = list(
            self.mongo.orders.find(
                {
                    "user_id": user_id,
                    "created_at": {"$gte": since},
                    "items.product_id": product_id,
                }
            )
        )
        if recent_orders:
            return

        product = db.get_product(product_id)
        user = db.get_user_flexible(user_id)
        self._create_call_workflow(
            user_id=user_id,
            scenario="product_interest",
            script=self._build_call_script(
                "product_interest",
                user=user,
                metadata={"product_name": (product or {}).get("product_name", f"Product #{product_id}")},
            ),
            dedupe_key=f"product_interest:{user_id}:{product_id}:{utc_now().date().isoformat()}",
            metadata={"product_id": product_id, "product_name": (product or {}).get("product_name")},
        )

    def _process_cart_abandonment_calls(self) -> None:
        threshold = utc_now() - timedelta(minutes=30)
        carts = list(self.mongo.carts.find({"items.0": {"$exists": True}}))
        for cart in carts:
            user_id = cart.get("user_id")
            if not user_id:
                continue
            last_cart_activity = self.mongo.user_activity.find_one(
                {"user_id": user_id, "activity_type": {"$in": ["cart_add", "cart_update", "cart_remove"]}},
                sort=[("created_at", -1)],
            )
            if not last_cart_activity or parse_dt(last_cart_activity.get("created_at")) > threshold:
                continue
            checkout_after = self.mongo.user_activity.find_one(
                {
                    "user_id": user_id,
                    "activity_type": "checkout_started",
                    "created_at": {"$gte": last_cart_activity.get("created_at")},
                }
            )
            if checkout_after:
                continue

            user = db.get_user_flexible(user_id)
            self._create_call_workflow(
                user_id=user_id,
                scenario="cart_abandonment",
                script=self._build_call_script("cart_abandonment", user=user),
                dedupe_key=f"cart_abandonment:{user_id}:{parse_dt(last_cart_activity.get('created_at')).date().isoformat()}",
                metadata={"cart_items": len(cart.get("items", []))},
            )
            self._emit_event("cart_abandoned", user_id, {"cart_items": len(cart.get("items", []))})

    def _activate_due_call_workflows(self) -> None:
        now = utc_now()
        self.mongo.call_workflows.update_many(
            {"status": "scheduled", "scheduled_for": {"$lte": to_iso(now)}},
            {"$set": {"status": "ready", "updated_at": to_iso(now)}},
        )

    def record_user_activity(self, user_id: str, activity_type: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        now = utc_now()
        activity = {
            "activity_id": self._new_id("act"),
            "user_id": user_id,
            "activity_type": activity_type,
            "product_id": (payload or {}).get("product_id"),
            "order_number": (payload or {}).get("order_number"),
            "metadata": payload or {},
            "created_at": to_iso(now),
        }
        self.mongo.user_activity.insert_one(activity)

        event_type_map = {
            "product_view": "product_viewed",
            "cart_add": "cart_updated",
            "cart_remove": "cart_updated",
            "cart_update": "cart_updated",
            "checkout_started": "checkout_started",
        }
        event_type = event_type_map.get(activity_type)
        if event_type:
            self._emit_event(
                event_type,
                user_id,
                payload or {},
                order_number=(payload or {}).get("order_number"),
            )

        product_id = (payload or {}).get("product_id")
        if activity_type == "product_view" and product_id is not None:
            try:
                self._product_interest_trigger(user_id, int(product_id))
            except (TypeError, ValueError):
                pass

        return activity

    def get_user_activity_summary(self, user_id: str) -> Dict[str, Any]:
        activities = list(self.mongo.user_activity.find({"user_id": user_id}).sort("created_at", -1).limit(20))
        carts = db.get_user_cart(user_id)
        recent_views = [item for item in activities if item.get("activity_type") == "product_view"]
        last_activity = activities[0].get("created_at") if activities else None
        last_cart_activity = next(
            (item for item in activities if item.get("activity_type") in {"cart_add", "cart_remove", "cart_update"}),
            None,
        )
        abandoned_cart = bool(
            carts
            and last_cart_activity
            and parse_dt(last_cart_activity.get("created_at")) <= utc_now() - timedelta(minutes=30)
        )
        grouped_views: Dict[int, int] = {}
        for view in recent_views:
            product_id = view.get("product_id")
            if product_id is None:
                continue
            grouped_views[int(product_id)] = grouped_views.get(int(product_id), 0) + 1
        return {
            "last_activity_at": last_activity,
            "recent_activities": activities,
            "abandoned_cart": abandoned_cart,
            "cart_item_count": len(carts),
            "top_product_views": [
                {"product_id": product_id, "view_count": count}
                for product_id, count in sorted(grouped_views.items(), key=lambda item: item[1], reverse=True)[:5]
            ],
        }

    def get_user_communications(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        notifications = list(self.mongo.notifications.find({"user_id": user_id}).sort("created_at", -1).limit(50))
        call_workflows = list(self.mongo.call_workflows.find({"user_id": user_id}).sort("created_at", -1).limit(50))
        return {
            "notifications": notifications,
            "call_workflows": call_workflows,
        }

    def update_whatsapp_connection(
        self,
        user_id: str,
        phone_number: Optional[str],
        connected: bool,
        opt_in: bool = True,
    ) -> Optional[Dict[str, Any]]:
        from bson import ObjectId

        now = utc_now()
        connection = {
            "provider": "openclaw",
            "mode": "simulated",
            "status": "connected" if connected else "disconnected",
            "phone_number": phone_number,
            "opt_in": opt_in,
            "connected_at": to_iso(now) if connected else None,
            "updated_at": to_iso(now),
        }
        try:
            self.mongo.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "whatsapp_connection": connection,
                        "updated_at": to_iso(now),
                    }
                },
            )
        except Exception:
            return None

        self._emit_event(
            "whatsapp_connected" if connected else "whatsapp_disconnected",
            user_id,
            {"phone_number": phone_number, "opt_in": opt_in},
        )
        return db.get_user_by_id(user_id)

    def advance_order(
        self,
        order_number: str,
        target_status: str,
        note: Optional[str] = None,
        source: str = "admin",
    ) -> Optional[Dict[str, Any]]:
        order = self.get_order(order_number)
        if not order:
            return None

        now = utc_now()
        updated_order = self._update_order_status(order, target_status, source=source, note=note or "Manual simulation override applied.")

        if target_status == "payment_failed":
            self.mongo.orders.update_one({"order_number": order_number}, {"$set": {"payment_status": "failed"}})
        elif target_status in ORDER_STATUS_FLOW[1:]:
            self.mongo.orders.update_one({"order_number": order_number}, {"$set": {"payment_status": "success"}})

        remaining = [
            {
                "transition_id": self._new_id("ordtr"),
                "target_status": status,
                "due_at": to_iso(now + timedelta(seconds=delay)),
                "processed_at": None,
            }
            for status, delay in STATUS_CHAIN_DELAYS.get(target_status, [])
        ]
        self.mongo.orders.update_one(
            {"order_number": order_number},
            {"$set": {"scheduled_transitions": remaining, "updated_at": to_iso(now)}},
        )
        event_type = ORDER_EVENT_MAP.get(target_status)
        if event_type:
            self._emit_event(
                event_type,
                updated_order["user_id"],
                {"status": target_status, "source": source},
                order_number=order_number,
                payment_id=updated_order.get("latest_payment_id"),
            )
        return self.get_order(order_number)

    def retry_payment(
        self,
        order_number: str,
        payment_id: str,
        scenario: str = "success",
    ) -> Optional[Dict[str, Any]]:
        order = self.get_order(order_number)
        payment = self.get_payment(payment_id)
        if not order or not payment:
            return None

        now = utc_now()
        new_payment_id = self._new_id("pay")
        attempt_number = int(payment.get("attempt_number", 1)) + 1
        new_payment = {
            "payment_id": new_payment_id,
            "order_number": order_number,
            "user_id": order["user_id"],
            "amount": order.get("final_amount", 0),
            "method": payment.get("method", order.get("payment_method", "card")),
            "scenario": scenario,
            "status": "initiated",
            "attempt_number": attempt_number,
            "retry_of": payment_id,
            "timeline": [
                self._build_payment_timeline_entry(
                    "initiated",
                    "Payment retry simulation started.",
                    source="admin",
                    created_at=now,
                )
            ],
            "scheduled_updates": self._build_payment_updates(scenario, now),
            "created_at": to_iso(now),
            "updated_at": to_iso(now),
        }
        self.mongo.payments.insert_one(new_payment)
        self.mongo.orders.update_one(
            {"order_number": order_number},
            {
                "$set": {
                    "latest_payment_id": new_payment_id,
                    "payment_status": "initiated",
                    "order_status": "order_placed",
                    "status": "order_placed",
                    "scheduled_transitions": self._build_scheduled_transitions(scenario, now),
                    "updated_at": to_iso(now),
                },
                "$push": {
                    "timeline": self._build_order_timeline_entry(
                        "order_placed",
                        "Payment retry requested. Order moved back to waiting for payment confirmation.",
                        source="admin",
                        created_at=now,
                    )
                },
            },
        )
        self._emit_event(
            "payment_retry_initiated",
            order["user_id"],
            {"new_payment_id": new_payment_id, "retry_of": payment_id, "scenario": scenario},
            order_number=order_number,
            payment_id=new_payment_id,
        )
        return self.get_order(order_number)

    def get_order_timeline(self, order_number: str) -> List[Dict[str, Any]]:
        order = self.get_order(order_number)
        if not order:
            return []
        return order.get("timeline", [])

    def get_latest_order_context(self, user_id: str) -> Dict[str, Any]:
        order = self.mongo.orders.find_one({"user_id": user_id}, sort=[("created_at", -1)])
        if not order:
            return {}
        payment = None
        if order.get("latest_payment_id"):
            payment = self.get_payment(order["latest_payment_id"])
        return {
            "latest_order": self.get_order(order["order_number"]),
            "latest_payment": payment,
        }

    def get_chatbot_context(self, user_id: str) -> Dict[str, Any]:
        latest = self.get_latest_order_context(user_id)
        activity_summary = self.get_user_activity_summary(user_id)
        communications = self.get_user_communications(user_id)
        cart = db.get_user_cart(user_id)
        journey = "pre_order"
        if latest.get("latest_order"):
            journey = "post_order"
        elif activity_summary.get("abandoned_cart"):
            journey = "abandoned_cart"
        elif cart:
            journey = "active_cart"

        return {
            **latest,
            "activity_summary": activity_summary,
            "communications": communications,
            "cart_snapshot": cart,
            "journey": journey,
        }

    def maybe_build_chatbot_reply(self, user_id: Optional[str], message: str) -> Optional[str]:
        if not user_id:
            return None

        context = self.get_chatbot_context(user_id)
        lower = message.lower()
        latest_order = context.get("latest_order")
        latest_payment = context.get("latest_payment")
        activity_summary = context.get("activity_summary", {})
        cart_snapshot = context.get("cart_snapshot", [])

        if any(trigger in lower for trigger in ["where is my order", "track my order", "order status", "track order"]):
            if not latest_order:
                return "You do not have any orders yet. I can help you check out the items in your cart if you would like."
            tracking = ((latest_order.get("fulfillment") or {}).get("tracking_number")) or latest_order.get("tracking_number")
            return (
                f"Your latest order {latest_order['order_number']} is currently {latest_order.get('order_status', 'order_placed').replace('_', ' ')}. "
                f"Payment is {latest_order.get('payment_status', 'initiated')}. "
                f"{'Tracking number: ' + tracking + '. ' if tracking else ''}"
                "You can also review the full timeline in your orders page."
            )

        if any(trigger in lower for trigger in ["delivery", "when will it arrive", "out for delivery", "shipped"]):
            if not latest_order:
                return "I could not find an active delivery for your account yet."
            eta = ((latest_order.get("fulfillment") or {}).get("delivery_eta"))
            return (
                f"Your latest order {latest_order['order_number']} is {latest_order.get('order_status', 'order_placed').replace('_', ' ')}. "
                f"{'Current estimated delivery time is ' + eta + '. ' if eta else ''}"
                "I can also summarize the full status history if you want."
            )

        if any(trigger in lower for trigger in ["payment", "charged", "payment status", "transaction"]):
            if not latest_payment and not latest_order:
                return "I could not find a recent payment on your account yet."
            payment_status = (latest_payment or {}).get("status") or (latest_order or {}).get("payment_status", "initiated")
            return (
                f"Your latest payment status is {payment_status}. "
                f"{'Method: ' + str((latest_payment or {}).get('method')) + '. ' if latest_payment else ''}"
                f"{'Amount: $' + format(float((latest_payment or {}).get('amount', 0)), '.2f') + '. ' if latest_payment else ''}"
                "If it failed, you can retry it from the order controls."
            )

        if any(trigger in lower for trigger in ["abandoned cart", "my cart", "left in cart"]) and cart_snapshot:
            return (
                f"You currently have {len(cart_snapshot)} item(s) in your cart. "
                f"{'The cart looks abandoned based on inactivity, and a follow-up call may be queued. ' if activity_summary.get('abandoned_cart') else ''}"
                "If you want, I can help you check out or answer product questions before you purchase."
            )

        if "post delivery" in lower or "feedback" in lower:
            workflows = context.get("communications", {}).get("call_workflows", [])
            delivered_followups = [wf for wf in workflows if wf.get("scenario") == "post_delivery_followup"]
            if delivered_followups:
                return "A post-delivery follow-up workflow is already prepared for your account. You can review it from the voice console."
            return None

        return None


commerce_service = CommerceSimulationService()
