"""
API Key Management Script
Helps administrators manage API keys for production use

Usage:
    python scripts/manage_api_keys.py list
    python scripts/manage_api_keys.py add --user-id admin1 --role admin --rate-limit 100
    python scripts/manage_api_keys.py revoke sk-test-key-12345
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.api.auth import api_key_manager


def list_keys():
    """List all API keys (masked for security)"""
    print("\n" + "=" * 80)
    print("API Keys")
    print("=" * 80)
    
    if not api_key_manager.api_keys:
        print("No API keys configured.")
        return
    
    print(f"\n{'Key (masked)':<25} {'User ID':<20} {'Role':<15} {'Rate Limit':<15}")
    print("-" * 80)
    
    for key, info in api_key_manager.api_keys.items():
        masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
        print(f"{masked_key:<25} {info['user_id']:<20} {info['role']:<15} {info['rate_limit']:<15}")
    
    print(f"\nTotal: {len(api_key_manager.api_keys)} keys")
    print("=" * 80)


def add_key(user_id: str, role: str = "user", rate_limit: int = 30, description: str = ""):
    """Add a new API key"""
    import secrets
    
    # Generate a secure random API key
    api_key = f"sk-{secrets.token_hex(16)}"
    
    api_key_manager.add_key(
        api_key=api_key,
        user_id=user_id,
        role=role,
        rate_limit=rate_limit,
        description=description
    )
    
    print("\n" + "=" * 80)
    print("✅ New API Key Created")
    print("=" * 80)
    print(f"\nAPI Key: {api_key}")
    print(f"User ID: {user_id}")
    print(f"Role: {role}")
    print(f"Rate Limit: {rate_limit} requests/minute")
    if description:
        print(f"Description: {description}")
    print("\n⚠️  IMPORTANT: Save this key securely. It cannot be retrieved later!")
    print("=" * 80)
    
    # Optionally save to environment file
    save_to_env = input("\nSave to .env file? (y/n): ").lower().strip()
    if save_to_env == 'y':
        _save_key_to_env(api_key, user_id, role, rate_limit, description)


def revoke_key(api_key: str):
    """Revoke an API key"""
    success = api_key_manager.revoke_key(api_key)
    
    if success:
        print(f"\n✅ API key revoked successfully: {api_key[:8]}...")
    else:
        print(f"\n❌ API key not found: {api_key[:8]}...")


def _save_key_to_env(api_key: str, user_id: str, role: str, rate_limit: int, description: str):
    """Save API key to .env file"""
    env_file = project_root / ".env"
    
    # Load existing keys
    existing_keys = {}
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("API_KEYS="):
                    try:
                        keys_json = line.split("=", 1)[1].strip().strip("'\"")
                        existing_keys = json.loads(keys_json)
                    except:
                        pass
    
    # Add new key
    existing_keys[api_key] = {
        "user_id": user_id,
        "role": role,
        "rate_limit": rate_limit,
        "description": description
    }
    
    # Write back to .env
    with open(env_file, 'a', encoding='utf-8') as f:
        f.write(f"\nAPI_KEYS='{json.dumps(existing_keys)}'\n")
    
    print(f"✅ API key saved to {env_file}")


def main():
    parser = argparse.ArgumentParser(description="Manage API Keys")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    subparsers.add_parser("list", help="List all API keys")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new API key")
    add_parser.add_argument("--user-id", required=True, help="User ID")
    add_parser.add_argument("--role", default="user", choices=["user", "admin", "moderator"],
                          help="User role (default: user)")
    add_parser.add_argument("--rate-limit", type=int, default=30,
                          help="Rate limit in requests per minute (default: 30)")
    add_parser.add_argument("--description", default="", help="Key description")
    
    # Revoke command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke an API key")
    revoke_parser.add_argument("api_key", help="API key to revoke")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_keys()
    elif args.command == "add":
        add_key(args.user_id, args.role, args.rate_limit, args.description)
    elif args.command == "revoke":
        revoke_key(args.api_key)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
