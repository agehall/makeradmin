from random import randint
from datetime import date
from unittest import skip
from wsgiref import validate

from membership.models import MemberStorage, Span, StorageNags
from messages.models import Message
from service.db import db_session
from test_aid.systest_base import ApiTest
from multiaccess.box_terminator import box_terminator_validate, get_dates, check_status, get_storage_info, Reason, Status, EXPIRATION_TIME


class Test(ApiTest):
#TODO add nag db tests
#TODO add more nag email tests
#TODO more list all storage tests with filters
#TODO add temp storage tests

    def test_box_terminator_get_dates_box(self):
        member = self.db.create_member()
        span = self.db.create_span(enddate=self.date(-50), type=Span.LABACCESS)
        item = self.db.create_member_storage(MemberStorage.BOX)
        dates = get_dates(item)

        self.assertEqual(dates["expire_lab_date"], self.date(-50))
        self.assertEqual(dates["terminate_lab_date"], self.date(-50+EXPIRATION_TIME))

        self.assertIsNone(dates["expire_fixed_date"])
        self.assertIsNone(dates["terminate_fixed_date"])

        self.assertEqual(dates["to_termination_days"], -50+EXPIRATION_TIME)
        self.assertEqual(dates["days_after_expiration"], 50)
        self.assertEqual(dates["pending_labaccess_days"], 0)

    def test_box_terminator_get_dates_temp_active(self):
        member = self.db.create_member()
        span = self.db.create_span(enddate=self.date(50), type=Span.LABACCESS)
        item = self.db.create_member_storage(MemberStorage.TEMP, fixed_end_date=self.date(90))
        dates = get_dates(item)

        self.assertEqual(dates["expire_lab_date"], self.date(50))
        self.assertEqual(dates["terminate_lab_date"], self.date(50+EXPIRATION_TIME))

        self.assertEqual(dates["expire_fixed_date"], self.date(90))
        self.assertEqual(dates["terminate_fixed_date"], self.date(90+EXPIRATION_TIME))

        self.assertEqual(dates["to_termination_days"], 50+EXPIRATION_TIME)
        self.assertEqual(dates["days_after_expiration"], -50)
        self.assertEqual(dates["pending_labaccess_days"], 0)

    def test_box_terminator_get_dates_temp__lab_exp(self):
        member = self.db.create_member()
        span = self.db.create_span(enddate=self.date(-50), type=Span.LABACCESS)
        item = self.db.create_member_storage(MemberStorage.TEMP, fixed_end_date=self.date(90))
        dates = get_dates(item)

        self.assertEqual(dates["expire_lab_date"], self.date(-50))
        self.assertEqual(dates["terminate_lab_date"], self.date(-50+EXPIRATION_TIME))

        self.assertEqual(dates["expire_fixed_date"], self.date(90))
        self.assertEqual(dates["terminate_fixed_date"], self.date(90+EXPIRATION_TIME))

        self.assertEqual(dates["to_termination_days"], -50+EXPIRATION_TIME)
        self.assertEqual(dates["days_after_expiration"], 50)
        self.assertEqual(dates["pending_labaccess_days"], 0)

    def test_box_terminator_get_dates_temp_fixed_exp(self):
        member = self.db.create_member()
        span = self.db.create_span(enddate=self.date(50), type=Span.LABACCESS)
        item = self.db.create_member_storage(MemberStorage.TEMP, fixed_end_date=self.date(-30))
        dates = get_dates(item)

        self.assertEqual(dates["expire_lab_date"], self.date(50))
        self.assertEqual(dates["terminate_lab_date"], self.date(50+EXPIRATION_TIME))

        self.assertEqual(dates["expire_fixed_date"], self.date(-30))
        self.assertEqual(dates["terminate_fixed_date"], self.date(-30+EXPIRATION_TIME))

        self.assertEqual(dates["to_termination_days"], -30+EXPIRATION_TIME)
        self.assertEqual(dates["days_after_expiration"], 30)
        self.assertEqual(dates["pending_labaccess_days"], 0)

    def test_box_terminator_check_status_active_no_fixed(self):
        dates = {
            "expire_lab_date": self.date(10),
            "terminate_lab_date": self.date(10 + EXPIRATION_TIME),
            "expire_fixed_date": None,
            "terminate_fixed_date": None,
            "pending_labaccess_days": 0,
        }

        status, reason = check_status(dates)
        self.assertEqual(status, Status.ACTIVE)
        self.assertIsNone(reason)

    def test_box_terminator_check_status_expired_no_fixed(self):
        dates = {
            "expire_lab_date": self.date(-10),
            "terminate_lab_date": self.date(-10 + EXPIRATION_TIME),
            "expire_fixed_date": None,
            "terminate_fixed_date": None,
            "pending_labaccess_days": 0,
        }

        status, reason = check_status(dates)
        self.assertEqual(status, Status.EXPIRED)
        self.assertEqual(reason, Reason.LABACCESS_EXPIRED)

    def test_box_terminator_check_status_terminate_no_fixed(self):
        dates = {
            "expire_lab_date": self.date(-50),
            "terminate_lab_date": self.date(-50 + EXPIRATION_TIME),
            "expire_fixed_date": None,
            "terminate_fixed_date": None,
            "pending_labaccess_days": 0,
        }

        status, reason = check_status(dates)
        self.assertEqual(status, Status.TERMINATE)
        self.assertEqual(reason, Reason.LABACCESS_EXPIRED)

    #TODO check_status with fixed end date
    #TODO check_status with pending lab days

    def test_box_terminator_get_storage_info_box(self):
        member = self.db.create_member()
        item = self.db.create_member_storage(MemberStorage.BOX)

        item_info = get_storage_info(item)

        self.assertEqual(item_info["member_number"], member.member_number)
        self.assertEqual(item_info["item_label_id"], item.item_label_id)
        self.assertEqual(item_info["storage_type"], item.storage_type)
        self.assertEqual(item_info["status"], Status.TERMINATE)
        self.assertEqual(item_info["reason"], Reason.LABACCESS_EXPIRED)

        #TODO check nags of various kinds

    def test_box_terminator_get_storage_info_temp_lab_exp(self):
        member = self.db.create_member()
        item = self.db.create_member_storage(MemberStorage.TEMP, fixed_end_date=self.date(50))

        item_info = get_storage_info(item)

        self.assertEqual(item_info["member_number"], member.member_number)
        self.assertEqual(item_info["item_label_id"], item.item_label_id)
        self.assertEqual(item_info["storage_type"], item.storage_type)
        self.assertEqual(item_info["status"], Status.TERMINATE)
        self.assertEqual(item_info["reason"], Reason.LABACCESS_EXPIRED)

        #TODO check nags of various kinds

    def test_box_terminator_get_storage_info_temp_fixed_exp(self):
        member = self.db.create_member()
        item = self.db.create_member_storage(MemberStorage.TEMP, fixed_end_date=self.date(-50))

        item_info = get_storage_info(item)

        self.assertEqual(item_info["member_number"], member.member_number)
        self.assertEqual(item_info["item_label_id"], item.item_label_id)
        self.assertEqual(item_info["storage_type"], item.storage_type)
        self.assertEqual(item_info["status"], Status.TERMINATE)
        self.assertEqual(item_info["reason"], Reason.BOTH_EXPIRED)

        #TODO check nags of various kinds

    def test_box_terminator_validate_simple_without_post_box(self):
        member = self.db.create_member()
        item_label_id = randint(1e9, 9e9)
        storage_type=MemberStorage.BOX

        item_info = box_terminator_validate(member.member_number, item_label_id, storage_type, None)

        db_session.close()
        item = db_session.query(MemberStorage).filter_by(item_label_id=item_label_id).one()
        self.assertIsNotNone(item.last_check_at)
        self.assertEqual(item.member_id, member.member_id)
        self.assertEqual(item.item_label_id, item_label_id)
        self.assertEqual(item.storage_type, storage_type)

        self.assertEqual(item_info["member_number"], member.member_number)
        self.assertEqual(item_info["item_label_id"], item_label_id)
        self.assertEqual(item_info["storage_type"], storage_type)
        self.assertEqual(item_info["status"], Status.TERMINATE)
        self.assertEqual(item_info["reason"], Reason.LABACCESS_EXPIRED)

    def test_box_terminator_validate_simple_without_post_temp(self):
        member = self.db.create_member()
        item_label_id = randint(1e9, 9e9)
        storage_type=MemberStorage.TEMP
        fixed_end_date=self.date(50)

        item_info = box_terminator_validate(member.member_number, item_label_id, storage_type, fixed_end_date.isoformat())

        db_session.close()
        item = db_session.query(MemberStorage).filter_by(item_label_id=item_label_id).one()
        self.assertIsNotNone(item.last_check_at)
        self.assertEqual(item.member_id, member.member_id)
        self.assertEqual(item.item_label_id, item_label_id)
        self.assertEqual(item.storage_type, storage_type)

        self.assertEqual(item_info["member_number"], member.member_number)
        self.assertEqual(item_info["item_label_id"], item_label_id)
        self.assertEqual(item_info["storage_type"], storage_type)
        self.assertEqual(item_info["status"], Status.TERMINATE)
        self.assertEqual(item_info["reason"], Reason.LABACCESS_EXPIRED)

    def test_box_terminator_validate_creates_box_if_not_exists(self):
        member = self.db.create_member()
        item_label_id = randint(1e9, 9e9)
        storage_type = MemberStorage.BOX
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, storage_type=storage_type, item_label_id=item_label_id)).expect(
            200,
            data__member_number=member.member_number,
            data__expire_date='1997-09-27',
            data__terminate_date='1997-11-11',
            data__storage_type=storage_type,
            data__status='terminate'
        )
        
        db_session.close()
        
        item = db_session.query(MemberStorage).filter_by(item_label_id=item_label_id).one()
        
        self.assertIsNone(item.last_nag_at)
        self.assertIsNotNone(item.last_check_at)

    def test_box_terminator_validate_creates_temp_if_not_exists(self):
        member = self.db.create_member()
        item_label_id = randint(1e9, 9e9)
        storage_type=MemberStorage.TEMP
        fixed_end_date=self.date(50)
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, storage_type=storage_type, item_label_id=item_label_id, fixed_end_date=fixed_end_date.isoformat())).expect(
            200,
            data__member_number=member.member_number,
            data__expire_date='1997-09-27', #TODO
            data__terminate_date='1997-11-11', #TODO
            data__storage_type=storage_type,
            data__status='terminate' #TODO
        )
        
        db_session.close()
        
        item = db_session.query(MemberStorage).filter_by(item_label_id=item_label_id).one()
        
        self.assertIsNone(item.last_nag_at)
        self.assertIsNotNone(item.last_check_at)

