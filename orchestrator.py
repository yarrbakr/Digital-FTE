"""
Orchestrator - Coordinates Watchers and Claude Code
Main entry point for the AI Employee system
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
    2. Triggers Claude Code to process them
    3. Logs all activity
    """
    
    def __init__(self, vault_path: str, skill_path: str = None):
        """
        Initialize orchestrator.
        
        Args:
            vault_path: Path to Obsidian vault
            skill_path: Path to Agent Skill file (optional)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.logs = self.vault_path / 'Logs'
        
        # Default skill path
        if skill_path:
            self.skill_path = Path(skill_path)
        else:
            self.skill_path = self.vault_path / 'agent_skills' / 'email_processing_skill.md'
        
        # Create folders if needed
        self.needs_action.mkdir(exist_ok=True)
        self.done.mkdir(exist_ok=True)
        self.logs.mkdir(exist_ok=True)
        
        # Track processed files to avoid reprocessing
        self.processed_files = set()
        
        self.log('Orchestrator initialized')
        self.log(f'Vault: {self.vault_path}')
        self.log(f'Skill: {self.skill_path}')
    
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
    
    def check_for_pending_actions(self) -> List[Path]:
        """
        Check /Needs_Action for files to process.
        
        Returns:
            List of file paths that need processing
        """
        if not self.needs_action.exists():
            return []
        
        # Get all .md files in Needs_Action
        all_files = list(self.needs_action.glob('*.md'))
        
        # Filter out already processed
        new_files = [
            f for f in all_files
            if f not in self.processed_files
        ]
        
        return new_files
    
    def trigger_claude(self, files: List[Path]) -> bool:
        """
        Trigger Claude Code to process files.
        
        Args:
            files: List of files to process
            
        Returns:
            True if successful, False otherwise
        """
        if not files:
            return True
        
        self.log(f'Triggering Claude to process {len(files)} file(s)')
        
        # Build prompt that references the skill
        prompt = f"""Use the email processing skill located at {self.skill_path}.

Process all pending items in /Needs_Action folder. There are {len(files)} new items to process.

IMPORTANT: You have FULL permission to:
- Read/write all files in this vault
- Create files in any folder
- Move files between folders
- Update Dashboard.md
- You have FULL WRITE ACCESS to the vault to complete email processing.

Do NOT ask for permission. Just do the work.

Follow the skill instructions to:
1. Read each email file in /Needs_Action
2. Assess priority for each email
3. Draft responses if needed (create files directly)
4. Update Dashboard.md with current status
5. Move ALL processed files to /Done folder

When ALL files are in /Done and Dashboard is updated, output: TASK_COMPLETE

Work autonomously until complete.
"""
        
        # run with retry logic - keep trying until files move to /Done folder
        max_attempts = 3 
        for attempt in range(max_attempts):
            self.log(f'Claude attempt {attempt + 1}/{max_attempts}')
            cmd = ['claude', '-p', '--dangerously-skip-permissions', prompt]
            
            try:
                # Run Claude Code from the vault directory
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                    cwd=str(self.vault_path),
                    # Set working directory here
                )
                
                if result.returncode == 0:
                    self.log('Claude processing completed successfully')
                    
                    # Log Claude's output
                    if result.stdout:
                        output_log = self.logs / f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_claude_output.md'
                        output_log.write_text(result.stdout)
                        self.log(f'Claude output saved to {output_log.name}')
                    
                    # Mark files as processed
                    for f in files:
                        self.processed_files.add(f)
                    
                    return True
                else:
                    self.log(f'Claude processing failed with code {result.returncode}', 'ERROR')
                    if result.stderr:
                        self.log(f'Error: {result.stderr}', 'ERROR')
                    return False
                    
            except subprocess.TimeoutExpired:
                self.log('Claude processing timed out', 'ERROR')
                return False
            except Exception as e:
                self.log(f'Error triggering Claude: {e}', 'ERROR')
                return False
        
        # If we get here, all attempts failed
        self.log('Claude failed after all attempts', 'ERROR')
        return False
    
    def update_dashboard(self):
        """
        Update Dashboard.md with current status.
        """
        dashboard_path = self.vault_path / 'Dashboard.md'
        
        # Count items in each folder
        needs_action_count = len(list(self.needs_action.glob('*.md')))
        done_count = len(list(self.done.glob('*.md')))
        
        # Create dashboard content
        content = f"""---
last_updated: {datetime.now().isoformat()}
---

# 🎯 AI Employee Dashboard

## Status
- **System Status**: 🟢 Online
- **Last Check**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Pending Actions
- **Needs Action**: {needs_action_count} item(s)
- **Completed**: {done_count} item(s)

## Recent Activity
*Check logs for detailed activity*

---
*Auto-updated by Orchestrator*
"""
        
        dashboard_path.write_text(content)
    
    def run_once(self):
        """
        Run one cycle of checking and processing.
        """
        self.log('Running check cycle...')
        
        # Check for pending files
        pending = self.check_for_pending_actions()
        
        if pending:
            self.log(f'Found {len(pending)} pending action(s)')
            
            # Trigger Claude to process
            success = self.trigger_claude(pending)
            
            if not success:
                self.log('Claude processing failed, will retry next cycle', 'WARNING')
        else:
            self.log('No pending actions found')
        
        # Update dashboard
        self.update_dashboard()
    
    def run(self, check_interval: int = 60):
        """
        Run continuous monitoring loop.
        
        Args:
            check_interval: Seconds between checks
        """
        self.log(f'Starting orchestrator loop (checking every {check_interval}s)')
        self.log('Press Ctrl+C to stop')
        
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
    # Load environment variables
    load_dotenv()
    
    vault_path = os.getenv('VAULT_PATH')
    skill_path = os.getenv('SKILL_PATH')  # Optional
    check_interval = int(os.getenv('CHECK_INTERVAL', '60'))
    
    if not vault_path:
        print('Error: VAULT_PATH not set in .env file')
        return
    
    print('=== AI Employee Orchestrator ===')
    print(f'Vault: {vault_path}')
    print(f'Check interval: {check_interval}s')
    print()
    
    # Create and run orchestrator
    orchestrator = Orchestrator(vault_path, skill_path)
    orchestrator.run(check_interval)


if __name__ == '__main__':
    main()