"""
Gmail Watcher
Monitors Gmail for important/urgent emails and creates action files
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from base_watcher import BaseWatcher

# Gmail API scopes - what permissions we need
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
]


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail for new important/unread emails.

    Uses Gmail API to check for emails matching specific criteria
    (by default: unread + important), then creates markdown files
    for Claude to process.
    """

    # Sender patterns that indicate bulk/newsletter emails — skip these
    SKIP_SENDER_PATTERNS = [
        'noreply@', 'no-reply@', 'newsletter@', 'marketing@',
        'notifications@', 'updates@', 'mailer@', 'digest@',
        'promo@', 'info@', 'hello@', 'team@',
        'mailer-daemon@', 'postmaster@',
    ]

    def __init__(
        self,
        vault_path: str,
        credentials_path: str,
        check_interval: int = 120,
        search_query: str = 'is:unread newer_than:1d in:inbox category:primary'
    ):
        """
        Initialize Gmail Watcher.
        
        Args:
            vault_path: Path to Obsidian vault
            credentials_path: Path to credentials.json from Google Cloud
            check_interval: Seconds between checks (default: 120 = 2 min)
            search_query: Gmail search query (default: unread + important)
        """
        super().__init__(vault_path, check_interval)
        
        self.credentials_path = Path(credentials_path)
        self.token_path = self.credentials_path.parent / 'token.json'
        self.search_query = search_query
        self.processed_ids = set()  # Track which emails we've already processed
        
        # Initialize Gmail service
        self.service = self._initialize_gmail_service()
        self.log_activity('Gmail service initialized successfully')
    
    def _initialize_gmail_service(self):
        """
        Set up Gmail API authentication and create service object.
        
        Returns:
            Gmail API service object
        """
        creds = None
        
        # Check if we have a valid token saved
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(self.token_path),
                    SCOPES
                )
                self.log_activity('Loaded existing credentials')
            except Exception as e:
                self.log_activity(f'Error loading credentials: {e}', level='warning')
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh expired token
                self.log_activity('Refreshing expired credentials')
                creds.refresh(Request())
            else:
                # First time setup - opens browser for auth
                self.log_activity('No valid credentials found, starting OAuth flow')
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f'Credentials file not found: {self.credentials_path}\n'
                        'Please download credentials.json from Google Cloud Console'
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path),
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
                self.log_activity('Successfully authenticated with Gmail')
            
            # Save credentials for next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
                self.log_activity(f'Saved credentials to {self.token_path}')
        
        # Build and return Gmail service
        return build('gmail', 'v1', credentials=creds)
    
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Gmail for new emails matching our search query.
        
        Returns:
            List of email dicts with message data
        """
        try:
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=self.search_query
            ).execute()
            
            messages = results.get('messages', [])
            
            # Filter out already processed messages
            new_messages = [
                m for m in messages
                if m['id'] not in self.processed_ids
            ]
            
            if new_messages:
                self.log_activity(
                    f'Found {len(new_messages)} new message(s) '
                    f'(total unprocessed: {len(messages)})'
                )
            
            return new_messages
            
        except HttpError as error:
            self.log_activity(f'Gmail API error: {error}', level='error')
            return []
        except Exception as e:
            self.log_activity(f'Unexpected error checking Gmail: {e}', level='error')
            return []
    
    def _get_message_details(self, message_id: str) -> Dict[str, Any]:
        """
        Get full details of a specific message.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            Dict with message details
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = {
                h['name']: h['value']
                for h in message['payload']['headers']
            }
            
            # Try to get message body
            body = ''
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = part.get('body', {}).get('data', '')
                        break
            else:
                body = message['payload'].get('body', {}).get('data', '')
            
            # Get snippet (preview text)
            snippet = message.get('snippet', '')
            
            return {
                'id': message_id,
                'from': headers.get('From', 'Unknown'),
                'to': headers.get('To', 'Unknown'),
                'subject': headers.get('Subject', 'No Subject'),
                'date': headers.get('Date', 'Unknown'),
                'snippet': snippet,
                'body': body,
                'has_unsubscribe': 'List-Unsubscribe' in headers,
            }
            
        except HttpError as error:
            self.log_activity(
                f'Error getting message {message_id}: {error}',
                level='error'
            )
            return None
    
    def _determine_priority(self, message_details: Dict[str, Any]) -> str:
        """
        Determine priority level of an email.
        
        Args:
            message_details: Dict with email details
            
        Returns:
            'high', 'medium', or 'low'
        """
        # Keywords that indicate high priority
        high_priority_keywords = [
            'urgent', 'asap', 'immediately', 'important',
            'deadline', 'critical', 'emergency', 'payment',
            'invoice', 'contract', 'signature required'
        ]
        
        subject = message_details.get('subject', '').lower()
        snippet = message_details.get('snippet', '').lower()
        
        # Check if any high priority keywords in subject or snippet
        for keyword in high_priority_keywords:
            if keyword in subject or keyword in snippet:
                return 'high'
        
        # Default to medium priority
        return 'medium'
    
    def _is_bulk_email(self, details: Dict[str, Any]) -> bool:
        """Check if an email looks like a newsletter or bulk sender."""
        sender = details.get('from', '').lower()

        # List-Unsubscribe header is a strong signal for bulk/marketing mail
        if details.get('has_unsubscribe', False):
            return True

        # Check sender against known bulk patterns
        for pattern in self.SKIP_SENDER_PATTERNS:
            if pattern in sender:
                return True

        return False

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create a markdown action file for an email.

        Args:
            item: Dict with message ID

        Returns:
            Path to created file, or None if skipped
        """
        message_id = item['id']

        # Get full message details
        details = self._get_message_details(message_id)
        if not details:
            raise ValueError(f'Could not get details for message {message_id}')

        # Skip newsletters/bulk emails — mark processed but don't create file
        if self._is_bulk_email(details):
            self.processed_ids.add(message_id)
            self.log_activity(
                f'Skipped bulk/newsletter: {details["subject"][:60]} '
                f'(from: {details["from"][:40]})'
            )
            return None
        
        # Determine priority
        priority = self._determine_priority(details)
        
        # Create file content
        content = f"""---
