"""
WhatsApp Watcher
Monitors WhatsApp Web for new messages from specific contacts via Playwright
"""

import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright

from base_watcher import BaseWatcher

# WhatsApp Web rejects HeadlessChrome user agents
_CHROME_UA = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
)


class WhatsAppWatcher(BaseWatcher):
    """
    Watches WhatsApp Web for new unread messages from monitored contacts.

    Uses Playwright to automate a Chromium browser with a persistent session.
    First run requires manual QR code scan; subsequent runs reuse the session.
    """

    def __init__(
        self,
        vault_path: str,
        session_path: str,
        check_interval: int = 30,
    ):
        super().__init__(vault_path, check_interval)

        self.session_path = Path(session_path).resolve()
        self.session_path.mkdir(parents=True, exist_ok=True)

        self.processed_ids: set = set()

        self.high_priority_keywords = [
            'urgent', 'asap', 'immediately', 'important',
            'deadline', 'critical', 'emergency', 'payment',
            'invoice', 'contract', 'signature required',
        ]

        self.contacts = self._load_contacts()
        self.log_activity(f'Monitoring {len(self.contacts)} contact(s)')

    # ── Contact list ────────────────────────────────────────────

    def _load_contacts(self) -> List[str]:
        """
        Read monitored contact names from Whatsapp_Contacts.md in the vault.
        Re-called each cycle so edits are picked up live.
        """
        contacts_file = self.vault_path / 'Whatsapp_Contacts.md'
        if not contacts_file.exists():
            self.log_activity(
                f'Contacts file not found: {contacts_file}', level='warning'
            )
            return []

        lines = contacts_file.read_text().splitlines()
        contacts = []
        in_section = False

        for line in lines:
            stripped = line.strip()
            if stripped == '## Monitored Contacts':
                in_section = True
                continue
            if in_section:
                if stripped.startswith('##'):
                    break
                if stripped.startswith('- '):
                    name = stripped[2:].strip()
                    if name:
                        contacts.append(name)

        return contacts

    # ── Core watcher methods ────────────────────────────────────

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Launch Playwright, read the WhatsApp Web sidebar, and return
        new unread messages from monitored contacts.
        """
        # Reload contacts each cycle to pick up live edits
        self.contacts = self._load_contacts()
        if not self.contacts:
            return []

        new_items: List[Dict[str, Any]] = []

        # Check for a real logged-in session (not just an empty session dir)
        has_session = (self.session_path / 'Default' / 'Cookies').exists()

        try:
            with sync_playwright() as pw:
                context = pw.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=has_session,  # visible on first run for QR scan
                    user_agent=_CHROME_UA,
                    args=['--disable-blink-features=AutomationControlled'],
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto('https://web.whatsapp.com', wait_until='domcontentloaded')

                # Wait for either the chat list or the QR code screen
                try:
                    page.wait_for_selector(
                        'div[aria-label="Chat list"], div[data-testid="qrcode"]',
                        timeout=30_000,
                    )
                except Exception:
                    self.log_activity('Timed out waiting for WhatsApp Web to load', level='warning')
                    context.close()
                    return []

                # If QR code is showing, user needs to scan — bail out
                if page.query_selector('div[data-testid="qrcode"]'):
                    self.log_activity(
                        'QR code detected — please scan with your phone to log in',
                        level='warning',
                    )
                    # Keep browser open briefly so user can scan on first run
                    if not has_session:
                        self.log_activity('Waiting 60s for QR scan...')
                        page.wait_for_selector(
                            'div[aria-label="Chat list"]', timeout=60_000
                        )
                    else:
                        context.close()
                        return []

                # Give chats a moment to fully render
                page.wait_for_timeout(3000)

                # Read sidebar chat entries (each row is role="row")
                chat_rows = page.query_selector_all(
                    'div[aria-label="Chat list"] div[role="row"]'
                )

                for row in chat_rows:
                    try:
                        # Each row has multiple span[title] elements:
                        # first = contact name, second = message preview
                        title_spans = row.query_selector_all('span[title]')
                        if not title_spans:
                            continue

                        contact_name = title_spans[0].get_attribute('title') or ''

                        # Only care about monitored contacts
                        if contact_name not in self.contacts:
                            continue

                        # Check for unread badge
                        unread_el = row.query_selector(
                            'span[data-testid="icon-unread-count"], '
                            'span[aria-label*="unread"]'
                        )
                        if not unread_el:
                            continue

                        # Get the preview snippet (second span[title] in the row)
                        preview = ''
                        if len(title_spans) > 1:
                            preview = title_spans[1].get_attribute('title') or ''

                        # Deduplicate using contact+preview hash
                        msg_hash = hashlib.md5(
                            f'{contact_name}:{preview}'.encode()
                        ).hexdigest()

                        if msg_hash in self.processed_ids:
                            continue

                        new_items.append({
                            'contact': contact_name,
                            'preview': preview,
                            'timestamp': datetime.now().isoformat(),
                            'msg_hash': msg_hash,
                        })

                    except Exception as e:
                        self.log_activity(
                            f'Error reading chat row: {e}', level='warning'
                        )
                        continue

                context.close()

        except Exception as e:
            self.log_activity(f'Playwright error: {e}', level='error')

        if new_items:
            self.log_activity(f'Found {len(new_items)} new message(s)')

        return new_items

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Write a WHATSAPP_*.md file into /Needs_Action for the orchestrator.
        """
        contact = item['contact']
        preview = item['preview']
        priority = self._determine_priority(item)
        timestamp = datetime.now()

        safe_contact = ''.join(
            c for c in contact if c.isalnum() or c in (' ', '-', '_')
        ).rstrip().replace(' ', '_')

        filename = f"WHATSAPP_{safe_contact}_{timestamp.strftime('%Y%m%d_%H%M%S')}.md"
        filepath = self.needs_action / filename

        content = f"""---
type: whatsapp
from: {contact}
received: {timestamp.isoformat()}
priority: {priority}
status: pending
---

## WhatsApp Message

**From**: {contact}
**Received**: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Priority**: {priority}

### Message Preview

{preview}

## Suggested Actions

- [ ] Review message content
- [ ] Draft response if needed
- [ ] Archive after processing
"""

        filepath.write_text(content)
        self.processed_ids.add(item['msg_hash'])
        self.log_activity(f'Created action file: {filename}')
        return filepath

    # ── Helpers ──────────────────────────────────────────────────

    def _determine_priority(self, item: Dict[str, Any]) -> str:
        preview = item.get('preview', '').lower()
        contact = item.get('contact', '').lower()
        text = f'{contact} {preview}'

        for keyword in self.high_priority_keywords:
            if keyword in text:
                return 'high'
        return 'medium'

    def test_connection(self) -> bool:
        """
        Check whether WhatsApp Web loads with an active session.
        If no session exists, opens a visible browser and waits for the user
        to scan the QR code (up to 120 seconds).
        """
        has_session = (self.session_path / 'Default' / 'Cookies').exists()

        try:
            with sync_playwright() as pw:
                context = pw.chromium.launch_persistent_context(
                    user_data_dir=str(self.session_path),
                    headless=False if not has_session else True,
                    user_agent=_CHROME_UA,
                    args=['--disable-blink-features=AutomationControlled'],
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto('https://web.whatsapp.com', wait_until='domcontentloaded')

                if not has_session:
                    self.log_activity(
                        'No existing session. Browser is open — scan the QR code with your phone.'
                    )
                    self.log_activity('Waiting up to 120 seconds for login...')

                try:
                    page.wait_for_selector(
                        'div[aria-label="Chat list"]', timeout=120_000
                    )
                    self.log_activity('WhatsApp Web session is active')
                    context.close()
                    return True
                except Exception:
                    self.log_activity(
                        'Timed out waiting for WhatsApp Web chat list',
                        level='warning',
                    )
                    context.close()
                    return False

        except Exception as e:
            self.log_activity(f'Connection test failed: {e}', level='error')
            return False


def main():
    from dotenv import load_dotenv

    load_dotenv()

    vault_path = os.getenv('VAULT_PATH')
    session_path = os.getenv('WHATSAPP_SESSION_PATH', './.whatsapp-session')
    check_interval = int(os.getenv('WHATSAPP_CHECK_INTERVAL', '30'))

    if not vault_path:
        print('Error: VAULT_PATH not set in .env file')
        return

    print('=== WhatsApp Watcher ===')
    print(f'Vault: {vault_path}')
    print(f'Session: {session_path}')
    print(f'Check interval: {check_interval}s')
    print()

    watcher = WhatsAppWatcher(
        vault_path=vault_path,
        session_path=session_path,
        check_interval=check_interval,
    )

    if watcher.test_connection():
        print('Session active — starting watch loop...')
        print('Press Ctrl+C to stop')
        print()
        watcher.run()
    else:
        print('QR scan timed out or failed. Please try again.')


if __name__ == '__main__':
    main()
