from logging import getLogger

from flask import request, render_template

import stripe
import os
from decimal import Decimal, Rounded, localcontext

from service.db import db_session
from shop.models import TransactionContent, TransactionAction, PENDING, Action, Transaction, COMPLETED
from typing import Set, List, Dict, Any, Tuple
from datetime import datetime
from dateutil import parser
from werkzeug.exceptions import HTTPException, NotFound
from dataclasses import dataclass


logger = getLogger('makeradmin')


#instance = backend_service.create(name="webshop", url="webshop", port=80, version="1.0")

# stripe.api_key = os.environ["STRIPE_PRIVATE_KEY"]
# stripe_signing_secret = os.environ["STRIPE_SIGNING_SECRET"]

# All stripe calculations are done with cents (ören in Sweden)
stripe_currency_base = 100
currency = "sek"


def pending_actions(member_id=None):
    """
    Finds every item in a transaction and checks the actions it has, then checks to see if all those actions have been completed (and are not deleted).
    The actions that are valid for a transaction are precisely those that existed at the time the transaction was made. Therefore if an action is added to a product
    in the future, that action will *not* be retroactively applied to all existing transactions.
    """

    query = (
        db_session
        .query(TransactionAction, Action, TransactionContent, Transaction)
        .join(Action)
        .join(TransactionContent)
        .join(Transaction)
        .filter(TransactionAction.status == PENDING)
        .filter(Transaction.status == COMPLETED)
    )

    if member_id:
        query = query.filter(Transaction.member_id == member_id)
    
    return [
        {
            "item": {
                "id": content.id,
                "transaction_id": content.transaction_id,
                "product_id": content.product_id,
                "count": content.count,
                "amount": str(content.amount),
            },
            "action": {
                "id": action_type.id,
                "name": action_type.name,
            },
            "pending_action": {
                "id": action.id,
                "value": action.value,
            },
            "member_id": transaction.member_id,
            "created_at": transaction.created_at.isoformat(),
        } for action, action_type, content, transaction in query.all()
    ]

