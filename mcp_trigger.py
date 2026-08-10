"""
MCP Trigger Script - Silver Tier
Watches /Approved folder and executes actions via Gmail API, LinkedIn (Playwright),
and WhatsApp (Playwright).

The Gmail and LinkedIn MCP servers are designed for Claude Code tool integration
(stdio transport). This script calls the underlying APIs directly instead.
"""

import os
import re
import time
import json
import base64
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# WhatsApp Web rejects HeadlessChrome user agents
_CHROME_UA = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
)

# Load environment variables
load_dotenv()

# Configuration
VAULT_PATH = Path(os.getenv('VAULT_PATH'))
APPROVED = VAULT_PATH / 'Approved'
DONE = VAULT_PATH / 'Done'
FAILED = VAULT_PATH / 'Failed'
LOGS = VAULT_PATH / 'Logs'
CHECK_INTERVAL = int(os.getenv('MCP_CHECK_INTERVAL', 10))

PROJECT_ROOT = Path(__file__).parent

# Gmail credentials
GMAIL_CREDENTIALS_PATH = Path(os.getenv('GMAIL_CREDENTIALS', './credentials.json'))
GMAIL_TOKEN_PATH = GMAIL_CREDENTIALS_PATH.parent / 'token.json'

# LinkedIn session
LINKEDIN_SESSION_PATH = Path(os.getenv('LINKEDIN_SESSION_PATH', './.linkedin-session')).resolve()

# WhatsApp session (shared with whatsapp_watcher)
WHATSAPP_SESSION_PATH = Path(os.getenv('WHATSAPP_SESSION_PATH', './.whatsapp-session')).resolve()

# Ensure directories exist
APPROVED.mkdir(exist_ok=True)
DONE.mkdir(exist_ok=True)
FAILED.mkdir(exist_ok=True)
LOGS.mkdir(exist_ok=True)


def log_message(message, level="INFO"):
    """Log message to console with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}")


def parse_markdown_file(filepath):
    """
    Parse markdown file to extract YAML frontmatter and body content.

    Returns: (frontmatter_dict, body_text)
    Body retains markdown headers so extract_message_content can locate
    section markers like "## Content Preview".
    """
    content = filepath.read_text()
    lines = content.split('\n')

    frontmatter = {}
    content_lines = []
    in_frontmatter = False
    frontmatter_count = 0

    for line in lines:
        if line.strip() == '---':
            frontmatter_count += 1
            if frontmatter_count == 1:
                in_frontmatter = True
                continue
            elif frontmatter_count == 2:
                in_frontmatter = False
                continue

        if in_frontmatter:
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip()
        else:
            content_lines.append(line)

    body = '\n'.join(content_lines).strip()
    return frontmatter, body


def extract_message_content(body):
    """
    Extract the actual sendable message from a Content Preview section.

    Handles three formats:
    1. Content between --- markers after "Content Preview" / "Proposed"
    2. Blockquote lines (> ...) after "Content Preview" / "Proposed"
    3. Falls back to the full body if nothing matched
    """
    lines = body.split('\n')

    content_start = None
    content_end = None
    found_preview_section = False

    for i, line in enumerate(lines):
        if 'Content Preview' in line or 'Proposed' in line:
            found_preview_section = True
            continue
        if found_preview_section and line.strip() == '---':
            if content_start is None:
                content_start = i + 1
            else:
                content_end = i
                break

    # Format 1: content between --- markers
    if content_start is not None and content_end is not None:
        message_lines = lines[content_start:content_end]
        return '\n'.join(message_lines).strip()

    # Format 2: blockquote lines (> ...) after the section header
    found_preview_section = False
    quote_lines = []
    in_quote = False

    for line in lines:
        if 'Content Preview' in line or 'Proposed' in line:
            found_preview_section = True
            continue
        if found_preview_section:
            stripped = line.strip()
            if stripped.startswith('>'):
                in_quote = True
                # Strip the leading '>' and optional space
                text = stripped[1:]
                if text.startswith(' '):
                    text = text[1:]
                quote_lines.append(text)
            elif in_quote:
                # First non-quote line after quotes started → we're done
                break

    if quote_lines:
        return '\n'.join(quote_lines).strip()

    return body


def get_recipient(frontmatter):
    """Get recipient from frontmatter, checking both 'to' and 'target' fields."""
    return frontmatter.get('to', '') or frontmatter.get('target', '')


def log_action(filepath, action_type, status, details=""):
    """Log action to daily log file"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': filepath.stem,
        'action_type': action_type,
        'status': status,
        'details': details
    }
    
    log_file = LOGS / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    
    logs = []
    if log_file.exists():
        try:
            logs = json.loads(log_file.read_text())
        except json.JSONDecodeError:
            logs = []
    
    logs.append(log_entry)
    log_file.write_text(json.dumps(logs, indent=2))
    log_message(f"Logged: {action_type} - {status}")


