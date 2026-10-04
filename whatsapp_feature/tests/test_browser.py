from pathlib import Path
import unittest
from unittest.mock import patch

from whatsapp_feature.browser import Browser, COMPOSER, SEND, INFO, exact_phone_line
from whatsapp_feature.models import BeforeSendError


class Element:
    def __init__(self, text='', title=None, children=None, click=None):
        self.text = text
        self.title = title
        self.children = children or {}
        self.on_click = click
        self.clicks = 0
        self.attrs = {}
        self.visible = True

    def is_displayed(self): return self.visible
    def is_enabled(self): return True
    def get_attribute(self, key): return self.title if key == 'title' else self.attrs.get(key)
    def get_property(self, key): return self.text if key == 'innerText' else None
    def find_elements(self, by, selector): return self.children.get(selector, [])
    def click(self):
        self.clicks += 1
        if self.on_click: self.on_click()
    def send_keys(self, text): self.text += text


class Driver:
    def __init__(self):
        self.selector_log = []
        self.header = Element(title='+880 1712-345678', click=self.open_info)
        self.composer = Element()
        self.button = Element()
        self.info_open = False
        self.info = Element('Contact info\n+880 1712-345678', children={"button[aria-label='Close']": [Element(click=self.close_info)]})
        self.login = False
        self.loaded = True
        self.expose_send = True
        self.dialog = None
        self.url = ''

    def open_info(self): self.info_open = True
    def close_info(self): self.info_open = False
    def get(self, url): self.url = url
    def find_elements(self, by, selector):
        self.selector_log.append(selector)
        if selector == '#main header span[title]': return [self.header]
        if selector == '#side' and self.loaded and not self.login: return [Element()]
        if selector == "[data-testid='qrcode']" and self.login: return [Element()]
        if selector in COMPOSER and self.loaded and not self.login: return [self.composer]
        if selector in INFO and self.info_open: return [self.info]
        if selector in SEND and self.composer.text and self.expose_send: return [self.button]
        if selector == "[role='dialog']" and self.dialog: return [Element(self.dialog)]
        return []


