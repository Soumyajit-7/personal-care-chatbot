"""
Docker entrypoint script to wait for PostgreSQL and Redis
before starting the main application.
"""

import os
import sys
import time
import subprocess

def wait_for_postgres():
    """Wait for PostgreSQL to be ready"""
    print("🔍 Waiting for PostgreSQL...")
    max_retries = 30
    retries = 0
    
    postgres_host = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_user = os.getenv("POSTGRES_USER", "chatbot_user")
    
    while retries < max_retries:
        try:
            result = subprocess.run(
                ["pg_isready", "-h", postgres_host, "-p", postgres_port, "-U", postgres_user],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                print("✅ PostgreSQL is ready!")
                return True
        except subprocess.TimeoutExpired:
            print("⏱️  PostgreSQL check timed out, retrying...")
        except Exception as e:
            print(f"⚠️  Error checking PostgreSQL: {e}")
        
        retries += 1
        print(f"   Retry {retries}/{max_retries}...")
        time.sleep(1)
    
    print("❌ PostgreSQL failed to become ready")
    return False

def wait_for_redis():
    """Wait for Redis to be ready"""
    print("🔍 Waiting for Redis...")
    max_retries = 30
    retries = 0
    
    redis_host = os.getenv("REDIS_HOST", "redis")
    
    while retries < max_retries:
        try:
            result = subprocess.run(
                ["redis-cli", "-h", redis_host, "ping"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if "PONG" in result.stdout:
                print("✅ Redis is ready!")
                return True
        except subprocess.TimeoutExpired:
            print("⏱️  Redis check timed out, retrying...")
        except Exception as e:
            print(f"⚠️  Error checking Redis: {e}")
        
        retries += 1
        print(f"   Retry {retries}/{max_retries}...")
        time.sleep(1)
    
    print("❌ Redis failed to become ready")
    return False

def main():
    """Main entrypoint logic"""
    print("="*60)
    print("🚀 Starting Personal Care Chatbot")
    print("="*60)
    
    # Wait for services
    postgres_ready = wait_for_postgres()
    redis_ready = wait_for_redis()
    
    if not postgres_ready or not redis_ready:
        print("\n❌ Failed to connect to required services")
        sys.exit(1)
    
    print("\n✅ All services are ready!")
    print("="*60)
    print()
    
    # Execute the command passed to the container
    if len(sys.argv) > 1:
        print(f"▶️  Executing: {' '.join(sys.argv[1:])}")
        print()
        os.execvp(sys.argv[1], sys.argv[1:])
    else:
        print("❌ No command specified")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
