from dataclasses import dataclass
from logging import getLogger
from typing import Any, List, Literal, Optional, Union

import stripe

import datetime

from stripe.error import InvalidRequestError, CardError, StripeError
from service.error import BadRequest, InternalServerError, EXCEPTION
from service.db import db_session
from membership.models import Member
from membership.membership import get_membership_summary
from shop.stripe_constants import MakerspaceMetadataKeys as MSMetaKeys
from shop.stripe_constants import SubscriptionStatus

# print(f"Stripe api_key={stripe.api_key}")

# stripe.api_key = 'sk_test_4QHS9UR02FMGKPqdjElznDRI'

class SubscriptionTypes:
  MEMBERSHIP = "membership"
  LAB        = "labaccess"

logger = getLogger('makeradmin')


def get_stripe_subscriptions(stripe_customer_id:str, active_only: bool=True) -> List[stripe.Subscription]:
  '''Returns the list of subscription objects for the given user.'''
  resp = stripe.Subscription.list(customer=stripe_customer_id)
  return [sub for sub in resp["data"] if not active_only or sub['status'] in  [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRAILING]]


def get_stripe_customer(member_info:Member) -> Optional[stripe.Customer]:
  try:
    customer_search_result = stripe.Customer.search(
      query=f"metadata['{MSMetaKeys.MEMBER_NUMBER}']:'{member_info.member_number}'"
      )

    # If we find exactly one customer matching the e-mail, we return it
    if (len(customer_search_result.data) == 1):
      customer = customer_search_result.data[0]

      # Update the metadata if needed
      if (MSMetaKeys.USER_ID not in customer.metadata or
          MSMetaKeys.MEMBER_NUMBER not in customer.metadata):
        stripe.Customer.modify(customer["id"],
          metadata = {
            MSMetaKeys.USER_ID       : member_info.member_id,
            MSMetaKeys.MEMBER_NUMBER : member_info.member_number,
          })
      return customer

    # If no customer is found, we create one
    if (len(customer_search_result.data) == 0):
      customer = stripe.Customer.create(
        description="Created by Makeradmin",
        email=member_info.email,
        name=f"{member_info.firstname} {member_info.lastname}",
        metadata = {
          MSMetaKeys.USER_ID : member_info.member_id,
          MSMetaKeys.MEMBER_NUMBER : member_info.member_number,
        }
      )
      return customer

    # FIXME: Can we have multiple customers with the same e-mail???
    for customer in customer_search_result:
      if (MSMetaKeys.MEMBER_NUMBER in customer.metadata and int(customer.metadata[MSMetaKeys.MEMBER_NUMBER]) == member_info.member_id):
        return customer

  except Exception as e:
    print(f"Unable to get or create stripe user: {e}")
  
  return None

# Helper that can look up relevant price for the given member/subscription combo
# This would be a good place to implement discounts as the member_info could give
# the user a different price compared to the standard price for the products.
def lookup_subscription_price_for(member_info:Member, subscription_type:SubscriptionTypes) -> str:
    products = stripe.Product.search(query=f"metadata['{MSMetaKeys.PRICING_TYPE}']:'{subscription_type}'")
    assert len(products.data) == 1, f"Expected to find a single stripe product for the subscription type {subscription_type}, but found {len(products.data)}"
    product = products.data[0]
    default_price = product["default_price"]
    assert type(default_price) == str
    return default_price

def calc_start_ts(current_end_date: datetime.date) -> int | Literal["now"]:
  dt = datetime.datetime.combine(current_end_date, datetime.datetime.min.time())
  tmp = int(dt.timestamp())
  utc_now = int(datetime.datetime.utcnow().timestamp())

  # If the trial lasts for more than a day, we reduce the period by a day to 
  # make sure we start billing the customer in time.
  if (tmp - utc_now > 86400):
    return tmp - 86400
  return 'now'
  