def _get_gmail_service():
    """Authenticate with Gmail API and return a service object."""
    if not GMAIL_TOKEN_PATH.exists():
        raise FileNotFoundError(
            f"Token file not found: {GMAIL_TOKEN_PATH}. "
            "Run the Gmail watcher first to complete OAuth flow."
        )

    creds = Credentials.from_authorized_user_file(
        str(GMAIL_TOKEN_PATH),
        ['https://www.googleapis.com/auth/gmail.send'],
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        GMAIL_TOKEN_PATH.write_text(creds.to_json())

    return build('gmail', 'v1', credentials=creds)


def execute_gmail_send(filepath):
    """Execute email send via Gmail API directly."""
    try:
        log_message(f"Processing email send: {filepath.name}")

        frontmatter, body = parse_markdown_file(filepath)

        # Extract email details (check both 'to'/'target' and body for fallbacks)
        to_email = get_recipient(frontmatter)
        subject = frontmatter.get('subject', '')

        # If subject not in frontmatter, look for **Subject:** in body
        if not subject:
            subject_match = re.search(r'\*\*Subject:\*\*\s*(.+)', body)
            if subject_match:
                subject = subject_match.group(1).strip()
            else:
                subject = 'No Subject'

        # If to_email not in frontmatter, look for **To:** in body
        if not to_email:
            to_match = re.search(r'\*\*To:\*\*\s*(.+)', body)
            if to_match:
                to_email = to_match.group(1).strip()

        if not to_email:
            raise ValueError("No recipient specified in 'to'/'target' field or body")

        # Extract just the actual email message from "Content Preview" section
        email_body = extract_message_content(body)

        log_message(f"Sending email to: {to_email}")

        # Build RFC 2822 message and send via Gmail API
        raw_email = '\n'.join([
            f'To: {to_email}',
            f'Subject: {subject}',
            'Content-Type: text/plain; charset=utf-8',
            '',
            email_body,
        ])
        encoded = base64.urlsafe_b64encode(raw_email.encode()).decode()

        service = _get_gmail_service()
        service.users().messages().send(
            userId='me',
            body={'raw': encoded},
        ).execute()

        log_message(f"Email sent successfully to {to_email}")
        log_action(filepath, 'email_send', 'success', f'to: {to_email}')
        filepath.rename(DONE / filepath.name)

    except Exception as e:
        log_message(f"Error sending email: {e}", "ERROR")
        log_action(filepath, 'email_send', 'failed', str(e))
        filepath.rename(FAILED / filepath.name)


def execute_linkedin_post(filepath):
    """Execute LinkedIn post via Playwright directly."""
    try:
        log_message(f"Processing LinkedIn post: {filepath.name}")

        frontmatter, content = parse_markdown_file(filepath)

        # Extract post content (skip frontmatter sections)
        post_lines = []
        in_content_section = False

        for line in content.split('\n'):
            if '## Post Content' in line:
                in_content_section = True
                continue
            elif line.startswith('##'):
                in_content_section = False
            elif in_content_section and line.strip():
                post_lines.append(line)

        post_content = '\n'.join(post_lines).strip()

        if not post_content:
            # Try extracting from Content Preview section, fall back to full body
            post_content = extract_message_content(content) or content

        log_message(f"Posting to LinkedIn: {len(post_content)} characters")

        with sync_playwright() as pw:
            LINKEDIN_SESSION_PATH.mkdir(parents=True, exist_ok=True)
            context = pw.chromium.launch_persistent_context(
                user_data_dir=str(LINKEDIN_SESSION_PATH),
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox'],
            )
            page = context.pages[0] if context.pages else context.new_page()

            # Navigate to feed
            page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded')
            page.wait_for_timeout(3000)

            # Login if needed
            if '/feed/' not in page.url:
                linkedin_email = os.getenv('LINKEDIN_EMAIL', '')
                linkedin_password = os.getenv('LINKEDIN_PASSWORD', '')
                if not linkedin_email or not linkedin_password:
                    context.close()
                    raise ValueError("LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env")

                page.goto('https://www.linkedin.com/login')
                page.wait_for_timeout(2000)
                page.fill('#username', linkedin_email)
                page.wait_for_timeout(500)
                page.fill('#password', linkedin_password)
                page.wait_for_timeout(500)
                page.click('button[type="submit"]')

                try:
                    page.wait_for_url('**/feed/**', timeout=30_000)
                except Exception:
                    page_content = page.content()
                    context.close()
                    if 'captcha' in page_content.lower():
                        raise RuntimeError("CAPTCHA detected during LinkedIn login")
                    raise RuntimeError("LinkedIn login failed")

            # Click "Start a post"
            clicked = False
            for sel in ['button[aria-label*="Start a post"]', 'button:has-text("Start a post")']:
                try:
                    page.click(sel, timeout=5000)
                    clicked = True
                    break
                except Exception:
                    continue

            if not clicked:
                context.close()
                raise RuntimeError("Could not find 'Start a post' button")

            page.wait_for_timeout(2000)
            page.wait_for_selector('.ql-editor, [role="textbox"]', timeout=10_000)
            page.wait_for_timeout(1000)

            # Type post content
            typed = False
            for sel in ['.ql-editor', '[role="textbox"]']:
                try:
                    page.fill(sel, post_content)
                    typed = True
                    break
                except Exception:
                    continue

            if not typed:
                context.close()
                raise RuntimeError("Could not find LinkedIn post editor")

            page.wait_for_timeout(2000)

            # Click Post button
            posted = False
            for sel in ['button[aria-label="Post"]', 'button:has-text("Post")']:
                try:
                    page.click(sel, timeout=5000)
                    posted = True
                    break
                except Exception:
                    continue

            if not posted:
                context.close()
                raise RuntimeError("Could not find Post button")

            # Wait for LinkedIn to process the post
            page.wait_for_timeout(5000)

            # VERIFY: Navigate to feed and confirm post actually published
            log_message("Verifying LinkedIn post appeared in feed...")
            page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded')
            page.wait_for_timeout(3000)

            search_text = post_content[:50]
            feed_html = page.content()
            post_verified = search_text in feed_html

            if not post_verified:
                log_message(f"Post not found in feed. Searched for: \"{search_text}\"", "WARN")
                context.close()
                raise RuntimeError("Post not found in feed after publishing — possible silent failure")

            log_message("Post verified in feed")
            context.close()

        log_message(f"LinkedIn post successful (verified)")
        log_action(filepath, 'linkedin_post', 'success', f'{len(post_content)} chars, verified')
        filepath.rename(DONE / filepath.name)

    except Exception as e:
        log_message(f"Error posting to LinkedIn: {e}", "ERROR")
        log_action(filepath, 'linkedin_post', 'failed', str(e))
        filepath.rename(FAILED / filepath.name)


def execute_whatsapp_send(filepath):
    """Execute WhatsApp message send via Playwright"""
    try:
        log_message(f"Processing WhatsApp send: {filepath.name}")

        frontmatter, body = parse_markdown_file(filepath)

        contact_name = get_recipient(frontmatter)
        # Strip "(WhatsApp)" suffix if present
        contact_name = contact_name.replace('(WhatsApp)', '').strip()

        if not contact_name:
            raise ValueError("No recipient specified in 'to'/'target' field")

        # Extract just the actual message from "Content Preview" section
        message_text = extract_message_content(body)

        if not message_text:
            raise ValueError("No message content found in file body")

        log_message(f"Sending WhatsApp message to: {contact_name}")

        with sync_playwright() as pw:
            has_session = (WHATSAPP_SESSION_PATH / 'Default' / 'Cookies').exists()
            context = pw.chromium.launch_persistent_context(
                user_data_dir=str(WHATSAPP_SESSION_PATH),
                headless=has_session,
                user_agent=_CHROME_UA,
                args=['--disable-blink-features=AutomationControlled'],
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto('https://web.whatsapp.com', wait_until='domcontentloaded')

            # Wait for chat list or QR code
            try:
                page.wait_for_selector(
                    'div[aria-label="Chat list"], div[data-testid="qrcode"]',
                    timeout=30_000,
                )
            except Exception:
                context.close()
                raise RuntimeError("WhatsApp Web timed out loading")

            # If QR code is showing, session expired — relaunch visible
            if page.query_selector('div[data-testid="qrcode"]'):
                if has_session:
                    log_message("Session expired — relaunching visible browser for QR scan")
                    context.close()
                    context = pw.chromium.launch_persistent_context(
                        user_data_dir=str(WHATSAPP_SESSION_PATH),
                        headless=False,
                        user_agent=_CHROME_UA,
                        args=['--disable-blink-features=AutomationControlled'],
                    )
                    page = context.pages[0] if context.pages else context.new_page()
                    page.goto('https://web.whatsapp.com', wait_until='domcontentloaded')

                log_message("QR code detected — please scan with your phone (waiting 120s)...")
                try:
                    page.wait_for_selector(
                        'div[aria-label="Chat list"]', timeout=120_000
                    )
                    log_message("QR scan successful — session restored")
                except Exception:
                    context.close()
                    raise RuntimeError("QR scan timed out after 120s")

            # Search for the contact
            search_box = page.wait_for_selector(
                'div[data-testid="chat-list-search"], '
                'div[contenteditable="true"][data-tab="3"]',
                timeout=10_000,
            )
            search_box.click()
            page.keyboard.type(contact_name, delay=50)
            page.wait_for_timeout(2000)

            # Click on the matching contact in search results
            contact_result = page.wait_for_selector(
                f'span[title="{contact_name}"]', timeout=10_000
            )
            contact_result.click()
            page.wait_for_timeout(1000)

            # Type message into the compose box
            compose_box = page.wait_for_selector(
                'div[data-testid="conversation-compose-box-input"], '
                'div[contenteditable="true"][data-tab="10"]',
                timeout=10_000,
            )
            compose_box.click()

            # Handle multi-line messages: Shift+Enter for newlines
            lines = message_text.split('\n')
            for i, line in enumerate(lines):
                page.keyboard.type(line, delay=20)
                if i < len(lines) - 1:
                    page.keyboard.down('Shift')
                    page.keyboard.press('Enter')
                    page.keyboard.up('Shift')

            # Send
            page.keyboard.press('Enter')
            page.wait_for_timeout(2000)

            context.close()

        log_message(f"✅ WhatsApp message sent to {contact_name}")
        log_action(filepath, 'whatsapp_send', 'success', f'to: {contact_name}')
        filepath.rename(DONE / filepath.name)

    except Exception as e:
        log_message(f"❌ Error sending WhatsApp message: {e}", "ERROR")
        log_action(filepath, 'whatsapp_send', 'failed', str(e))
        filepath.rename(FAILED / filepath.name)


def process_approved_files():
    """Main loop: watch /Approved and execute actions"""
    log_message(f"MCP Trigger started. Watching: {APPROVED}")
    log_message(f"Check interval: {CHECK_INTERVAL} seconds")
    
    while True:
        try:
            # Process email sends (via Gmail API)
            email_files = list(APPROVED.glob('EMAIL_SEND_*.md'))
            for file in email_files:
                execute_gmail_send(file)
                time.sleep(2)  # Small delay between actions

            # Process LinkedIn posts (via Playwright)
            linkedin_files = list(APPROVED.glob('LINKEDIN_*.md'))
            for file in linkedin_files:
                execute_linkedin_post(file)
                time.sleep(2)

            # Process WhatsApp replies (via Playwright)
            whatsapp_files = list(APPROVED.glob('WHATSAPP_reply_*.md'))
            for file in whatsapp_files:
                execute_whatsapp_send(file)
                time.sleep(2)

            # Check for any unprocessed files
            IGNORED_FILES = ['README.md']
            other_files = [f for f in APPROVED.glob('*.md')
                          if not f.name.startswith(('EMAIL_SEND_', 'LINKEDIN_', 'WHATSAPP_reply_'))
                          and f.name not in IGNORED_FILES]
            if other_files:
                log_message(f"⚠️  Unknown file types: {[f.name for f in other_files]}", "WARN")
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log_message("MCP Trigger stopped by user")
            break
        except Exception as e:
            log_message(f"Unexpected error: {e}", "ERROR")
            time.sleep(CHECK_INTERVAL)


if __name__ == '__main__':
    log_message("=" * 60)
    log_message("MCP TRIGGER - SILVER TIER (2 CUSTOM MCPs)")
    log_message("=" * 60)
    log_message(f"Vault: {VAULT_PATH}")
    log_message(f"Approved folder: {APPROVED}")
    log_message("Press Ctrl+C to stop")
    log_message("=" * 60)
    
    process_approved_files()