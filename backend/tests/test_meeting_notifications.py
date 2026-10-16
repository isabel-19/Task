import unittest
from datetime import datetime, timedelta
from sqlalchemy import select
import test_api
from app import models as m


class MeetingNotificationsTest(unittest.TestCase):
    setUpClass = classmethod(test_api.APITest.setUpClass.__func__)
    tearDownClass = classmethod(test_api.APITest.tearDownClass.__func__)
    setUp = test_api.APITest.setUp
    tearDown = test_api.APITest.tearDown
    sign_in = test_api.APITest.sign_in
    create = test_api.APITest.create

    def meeting(self, **kwargs):
        body = {'title': 'Reunión ficticia', 'date': (datetime.now() + timedelta(days=3)).replace(microsecond=0).isoformat(),
                'agenda': 'Agenda ficticia', 'location': 'Sala ficticia', 'responsible_id': self.admin.id,
                'project_id': self.project['id']} | kwargs
        response = self.client.post('/api/meetings', json=body)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def notices_for(self, email):
        self.sign_in(email)
        notices = self.client.get('/api/notifications')
        self.assertEqual(notices.status_code, 200, notices.text)
        self.sign_in()
        return notices.json()

    def test_scheduling_notifies_only_selected_attendees(self):
        meeting = self.meeting(attendee_ids=[self.member.id])
        member = self.notices_for('member@example.invalid')
        self.assertEqual([(n['kind'], n['record_id']) for n in member], [('meeting_invited', meeting['id'])])
        self.assertIn('Reunión ficticia', member[0]['title'])
        self.assertIn('Sala ficticia', member[0]['message'])
        self.assertEqual(self.notices_for('reader@example.invalid'), [])
        self.assertEqual(self.notices_for('admin@example.invalid'), [])

    def test_changes_and_cancellation_notify_attendees_once_per_change(self):
        meeting = self.meeting(attendee_ids=[self.member.id, self.reader.id])
        moved = self.client.patch('/api/meetings/' + meeting['id'], json={'revision': meeting['revision'], 'location': 'Sala nueva'})
        self.assertEqual(moved.status_code, 200, moved.text)
        kinds = [n['kind'] for n in self.notices_for('member@example.invalid')]
        self.assertEqual(sorted(kinds), ['meeting_invited', 'meeting_updated'])
        untouched = self.client.patch('/api/meetings/' + meeting['id'], json={'revision': moved.json()['revision'], 'agenda': 'Agenda corregida'})
        self.assertEqual(untouched.status_code, 200, untouched.text)
        self.assertEqual(len(self.notices_for('member@example.invalid')), 2)
        cancelled = self.client.patch('/api/meetings/' + meeting['id'], json={'revision': untouched.json()['revision'], 'status': 'cancelada'})
        self.assertEqual(cancelled.status_code, 200, cancelled.text)
        self.assertIn('meeting_cancelled', [n['kind'] for n in self.notices_for('reader@example.invalid')])

    def test_adding_attendee_later_notifies_that_person(self):
        meeting = self.meeting()
        self.assertEqual(self.notices_for('member@example.invalid'), [])
        self.create('attendees', meeting_id=meeting['id'], user_id=self.member.id, attended=False)
        notices = self.notices_for('member@example.invalid')
        self.assertEqual([n['kind'] for n in notices], ['meeting_invited'])

    def test_inactive_or_duplicate_attendees_are_rejected(self):
        with self.factory() as db:
            inactive = m.User(name='Persona inactiva ficticia', email='inactive@example.invalid', password_hash='x', active=False)
            db.add(inactive)
            db.commit()
            inactive_id = inactive.id
        response = self.client.post('/api/meetings', json={'title': 'Reunión ficticia', 'date': datetime.now().isoformat(),
                                                           'agenda': 'Agenda', 'location': 'Sala', 'responsible_id': self.admin.id,
                                                           'project_id': self.project['id'], 'attendee_ids': [inactive_id]})
        self.assertEqual(response.status_code, 422, response.text)
        meeting = self.meeting(attendee_ids=[self.member.id, self.member.id])
        with self.factory() as db:
            self.assertEqual(len(list(db.scalars(select(m.Attendee).where(m.Attendee.meeting_id == meeting['id'])))), 1)

    def test_notice_can_be_read_only_by_its_recipient(self):
        meeting = self.meeting(attendee_ids=[self.member.id])
        self.sign_in('member@example.invalid')
        notice = self.client.get('/api/notifications').json()[0]
        self.sign_in()
        self.assertEqual(self.client.post('/api/notifications/' + notice['id'] + '/read').status_code, 404)
        self.sign_in('member@example.invalid')
        self.assertEqual(self.client.post('/api/notifications/' + notice['id'] + '/read').status_code, 200)
        self.assertEqual(self.client.get('/api/notifications').json(), [])
        self.assertEqual(meeting['id'], notice['record_id'])


if __name__ == '__main__':
    unittest.main()