def start_subscription(member_id: int, subscription_type: SubscriptionTypes, checkout_session_id: Optional[str] = None) -> None:
    try:
        print(
            f"Attempting to start new subscription {subscription_type} using checkout session id {checkout_session_id}")
        subscription_start: Union[int, Literal['now']] = "now"

        memberships = get_membership_summary(member_id)

        if memberships.membership_active and subscription_type == SubscriptionTypes.MEMBERSHIP:
          assert memberships.membership_end is not None
          subscription_start = calc_start_ts(memberships.membership_end)
        elif memberships.labaccess_active and subscription_type == SubscriptionTypes.LAB:
          assert memberships.labaccess_end is not None
          subscription_start = calc_start_ts(memberships.labaccess_end)

        member: Member = db_session.query(Member).get(member_id)
        stripe_customer = get_stripe_customer(member)
        if stripe_customer is None:
          raise BadRequest(f"Unable to find corresponding stripe member {member}")

        price_id = lookup_subscription_price_for(member, subscription_type)
        if (price_id == None):
          raise BadRequest(f"Unable to find suitable subscription type {subscription_type} for {member}")

        active_subscriptions = get_stripe_subscriptions(stripe_customer['id'])
        print(f"Checking if user has active subscription for price {price_id}")
        for active_subscription in active_subscriptions:
          for item in active_subscription['items']['data']:
            print(f" - Found price id {item['price']['id']}")
            if (item['price']['id'] == price_id):
              # There is already an active subscription. Let's bail out
              raise BadRequest(f"Member already has active subscription")

        metadata = {
            MSMetaKeys.USER_ID: member_id,
            MSMetaKeys.MEMBER_NUMBER: member.member_number,
            "subscription_type": subscription_type,
        }

        subscription_schedule = stripe.SubscriptionSchedule.create(
            start_date=subscription_start,
            customer=stripe_customer['id'],
            phases=[
                {
                    'items': [
                        {
                            'price': price_id,
                            'metadata': metadata,
                        },
                    ],
                    'collection_method': 'charge_automatically',
                    'metadata': metadata,
                    'proration_behavior': 'none',
                }
            ])

        # Update the stripe customer id in the member just to be sure
        member.stripe_customer_id = stripe_customer['id']
        # We set the subscription schedule id in the membership_subscription_column as this
        # is also used to indicate pending subscriptions
        if (subscription_type == SubscriptionTypes.MEMBERSHIP):
          member.stripe_membership_subscription_id = subscription_schedule['id']
        elif (subscription_type == SubscriptionTypes.LAB):
          member.stripe_labaccess_subscription_id = subscription_schedule['id']
        db_session.flush()

    except Exception as e:
      raise BadRequest("Internal error: " + str(e))

@dataclass
class ReloadPage:
  def __init__(self) -> None:
    self.reload = True

# FIXME: Do we want business logic to prevent users from unsubscribing within X months?

def cancel_subscription(member_id: int, subscription_type: SubscriptionTypes) -> Union[ReloadPage, None]:
    try:
        member: Member = db_session.query(Member).get(member_id)
        stripe_customer = get_stripe_customer(member)
        assert stripe_customer is not None

        subscription_id = None

        if subscription_type == SubscriptionTypes.MEMBERSHIP:
          subscription_id = member.stripe_membership_subscription_id
        elif subscription_type == SubscriptionTypes.LAB:
          subscription_id = member.stripe_labaccess_subscription_id

        if subscription_id is None:
          return None

        # The subscription might be a scheduled one so we need to check the id prefix
        # to determine which API to use.
        if (subscription_id.startswith('sub_sched_')):
          stripe.SubscriptionSchedule.release(subscription_id)
          # No events from schedules so we need to remove the corresponding reference from the member here
          if (subscription_type == SubscriptionTypes.MEMBERSHIP):
            member.stripe_membership_subscription_id = None
          elif (subscription_type == SubscriptionTypes.LAB):
            member.stripe_labaccess_subscription_id = None

        elif (subscription_id.startswith('sub_')):
          stripe.Subscription.delete(sid=subscription_id)

        assert ("id" in stripe_customer)
        member.stripe_customer_id = stripe_customer['id']
        db_session.flush()

        return ReloadPage()
    except Exception as e:
      return str(e)  # FIXME: We could use some structured error reporting

def create_stripe_checkout_session(member_id:int, data:Any = None) -> str:
  print('Creating stripe checkout session')
  checkout_session = None

  member: Member = db_session.query(Member).get(member_id)
  stripe_customer = get_stripe_customer(member)
  if stripe_customer is None:
    raise BadRequest("Unable to find corresponding stripe member")

  metadata = {
      MSMetaKeys.USER_ID: member_id,
      MSMetaKeys.MEMBER_NUMBER: member.member_number,
  }

  checkout_session = stripe.checkout.Session.create(
    payment_method_types=['card'],
    mode='setup',
    metadata=metadata,
    customer=stripe_customer['id'],
    success_url=data["success_url"],
    cancel_url=data["cancel_url"],
  )

  # TODO: Handle normal shop payments?
  return checkout_session.url

def open_stripe_customer_portal(member_id:int) -> str:
  """Create a customer portal session and return the URL to which the user should be redirected."""
  member: Member = db_session.query(Member).get(member_id)
  stripe_customer = get_stripe_customer(member)

  billing_portal_session = stripe.billing_portal.Session.create(customer=stripe_customer['id'])
  print(billing_portal_session)

  return billing_portal_session.url