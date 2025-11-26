import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import aiofiles
from pathlib import Path

class CookieManager:
    """Manages multiple Perplexity accounts and their cookies."""
    
    def __init__(self, storage_file: str = "accounts.json"):
        self.storage_file = storage_file
        self.storage_path = Path(storage_file)
        self.accounts = {}
        self.load_accounts()
    
    def load_accounts(self):
        """Load accounts from storage file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.accounts = data.get('accounts', {})
            except (json.JSONDecodeError, FileNotFoundError):
                self.accounts = {}
        else:
            self.accounts = {}
    
    async def save_accounts(self):
        """Save accounts to storage file."""
        data = {
            'accounts': self.accounts,
            'last_updated': datetime.now().isoformat()
        }
        async with aiofiles.open(self.storage_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(data, indent=2))
    
    def convert_chrome_cookies_to_perplexity(self, chrome_cookies: List[Dict]) -> Dict[str, str]:
        """Convert Chrome extension cookie format to perplexity wrapper format."""
        perplexity_cookies = {}
        for cookie in chrome_cookies:
            if cookie.get('domain') in ['.perplexity.ai', 'www.perplexity.ai']:
                perplexity_cookies[cookie['name']] = cookie['value']
        return perplexity_cookies
    
    async def add_account(self, account_name: str, chrome_cookies: List[Dict], display_name: Optional[str] = None) -> Dict:
        """Add a new account with Chrome extension cookies."""
        if account_name in self.accounts:
            raise ValueError(f"Account '{account_name}' already exists")
        
        # Convert cookies
        perplexity_cookies = self.convert_chrome_cookies_to_perplexity(chrome_cookies)
        
        # Validate essential cookies are present
        essential_cookies = ['__Secure-next-auth.session-token']
        missing_cookies = [cookie for cookie in essential_cookies if cookie not in perplexity_cookies]
        
        if missing_cookies:
            raise ValueError(f"Missing essential cookies: {', '.join(missing_cookies)}")
        
        # Add account
        self.accounts[account_name] = {
            'name': display_name or account_name,
            'cookies': perplexity_cookies,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'last_validated': None
        }
        
        await self.save_accounts()
        return self.accounts[account_name]
    
    async def update_account(self, account_name: str, chrome_cookies: List[Dict]) -> Dict:
        """Update existing account with new cookies."""
        if account_name not in self.accounts:
            raise ValueError(f"Account '{account_name}' not found")
        
        # Convert cookies
        perplexity_cookies = self.convert_chrome_cookies_to_perplexity(chrome_cookies)
        
        # Validate essential cookies
        essential_cookies = ['__Secure-next-auth.session-token']
        missing_cookies = [cookie for cookie in essential_cookies if cookie not in perplexity_cookies]
        
        if missing_cookies:
            raise ValueError(f"Missing essential cookies: {', '.join(missing_cookies)}")
        
        # Update account
        self.accounts[account_name]['cookies'] = perplexity_cookies
        self.accounts[account_name]['status'] = 'active'
        self.accounts[account_name]['last_validated'] = datetime.now().isoformat()
        
        await self.save_accounts()
        return self.accounts[account_name]
    
    def get_account_cookies(self, account_name: str) -> Dict[str, str]:
        """Get cookies for a specific account."""
        if account_name not in self.accounts:
            raise ValueError(f"Account '{account_name}' not found")
        
        return self.accounts[account_name]['cookies'].copy()
    
    def get_all_accounts(self) -> Dict[str, Dict]:
        """Get all accounts info (without cookies for security)."""
        result = {}
        for name, account in self.accounts.items():
            result[name] = {
                'name': account['name'],
                'status': account['status'],
                'created_at': account['created_at'],
                'last_used': account['last_used'],
                'last_validated': account['last_validated']
            }
        return result
    
    async def delete_account(self, account_name: str) -> bool:
        """Delete an account."""
        if account_name in self.accounts:
            del self.accounts[account_name]
            await self.save_accounts()
            return True
        return False
    
    async def mark_account_used(self, account_name: str):
        """Mark account as used (update last_used timestamp)."""
        if account_name in self.accounts:
            self.accounts[account_name]['last_used'] = datetime.now().isoformat()
            await self.save_accounts()
    
    async def mark_account_validated(self, account_name: str, is_valid: bool):
        """Mark account validation status."""
        if account_name in self.accounts:
            self.accounts[account_name]['status'] = 'valid' if is_valid else 'invalid'
            self.accounts[account_name]['last_validated'] = datetime.now().isoformat()
            await self.save_accounts()
