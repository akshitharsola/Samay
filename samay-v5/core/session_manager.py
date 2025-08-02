"""
Persistent Session Manager
Handles authentication and session persistence with secure credential storage
"""

import asyncio
import logging
import sqlite3
import json
import time
import os
import hashlib
import secrets
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import yaml

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    AUTHENTICATED = "authenticated"
    UNAUTHENTICATED = "unauthenticated"
    TOKEN_EXPIRED = "token_expired"
    ERROR = "error"


@dataclass
class ServiceCredentials:
    service_name: str
    api_key: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    session_cookies: Optional[Dict[str, str]] = None
    profile_path: Optional[str] = None
    expires_at: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UserSession:
    session_id: str
    user_id: str
    created_at: float
    last_active: float
    expires_at: float
    is_active: bool
    metadata: Dict[str, Any]


class CredentialManager:
    """Secure credential storage with encryption"""
    
    def __init__(self, storage_path: str = "storage/credentials.db", master_key: str = None):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        self.master_key = master_key or os.getenv('ENCRYPTION_KEY', self._generate_key())
        self.fernet = self._setup_encryption()
        
        # Initialize database
        self._init_database()

    def _generate_key(self) -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()

    def _setup_encryption(self) -> Fernet:
        """Setup encryption using the master key"""
        try:
            if isinstance(self.master_key, str):
                key = self.master_key.encode()
            else:
                key = self.master_key
                
            # Ensure key is proper length for Fernet
            if len(key) != 44:  # Base64 encoded 32-byte key
                # Derive key from password using PBKDF2
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b'samay_salt_v5',  # In production, use random salt per user
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(key))
            
            return Fernet(key)
            
        except Exception as e:
            logger.error(f"Failed to setup encryption: {e}")
            # Fallback to new key
            return Fernet(Fernet.generate_key())

    def _init_database(self):
        """Initialize SQLite database for credential storage"""
        with sqlite3.connect(self.storage_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT UNIQUE NOT NULL,
                    encrypted_data BLOB NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    encrypted_data BLOB NOT NULL,
                    created_at REAL NOT NULL,
                    last_active REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1
                )
            """)
            
            conn.commit()

    def store_credentials(self, service_name: str, credentials: ServiceCredentials):
        """Encrypt and store service credentials"""
        try:
            # Serialize credentials
            cred_data = asdict(credentials)
            cred_json = json.dumps(cred_data)
            
            # Encrypt data
            encrypted_data = self.fernet.encrypt(cred_json.encode())
            
            # Store in database
            with sqlite3.connect(self.storage_path) as conn:
                now = time.time()
                conn.execute("""
                    INSERT OR REPLACE INTO credentials 
                    (service_name, encrypted_data, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (service_name, encrypted_data, now, now))
                conn.commit()
                
            logger.info(f"Stored credentials for service: {service_name}")
            
        except Exception as e:
            logger.error(f"Failed to store credentials for {service_name}: {e}")
            raise

    def get_credentials(self, service_name: str) -> Optional[ServiceCredentials]:
        """Retrieve and decrypt service credentials"""
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.execute(
                    "SELECT encrypted_data FROM credentials WHERE service_name = ?",
                    (service_name,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return None
                    
                # Decrypt data
                encrypted_data = result[0]
                decrypted_json = self.fernet.decrypt(encrypted_data).decode()
                cred_data = json.loads(decrypted_json)
                
                # Create ServiceCredentials object
                return ServiceCredentials(**cred_data)
                
        except Exception as e:
            logger.error(f"Failed to retrieve credentials for {service_name}: {e}")
            return None

    def delete_credentials(self, service_name: str) -> bool:
        """Delete stored credentials for a service"""
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM credentials WHERE service_name = ?",
                    (service_name,)
                )
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Deleted credentials for service: {service_name}")
                    return True
                else:
                    logger.warning(f"No credentials found for service: {service_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to delete credentials for {service_name}: {e}")
            return False

    def list_stored_services(self) -> List[str]:
        """List all services with stored credentials"""
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.execute("SELECT service_name FROM credentials")
                results = cursor.fetchall()
                return [row[0] for row in results]
                
        except Exception as e:
            logger.error(f"Failed to list stored services: {e}")
            return []


class SessionManager:
    """Handle authentication and session persistence"""
    
    def __init__(self, config_path: str = "config/authentication.yaml", storage_path: str = "storage"):
        self.config_path = config_path
        self.storage_path = Path(storage_path)
        self.config = self._load_config()
        
        # Initialize credential manager
        self.credential_manager = CredentialManager(
            storage_path=str(self.storage_path / "credentials.db")
        )
        
        # Active sessions cache
        self.active_sessions: Dict[str, UserSession] = {}
        
        # Service status cache
        self.service_status: Dict[str, ServiceStatus] = {}
        
        # Load existing sessions
        self._load_active_sessions()

    def _load_config(self) -> Dict[str, Any]:
        """Load authentication configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load authentication config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default authentication configuration"""
        return {
            'session_management': {
                'timeout': 3600,
                'max_sessions': 10,
                'cleanup_interval': 300
            },
            'credential_storage': {
                'encryption_algorithm': 'Fernet',
                'key_rotation_days': 90,
                'backup_enabled': True
            },
            'browser_profiles': {
                'claude': {'profile_path': './profiles/claude', 'persistent': True},
                'gemini': {'profile_path': './profiles/gemini', 'persistent': True},
                'perplexity': {'profile_path': './profiles/perplexity', 'persistent': True}
            }
        }

    def _load_active_sessions(self):
        """Load active sessions from database"""
        try:
            with sqlite3.connect(self.credential_manager.storage_path) as conn:
                cursor = conn.execute("""
                    SELECT session_id, user_id, encrypted_data, created_at, 
                           last_active, expires_at, is_active 
                    FROM sessions 
                    WHERE is_active = 1 AND expires_at > ?
                """, (time.time(),))
                
                for row in cursor.fetchall():
                    session_id, user_id, encrypted_data, created_at, last_active, expires_at, is_active = row
                    
                    try:
                        # Decrypt session data
                        decrypted_data = self.credential_manager.fernet.decrypt(encrypted_data).decode()
                        metadata = json.loads(decrypted_data)
                        
                        session = UserSession(
                            session_id=session_id,
                            user_id=user_id,
                            created_at=created_at,
                            last_active=last_active,
                            expires_at=expires_at,
                            is_active=bool(is_active),
                            metadata=metadata
                        )
                        
                        self.active_sessions[session_id] = session
                        
                    except Exception as e:
                        logger.error(f"Failed to decrypt session {session_id}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to load active sessions: {e}")

    def create_session(self, user_id: str, metadata: Dict[str, Any] = None) -> str:
        """Create a new user session"""
        session_id = f"session_{secrets.token_urlsafe(16)}"
        now = time.time()
        timeout = self.config['session_management']['timeout']
        
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            created_at=now,
            last_active=now,
            expires_at=now + timeout,
            is_active=True,
            metadata=metadata or {}
        )
        
        # Store in database
        self._store_session(session)
        
        # Add to active sessions
        self.active_sessions[session_id] = session
        
        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id

    def _store_session(self, session: UserSession):
        """Store session in database"""
        try:
            # Encrypt session metadata
            metadata_json = json.dumps(session.metadata)
            encrypted_data = self.credential_manager.fernet.encrypt(metadata_json.encode())
            
            with sqlite3.connect(self.credential_manager.storage_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sessions 
                    (session_id, user_id, encrypted_data, created_at, last_active, expires_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session.session_id, session.user_id, encrypted_data,
                    session.created_at, session.last_active, session.expires_at, session.is_active
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store session {session.session_id}: {e}")

    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        session = self.active_sessions.get(session_id)
        
        if session and session.expires_at > time.time():
            # Update last active time
            session.last_active = time.time()
            self._store_session(session)
            return session
        elif session:
            # Session expired
            self.invalidate_session(session_id)
            return None
            
        return None

    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.is_active = False
                self._store_session(session)
                del self.active_sessions[session_id]
                
            logger.info(f"Invalidated session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate session {session_id}: {e}")
            return False

    def store_api_credentials(self, service: str, api_key: str = None, **kwargs):
        """Securely store API keys with encryption"""
        credentials = ServiceCredentials(
            service_name=service,
            api_key=api_key,
            **kwargs
        )
        
        self.credential_manager.store_credentials(service, credentials)
        self.service_status[service] = ServiceStatus.AUTHENTICATED

    def get_api_credentials(self, service: str) -> Optional[ServiceCredentials]:
        """Retrieve and decrypt API keys"""
        return self.credential_manager.get_credentials(service)

    def maintain_sessions(self):
        """Keep API sessions alive and handle token refresh"""
        # Clean up expired sessions
        current_time = time.time()
        expired_sessions = [
            sid for sid, session in self.active_sessions.items()
            if session.expires_at <= current_time
        ]
        
        for session_id in expired_sessions:
            self.invalidate_session(session_id)
            
        # Update service status
        self._update_service_status()

    def _update_service_status(self):
        """Update service status based on stored credentials"""
        stored_services = self.credential_manager.list_stored_services()
        
        for service in stored_services:
            credentials = self.credential_manager.get_credentials(service)
            if credentials:
                # Check if credentials are expired
                if credentials.expires_at and credentials.expires_at <= time.time():
                    self.service_status[service] = ServiceStatus.TOKEN_EXPIRED
                else:
                    self.service_status[service] = ServiceStatus.AUTHENTICATED
            else:
                self.service_status[service] = ServiceStatus.UNAUTHENTICATED

    def get_service_status(self) -> Dict[str, ServiceStatus]:
        """Check all service availability and authentication status"""
        self._update_service_status()
        return self.service_status.copy()

    def get_browser_profile_path(self, service: str) -> Optional[str]:
        """Get browser profile path for a service"""
        browser_profiles = self.config.get('browser_profiles', {})
        service_config = browser_profiles.get(service, {})
        return service_config.get('profile_path')

    def is_profile_persistent(self, service: str) -> bool:
        """Check if browser profile should be persistent"""
        browser_profiles = self.config.get('browser_profiles', {})
        service_config = browser_profiles.get(service, {})
        return service_config.get('persistent', False)

    def cleanup_expired_sessions(self):
        """Clean up expired sessions from database"""
        try:
            with sqlite3.connect(self.credential_manager.storage_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM sessions WHERE expires_at <= ? OR is_active = 0",
                    (time.time(),)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} expired sessions")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")

    def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for a user"""
        return [
            session for session in self.active_sessions.values()
            if session.user_id == user_id and session.expires_at > time.time()
        ]

    def revoke_all_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user"""
        user_sessions = self.get_user_sessions(user_id)
        revoked_count = 0
        
        for session in user_sessions:
            if self.invalidate_session(session.session_id):
                revoked_count += 1
                
        return revoked_count

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        active_count = len(self.active_sessions)
        unique_users = len(set(session.user_id for session in self.active_sessions.values()))
        
        return {
            'active_sessions': active_count,
            'unique_users': unique_users,
            'stored_services': len(self.credential_manager.list_stored_services()),
            'service_status': dict(self.service_status)
        }


# Premium Account Manager for browser automation
class PremiumAccountManager:
    """Manage user's premium subscriptions and persistent sessions"""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.user_accounts = self._load_premium_accounts()

    def _load_premium_accounts(self) -> Dict[str, Dict[str, Any]]:
        """Load premium account configuration"""
        config = self.session_manager.config
        return config.get('premium_accounts', {})

    def get_subscription_type(self, service: str) -> Optional[str]:
        """Get subscription type for a service"""
        account_info = self.user_accounts.get(service, {})
        return account_info.get('subscription_type')

    def get_premium_features(self, service: str) -> List[str]:
        """Get available premium features for a service"""
        account_info = self.user_accounts.get(service, {})
        return account_info.get('features', [])

    def validate_subscription_access(self, service: str, feature: str) -> bool:
        """Verify premium features are available"""
        features = self.get_premium_features(service)
        return feature in features

    def maintain_login_sessions(self):
        """Keep user logged in to their premium accounts"""
        # This would integrate with browser automation
        # to maintain persistent login sessions
        for service in self.user_accounts.keys():
            profile_path = self.session_manager.get_browser_profile_path(service)
            if profile_path and self.session_manager.is_profile_persistent(service):
                logger.info(f"Maintaining login session for {service} using profile: {profile_path}")


# Example usage
async def main():
    """Test the session manager"""
    session_manager = SessionManager()
    
    # Create a session
    session_id = session_manager.create_session("user123", {"test": True})
    print(f"Created session: {session_id}")
    
    # Store API credentials
    session_manager.store_api_credentials("weather", api_key="test_key")
    
    # Get session
    session = session_manager.get_session(session_id)
    print(f"Retrieved session: {session.session_id if session else 'None'}")
    
    # Get service status
    status = session_manager.get_service_status()
    print(f"Service status: {status}")
    
    # Get stats
    stats = session_manager.get_session_stats()
    print(f"Session stats: {stats}")


if __name__ == "__main__":
    asyncio.run(main())