class BrowserTests(unittest.TestCase):
    def setUp(self):
        self.driver = Driver()
        self.browser = Browser(self.driver, timeout=.01, observation_timeout=.01)

    def test_ready_chat_navigates_to_exact_number(self):
        self.browser.open_chat('8801712345678')
        self.assertEqual(self.driver.url, 'https://web.whatsapp.com/send?phone=8801712345678')

    def test_login_shows_retry_without_composing(self):
        self.driver.login = True
        with self.assertRaises(BeforeSendError) as error:
            self.browser.open_chat('8801712345678')
        self.assertEqual(error.exception.status, 'login_required')
        self.assertEqual(self.driver.composer.text, '')

    def test_loading_delay_waits_for_ready(self):
        original = self.driver.find_elements
        count = 0
        def delayed(by, selector):
            nonlocal count
            count += 1
            self.driver.loaded = count > 6
            return original(by, selector)
        self.driver.find_elements = delayed
        self.browser.timeout = 1
        self.browser.open_chat('8801712345678')
        self.assertGreater(count, 6)

    def test_load_timeout_does_not_send(self):
        self.driver.loaded = False
        with self.assertRaises(BeforeSendError): self.browser.open_chat('8801712345678')
        self.assertEqual(self.driver.button.clicks, 0)

    def test_invalid_number_dialog(self):
        self.driver.dialog = "Phone number shared via url is invalid"
        with self.assertRaises(BeforeSendError) as error: self.browser.open_chat('8801712345678')
        self.assertEqual(error.exception.status, 'invalid_recipient')

    def test_direct_header_phone_is_exact(self):
        self.browser.verify_recipient('8801712345678')
        self.assertEqual(self.browser.verified_phone, '8801712345678')
        self.assertFalse(self.driver.info_open)
        self.assertGreater(self.driver.header.clicks, 0)

    def test_phone_shaped_contact_name_cannot_bypass_info(self):
        self.driver.info.text = 'Contact info\n+8801712345679'
        with self.assertRaises(BeforeSendError): self.browser.verify_recipient('8801712345678')

    def test_group_info_is_rejected_even_with_matching_phone(self):
        self.driver.info.text = 'Group info\n+880 1712-345678'
        with self.assertRaises(BeforeSendError): self.browser.verify_recipient('8801712345678')

    def test_saved_name_requires_contact_panel_phone(self):
        self.driver.header.title = 'Rahim'
        self.browser.verify_recipient('8801712345678')
        self.assertFalse(self.driver.info_open)
        self.assertGreater(self.driver.header.clicks, 0)

    def test_suffix_match_is_rejected(self):
        self.driver.header.title = 'Rahim'
        self.driver.info.text = 'Contact info\n+9901712345678'
        with self.assertRaises(BeforeSendError): self.browser.verify_recipient('8801712345678')

    def test_recipient_number_in_body_never_used(self):
        self.driver.header.title = 'Wrong Person'
        self.driver.info.text = 'Contact info\n+8801712345679'
        with self.assertRaises(BeforeSendError): self.browser.verify_recipient('8801712345678')
        self.assertNotIn('body', self.driver.selector_log)

    def test_multiple_contact_numbers_fail_closed(self):
        self.driver.header.title = 'Rahim'
        self.driver.info.text += '\n+8801712345679'
        with self.assertRaises(BeforeSendError): self.browser.verify_recipient('8801712345678')

    def test_phone_embedded_in_prose_not_accepted(self):
        self.assertIsNone(exact_phone_line('My number is 8801712345678'))
        self.assertEqual(exact_phone_line('+880 1712-345678'), '8801712345678')

    def test_existing_draft_is_not_overwritten(self):
        self.driver.composer.text = 'personal draft'
        with self.assertRaises(BeforeSendError) as error: self.browser.compose('hello')
        self.assertEqual(error.exception.status, 'draft_present')
        self.assertEqual(self.driver.composer.text, 'personal draft')

    def test_send_button_only_looked_up_after_composing(self):
        self.browser.verify_recipient('8801712345678')
        self.browser.compose('hello')
        self.assertFalse(any(s in SEND for s in self.driver.selector_log))
        self.assertIs(self.browser.prepare_send('8801712345678', 'hello'), self.driver.button)

    def test_missing_send_button_stops_before_click(self):
        self.browser.verify_recipient('8801712345678')
        self.browser.compose('hello')
        self.driver.expose_send = False
        with self.assertRaises(BeforeSendError): self.browser.prepare_send('8801712345678', 'hello')
        self.assertEqual(self.driver.button.clicks, 0)

    def test_text_changed_before_send_is_rejected(self):
        self.browser.verify_recipient('8801712345678')
        self.browser.compose('hello')
        self.driver.composer.text = 'changed'
        with self.assertRaises(BeforeSendError): self.browser.prepare_send('8801712345678', 'hello')

    def test_whitespace_is_not_silently_trimmed(self):
        self.browser.verify_recipient('8801712345678')
        self.browser.compose(' hello ')
        self.driver.composer.text = 'hello'
        with self.assertRaises(BeforeSendError): self.browser.prepare_send('8801712345678', ' hello ')

    def test_chat_changed_before_send_is_rejected(self):
        self.browser.verify_recipient('8801712345678')
        self.browser.compose('hello')
        self.driver.header.title = 'Someone else'
        with self.assertRaises(BeforeSendError): self.browser.prepare_send('8801712345678', 'hello')

    def test_no_new_message_is_unknown_not_sent(self):
        self.browser.verify_recipient('8801712345678')
        with patch.object(self.browser, '_outgoing', return_value=[]):
            self.assertEqual(self.browser.observe_result('hello', set()).status, 'unknown')

    def test_old_identical_message_cannot_confirm_send(self):
        self.browser.verify_recipient('8801712345678')
        with patch.object(self.browser, '_outgoing', return_value=[('old', 'hello', 'read')]):
            self.assertEqual(self.browser.observe_result('hello', {'old'}).status, 'unknown')

    def test_other_message_cannot_confirm_send(self):
        self.browser.verify_recipient('8801712345678')
        with patch.object(self.browser, '_outgoing', return_value=[('new', 'different', 'read')]):
            self.assertEqual(self.browser.observe_result('hello', set()).status, 'unknown')

    def test_new_outgoing_receipt_distinguishes_states(self):
        self.browser.verify_recipient('8801712345678')
        for status in ('submitted', 'sent', 'delivered', 'read'):
            with self.subTest(status=status):
                with patch.object(self.browser, '_outgoing', return_value=[('new', 'hello', status)]):
                    result = self.browser.observe_result('hello', {'old'})
                self.assertEqual(result.status, status)
                self.assertEqual(result.message_id, 'new')

    def test_ambiguous_new_messages_do_not_claim_success(self):
        self.browser.verify_recipient('8801712345678')
        with patch.object(self.browser, '_outgoing', return_value=[('a', 'hello', 'sent'), ('b', 'hello', 'sent')]):
            with self.assertRaises(RuntimeError): self.browser.observe_result('hello', set())

    def test_chat_change_after_click_does_not_claim_success(self):
        self.browser.verify_recipient('8801712345678')
        self.driver.header.title = 'Other'
        with self.assertRaises(RuntimeError): self.browser.observe_result('hello', set())

    def test_dom_receipt_parser_only_accepts_outgoing_ids(self):
        span = Element('hello')
        owner = Element()
        icon = Element()
        bubble = Element(children={'.selectable-text.copyable-text': [span], '[data-icon]': [icon]})
        bubble.find_element = lambda by, selector: owner
        original = self.driver.find_elements
        self.driver.find_elements = lambda by, selector: [bubble] if selector == '#main .message-out' else original(by, selector)
        owner.attrs['data-id'] = 'false_incoming'
        self.assertEqual(self.browser._outgoing(), [])
        owner.attrs['data-id'] = 'true_outgoing'
        for token, status in (('msg-time', 'submitted'), ('msg-check', 'sent'), ('msg-dblcheck', 'delivered'), ('msg-dblcheck-ack', 'read')):
            icon.attrs['data-icon'] = token
            self.assertEqual(self.browser._outgoing(), [('true_outgoing', 'hello', status)])

    def test_multiline_composition_releases_shift(self):
        from selenium.webdriver.common.keys import Keys
        events = []
        composer = self.driver.composer
        class Chain:
            def __init__(self, driver): pass
            def key_down(self, key): events.append(('down', key)); return self
            def send_keys(self, key):
                events.append(('key', key))
                composer.text += '\n'
                return self
            def key_up(self, key): events.append(('up', key)); return self
            def perform(self): events.append(('perform', None))
        with patch('selenium.webdriver.common.action_chains.ActionChains', Chain):
            self.browser.compose('first\nsecond')
        self.assertEqual(composer.text, 'first\nsecond')
        self.assertEqual(events, [('down', Keys.SHIFT), ('key', Keys.ENTER), ('up', Keys.SHIFT), ('perform', None)])


if __name__ == '__main__':
    unittest.main()
