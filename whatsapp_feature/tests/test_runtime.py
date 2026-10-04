import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from whatsapp_feature.models import Result


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.env = patch.dict(os.environ, {'NEXA_LLM_ROUTER_ENABLED': 'false'})
        cls.env.start()
        from whatsapp_feature.run_backend import create_app
        cls.app, cls.sender, cls.pool = create_app(Path(cls.tmp.name))
        from fastapi.testclient import TestClient
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.pool.shutdown()
        cls.env.stop()
        cls.tmp.cleanup()

    def setUp(self):
        from app.permissions.store import set_permission
        set_permission('whatsapp_send_skill', False)

    def chat(self, message, request_id='runtime-test'):
        response = self.client.post('/api/chat/message', json={'message': message, 'request_id': request_id})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_extension_health_and_guide_available(self):
        health = self.client.get('/api/whatsapp-extension/health').json()
        self.assertTrue(health['enabled_in_this_process'])
        self.assertFalse(health['live_delivery_verified'])
        self.assertEqual(self.client.get('/whatsapp-extension').status_code, 200)

    def test_original_backend_health_available(self):
        self.assertEqual(self.client.get('/api/health').status_code, 200)

    def test_runtime_metadata_is_consistent(self):
        data = self.client.get('/api/permissions').json()
        rows = {r['key']: r for r in data['permissions']}
        self.assertIn('explicit text-send', rows['whatsapp_send_skill']['description'].lower())
        self.assertNotIn('Auto-send stays locked', rows['whatsapp_draft_skill']['description'])

    def test_existing_data_and_env_paths_are_not_used(self):
        from app.contacts.store import CONTACTS_FILE
        from app.permissions.store import PERMISSIONS_FILE
        from app.core.runtime_paths import env_file
        root = Path(self.tmp.name).resolve()
        for path in (CONTACTS_FILE, PERMISSIONS_FILE, env_file()):
            self.assertTrue(path.resolve().is_relative_to(root))

    def test_disabled_chat_send_never_calls_sender(self):
        with patch.object(self.sender, 'send', side_effect=AssertionError('send forbidden')):
            result = self.chat('Send a WhatsApp message to 01712345678 saying hello.')
        self.assertEqual(result['status'], 'blocked')

    def test_explicit_send_routes_to_extension_with_exact_multiline_body(self):
        from app.permissions.store import set_permission
        from app.chat import service
        set_permission('whatsapp_send_skill', True)
        body = 'Hello Rahim,\nThis is a longer message with more than sixteen words so that any old draft rewriting would normally be requested.'
        with patch.object(self.sender, 'send', return_value=Result('delivered', 'Delivered acknowledgement verified.')) as send:
            with patch.object(service, 'complete_llm', side_effect=AssertionError('Exact send must not invoke LLM')):
                result = self.chat('Send a WhatsApp message to 01712345678 saying ' + body, 'exact-body')
        send.assert_called_once_with('exact-body', '8801712345678', body, enabled=True)
        self.assertTrue(result['action']['executed'])
        self.assertIn('Delivered', result['answer'])

    def test_draft_does_not_route_to_sender(self):
        with patch.object(self.sender, 'send', side_effect=AssertionError('Draft cannot send')):
            result = self.chat('whatsapp e Unknown ke bolo hello')
        self.assertNotEqual(result['intent'], 'whatsapp_send')

    def test_negated_command_does_not_route_to_sender(self):
        with patch.object(self.sender, 'send', side_effect=AssertionError('Negated command cannot send')):
            result = self.chat("Don't send a WhatsApp message to Unknown saying hello.")
        self.assertNotEqual(result['intent'], 'whatsapp_send')

    def test_unknown_exact_contact_does_not_send(self):
        from app.permissions.store import set_permission
        set_permission('whatsapp_send_skill', True)
        with patch.object(self.sender, 'send', side_effect=AssertionError('Unresolved contact cannot send')):
            result = self.chat('Send a WhatsApp message to NotSavedContact saying hello.')
        self.assertEqual(result['status'], 'needs_more_info')

    def test_send_forms_preserve_banglish_and_bangla_text(self):
        from app.chat.service import _parse_whatsapp_draft
        for command, expected in (
            ('WhatsApp e Rahim ke message pathao: ami kal ashbo.', 'ami kal ashbo.'),
            ('রহিমকে হোয়াটসঅ্যাপে মেসেজ পাঠাও: আমি কাল আসব।', 'আমি কাল আসব।'),
        ):
            intent = _parse_whatsapp_draft(command)
            self.assertTrue(intent.send_requested, command)
            self.assertTrue(intent.exact)
            self.assertEqual(intent.raw_message, expected)


if __name__ == '__main__':
    unittest.main()
