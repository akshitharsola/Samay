#!/usr/bin/env python3
"""
Samay v3 - Gmail OTP Fetcher
============================
Automatically retrieves OTP codes from Gmail
Based on Comprehensive Implementation Plan
"""

import os
import re
import time
import base64
import email
import pickle
from typing import Optional
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import bs4

load_dotenv()

class GmailOTPFetcher:
    """Fetches OTP codes from Gmail automatically"""
    
    # Gmail API scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    # Common OTP patterns
    OTP_PATTERNS = [
        re.compile(r'\b(\d{6})\b'),          # 6-digit codes (most common)
        re.compile(r'\b(\d{4})\b'),          # 4-digit codes  
        re.compile(r'\b(\d{8})\b'),          # 8-digit codes
        re.compile(r'code[:\s]+(\d{4,8})', re.IGNORECASE),  # "Code: 123456"
        re.compile(r'verification[:\s]+(\d{4,8})', re.IGNORECASE),  # "Verification: 123456"
    ]
    
    def __init__(self, credentials_path: str = None, token_path: str = None):
        self.credentials_path = credentials_path or os.getenv('GMAIL_CREDENTIALS_PATH', 'otp_service/secrets/credentials.json')
        self.token_path = token_path or os.getenv('GMAIL_TOKEN_PATH', 'otp_service/secrets/token.pkl')
        
        # Ensure directories exist
        Path(self.credentials_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.token_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.service = None
    
    def authenticate(self) -> bool:
        """Authenticate with Gmail API"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print("🔄 Refreshing Gmail API token...")
                    creds.refresh(Request())
                except Exception as e:
                    print(f"❌ Token refresh failed: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    print(f"❌ Gmail credentials not found at: {self.credentials_path}")
                    print("📋 To set up Gmail API:")
                    print("   1. Go to https://console.developers.google.com/")
                    print("   2. Create a new project or select existing")
                    print("   3. Enable Gmail API")
                    print("   4. Create credentials (Desktop application)")
                    print("   5. Download credentials.json")
                    print(f"   6. Place it at: {self.credentials_path}")
                    return False
                
                print("🔐 Starting Gmail API authentication flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            print("✅ Gmail API authenticated successfully")
            return True
        except Exception as e:
            print(f"❌ Gmail API setup failed: {e}")
            return False
    
    def get_recent_messages(self, to_email: str, max_age_minutes: int = 10) -> list:
        """Get recent messages sent to the specified email"""
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            # Build query for recent messages
            query = f'to:{to_email} newer_than:{max_age_minutes}m'
            
            print(f"🔍 Searching for messages: {query}")
            
            # Search for messages
            results = self.service.users().messages().list(
                userId='me', 
                q=query,
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            print(f"📧 Found {len(messages)} recent messages")
            
            return messages
            
        except Exception as e:
            print(f"❌ Failed to fetch messages: {e}")
            return []
    
    def extract_message_text(self, message_id: str) -> str:
        """Extract text content from a Gmail message"""
        if not self.service:
            return ""
        
        try:
            # Get full message
            message = self.service.users().messages().get(
                userId='me', 
                id=message_id,
                format='raw'
            ).execute()
            
            # Decode the raw message
            raw_data = message['raw']
            decoded_data = base64.urlsafe_b64decode(raw_data)
            
            # Parse email
            email_message = email.message_from_bytes(decoded_data)
            
            # Extract text content
            text_content = ""
            
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        text_content += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    elif part.get_content_type() == "text/html":
                        html_content = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        # Extract text from HTML
                        soup = bs4.BeautifulSoup(html_content, 'html.parser')
                        text_content += soup.get_text()
            else:
                text_content = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            return text_content
            
        except Exception as e:
            print(f"❌ Failed to extract message text: {e}")
            return ""
    
    def find_otp_in_text(self, text: str, service_name: str = "") -> Optional[str]:
        """Extract OTP code from text using multiple patterns"""
        if not text:
            return None
        
        print(f"🔍 Searching for OTP in message text...")
        
        # Service-specific keywords to help identify the right code
        service_keywords = {
            "claude": ["claude", "anthropic"],
            "gemini": ["gemini", "google", "bard"],
            "perplexity": ["perplexity"]
        }
        
        # Try each pattern
        for pattern in self.OTP_PATTERNS:
            matches = pattern.findall(text)
            
            if matches:
                print(f"🎯 Found potential codes: {matches}")
                
                # If we have service context, prefer codes near service keywords
                if service_name and service_name in service_keywords:
                    keywords = service_keywords[service_name]
                    text_lower = text.lower()
                    
                    for keyword in keywords:
                        if keyword in text_lower:
                            # Find the position of the keyword
                            keyword_pos = text_lower.find(keyword)
                            
                            # Look for codes near this keyword (within 200 characters)
                            nearby_text = text[max(0, keyword_pos - 100):keyword_pos + 100]
                            nearby_matches = pattern.findall(nearby_text)
                            
                            if nearby_matches:
                                code = nearby_matches[0]
                                print(f"✅ Found {service_name} OTP near keyword '{keyword}': {code}")
                                return code
                
                # If no service-specific match, return the first reasonable code
                for match in matches:
                    # Prefer 6-digit codes (most common for OTP)
                    if len(match) == 6:
                        print(f"✅ Found 6-digit OTP: {match}")
                        return match
                
                # Fallback to first match
                code = matches[0]
                print(f"✅ Found OTP code: {code}")
                return code
        
        print("❌ No OTP pattern found in text")
        return None
    
    def get_latest_otp(self, to_email: str, service_name: str = "", max_wait_seconds: int = 90) -> Optional[str]:
        """
        Get the latest OTP code sent to the specified email
        
        Args:
            to_email: Email address to search for
            service_name: Service name for context (claude, gemini, perplexity)
            max_wait_seconds: Maximum time to wait for new messages
            
        Returns:
            OTP code string or None if not found
        """
        print(f"🔍 Looking for OTP sent to: {to_email}")
        if service_name:
            print(f"🎯 Service context: {service_name}")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            messages = self.get_recent_messages(to_email, max_age_minutes=5)
            
            for message in messages:
                message_id = message['id']
                text_content = self.extract_message_text(message_id)
                
                if text_content:
                    otp = self.find_otp_in_text(text_content, service_name)
                    if otp:
                        return otp
            
            if time.time() - start_time < max_wait_seconds:
                print(f"⏳ No OTP found yet, waiting 5 seconds... ({int(max_wait_seconds - (time.time() - start_time))}s remaining)")
                time.sleep(5)
        
        print(f"❌ No OTP found within {max_wait_seconds} seconds")
        return None
    
    def test_connection(self) -> bool:
        """Test the Gmail API connection"""
        print("🧪 Testing Gmail API connection...")
        
        if not self.authenticate():
            return False
        
        try:
            # Try to get profile info
            profile = self.service.users().getProfile(userId='me').execute()
            email_address = profile.get('emailAddress', 'Unknown')
            
            print(f"✅ Connected to Gmail account: {email_address}")
            return True
            
        except Exception as e:
            print(f"❌ Gmail API test failed: {e}")
            return False


def main():
    """Test the Gmail OTP fetcher"""
    fetcher = GmailOTPFetcher()
    
    print("🚀 Samay v3 - Gmail OTP Fetcher Test")
    print("=" * 50)
    
    print("\n🎛️  Options:")
    print("1. Test Gmail API connection")
    print("2. Get latest OTP for email")
    print("3. Setup Gmail API credentials")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        fetcher.test_connection()
    
    elif choice == "2":
        if not fetcher.test_connection():
            print("❌ Gmail API not working. Set up credentials first.")
            return
        
        email_address = input("Enter email address to search: ").strip()
        if not email_address:
            email_address = os.getenv("CLAUDE_EMAIL", "")
            if email_address:
                print(f"Using email from .env: {email_address}")
            else:
                print("❌ No email address provided")
                return
        
        service_name = input("Enter service name (claude/gemini/perplexity) or press Enter: ").strip()
        
        print(f"\n🔍 Searching for OTP sent to: {email_address}")
        otp = fetcher.get_latest_otp(email_address, service_name, max_wait_seconds=30)
        
        if otp:
            print(f"✅ Found OTP: {otp}")
        else:
            print("❌ No OTP found")
    
    elif choice == "3":
        print("\n📋 Gmail API Setup Instructions:")
        print("=" * 40)
        print("1. Go to https://console.developers.google.com/")
        print("2. Create a new project or select existing project")
        print("3. Enable the Gmail API for your project")
        print("4. Go to 'Credentials' and create credentials")
        print("5. Choose 'Desktop application' as the application type")
        print("6. Download the credentials JSON file")
        print(f"7. Place the file at: {fetcher.credentials_path}")
        print("8. Run this test again to authenticate")
        
        # Check if credentials file exists
        if os.path.exists(fetcher.credentials_path):
            print(f"\n✅ Credentials file found at: {fetcher.credentials_path}")
            print("🔄 You can now test the connection (option 1)")
        else:
            print(f"\n❌ Credentials file not found at: {fetcher.credentials_path}")
            print("📥 Please download and place the credentials file first")
    
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()