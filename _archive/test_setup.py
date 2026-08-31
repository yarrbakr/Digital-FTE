"""
Test Suite for Bronze Tier Gmail Watcher
Run this to verify your setup is working correctly
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

def print_section(title):
    """Print a formatted section header"""
    print('\n' + '='*60)
    print(f'  {title}')
    print('='*60)

def test_environment():
    """Test environment variables"""
    print_section('Testing Environment Variables')
    
    vault_path = os.getenv('VAULT_PATH')
    gmail_creds = os.getenv('GMAIL_CREDENTIALS', './credentials.json')
    
    if not vault_path:
        print('❌ VAULT_PATH not set in .env')
        return False
    
    print(f'✅ VAULT_PATH: {vault_path}')
    
    if not Path(vault_path).exists():
        print(f'❌ Vault path does not exist: {vault_path}')
        return False
    
    print(f'✅ Vault exists at: {vault_path}')
    
    creds_path = Path(gmail_creds)
    if not creds_path.exists():
        print(f'❌ Gmail credentials not found: {gmail_creds}')
        print('   Download credentials.json from Google Cloud Console')
        return False
    
    print(f'✅ Gmail credentials found: {gmail_creds}')
    return True

def test_vault_structure():
    """Test vault folder structure"""
    print_section('Testing Vault Structure')
    
    vault_path = Path(os.getenv('VAULT_PATH'))
    required_folders = ['Needs_Action', 'Done', 'Logs', 'agent_skills']
    
    all_good = True
    for folder in required_folders:
        folder_path = vault_path / folder
        if folder_path.exists():
            print(f'✅ {folder}/ exists')
        else:
            print(f'❌ {folder}/ missing')
            all_good = False
    
    # Check for skill file
    skill_file = vault_path / 'agent_skills' / 'email_processing_skill.md'
    if skill_file.exists():
        print(f'✅ email_processing_skill.md exists')
    else:
        print(f'❌ email_processing_skill.md missing')
        all_good = False
    
    return all_good

def test_dependencies():
    """Test Python dependencies"""
    print_section('Testing Python Dependencies')
    
    required = [
        'google.auth',
        'googleapiclient',
        'dotenv'
    ]
    
    all_good = True
    for package in required:
        try:
            __import__(package)
            print(f'✅ {package} installed')
        except ImportError:
            print(f'❌ {package} not installed')
            all_good = False
    
    return all_good

def test_claude_code():
    """Test Claude Code installation"""
    print_section('Testing Claude Code')
    
    import subprocess
    
    try:
        result = subprocess.run(
            ['claude', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f'✅ Claude Code is installed')
            print(f'   Version info: {result.stdout.strip()}')
            return True
        else:
            print(f'❌ Claude Code returned error')
            return False
    except FileNotFoundError:
        print(f'❌ Claude Code not found in PATH')
        print('   Install from: https://github.com/anthropics/claude-code')
        return False
    except Exception as e:
        print(f'❌ Error testing Claude Code: {e}')
        return False

def test_gmail_connection():
    """Test Gmail API connection"""
    print_section('Testing Gmail Connection')
    
    try:
        # Import after checking dependencies
        from watchers.gmail_watcher import GmailWatcher
        
        vault_path = os.getenv('VAULT_PATH')
        gmail_creds = os.getenv('GMAIL_CREDENTIALS', './credentials.json')
        
        print('Creating Gmail Watcher...')
        watcher = GmailWatcher(
            vault_path=vault_path,
            credentials_path=gmail_creds,
            check_interval=60
        )
        
        print('Testing connection...')
        if watcher.test_connection():
            print('✅ Gmail connection successful!')
            return True
        else:
            print('❌ Gmail connection failed')
            return False
            
    except Exception as e:
        print(f'❌ Error testing Gmail: {e}')
        return False

def create_test_email_file():
    """Create a test email file for manual testing"""
    print_section('Creating Test Email File')
    
    vault_path = Path(os.getenv('VAULT_PATH'))
    needs_action = vault_path / 'Needs_Action'
    
    test_file = needs_action / 'EMAIL_test_manual.md'
    
    content = """---
type: email
message_id: test123
from: test@example.com
subject: Test Email for AI Employee
date: 2026-01-21
priority: high
status: pending
---

## Email Content

**From**: test@example.com
**Subject**: Test Email for AI Employee
**Date**: 2026-01-21

This is a test email to verify the AI Employee system is working.
Please draft a polite response acknowledging receipt.

## Suggested Actions

- [ ] Draft response
- [ ] Archive after processing

## Notes

This is a manual test file.
"""
    
    test_file.write_text(content)
    print(f'✅ Created test email file: {test_file.name}')
    print(f'   Location: {test_file}')
    print()
    print('To test Claude processing, run:')
    print(f'   claude --cwd {vault_path} --skill {vault_path}/.agent_skills/email_processing_skill.md "Process test email"')
    return True

def main():
    """Run all tests"""
    print('\n' + '🤖 '*20)
    print('   AI EMPLOYEE - BRONZE TIER TEST SUITE')
    print('🤖 '*20)
    
    results = []
    
    # Run tests
    results.append(('Environment', test_environment()))
    results.append(('Vault Structure', test_vault_structure()))
    results.append(('Dependencies', test_dependencies()))
    results.append(('Claude Code', test_claude_code()))
    
    # Optional: Gmail connection test (requires credentials)
    try_gmail = input('\n📧 Test Gmail connection? This will open a browser for auth (y/n): ').lower()
    if try_gmail == 'y':
        results.append(('Gmail Connection', test_gmail_connection()))
    
    # Optional: Create test file
    create_test = input('\n📝 Create test email file? (y/n): ').lower()
    if create_test == 'y':
        results.append(('Test File Creation', create_test_email_file()))
    
    # Summary
    print_section('Test Summary')
    all_passed = True
    for name, passed in results:
        status = '✅' if passed else '❌'
        print(f'{status} {name}')
        if not passed:
            all_passed = False
    
    print('\n' + '='*60)
    if all_passed:
        print('🎉 All tests passed! You\'re ready to run your AI Employee!')
        print('\nNext steps:')
        print('1. Run the watcher: uv run python watchers/gmail_watcher.py')
        print('2. In another terminal, run: uv run python orchestrator.py')
        print('3. Send yourself a test email to see it work!')
    else:
        print('⚠️  Some tests failed. Please fix the issues above.')
    print('='*60 + '\n')

if __name__ == '__main__':
    main()
