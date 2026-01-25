# Test Redis connection
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

print("=" * 60)
print("🔍 Redis Configuration Test")
print("=" * 60)
print(f"\n📋 REDIS_URL: {REDIS_URL}")

if not REDIS_URL:
    print("\n❌ REDIS_URL not set in .env file")
    print("💡 Add: REDIS_URL=redis://your-redis-url")
    exit(1)

try:
    import redis
    print("\n✅ Redis package installed")
    
    # Try to connect
    print(f"\n🔗 Attempting to connect to: {REDIS_URL[:20]}...")
    client = redis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )
    
    # Test ping
    response = client.ping()
    print(f"✅ Connection successful! Ping response: {response}")
    
    # Test set/get
    client.set("test_key", "Hello Redis!", ex=10)
    value = client.get("test_key")
    print(f"✅ Set/Get test: {value}")
    
    # Get info
    info = client.info("server")
    print(f"\n📊 Redis Server Info:")
    print(f"   Version: {info.get('redis_version', 'unknown')}")
    print(f"   Mode: {info.get('redis_mode', 'unknown')}")
    
    print("\n" + "=" * 60)
    print("🎉 Redis is working perfectly!")
    print("=" * 60)
    
except ImportError:
    print("\n❌ Redis package not installed")
    print("💡 Run: pip install redis hiredis")
    exit(1)
    
except redis.exceptions.ConnectionError as e:
    print(f"\n❌ Connection failed: {e}")
    print("\n💡 Check:")
    print("   1. Is your Redis server running?")
    print("   2. Is the REDIS_URL correct?")
    print("   3. Can your network reach the Redis server?")
    exit(1)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    exit(1)
