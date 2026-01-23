"""
Base Watcher Class
Template for all watcher scripts in the AI Employee system
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseWatcher(ABC):
    """
    Abstract base class for all watchers.
    
    All watchers follow the same pattern:
    1. Check for new items at regular intervals
    2. Create action files in the vault's /Needs_Action folder
    3. Log activity for debugging
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher.
        
        Args:
            vault_path: Absolute path to Obsidian vault
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.logs = self.vault_path / 'Logs'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Create necessary folders if they don't exist
        self.needs_action.mkdir(exist_ok=True)
        self.logs.mkdir(exist_ok=True)
        
        self.logger.info(f'Initialized {self.__class__.__name__}')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')
    
    @abstractmethod
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check for new items that need processing.
        
        Must be implemented by each specific watcher.
        Should return a list of items (dicts) to process.
        
        Returns:
            List of items to process, each as a dict with relevant data
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create a markdown file in /Needs_Action for Claude to process.
        
        Must be implemented by each specific watcher.
        Should create a file with frontmatter and content.
        
        Args:
            item: Dict containing item data
            
        Returns:
            Path to created file
        """
        pass
    
    def log_activity(self, message: str, level: str = 'info'):
        """
        Log activity to both console and log file.
        
        Args:
            message: Message to log
            level: Log level ('info', 'warning', 'error')
        """
        # Log to console
        log_func = getattr(self.logger, level)
        log_func(message)
        
        # Log to file
        log_file = self.logs / f'{datetime.now().strftime("%Y-%m-%d")}.log'
        timestamp = datetime.now().isoformat()
        with open(log_file, 'a') as f:
            f.write(f'[{timestamp}] [{level.upper()}] {message}\n')
    
    def run(self):
        """
        Main run loop - continuously checks for updates.
        
        This is the method you call to start the watcher.
        It runs forever until interrupted (Ctrl+C).
        """
        self.log_activity(f'Starting {self.__class__.__name__} watch loop')
        
        try:
            while True:
                try:
                    # Check for new items
                    items = self.check_for_updates()
                    
                    if items:
                        self.log_activity(f'Found {len(items)} new item(s)')
                        
                        # Create action file for each item
                        for item in items:
                            try:
                                filepath = self.create_action_file(item)
                                self.log_activity(f'Created action file: {filepath.name}')
                            except Exception as e:
                                self.log_activity(
                                    f'Error creating action file: {e}',
                                    level='error'
                                )
                    
                    # Wait before next check
                    time.sleep(self.check_interval)
                    
                except KeyboardInterrupt:
                    # Allow clean shutdown with Ctrl+C
                    raise
                    
                except Exception as e:
                    # Log error but keep running
                    self.log_activity(
                        f'Error in watch loop: {e}',
                        level='error'
                    )
                    time.sleep(self.check_interval)
                    
        except KeyboardInterrupt:
            self.log_activity(f'Stopping {self.__class__.__name__} (user interrupted)')
            
        except Exception as e:
            self.log_activity(
                f'Fatal error, stopping {self.__class__.__name__}: {e}',
                level='error'
            )
            raise
    
    def test_connection(self) -> bool:
        """
        Test if the watcher can connect to its source.
        Override in child class if needed.
        
        Returns:
            True if connection successful, False otherwise
        """
        return True