"""
    def test_box_terminator_validate_uses_existing_box_if_it_exists(self):
        member = self.db.create_member()
        item = self.db.create_member_storage(MemberStorage.BOX)
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, item_label_id=item.item_label_id)).expect(200)
        
        db_session.close()
        
        db_item = db_session.query(MemberStorage).filter_by(member_id=member.member_id).one()
        
        self.assertEqual(item.item_label_id, db_item.item_label_id)
        self.assertIsNone(db_item.last_nag_at)
        self.assertIsNotNone(db_item.last_check_at)

    def test_box_terminator_validate_status_terminate(self):
        member = self.db.create_member()
        item = self.db.create_member_storage(MemberStorage.BOX)
        span = self.db.create_span(enddate=self.date(-50), type=Span.LABACCESS)
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, item_label_id=item.item_label_id)).expect(
            200,
            data__expire_date=self.date(-50 + 1).isoformat(),
            data__terminate_date=self.date(-50 + EXPIRATION_TIME + 1).isoformat(),
            data__status='terminate'
        )

    def test_box_terminator_validate_status_expired(self):
        member = self.db.create_member()
        item = self.db.create_member_storage(MemberStorage.BOX)
        span = self.db.create_span(enddate=self.date(-10), type=Span.LABACCESS)
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, item_label_id=item.item_label_id)).expect(
            200,
            data__expire_date=self.date(-10 + 1).isoformat(),
            data__terminate_date=self.date(-10 + EXPIRATION_TIME + 1).isoformat(),
            data__status='expired'
        )

    def test_box_terminator_validate_status_active(self):
        member = self.db.create_member()
        item = self.db.create_member_storage(MemberStorage.BOX)
        span = self.db.create_span(enddate=self.date(10), type=Span.LABACCESS)
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, item_label_id=item.item_label_id)).expect(
            200,
            data__expire_date=self.date(10 + 1).isoformat(),
            data__terminate_date=self.date(10 + EXPIRATION_TIME + 1).isoformat(),
            data__status='active'
        )

    def test_box_terminator_validate_deleted_span_is_filtered(self):
        member = self.db.create_member()
        item = self.db.create_member_storage(MemberStorage.BOX)
        span = self.db.create_span(enddate=self.date(10), type=Span.LABACCESS, deleted_at=self.datetime())
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, item_label_id=item.item_label_id)).expect(
            200,
            data__status='terminate'
        )

    def test_box_terminator_validate_membership_span_is_filtered(self):
        member = self.db.create_member()
        item = self.db.create_member_storage(MemberStorage.BOX)
        span = self.db.create_span(enddate=self.date(10), type=Span.MEMBERSHIP)
        
        self.api.post('/multiaccess/box-terminator/validate',
                      dict(member_number=member.member_number, item_label_id=item.item_label_id)).expect(
            200,
            data__status='terminate'
        )
    
    def test_box_terminator_send_nag_email(self):
        member = self.db.create_member()
        item = self.db.create_member_storage(MemberStorage.BOX)
        
        self.api.post('/multiaccess/box-terminator/nag',
                      dict(member_number=member.member_number, item_label_id=item.item_label_id, nag_type="nag-warning"))\
             .expect(200)
        
        db_session.close()
        
        message = db_session.query(Message).filter_by(member_id=member.member_id).one()
        
        self.assertIn('lådan', message.body) #TODO improve

    def test_box_terminator_list_all_boxes(self): #TODO fix
        token = self.db.create_access_token()

        member1 = self.db.create_member()
        item11 = self.db.create_member_storage(MemberStorage.BOX)
        item12 = self.db.create_member_storage(MemberStorage.BOX)

        member2 = self.db.create_member()
        item21 = self.db.create_member_storage(MemberStorage.BOX)
        
        self.api.post('/multiaccess/box-terminator/validate', token=token.access_token,
                      json=dict(member_number=member1.member_number, item_label_id=item11.item_label_id)).expect(200)

        self.api.post('/multiaccess/box-terminator/validate', token=token.access_token,
                      json=dict(member_number=member1.member_number, item_label_id=item12.item_label_id)).expect(200)

        self.api.post('/multiaccess/box-terminator/validate', token=token.access_token,
                      json=dict(member_number=member2.member_number, item_label_id=item21.item_label_id)).expect(200)
        
        data = self.api.get('/multiaccess/box-terminator/stored_items', token=token.access_token).expect(200).data
    
        item_ids = [b['item_label_id'] for b in data]
    
        self.assertIn(item11.item_label_id, item_ids)
        self.assertIn(item12.item_label_id, item_ids)
        self.assertIn(item21.item_label_id, item_ids)
    """