type: email
message_id: {message_id}
from: {details['from']}
to: {details['to']}
subject: {details['subject']}
date: {details['date']}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
---

## Email Content

**From**: {details['from']}
**Subject**: {details['subject']}
**Date**: {details['date']}

{details['snippet']}

## Suggested Actions

- [ ] Read full email
- [ ] Draft response
- [ ] Archive after processing

## Notes

*Add any notes or context here*
"""
        
        # Create filename (sanitize subject for filename)
        safe_subject = ''.join(
            c for c in details['subject'][:50]
            if c.isalnum() or c in (' ', '-', '_')
        ).rstrip()
        filename = f'EMAIL_{message_id[:8]}_{safe_subject}.md'
        filepath = self.needs_action / filename
        
        # Write file
        filepath.write_text(content)
        
        # Mark this message as processed
        self.processed_ids.add(message_id)
        
        self.log_activity(f'Created action file: {filename}')
        return filepath
    
    def test_connection(self) -> bool:
        """
        Test Gmail API connection.
        
        Returns:
            True if can connect, False otherwise
        """
        try:
            # Try to get user profile
            profile = self.service.users().getProfile(userId='me').execute()
            email = profile.get('emailAddress', 'Unknown')
            self.log_activity(f'Successfully connected to Gmail: {email}')
            return True
        except Exception as e:
            self.log_activity(
                f'Failed to connect to Gmail: {e}',
                level='error'
            )
            return False


def main():
    """
    Test the Gmail Watcher.
    Run this directly to test your Gmail connection.
    """
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    vault_path = os.getenv('VAULT_PATH')
    credentials_path = os.getenv('GMAIL_CREDENTIALS', './credentials.json')
    check_interval = int(os.getenv('CHECK_INTERVAL', '120'))
    
    if not vault_path:
        print('Error: VAULT_PATH not set in .env file')
        return
    
    print('=== Gmail Watcher Test ===')
    print(f'Vault: {vault_path}')
    print(f'Credentials: {credentials_path}')
    print(f'Check interval: {check_interval}s')
    print()
    
    # Create watcher
    watcher = GmailWatcher(
        vault_path=vault_path,
        credentials_path=credentials_path,
        check_interval=check_interval
    )
    
    # Test connection
    if watcher.test_connection():
        print('✅ Connection test passed!')
        print()
        print('Starting watch loop...')
        print('Press Ctrl+C to stop')
        print()
        
        # Run watcher
        watcher.run()
    else:
        print('❌ Connection test failed!')


if __name__ == '__main__':
    main()
