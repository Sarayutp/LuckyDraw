import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import app as app_module
from models import db, Event, Participant, Prize, History


class LuckyDrawApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fd, db_path = tempfile.mkstemp(prefix='luckydraw_test_', suffix='.db')
        os.close(fd)
        cls.db_path = db_path

        app_module.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )

        with app_module.app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

    @classmethod
    def tearDownClass(cls):
        with app_module.app.app_context():
            db.session.remove()
        if os.path.exists(cls.db_path):
            os.unlink(cls.db_path)

    def setUp(self):
        with app_module.app.app_context():
            History.query.delete()
            Prize.query.delete()
            Participant.query.delete()
            Event.query.delete()
            db.session.commit()

    def _create_classic_event(self, participant_names, prize_name='Gift', prize_qty=1):
        with app_module.app.app_context():
            event = Event(name='Test Event', event_type='classic')
            db.session.add(event)
            db.session.flush()

            for name in participant_names:
                db.session.add(Participant(name=name, event_id=event.id))

            db.session.add(
                Prize(
                    name=prize_name,
                    total_quantity=prize_qty,
                    remaining_quantity=prize_qty,
                    event_id=event.id,
                )
            )
            db.session.commit()
            return event.id

    def _selected_prizes_payload(self, event_id, quantity=1):
        with app_module.app.app_context():
            prize = Prize.query.filter_by(event_id=event_id).first()
            return [{'prize_id': prize.id, 'quantity': quantity}]

    def test_shuffle_only_returns_remaining_participants(self):
        event_id = self._create_classic_event(['A', 'B', 'C', 'D'], prize_qty=2)
        selected_prizes = self._selected_prizes_payload(event_id, quantity=1)

        client = app_module.app.test_client()
        draw_response = client.post(
            f'/api/event/{event_id}/draw',
            json={'selected_prizes': selected_prizes}
        )
        self.assertEqual(draw_response.status_code, 200)

        with app_module.app.app_context():
            won_ids = {r.receiver_participant_id for r in History.query.filter_by(event_id=event_id).all()}
            remaining = Participant.query.filter(
                Participant.event_id == event_id,
                ~Participant.id.in_(won_ids)
            ).all()
            remaining_ids = {p.id for p in remaining}

        shuffle_response = client.post(f'/api/event/{event_id}/shuffle_participants')
        self.assertEqual(shuffle_response.status_code, 200)
        payload = shuffle_response.get_json()
        shuffled_ids = {item['id'] for item in payload['participants']}

        self.assertEqual(shuffled_ids, remaining_ids)
        self.assertTrue(shuffled_ids.isdisjoint(won_ids))

    def test_concurrent_draw_is_blocked_by_event_lock(self):
        event_id = self._create_classic_event(['A', 'B', 'C'], prize_qty=3)
        selected_prizes = self._selected_prizes_payload(event_id, quantity=1)

        original_handle_classic_draw = app_module.handle_classic_draw

        def slow_handle_classic_draw(event):
            time.sleep(0.2)
            return original_handle_classic_draw(event)

        statuses = []
        lock = threading.Lock()
        barrier = threading.Barrier(2)

        def call_draw():
            client = app_module.app.test_client()
            barrier.wait()
            response = client.post(
                f'/api/event/{event_id}/draw',
                json={'selected_prizes': selected_prizes}
            )
            with lock:
                statuses.append(response.status_code)

        with patch.object(app_module, 'handle_classic_draw', side_effect=slow_handle_classic_draw):
            t1 = threading.Thread(target=call_draw)
            t2 = threading.Thread(target=call_draw)
            t1.start()
            t2.start()
            t1.join()
            t2.join()

        self.assertEqual(len(statuses), 2)
        self.assertEqual(statuses.count(200), 1)
        self.assertEqual(statuses.count(409), 1)

        with app_module.app.app_context():
            history_count = History.query.filter_by(event_id=event_id).count()
        self.assertEqual(history_count, 1)

    def test_draw_requires_selected_prizes_in_classic_mode(self):
        event_id = self._create_classic_event(['A', 'B'], prize_qty=2)
        client = app_module.app.test_client()

        response = client.post(f'/api/event/{event_id}/draw', json={})
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload.get('error'), 'Please select at least one prize to draw')

        response = client.post(f'/api/event/{event_id}/draw', json={'selected_prizes': []})
        self.assertEqual(response.status_code, 400)

        response = client.post(
            f'/api/event/{event_id}/draw',
            json={'selected_prizes': [{'prize_id': 999999, 'quantity': 1}]}
        )
        self.assertEqual(response.status_code, 400)

    def test_settings_round_trip_and_validation(self):
        event_id = self._create_classic_event(['A', 'B'], prize_qty=1)
        client = app_module.app.test_client()

        payload = {
            'delay': 2.5,
            'draw_text': 'ทดสอบปุ่ม',
            'music': 'snare_and_drum.mp3',
            'random_animation': 'spinning_wheel',
            'winner_animation': 'fireworks',
            'background_url': '',
            'logo_url': ''
        }
        res = client.post(f'/api/event/{event_id}/settings', json=payload)
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body.get('success'))
        self.assertEqual(body['config']['music_id'], 'snare_and_drum.mp3')

        state = client.get(f'/api/event/{event_id}/state')
        self.assertEqual(state.status_code, 200)
        self.assertEqual(state.get_json()['config']['music_id'], 'snare_and_drum.mp3')

        invalid = client.post(f'/api/event/{event_id}/settings', json={'music': 'default_upbeat'})
        self.assertEqual(invalid.status_code, 400)


if __name__ == '__main__':
    unittest.main()
