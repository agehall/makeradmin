from membership.models import Member
from messages.message import send_message
from messages.models import MessageTemplate
from service.db import db_session
from service.util import date_to_str


def send_membership_updated_email(member_id, extended_days, end_date):
    member = db_session.query(Member).get(member_id)

    send_message(
        MessageTemplate.ADD_MEMBERSHIP_TIME, member,
        extended_days=extended_days,
        end_date=date_to_str(end_date)
    )


def send_key_updated_email(member_id, extended_days, end_date):
    member = db_session.query(Member).get(member_id)

    send_message(
        MessageTemplate.ADD_LABACCESS_TIME, member,
        extended_days=extended_days,
        end_date=date_to_str(end_date)
    )


def send_receipt_email(transaction):
    contents = transaction.contents
    products = [content.product for content in contents]

    send_message(
        MessageTemplate.RECEIPT, transaction.member,
        cart=list(zip(products, contents)),
        transaction=transaction,
        currency="kr",
    )


def send_new_member_created_email(member, login_url):
    send_message(MessageTemplate.NEW_MEMBER_CREATED, member, login_url=login_url)


def send_new_member_registred_email(member):
    send_message(MessageTemplate.NEW_MEMBER_REGISTRED, member)


