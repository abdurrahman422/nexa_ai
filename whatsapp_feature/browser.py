"""Conservative public-DOM adapter. WhatsApp selectors require live validation.

No internal WhatsApp JavaScript APIs, message history exports or background sends.
An unsupported UI stops the operation rather than broadening recipient checks.
"""
import re
from urllib.parse import quote

from .models import BeforeSendError, Result, normalize_phone

LOGIN = ("canvas[aria-label*='Scan']", "[data-testid='qrcode']", "[data-testid='intro-title']")
SIDE = ("#side", "[data-testid='chat-list']")
COMPOSER = ("#main footer div[contenteditable='true'][role='textbox']", "#main [data-testid='conversation-compose-box-input']")
SEND = ("#main footer button[aria-label='Send']", "#main footer [role='button'][aria-label='Send']", "#main footer [data-testid='send']", "#main footer button:has(span[data-icon='send'])")
INFO = ("[data-testid='contact-info-drawer']", "[data-testid='drawer-right']", "[data-testid='drawer-right-body']")


def exact_phone_line(value):
    value = (value or '').strip().replace('\u200e', '').replace('\u200f', '').replace('\u00a0', ' ')
    if not re.fullmatch(r'\+?[0-9 ()-]+', value):
        return None
    try:
        return normalize_phone(value)
    except ValueError:
        return None


