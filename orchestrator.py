"""
Orchestrator - Coordinates Watchers and Claude Code
Main entry point for the AI Employee system
Updated for Silver Tier: Context-aware prompts based on file type
"""

import os
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import List
from dotenv import load_dotenv


class Orchestrator:
    """
    Coordinates the AI Employee system:
    1. Monitors /Needs_Action folder for new files
    2. Determines file type and builds context-aware prompt
    3. Triggers Claude Code with correct skills and instructions
    4. Logs all activity
    """
    
    def __init__(self, vault_path: str):
        """
        Initialize orchestrator.
        
        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.failed = self.vault_path / 'Failed'
        self.plans = self.vault_path / 'Plans'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.logs = self.vault_path / 'Logs'
        self.skills = self.vault_path / 'agent_skills'
        
        # Create folders if needed
        for folder in [self.needs_action, self.done, self.failed, 
                       self.plans, self.pending_approval, self.logs]:
            folder.mkdir(exist_ok=True)
        
        # Track files currently being processed to avoid reprocessing
        self.processing = set()
        
        # Ignored files in Needs_Action
        self.ignored_files = ['README.md']
        
        self.log('Orchestrator initialized')
        self.log(f'Vault: {self.vault_path}')
        self.log(f'Skills: {self.skills}')
    
    def log(self, message: str, level: str = 'INFO'):
        """
        Log message to both console and log file.
        
        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().isoformat()
        log_msg = f'[{timestamp}] [{level}] {message}'
        
        # Print to console
        print(log_msg)
        
        # Write to log file
        log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}_orchestrator.log'
        with open(log_file, 'a') as f:
            f.write(log_msg + '\n')
    
    def detect_file_type(self, filepath: Path) -> str:
        """
        Determine file type based on filename prefix.
        
        Returns:
            File type string: linkedin_weekly, email, whatsapp, or unknown
        """
        name = filepath.name.upper()
        
        if name.startswith('LINKEDIN_WEEKLY_TRIGGER'):
            return 'linkedin_weekly'
        elif name.startswith('EMAIL_'):
            return 'email'
        elif name.startswith('WHATSAPP_'):
            return 'whatsapp'
        else:
            return 'unknown'
    
    def build_prompt(self, filepath: Path) -> str:
        """
        Build context-aware prompt based on detected file type.
        Tells Claude exactly which skills to read and what action to take.
        
        Args:
            filepath: Path to the trigger file
            
        Returns:
            Prompt string for Claude
        """
        content = filepath.read_text()
        filename = filepath.name
        file_type = self.detect_file_type(filepath)
        
        # Base prompt shared by all types
        base = f"""You are the AI Employee. A new task has arrived.

DETECTED FILE: {filename}
LOCATION: /Needs_Action/{filename}
CONTENT:
{content}

VAULT PATH: {self.vault_path}
SKILLS LOCATION: {self.skills}

GLOBAL RULES:
- ALWAYS create Plan.md FIRST in /Plans before any action
- NEVER move the trigger file to /Done until a draft or action file is created
- ALWAYS follow Company_Handbook.md rules
- You have FULL permission to read/write files in this vault
- Do NOT ask for permission. Work autonomously.

"""
        
        # Type-specific instructions
        if file_type == 'linkedin_weekly':
            instructions = f"""TASK TYPE: Weekly LinkedIn Progress Post

SKILLS TO READ (in this order):
1. {self.skills}/planning_skill.md
2. {self.skills}/approval_workflow_skill.md
3. {self.skills}/linkedin_posting_skill.md

ADDITIONAL FILES TO READ:
- {self.vault_path}/AI_Employee_Progress.md
- {self.vault_path}/Company_Handbook.md

STEPS:
1. Read all skills and files listed above
2. Create Plan.md in /Plans/PLAN_linkedin_post_weekly_[YYYYMMDD].md
   - Analyze what progress was made this week
   - Review AI_Employee_Progress.md for milestones
   - Draft post content following linkedin_posting_skill.md template
3. Draft LinkedIn post in /Pending_Approval/LINKEDIN_post_weekly_[YYYYMMDD].md
   - Follow the weekly progress post template from linkedin_posting_skill.md
   - Include specific achievements, not generic statements
   - Apply privacy rules from Company_Handbook.md
4. Move trigger file from /Needs_Action to /Done
5. Output: TASK_COMPLETE
"""

        elif file_type == 'email':
            instructions = f"""TASK TYPE: Email Processing

SKILLS TO READ (in this order):
1. {self.skills}/planning_skill.md
2. {self.skills}/approval_workflow_skill.md
3. {self.skills}/email_processing_skill.md
4. {self.skills}/linkedin_posting_skill.md

ADDITIONAL FILES TO READ:
- {self.vault_path}/Company_Handbook.md
- {self.vault_path}/Fake_Client_Projects.md
- Check /Done folder for previous emails from this sender

STEPS:
1. Read all skills and files listed above
2. Determine if sender is a known contact:
   - Check /Done for previous EMAIL_ files from this sender
   - Check Company_Handbook.md Trusted Contacts section
3. Create Plan.md in /Plans/PLAN_[action_type]_[identifier]_[YYYYMMDD].md
   - Document known/unknown contact decision
   - List all auto-approval conditions and whether they pass
   - Determine if email triggers a LinkedIn client success post
4. Based on Plan.md:
   - Known contact + all conditions met: Draft reply in /Approved/EMAIL_SEND_[identifier].md
   - Unknown contact OR any condition fails: Draft reply in /Pending_Approval/EMAIL_SEND_[identifier].md
5. Check if email contains success keywords (thank you, works great, completed, success, perfect, amazing, saved, transformed):
   - If YES: Also draft LinkedIn post in /Pending_Approval/LINKEDIN_post_client_[YYYYMMDD].md
   - Match email to project in Fake_Client_Projects.md
   - Follow linkedin_posting_skill.md client success post template
6. Move trigger file from /Needs_Action to /Done
7. Output: TASK_COMPLETE
"""

        elif file_type == 'whatsapp':
            instructions = f"""TASK TYPE: WhatsApp Message Processing

SKILLS TO READ (in this order):
1. {self.skills}/planning_skill.md
2. {self.skills}/approval_workflow_skill.md

ADDITIONAL FILES TO READ:
- {self.vault_path}/Company_Handbook.md
- {self.vault_path}/Fake_Client_Projects.md

STEPS:
1. Read all skills and files listed above
2. Analyze the WhatsApp message for urgency and intent
3. Create Plan.md in /Plans/PLAN_whatsapp_[identifier]_[YYYYMMDD].md
   - Determine urgency level
   - Identify what action is needed
   - Decide if approval is required
4. Draft response in /Pending_Approval/WHATSAPP_reply_[identifier].md
   - All WhatsApp replies require approval
   - Follow Company_Handbook.md tone rules
5. Check if message contains success keywords:
   - If YES: Also draft LinkedIn post following linkedin_posting_skill.md
6. Move trigger file from /Needs_Action to /Done
7. Output: TASK_COMPLETE
"""

        else:
            instructions = f"""TASK TYPE: Unknown

This file type is not recognized. 
Filename: {filename}

Do NOT process this file. Log a warning and leave it in /Needs_Action.
Output: UNKNOWN_FILE_TYPE
"""

        return base + instructions
    
    def trigger_claude(self, filepath: Path) -> bool:
        """
        Trigger Claude Code with context-aware prompt for a single file.
        
        Args:
            filepath: Path to the trigger file
            
        Returns:
            True if successful, False otherwise
        """
        file_type = self.detect_file_type(filepath)
        self.log(f'Triggering Claude for: {filepath.name} (type: {file_type})')
        
        prompt = self.build_prompt(filepath)
        
        max_attempts = 3
        for attempt in range(max_attempts):
            self.log(f'Claude attempt {attempt + 1}/{max_attempts} for {filepath.name}')
            
            try:
                result = subprocess.run(
                    ['claude', '-p', '--dangerously-skip-permissions', prompt],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=str(self.vault_path),
                )
                
                if result.returncode == 0:
                    self.log(f'✅ Claude completed: {filepath.name}')
                    
                    # Save Claude output to logs
                    if result.stdout:
                        output_log = self.logs / f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_{filepath.stem}_output.md'
                        output_log.write_text(result.stdout)
                        self.log(f'Output saved: {output_log.name}')
                    
                    return True
                else:
                    self.log(f'❌ Claude failed (code {result.returncode}): {filepath.name}', 'ERROR')
                    if result.stderr:
                        self.log(f'Error: {result.stderr}', 'ERROR')
                    
                    # Don't retry on logic errors, only transient failures
                    if attempt == max_attempts - 1:
                        # Move to Failed after all attempts
                        failed_path = self.failed / filepath.name
                        filepath.rename(failed_path)
                        self.log(f'Moved to /Failed: {filepath.name}', 'ERROR')
                    
            except subprocess.TimeoutExpired:
                self.log(f'❌ Claude timed out: {filepath.name}', 'ERROR')
                if attempt == max_attempts - 1:
                    failed_path = self.failed / filepath.name
                    filepath.rename(failed_path)
                    self.log(f'Moved to /Failed: {filepath.name}', 'ERROR')
                    
            except Exception as e:
                self.log(f'❌ Error: {e}', 'ERROR')
                return False
        
        return False
    
    # Priority order: lower number = processed first
    _TYPE_PRIORITY = {
        'whatsapp': 0,
        'linkedin_weekly': 1,
        'email': 2,
        'unknown': 3,
    }

    def _file_sort_key(self, filepath: Path) -> tuple:
        """Return (type_priority, is_not_high_priority) for sorting."""
        file_type = self.detect_file_type(filepath)
        type_prio = self._TYPE_PRIORITY.get(file_type, 99)

        # For emails, peek at frontmatter to check priority
        is_high = False
        if file_type == 'email':
            try:
                head = filepath.read_text(errors='replace')[:500]
                if 'priority: high' in head:
                    is_high = True
            except Exception:
                pass

        # High-priority emails sort before medium/low ones
        return (type_prio, not is_high)

    def check_for_pending_actions(self) -> List[Path]:
        """
        Check /Needs_Action for new files to process.
        Returns files sorted by priority: WHATSAPP > LINKEDIN > high-priority EMAIL > rest.
        """
        if not self.needs_action.exists():
            return []

        new_files = [
            f for f in self.needs_action.glob('*.md')
            if f.name not in self.ignored_files
            and f.name not in self.processing
        ]

        new_files.sort(key=self._file_sort_key)
        return new_files
    
    def update_dashboard(self):
        """
        Update Dashboard.md with current system status.
        """
        dashboard_path = self.vault_path / 'Dashboard.md'
        
        # Count items in each folder
        needs_action_count = len([f for f in self.needs_action.glob('*.md') if f.name not in self.ignored_files])
        done_count = len(list(self.done.glob('*.md')))
        pending_count = len(list(self.pending_approval.glob('*.md')))
        plans_count = len(list(self.plans.glob('*.md')))
        failed_count = len(list(self.failed.glob('*.md')))
        
        content = f"""---
last_updated: {datetime.now().isoformat()}
---

# 🎯 AI Employee Dashboard

## System Status
- **Status**: 🟢 Online
- **Last Check**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Folder Summary
| Folder | Count |
|--------|-------|
| Needs Action | {needs_action_count} |
| Plans | {plans_count} |
| Pending Approval | {pending_count} |
| Done | {done_count} |
| Failed | {failed_count} |

## How to Approve Actions
1. Check /Pending_Approval folder
2. Review the draft
3. Move file to /Approved to execute
4. Move file to /Rejected to deny

## Recent Activity
*Check /Logs for detailed activity*

---
*Auto-updated by Orchestrator*
"""
        
        dashboard_path.write_text(content)
    
    def run_once(self):
        """
        Run one cycle of checking and processing.
        Processes each file individually with its own context.
        """
        # Check for pending files
        pending = self.check_for_pending_actions()
        
        if pending:
            for file in pending:
                self.processing.add(file.name)
                self.log(f'📥 New file detected: {file.name} (type: {self.detect_file_type(file)})')
                
                # Trigger Claude for each file individually
                self.trigger_claude(file)
                
                self.processing.discard(file.name)
        
        # Update dashboard
        self.update_dashboard()
    
    def run(self, check_interval: int = 60):
        """
        Run continuous monitoring loop.
        
        Args:
            check_interval: Seconds between checks
        """
        self.log('=' * 60)
        self.log('ORCHESTRATOR - SILVER TIER')
        self.log('=' * 60)
        self.log(f'Vault: {self.vault_path}')
        self.log(f'Watching: {self.needs_action}')
        self.log(f'Check interval: {check_interval}s')
        self.log(f'Supported file types: LINKEDIN_WEEKLY_TRIGGER, EMAIL_, WHATSAPP_')
        self.log('Press Ctrl+C to stop')
        self.log('=' * 60)
        
        try:
            while True:
                self.run_once()
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            self.log('Orchestrator stopped by user')
        except Exception as e:
            self.log(f'Fatal error: {e}', 'ERROR')
            raise


def main():
    """
    Main entry point for orchestrator.
    """
    load_dotenv()
    
    vault_path = os.getenv('VAULT_PATH')
    check_interval = int(os.getenv('CHECK_INTERVAL', '60'))
    
    if not vault_path:
        print('Error: VAULT_PATH not set in .env file')
        return
    
    # Create and run orchestrator
    orchestrator = Orchestrator(vault_path)
    orchestrator.run(check_interval)


if __name__ == '__main__':
    main()