# @instance.route("transaction/<int:id>/content", methods=["GET"], permission="webshop")
# @route_helper
# def transaction_contents(id: int) -> List[Dict]:
#     '''
#     Return all content related to a transaction
#     '''
# 
#     with db.cursor() as cur:
#         cur.execute("""
#             SELECT webshop_transaction_contents.id AS content_id, webshop_products.name AS product_name,
#                    webshop_products.id AS product_id, webshop_transaction_contents.count, webshop_transaction_contents.amount
#             FROM webshop_transaction_contents
#             INNER JOIN webshop_products ON webshop_products.id = webshop_transaction_contents.product_id
#             WHERE  webshop_transaction_contents.transaction_id = %s
#             """, id)
#         return [
#             {
#                 "content_id": v[0],
#                 "product_name": v[1],
#                 "product_id": v[2],
#                 "count": v[3],
#                 "amount": str(v[4]),
#             } for v in cur.fetchall()
#         ]
# 
# 
# @instance.route("transaction/<int:id>/actions", methods=["GET"], permission="webshop")
# @route_helper
# def transaction_actions(id: int) -> List[Dict[str,Any]]:
#     '''
#     Return all actions related to a transaction
#     '''
# 
#     with db.cursor() as cur:
#         cur.execute("""
#             SELECT webshop_actions.id AS action_id, webshop_actions.name AS action, 
#                     webshop_transaction_contents.id AS content_id, webshop_transaction_actions.value, webshop_transaction_actions.status, webshop_transaction_actions.completed_at
#             FROM webshop_transaction_contents
#             INNER JOIN webshop_transaction_actions ON webshop_transaction_actions.content_id = webshop_transaction_contents.id
#             INNER JOIN webshop_actions ON webshop_actions.id = webshop_transaction_actions.action_id
#             WHERE webshop_transaction_contents.transaction_id = %s
#             """, id)
#         return [
#             {
#                 "action_id": v[0],
#                 "action": v[1],
#                 "content_id": v[2],
#                 "value": v[3],
#                 "status": v[4],
#                 "completed_at": format_datetime(v[5]),
#             } for v in cur.fetchall()
#         ]
# 
# 
# @instance.route("transaction/<int:id>/events", methods=["GET"], permission="webshop")
# @route_helper
# def transaction_events(id: int):
#     return transaction_content_entity.list("transaction_id=%s", id)
# 
# 
# @instance.route("transactions_extended_info", methods=["GET"], permission="webshop")
# @route_helper
# def list_orders():
#     with db.cursor() as cur:
#         cur.execute("""
#             SELECT
#                 webshop_transactions.id AS id,
#                 webshop_transactions.member_id AS member_id,
#                 webshop_transactions.status AS status,
#                 webshop_transactions.amount AS amount,
#                 DATE_FORMAT(webshop_transactions.created_at, '%Y-%m-%dT%H:%i:%sZ') AS created_at,
#                 membership_members.firstname AS firstname,
#                 membership_members.lastname AS lastname,
#                 membership_members.member_number AS member_number,
#                 membership_members.deleted_at
#             FROM webshop_transactions
#             INNER JOIN membership_members ON membership_members.member_id = webshop_transactions.member_id
#             """)
#         return [
#             {
#                 "id": v[0],
#                 "member_id": v[1],
#                 "status": v[2],
#                 "amount": str(v[3]),
#                 "created_at": v[4],
#                 "member_name": f"{v[5]} {v[6]}" if not v[8] else "Unknown member",
#                 "member_number": v[7] if not v[8] else None,
#             } for v in cur.fetchall()
#         ]
#     return []
# 
# 
# @instance.route("member/current/transactions", methods=["GET"], permission='user')
# @route_helper
# def member_history() -> Dict[str, Any]:
#     '''
#     Helper for listing the full transaction history of a member, with product info included.
#     '''
#     user_id = assert_get(request.headers, "X-User-Id")
# 
#     transactions = transaction_entity.list("member_id=%s", user_id)
#     transactions.reverse()
#     for tr in transactions:
#         items = transaction_content_entity.list("transaction_id=%s", tr["id"])
#         for item in items:
#             item["product"] = product_entity.get(item["product_id"])
# 
#         tr["content"] = items
# 
#     return transactions
# 
# 
# def copy_dict(source: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
#     return {key: source[key] for key in fields if key in source}
# 
# 
# def send_new_member_email(member_id: int) -> None:
#     eprint("====== Getting member")
#     r = instance.gateway.get(f"membership/member/{member_id}")
#     assert r.ok
#     member = r.json()["data"]
#     eprint("====== Generating email body")
#     email_body = render_template("new_member_email.html", member=member, public_url=instance.gateway.get_public_url)
#     eprint("====== Sending new member email")
# 
#     r = instance.gateway.post("messages/message", {
#         "recipients": [
#             {
#                 "type": "member",
#                 "id": member_id
#             },
#         ],
#         "message_type": "email",
#         "title": "Välkommen till Stockholm Makerspace",
#         "description": email_body
#     })
# 
#     if not r.ok:
#         eprint("Failed to send new member email")
#         eprint(r.text)
#     eprint("====== Sent email body")
# 
# 
# @instance.route("register", methods=["POST"], permission=None)
# @route_helper
# def register() -> Dict[str, int]:
#     ''' Register a new member.
#         See frontend.py:register_member
#     '''
# 
#     data = request.get_json()
#     if data is None:
#         raise errors.MissingJson()
# 
#     products = membership_products(db)
# 
#     purchase = assert_get(data, "purchase")
#     if len(purchase["cart"]) != 1:
#         raise errors.CartMustContainNItems(1)
#     item = purchase["cart"][0]
#     if item["count"] != 1:
#         raise errors.CartMustContainNItems(1)
#     if "id" not in item:
#         abort(400, "Missing parameter 'id' on item in cart")
#     if item["id"] not in (p["id"] for p in products):
#         raise errors.NotAllowedToPurchase(item)
# 
#     # Register the new member.
#     # We need to copy the member info for security reasons.
#     # Otherwise an attacker could inject evil inputs like for example the 'groups' field which is a list of groups the member should be added to.
#     # It would be quite a security risk if the member could add itself to the admins group when registering.
#     valid_member_fields = [
#         "email", "firstname", "lastname", "civicregno", "company",
#         "orgno", "address_street", "address_extra", "address_zipcode", "address_city", "address_country", "phone"
#     ]
#     member = copy_dict(assert_get(data, "member"), valid_member_fields)
#     member["validate_only"] = True
#     # Disabled create deleted (possibly temporarily) since it prevents user from log in and see receipt.
#     # member["create_deleted"] = True
#     r = instance.gateway.post("membership/member", member)
#     if not r.ok:
#         data = r.json()
#         if r.status_code == 422 and data['what'] == 'not_unique' and data['fields'] == 'email':
#             raise errors.RegisterEmailAlreadyExists()
#         abort(r.status_code, data["message"])
# 
#     member = r.json()["data"]
#     member_id = member["member_id"]
# 
#     # Construct the purchase object again, using user data is always risky
#     purchase = {
#         "cart": [
#             {
#                 "id": item["id"],
#                 "count": 1
#             }
#         ],
#         "expectedSum": purchase["expectedSum"],
#         "stripeSource": purchase["stripeSource"],
#         "stripeThreeDSecure": purchase["stripeThreeDSecure"],
#         "duplicatePurchaseRand": purchase["duplicatePurchaseRand"],
#     }
# 
#     # Note this will throw if the payment fails
#     result = pay(member_id=member_id, data=purchase, activates_member=True)
# 
#     # If the pay succeeded (not same as the payment is completed) and the member does not already exists,
#     # the user will be logged in.
#     response = instance.gateway.post("oauth/force_token", {"user_id": member_id}).json()
#     result['token'] = response["access_token"]
# 
#     return result
# 
# 
# def complete_transaction(transaction_id: int):
#     tr = transaction_entity.get(transaction_id)
#     if tr['status'] == 'pending':
#         tr["status"] = "completed"
#         transaction_entity.put(tr, transaction_id)
#         try:
#             # Unclear if this is a performance issue or not, hopefully there shouldn't be that many pending actions, so this will be quick
#             ship_orders(labaccess=False)
#         except Exception as e:
#             logger.exception(f"failed to ship orders in transaction {transaction_id}")
#     elif tr['status'] not in {'completed'}:
#         logger.error(f"unable to set transaction {transaction_id} to completed")
# 
# 
# def _fail_transaction(transaction_id: int) -> None:
#     with db.cursor() as cur:
#         affected_rows = cur.execute("UPDATE webshop_transactions AS tt SET tt.status = 'failed' WHERE tt.status = 'pending' AND tt.id = %s", (transaction_id,))
#         if affected_rows != 1:
#             eprint(f"Unable to set transaction {transaction_id} to failed!")
# 
# 
# def fail_transaction(transaction_id: int, error_code: int, reason: str) -> None:
#     _fail_transaction(transaction_id)
#     abort(error_code, reason)
# 
# 
# def _fail_stripe_source(source_id: str) -> None:
#     with db.cursor() as cur:
#         affected_rows = cur.execute(
#             "UPDATE webshop_transactions AS tt INNER JOIN webshop_stripe_pending AS sp ON tt.id = sp.transaction_id SET tt.status = 'failed' WHERE sp.stripe_token = %s and tt.status = 'pending'", (source_id,))
#         if affected_rows != 1:
#             eprint(f"Unable to set status to 'failed' for transaction corresponding to source {source_id}")
# 
# 
# def fail_stripe_source(source_id: str, error_code: int, reason: str) -> None:
#     _fail_stripe_source(source_id)
#     abort(error_code, reason)
# 
# 
# def source_to_transaction_id(source_id: str) -> int:
#     with db.cursor() as cur:
#         cur.execute("SELECT transaction_id FROM webshop_transactions INNER JOIN webshop_stripe_pending ON webshop_transactions.id=webshop_stripe_pending.transaction_id WHERE webshop_stripe_pending.stripe_token=%s", (source_id,))
#         return cur.fetchone()
# 
# 
# def stripe_handle_source_callback(subtype: str, event) -> None:
#     if subtype in ["chargeable", "failed", "canceled"]:
#         source = event.data.object
#         transaction_id = source_to_transaction_id(source.id)
#         if transaction_id is None:
#             logger.info(f"Got callback, but no transaction exists for that token ({source.id}). Ignoring this event (this is usually fine)")
#             return None
# 
#         if subtype == "chargeable":
#             # Asynchronous charge should only be initiated from a 3D Secure source
#             if source.type == 'three_d_secure':
#                 # Payment should happen now
#                 try:
#                     create_stripe_payment(transaction_id, source.id)
#                 except Exception as e:
#                     logger.error(f"Error in create_stripe_payment: {str(e)}. Source '{source.id}' for transaction {transaction_id}")
#             elif source.type == 'card':
#                 # All 'card' type sources that should be charged are handled synchonously, not here.
#                 return None
#             else:
#                 # Unknown source type, log and do nothing
#                 logger.warning(f'Unexpected source type {source.type} in stripe webhook: {source}')
#                 return None
#         else:
#             # Payment failed
#             logger.info("Mark transaction as failed")
#             _fail_transaction(transaction_id)
# 
# 
# def stripe_handle_charge_callback(subtype: str, event) -> None:
#     charge = event.data.object
#     if subtype == 'succeeded':
#         transaction_id = source_to_transaction_id(charge.source.id)
#         if transaction_id is None:
#             abort(400, f"Unknown charge '{charge.id}' succeeded, no transaction found for charge source '{charge.source.id}'!")
#         else:
#             handle_payment_success(transaction_id)
#     elif subtype == 'failed':
#         _fail_stripe_source(charge.source.id)
#         logger.info(f"Charge '{charge.id}' failed with message '{charge.failure_message}'")
#     elif subtype.startswith('dispute'):
#         # todo: log disputes for display in admin frontend.
#         pass
#     elif subtype.startswith('refund'):
#         # todo: log refund for display in admin frontend.
#         # todo: option in frontend to roll back actions.
#         pass
# 
# 
# @instance.route("stripe_callback", methods=["POST"], permission=None)
# @route_helper
# def stripe_callback() -> None:
#     payload = request.data
#     eprint("Headers: " + str(request.headers))
#     sig_header = request.headers['Stripe-Signature']
# 
#     try:
#         event = stripe.Webhook.construct_event(payload, sig_header, stripe_signing_secret)
#     except ValueError as e:
#         # Invalid payload
#         abort(400)
#     except stripe.error.SignatureVerificationError as e:
#         # Invalid signature
#         abort(400)
# 
#     eprint(f"Received stripe callback of type {event.type}")
#     (event_type, event_subtype) = tuple(event.type.split('.', 1))
#     if event_type == 'source':
#         stripe_handle_source_callback(event_subtype, event)
#     elif event_type == 'charge':
#         stripe_handle_charge_callback(event_subtype, event)
# 
# 
# def _reprocess_stripe_event(event) -> None:
#     try:
#         logger.info(f"Processing stripe event of type {event.type}")
#         (event_type, event_subtype) = tuple(event.type.split('.', 1))
#         if event_type == 'source':
#             stripe_handle_source_callback(event_subtype, event)
#         elif event_type == 'charge':
#             stripe_handle_charge_callback(event_subtype, event)
#     except HTTPException as e:
#         # Catch and ignore all event processing errors
#         pass
# 
# 
# @instance.route("process_stripe_events", methods=["PUT"])
# @route_helper
# def process_stripe_events() -> None:
#     payload = request.get_json() or {}
#     source_id = payload.get('source_id', None)
#     start = payload.get('start', None)
#     logger.info(f"getting stripe events with start {start} and source_id {source_id}")
#     events = stripe.Event.list(created={'gt': start} if start else None)
#     logger.info(f"got {len(events)} events")
#     for event in events.auto_paging_iter():
#         obj = event.get('data', {}).get('object', {})
#         if source_id and source_id in (obj.get('source', {}).get('id'), obj.get('id')) or not source_id:
#             _reprocess_stripe_event(event)
#         else:
#             logger.info(f"skipping event, not matching source_id")
# 
# 
# def process_cart(member_id: int, cart: List[Dict[str, Any]]) -> Tuple[Decimal, List[CartItem]]:
#     items = []
#     with db.cursor() as cur:
#         with localcontext() as ctx:
#             ctx.clear_flags()
#             total_amount = Decimal(0)
# 
#             for item in cart:
#                 cur.execute("SELECT name,price,smallest_multiple,filter FROM webshop_products WHERE id=%s AND deleted_at IS NULL", item["id"])
#                 tup: Tuple[str, Decimal, int, str] = cur.fetchone()
#                 if tup is None:
#                     raise errors.NoSuchItem(str(item["id"]))
#                 name, price, smallest_multiple, product_filter = tup
# 
#                 if price < 0:
#                     abort(400, "Item seems to have a negatice price. Not allowing purchases that item just in case. Item: " + str(item["id"]))
# 
#                 count = int(item["count"])
#                 if count <= 0:
#                     raise errors.NonNegativeItemCount(str(item["id"]))
#                 if (count % smallest_multiple) != 0:
#                     raise errors.InvalidItemCountMultiple(str(item["id"]), smallest_multiple, count)
# 
#                 item_amount = price * count
#                 cart_item = CartItem(name, item["id"], count, item_amount)
#                 items.append(cart_item)
#                 total_amount += item_amount
# 
#                 if product_filter:
#                     product_filters[product_filter](gateway=instance.gateway, item=cart_item, member_id=member_id)
# 
#             if ctx.flags[Rounded]:
#                 # This can possibly happen with huge values, I suppose they will be caught below anyway but it's good to catch in any case
#                 raise errors.RoundingError()
# 
#     return total_amount, items
# 
# 
# def validate_payment(member_id: int, cart: List[Dict[str, Any]], expected_amount: Decimal) -> Tuple[Decimal, List[CartItem]]:
#     if len(cart) == 0:
#         raise errors.EmptyCart()
# 
#     total_amount, items = process_cart(member_id, cart)
# 
#     # Ensure that the frontend hasn't calculated the amount to pay incorrectly
#     if abs(total_amount - Decimal(expected_amount)) > Decimal("0.01"):
#         raise errors.NonMatchingSums(expected_amount, total_amount)
# 
#     if total_amount > 10000:
#         raise errors.TooLargeAmount(10000)
# 
#     # Assert that the amount can be converted to a valid stripe amount
#     convert_to_stripe_amount(total_amount)
# 
#     return total_amount, items
# 
# 
# def convert_to_stripe_amount(amount: Decimal) -> int:
#     # Ensure that the amount to pay is in whole cents (ören)
#     # This shouldn't be able to fail as all products in the database have prices in cents, but you never know.
#     stripe_amount = amount * stripe_currency_base
#     if (stripe_amount % 1) != 0:
#         raise errors.NotPurelyCents(amount)
# 
#     # The amount is stored as a Decimal, convert it to an int
#     return int(stripe_amount)
# 
# 
# def create_stripe_payment(transaction_id: int, token: str) -> stripe.Charge:
#     transaction = transaction_entity.get(transaction_id)
# 
#     if transaction["status"] != "pending":
#         raise Exception("To complete a payment, it must be currently pending")
# 
#     stripe_amount = convert_to_stripe_amount(Decimal(transaction["amount"]))
# 
#     return stripe.Charge.create(
#         amount=stripe_amount,
#         currency=currency,
#         description=f'Charge for transaction id {transaction_id}',
#         source=token,
#     )
# 
# 
# def handle_payment_success(transaction_id: int) -> None:
#     complete_transaction(transaction_id)
#     transaction = transaction_entity.get(transaction_id)
#     if transaction['status'] != 'completed':
#         eprint(f"handle_payment_success called but transaction marked as '{transaction['status']}', aborting!")
#         return
# 
#     # Check if this transaction is a new member registration
#     if webshop_pending_registrations.list("transaction_id=%s", [transaction_id]):
#         activate_member(transaction["member_id"])
# 
#     eprint("====== Sending receipt email")
#     send_receipt_email(transaction["member_id"], transaction_id)
#     eprint("Payment complete. id: " + str(transaction_id))
# 
# 
# def card_stripe_payment(transaction_id: int, token: str) -> None:
#     try:
#         charge = create_stripe_payment(transaction_id, token)
#         if charge.status == 'succeeded':
#             # Avoid delay of feedback to customer, could be skipped and handled when webhook is called.
#             complete_transaction(transaction_id)
#     except stripe.error.InvalidRequestError as e:
#         if "Amount must convert to at least" in str(e):
#             _fail_transaction(transaction_id)
#             raise errors.TooSmallAmount()
#         else:
#             eprint("Stripe Charge Failed")
#             eprint(e)
#             _fail_transaction(transaction_id)
#             raise errors.PaymentFailed()
#     except stripe.error.CardError as e:
#         body = e.json_body
#         err = body.get('error', {})
#         eprint("Stripe Charge Failed\n" + str(err))
#         _fail_transaction(transaction_id)
#         raise errors.PaymentFailed(err.get("message"))
#     except stripe.error.StripeError as e:
#         eprint("Stripe Charge Failed\n" + str(e))
#         _fail_transaction(transaction_id)
#         raise errors.PaymentFailed()
#     except Exception as e:
#         eprint("Stripe Charge Failed")
#         eprint(e)
#         _fail_transaction(transaction_id)
#         raise errors.PaymentFailed()
# 
# 
# def activate_member(member_id: int) -> None:
#     eprint("====== Activating member")
#     # Make the member not be deleted
#     r = instance.gateway.post(f"membership/member/{member_id}/activate", {})
#     assert r.ok
#     eprint("====== Activated member")
# 
#     send_new_member_email(member_id)
# 
# 
# def send_receipt_email(member_id: int, transaction_id: int) -> None:
#     transaction = transaction_entity.get(transaction_id)
#     items = transaction_content_entity.list("transaction_id=%s", transaction_id)
#     products = [product_entity.get(item["product_id"]) for item in items]
# 
#     r = instance.gateway.get(f"membership/member/{member_id}")
#     assert r.ok
# 
#     member = r.json()["data"]
# 
#     r = instance.gateway.post("messages/message", {
#         "recipients": [
#             {
#                 "type": "member",
#                 "id": member_id
#             },
#         ],
#         "message_type": "email",
#         "title": "Kvitto - Stockholm Makerspace",
#         "description": render_template("receipt_email.html", cart=zip(products, items), transaction=transaction, currency="kr", member=member, public_url=instance.gateway.get_public_url)
#     })
# 
#     if not r.ok:
#         eprint("Failed to send receipt email")
#         eprint(r.text)
# 
# 
# duplicatePurchaseRands: Set[int] = set()
# 
# 
# @instance.route("pay", methods=["POST"], permission='user')
# @route_helper
# def pay_route() -> Dict[str, int]:
#     data = request.get_json()
#     if data is None:
#         raise errors.MissingJson()
# 
#     member_id = int(assert_get(request.headers, "X-User-Id"))
#     return pay(member_id, data)
# 
# 
# def add_transaction_to_db(member_id: int, total_amount: Decimal, items: List[CartItem]) -> int:
#     transaction_id = transaction_entity.post({"member_id": member_id, "amount": total_amount, "status": "pending"})["id"]
#     for item in items:
#         item_content = transaction_content_entity.post({"transaction_id": transaction_id, "product_id": item.id, "count": item.count, "amount": item.amount})
#         with db.cursor() as cur:
#             cur.execute("""
#                 INSERT INTO webshop_transaction_actions (content_id, action_id, value, status)
#                 SELECT %s AS content_id, action_id, SUM(%s * value) AS value, 'pending' AS status
#                 FROM webshop_product_actions
#                 WHERE product_id=%s AND deleted_at IS NULL
#                 GROUP BY action_id
#                 """, (item_content["id"], item.count, item.id))
# 
#     return transaction_id
# 
# 
# def create_three_d_secure_source(transaction_id: int, card_source_id: str, total_amount: Decimal) -> stripe.Source:
#     stripe_amount = convert_to_stripe_amount(total_amount)
#     eprint("Token: " + str(card_source_id))
#     return stripe.Source.create(
#         amount=stripe_amount,
#         currency=currency,
#         type='three_d_secure',
#         three_d_secure={
#             'card': card_source_id,
#         },
#         redirect={
#             'return_url': instance.gateway.get_public_url(f"/shop/receipt/{transaction_id}")
#         },
#     )
# 
# 
# def handle_card_source(transaction_id: int, card_source_id: str, total_amount: Decimal) -> Dict[str, int]:
#     card_source = stripe.Source.retrieve(card_source_id)
#     if card_source.type != 'card' or card_source.card.three_d_secure != 'not_supported':
#         abort(500, f'Synchronous charges should only be made for cards not supporting 3D Secure')
# 
#     status = card_source.status
#     if status == "chargeable":
#         card_stripe_payment(transaction_id, card_source_id)
#     elif status == "failed":
#         fail_transaction(transaction_id, 400, "Payment failed")
#     elif status == "consumed":
#         # Not necessarily an error but shouldn't happen.
#         abort(500, f"Stripe source already marked as 'consumed'")
#     else:
#         logger.error(f"Unknown stripe source status '{status}'")
#         fail_transaction(transaction_id, 500, f"Unknown stripe source status '{status}'")
# 
#     return {"transaction_id": transaction_id}
# 
# 
# def handle_three_d_secure_source(transaction_id: int, card_source_id: str, total_amount: Decimal) -> Dict[str, Any]:
#     try:
#         source = create_three_d_secure_source(transaction_id, card_source_id, total_amount)
#     except stripe.error.InvalidRequestError as e:
#         if "Amount must convert to at least" in str(e):
#             _fail_transaction(transaction_id)
#             raise errors.TooSmallAmount()
#         else:
#             eprint("Stripe Charge Failed")
#             eprint(e)
#             fail_transaction(transaction_id, 400, "payment failed")
# 
#     webshop_stripe_pending.post({"transaction_id": transaction_id, "stripe_token": source.id})
#     eprint(source)
# 
#     status = source.status
#     if status in {"pending", "chargeable"}:
#         # Assert 3d secure is pending redirect
#         if source.redirect.status not in {'pending', 'not_required'}:
#             fail_transaction(transaction_id, 500, f"Unexpected value for source.redirect.status, '{source.redirect.status}'")
#         # Assert 3d secure is pending redirect
#         if not source.redirect.url:
#             fail_transaction(transaction_id, 500, f"Invalid value for source.redirect.url, '{source.redirect.url}'")
#         # Redirect the user to do the 3D secure confirmation step
#         if source.redirect.status == 'pending':
#             return {"transaction_id": transaction_id, "redirect": source.redirect.url}
#     elif status == "failed":
#         fail_transaction(transaction_id, 400, "Payment failed")
#     else:
#         eprint(f"Unknown stripe source status '{status}'")
#         fail_transaction(transaction_id, 500, f"Unknown stripe source status '{status}'")
# 
#     return {"transaction_id": transaction_id}
# 
# 
# def pay(member_id: int, data: Dict[str, Any], activates_member: bool = False) -> Dict[str, Any]:
#     # The frontend will add a per-page random value to the request.
#     # This will try to prevent duplicate payments due to sending the payment request twice
#     duplicatePurchaseRand = assert_get(data, "duplicatePurchaseRand")
#     if duplicatePurchaseRand in duplicatePurchaseRands:
#         raise errors.DuplicateTransaction()
# 
#     if member_id <= 0:
#         raise errors.NotMember()
# 
#     card_source_id = assert_get(data, "stripeSource")
#     card_three_d_secure = assert_get(data, "stripeThreeDSecure")
# 
#     total_amount, items = validate_payment(member_id, data["cart"], data["expectedSum"])
# 
#     transaction_id = add_transaction_to_db(member_id, total_amount, items)
# 
#     if activates_member:
#         # Mark this transaction as one that is for registering a member
#         webshop_pending_registrations.post({"transaction_id": transaction_id})
# 
#     webshop_stripe_pending.post({"transaction_id": transaction_id, "stripe_token": card_source_id})
# 
#     result: Dict[str, Any] = {}
#     if card_three_d_secure == 'not_supported':
#         result = handle_card_source(transaction_id, card_source_id, total_amount)
#     else:
#         result = handle_three_d_secure_source(transaction_id, card_source_id, total_amount)
# 
#     duplicatePurchaseRands.add(duplicatePurchaseRand)
#     return result
# 
# 
# def send_key_updated_email(member_id: int, extended_days: int, end_date: datetime) -> None:
#     r = instance.gateway.get(f"membership/member/{member_id}")
#     assert r.ok
#     member = r.json()["data"]
# 
#     r = instance.gateway.post("messages/message", {
#         "recipients": [
#             {
#                 "type": "member",
#                 "id": member_id
#             },
#         ],
#         "message_type": "email",
#         "title": "Din labaccess har utökats",
#         "description": render_template("updated_key_time_email.html", public_url=instance.gateway.get_public_url, member=member, extended_days=extended_days, end_date=end_date.strftime("%Y-%m-%d"))
#     })
# 
#     if not r.ok:
#         eprint("Failed to send key updated email")
#         eprint(r.text)
# 
# 
# def send_membership_updated_email(member_id: int, extended_days: int, end_date: datetime) -> None:
#     r = instance.gateway.get(f"membership/member/{member_id}")
#     assert r.ok
#     member = r.json()["data"]
# 
#     r = instance.gateway.post("messages/message", {
#         "recipients": [
#             {
#                 "type": "member",
#                 "id": member_id
#             },
#         ],
#         "message_type": "email",
#         "title": "Ditt medlemsskap har utökats",
#         "description": render_template("updated_membership_time_email.html", public_url=instance.gateway.get_public_url, member=member, extended_days=extended_days, end_date=end_date.strftime("%Y-%m-%d"))
#     })
# 
#     if not r.ok:
#         eprint("Failed to send membership updated email")
#         eprint(r.text)
# 
# 
# @instance.route("ship_orders", methods=["POST"], permission="webshop")
# @route_helper
# def ship_orders_route() -> None:
#     ship_orders(True)
# 
# 
# @dataclass
# class PendingAction:
#     member_id: int
#     action_name: str
#     action_value: int
#     pending_action_id: int
#     transaction: Dict[str, Any]
#     created_at: str
# 
# 
# def complete_pending_action(action: PendingAction) -> None:
#     now = datetime.now().astimezone()
#     webshop_transaction_actions.put({"status": "completed", "completed_at": str(now)}, action.pending_action_id)
# 
# 
# def ship_orders(labaccess: bool) -> None:
#     '''
#     Completes all orders for purchasing lab access and updates existing keys with new dates.
#     If a user has no key yet, then the order will remain as not completed.
#     If a user has multiple keys, all of them are updated with new dates.
#     '''
#     actions = pending_actions()
# 
#     for pending in actions:
#         action = PendingAction(
#             member_id=pending["member_id"],
#             action_name=pending["action"]["name"],
#             action_value=int(pending["pending_action"]["value"]),
#             pending_action_id=pending['pending_action']['id'],
#             transaction=pending["item"],
#             created_at=pending["created_at"]
#         )
# 
#         if labaccess and action.action_name == "add_labaccess_days":
#             ship_add_labaccess_action(action)
# 
#         if action.action_name == "add_membership_days":
#             ship_add_membership_action(action)
# 
# 
# def ship_add_labaccess_action(action: PendingAction) -> None:
#     r = instance.gateway.get(f"membership/member/{action.member_id}/keys")
#     assert r.ok, r.text
#     if len(r.json()["data"]) == 0:
#         # Skip this member because it has no keys
#         return
# 
#     days_to_add = action.action_value
#     assert(days_to_add >= 0)
#     r = instance.gateway.post(f"membership/member/{action.member_id}/addMembershipDays",
#                               {
#                                   "type": "labaccess",
#                                   "days": days_to_add,
#                                   "creation_reason": f"transaction_action_id: {action.pending_action_id}, transaction_id: {action.transaction['transaction_id']}",
#                               }
#                               )
#     assert r.ok, r.text
# 
#     r = instance.gateway.get(f"membership/member/{action.member_id}/membership")
#     assert r.ok, r.text
#     new_end_date = parser.parse(r.json()["data"]["labaccess_end"])
# 
#     complete_pending_action(action)
#     send_key_updated_email(action.member_id, days_to_add, new_end_date)
# 
# 
# def ship_add_membership_action(action: PendingAction) -> None:
#     days_to_add = action.action_value
#     assert(days_to_add >= 0)
#     r = instance.gateway.post(f"membership/member/{action.member_id}/addMembershipDays",
#                               {
#                                   "type": "membership",
#                                   "days": days_to_add,
#                                   "default_start_date": action.created_at[:10],
#                                   "creation_reason": f"transaction_action_id: {action.pending_action_id}, transaction_id: {action.transaction['transaction_id']}",
#                               }
#                               )
#     assert r.ok, r.text
# 
#     r = instance.gateway.get(f"membership/member/{action.member_id}/membership")
#     assert r.ok, r.text
#     new_end_date = parser.parse(r.json()["data"]["membership_end"])
# 
#     complete_pending_action(action)
#     send_membership_updated_email(action.member_id, days_to_add, new_end_date)
# 
# 
# def get_product_data() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
#     with db.cursor() as cur:
#         # Get all categories, as some products may exist in deleted categories
#         # (it is up to an admin to move them to another category)
#         categories: List[Dict[str, Any]] = category_entity.list(where=None, order_column='display_order')
# 
#         data = []
#         for cat in categories:
#             cur.execute("SELECT id,name,unit,price,smallest_multiple,IFNULL(image,'default_image.png'),display_order "
#                         "FROM webshop_products "
#                         "WHERE category_id=%s AND deleted_at IS NULL ORDER BY display_order", (cat["id"],))
#             products = cur.fetchall()
#             if len(products) > 0:
#                 data.append({
#                     "id": cat["id"],
#                     "name": cat["name"],
#                     "items": [
#                         {
#                             "id": item[0],
#                             "name": item[1],
#                             "unit": item[2],
#                             "price": str(item[3]),
#                             "smallest_multiple": item[4],
#                             "image": item[5],
#                             "display_order": item[6],
#                         } for item in products
#                     ]
#                 })
# 
#         # Only show existing columns in the sidebar
#         categories = category_entity.list(order_column='display_order')
#         return data, categories
# 
# 
# @instance.route("product_data", methods=["GET"], permission=None)
# @route_helper
# def product_data():
#     data, categories = get_product_data()
#     return {"data": data, "categories": categories}
# 
# 
# @instance.route("product_data/<int:product_id>/", methods=["GET"], permission=None)
# @route_helper
# def product_view_data(product_id: int):
#     product = product_entity.get(product_id)
#     images = product_image_entity.list("product_id=%s AND deleted_at IS NULL", product_id)
#     data, categories = get_product_data()
#     return {"product": product, "images": images, "data": data}
# 
# 
# @instance.route("product_edit_data/<int:product_id>/", methods=["GET"], permission="webshop_edit")
# @route_helper
# def product_edit_data(product_id: int):
#     _, categories = get_product_data()
# 
#     if product_id:
#         product = product_entity.get(product_id)
# 
#         # Find the ids and names of all actions that this product has
#         with db.cursor() as cur:
#             cur.execute("SELECT webshop_product_actions.id,webshop_actions.id,webshop_actions.name,webshop_product_actions.value"
#                         " FROM webshop_product_actions"
#                         " INNER JOIN webshop_actions ON webshop_product_actions.action_id=webshop_actions.id"
#                         " WHERE webshop_product_actions.product_id=%s AND webshop_product_actions.deleted_at IS NULL", product_id)
#             actions = cur.fetchall()
#             actions = [{
#                 "id": a[0],
#                 "action_id": a[1],
#                 "name": a[2],
#                 "value": a[3],
#             } for a in actions]
# 
#         images = product_image_entity.list("product_id=%s AND deleted_at IS NULL", product_id)
#     else:
#         product = {
#             "category_id": "",
#             "name": "",
#             "description": "",
#             "unit": "",
#             "price": 0.0,
#             "id": "new",
#             "smallest_multiple": 1,
#         }
#         actions = []
#         images = []
# 
#     action_categories = action_entity.list()
# 
#     filters = sorted(product_filters.keys())
# 
#     return {
#         "categories": categories,
#         "product": product,
#         "actions": actions,
#         "filters": filters,
#         "images": images,
#         "action_categories": action_categories,
#     }
# 
# 
# @instance.route("receipt/<int:transaction_id>", methods=["GET"], permission='user')
# @route_helper
# def receipt(transaction_id: int):
#     member_id = int(assert_get(request.headers, "X-User-Id"))
#     transaction = transaction_entity.get(transaction_id)
#     if transaction.get('member_id') != member_id:
#         raise NotFound()
# 
#     items = transaction_content_entity.list("transaction_id=%s", transaction_id)
#     products = [product_entity.get(item["product_id"]) for item in items]
#     r = instance.gateway.get(f"membership/member/{member_id}")
#     assert r.ok
#     member = r.json()["data"]
# 
#     return {
#         "cart": list(zip(products, items)),
#         "transaction": transaction,
#         "member": member,
#     }
# 
# 
# @instance.route("register_page_data", methods=["GET"], permission=None)
# @route_helper
# def register_page_data():
#     data, _ = get_product_data()
#     products = membership_products(db)
#     return {"data": data, "products": products}