class Browser:
    def __init__(self, driver, timeout=30, observation_timeout=15):
        self.driver = driver
        self.timeout = timeout
        self.observation_timeout = observation_timeout
        self.verified_phone = None
        self.header_identity = None
        self.on_close = None

    def _first(self, selectors, root=None, clickable=False):
        from selenium.common.exceptions import StaleElementReferenceException
        for selector in selectors:
            for element in (root or self.driver).find_elements('css selector', selector):
                try:
                    if element.is_displayed() and (not clickable or element.is_enabled()):
                        return element
                except StaleElementReferenceException:
                    continue
        return None

    def _wait(self, predicate, message):
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
        try:
            return WebDriverWait(self.driver, self.timeout, poll_frequency=.25,
                                 ignored_exceptions=(StaleElementReferenceException,)).until(lambda _: predicate())
        except TimeoutException as exc:
            raise BeforeSendError('ui_unavailable', message) from exc

    def _invalid_recipient(self):
        # Only inspect the explicit error dialog; never use page-wide text.
        for dialog in self.driver.find_elements('css selector', "[role='dialog']"):
            if dialog.is_displayed() and any(p in dialog.text.lower() for p in
                    ('phone number shared via url is invalid', "isn't on whatsapp", 'not on whatsapp', 'invalid phone number')):
                return True
        return False

    def open_chat(self, phone):
        self.driver.get('https://web.whatsapp.com/send?phone=' + quote(phone, safe=''))
        def ready():
            if self._first(LOGIN):
                raise BeforeSendError('login_required', 'Scan the QR code in the Nexa WhatsApp window. After login, repeat the SAME request ID; no message is queued.')
            if self._invalid_recipient():
                raise BeforeSendError('invalid_recipient', 'WhatsApp rejected this phone number. Nothing was sent.')
            return self._first(SIDE) and self._first(COMPOSER)
        self._wait(ready, 'WhatsApp did not load a usable chat. Check connection/session and retry the same request ID.')

    def _header(self):
        element = self._first(("#main header span[title]",))
        if element is None:
            raise BeforeSendError('recipient_unverified', 'The conversation header could not be verified. Nothing was sent.')
        return element

    def _header_value(self):
        header = self._header()
        return header.get_attribute('title') or header.text

    def verify_recipient(self, phone):
        header = self._header()
        title = header.get_attribute('title') or header.text
        # Even a phone-shaped header can be a saved contact name. Always open
        # ONLY this conversation's contact info, never trust the header alone.
        header.click()
        panel = self._wait(lambda: self._first(INFO), 'Contact info did not open; exact phone verification is required.')
        if any(label in panel.text.lower() for label in ('group info', 'group members', 'participants')):
            raise BeforeSendError('wrong_chat', 'Group sending is outside this text-to-phone feature. Nothing was sent.')
        values = {exact_phone_line(line) for line in panel.text.splitlines()}
        values.discard(None)
        # Reject multi-number or unexpected panels instead of guessing.
        if values != {phone}:
            raise BeforeSendError('wrong_chat', 'The contact-info phone number does not uniquely match the requested recipient. Nothing was sent.')
        close = self._first(("button[aria-label='Close']", "[role='button'][aria-label='Close']", "[data-testid='btn-closer-drawer']", "[data-icon='x']"), root=panel, clickable=True)
        if close is None:
            raise BeforeSendError('ui_unavailable', 'Contact info cannot be closed safely; nothing was sent.')
        close.click()
        self._wait(lambda: self._first(COMPOSER) and self._first(INFO) is None, 'Contact info remained open.')
        if self._header_value() != title:
            raise BeforeSendError('wrong_chat', 'The conversation changed during recipient verification.')
        self.header_identity = title
        self.verified_phone = phone

    def _composer_text(self, element):
        # textContent/innerText through WebDriver preserves leading/trailing spaces.
        return (element.get_property('innerText') or '').replace('\r\n', '\n')

    def compose(self, text):
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        composer = self._wait(lambda: self._first(COMPOSER, clickable=True), 'Message box is unavailable.')
        if self._composer_text(composer):
            raise BeforeSendError('draft_present', 'This chat already contains a draft. Review/clear it manually, then retry; it was not overwritten.')
        composer.click()
        for index, line in enumerate(text.split('\n')):
            if index:
                ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
            if line:
                composer.send_keys(line)
        if self._composer_text(composer) != text:
            raise BeforeSendError('text_mismatch', 'WhatsApp did not preserve the exact message. Nothing was sent; review its draft before retrying.')

    def prepare_send(self, phone, text):
        if phone != self.verified_phone or self._header_value() != self.header_identity:
            raise BeforeSendError('wrong_chat', 'The conversation changed before sending.')
        # Re-open contact info immediately before Send, rather than trusting a name.
        self.verify_recipient(phone)
        button = self._wait(lambda: self._first(SEND, clickable=True), 'Send button is unavailable after composing. Nothing was sent.')
        composer = self._first(COMPOSER)
        if composer is None or self._composer_text(composer) != text:
            raise BeforeSendError('text_mismatch', 'The message changed before Send. Nothing was sent.')
        if self._header_value() != self.header_identity:
            raise BeforeSendError('wrong_chat', 'The conversation changed before Send.')
        return button

    def _outgoing(self):
        from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
        rows = []
        for bubble in self.driver.find_elements('css selector', '#main .message-out'):
            try:
                owner = bubble.find_element('xpath', 'ancestor-or-self::*[@data-id][1]')
                identity = owner.get_attribute('data-id') or ''
                # Only a distinct, stable outgoing message identity can confirm send.
                if not identity.startswith('true_'):
                    continue
                spans = bubble.find_elements('css selector', '.selectable-text.copyable-text')
                if len(spans) != 1:
                    continue
                text = (spans[0].get_property('innerText') or '').replace('\r\n', '\n')
                icons = {e.get_attribute('data-icon') for e in bubble.find_elements('css selector', '[data-icon]')}
                labels = {e.get_attribute('aria-label') for e in bubble.find_elements('css selector', '[aria-label]')}
                status = 'submitted'
                if 'msg-dblcheck-ack' in icons or 'Read' in labels:
                    status = 'read'
                elif 'msg-dblcheck' in icons or 'Delivered' in labels:
                    status = 'delivered'
                elif 'msg-check' in icons or 'Sent' in labels:
                    status = 'sent'
                rows.append((identity, text, status))
            except (NoSuchElementException, StaleElementReferenceException):
                continue
        return rows

    def outgoing_ids(self):
        return {row[0] for row in self._outgoing()}

    def observe_result(self, text, previous):
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
        seen = None
        def evidence(_):
            nonlocal seen
            if self._header_value() != self.header_identity:
                raise RuntimeError('Conversation changed after click')
            fresh = [r for r in self._outgoing() if r[0] not in previous and r[1] == text]
            if len(fresh) > 1:
                raise RuntimeError('Ambiguous outgoing message evidence')
            if fresh:
                seen = fresh[0]
                return seen if seen[2] in ('sent', 'delivered', 'read') else False
            return False
        try:
            WebDriverWait(self.driver, self.observation_timeout, poll_frequency=.25,
                          ignored_exceptions=(StaleElementReferenceException,)).until(evidence)
        except TimeoutException:
            pass
        if seen is None:
            return Result('unknown', 'Send was clicked but no new matching outgoing message was verified. Check WhatsApp; do not retry with a new ID.')
        identity, _, status = seen
        labels = {
            'submitted': 'The new message is visible in WhatsApp; server acceptance/delivery is not confirmed.',
            'sent': 'The new message shows a sent acknowledgement. Recipient delivery is not confirmed.',
            'delivered': 'The new message shows a delivered acknowledgement. Read status is not confirmed.',
            'read': 'The new message shows an explicit read acknowledgement.',
        }
        return Result(status, labels[status], False, identity)

    def close(self, keep_open=False):
        if self.on_close:
            self.on_close(keep_open)
        elif not keep_open:
            self.driver.quit()


class BrowserPool:
    """One visible Chrome session per isolated profile. Retains QR login window."""
    def __init__(self, profile, timeout=30, observation_timeout=15):
        self.profile = profile
        self.timeout = timeout
        self.observation_timeout = observation_timeout
        self.driver = None

    def __call__(self):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        if self.driver is not None:
            try:
                _ = self.driver.window_handles
            except Exception:
                self.shutdown()
        if self.driver is None:
            import os
            self.profile.mkdir(parents=True, exist_ok=True)
            os.environ['SE_CACHE_PATH'] = str((self.profile.parent / 'selenium-cache').resolve())
            os.environ['SE_AVOID_STATS'] = 'true'
            options = Options()
            options.add_argument('--user-data-dir=' + str(self.profile.resolve()))
            options.add_argument('--profile-directory=NexaWhatsAppExtension')
            options.add_argument('--disable-notifications')
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(self.timeout)
        browser = Browser(self.driver, self.timeout, self.observation_timeout)
        browser.on_close = lambda keep: None if keep else self.shutdown()
        return browser

    def shutdown(self):
        driver, self.driver = self.driver, None
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
