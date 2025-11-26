"""
MatruRaksha AI - Setup Verification Script
Run this to verify your environment is configured correctly
"""

import os
import sys
from dotenv import load_dotenv

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_check(message, status):
    """Print a check with status"""
    if status:
        print(f"{Colors.GREEN}✅{Colors.END} {message}")
        return True
    else:
        print(f"{Colors.RED}❌{Colors.END} {message}")
        return False

def print_warning(message):
    """Print a warning"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    """Print info"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def check_environment():
    """Check environment variables"""
    print("\n" + "="*60)
    print("🔍 Checking Environment Variables")
    print("="*60)
    
    load_dotenv()
    
    checks_passed = 0
    total_checks = 4
    
    # Check Supabase URL
    supabase_url = os.getenv("SUPABASE_URL")
    if print_check("SUPABASE_URL is set", supabase_url is not None):
        checks_passed += 1
        if supabase_url and "supabase.co" in supabase_url:
            print(f"   📍 {supabase_url[:50]}...")
    
    # Check Supabase Key
    supabase_key = os.getenv("SUPABASE_KEY")
    if print_check("SUPABASE_KEY is set", supabase_key is not None):
        checks_passed += 1
        if supabase_key:
            print(f"   🔑 {supabase_key[:20]}...")
    
    # Check Telegram Token
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if print_check("TELEGRAM_BOT_TOKEN is set", telegram_token is not None):
        checks_passed += 1
        if telegram_token:
            print(f"   🤖 {telegram_token[:20]}...")
    
    # Check Gemini Key
    gemini_key = os.getenv("GEMINI_API_KEY")
    if print_check("GEMINI_API_KEY is set", gemini_key is not None):
        checks_passed += 1
        if gemini_key:
            print(f"   🤖 {gemini_key[:20]}...")
    else:
        print_warning("   Gemini AI won't be available for document analysis")
    
    return checks_passed, total_checks

def check_dependencies():
    """Check if required packages are installed"""
    print("\n" + "="*60)
    print("📦 Checking Dependencies")
    print("="*60)
    
    dependencies = {
        "fastapi": "FastAPI web framework",
        "uvicorn": "ASGI server",
        "supabase": "Supabase client",
        "telegram": "Telegram bot library",
        "google.generativeai": "Gemini AI (optional)",
        "dotenv": "Environment variables",
        "pydantic": "Data validation"
    }
    
    checks_passed = 0
    total_checks = len(dependencies)
    
    for package, description in dependencies.items():
        try:
            if package == "telegram":
                import telegram
            elif package == "dotenv":
                from dotenv import load_dotenv
            elif package == "google.generativeai":
                import google.generativeai as genai
            else:
                __import__(package)
            
            print_check(f"{package} - {description}", True)
            checks_passed += 1
        except ImportError:
            print_check(f"{package} - {description}", False)
            if package == "google.generativeai":
                print_warning(f"   Install with: pip install google-generativeai")
            else:
                print_warning(f"   Install with: pip install {package}")
    
    return checks_passed, total_checks

def check_supabase_connection():
    """Check Supabase connection"""
    print("\n" + "="*60)
    print("🔌 Checking Supabase Connection")
    print("="*60)
    
    try:
        from supabase import create_client
        load_dotenv()
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print_check("Supabase connection", False)
            print_warning("   Missing credentials in .env file")
            return 0, 2
        
        # Try to create client
        client = create_client(supabase_url, supabase_key)
        print_check("Supabase client created", True)
        
        # Try to query mothers table
        try:
            result = client.table("mothers").select("*").limit(1).execute()
            print_check("Can query 'mothers' table", True)
            
            # Check if due_date column exists
            if result.data and len(result.data) > 0:
                if 'due_date' in result.data[0]:
                    print_check("'due_date' column exists", True)
                else:
                    print_check("'due_date' column exists", False)
                    print_warning("   Run: ALTER TABLE mothers ADD COLUMN due_date DATE;")
            
            return 2, 2
        except Exception as e:
            print_check("Can query 'mothers' table", False)
            print_warning(f"   Error: {str(e)[:100]}")
            return 1, 2
            
    except Exception as e:
        print_check("Supabase connection", False)
        print_warning(f"   Error: {str(e)[:100]}")
        return 0, 2

def check_telegram_bot():
    """Check Telegram bot token"""
    print("\n" + "="*60)
    print("🤖 Checking Telegram Bot")
    print("="*60)
    
    try:
        import requests
        load_dotenv()
        
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not token:
            print_check("Telegram bot token", False)
            print_warning("   Set TELEGRAM_BOT_TOKEN in .env file")
            return 0, 1
        
        # Try to get bot info
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get("ok"):
                print_check("Telegram bot token is valid", True)
                bot_name = bot_info.get("result", {}).get("username", "Unknown")
                print(f"   🤖 Bot username: @{bot_name}")
                return 1, 1
        
        print_check("Telegram bot token is valid", False)
        print_warning("   Invalid token or network error")
        return 0, 1
        
    except Exception as e:
        print_check("Telegram bot check", False)
        print_warning(f"   Error: {str(e)[:100]}")
        return 0, 1

def check_gemini_api():
    """Check Gemini API"""
    print("\n" + "="*60)
    print("🤖 Checking Gemini AI")
    print("="*60)
    
    try:
        import google.generativeai as genai
        load_dotenv()
        
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            print_check("Gemini API key", False)
            print_warning("   Set GEMINI_API_KEY in .env file")
            print_info("   Get key from: https://makersuite.google.com/app/apikey")
            return 0, 1
        
        # Try to configure and test
        genai.configure(api_key=api_key)
        
        # Try different model names (API versions change)
        model_names = ['gemini-2.5-flash']
        success = False
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content("Hello")
                
                if response and response.text:
                    print_check("Gemini API is working", True)
                    print(f"   🤖 Model: {model_name}")
                    success = True
                    break
            except Exception as model_error:
                continue
        
        if success:
            return 1, 1
        else:
            print_check("Gemini API is working", False)
            print_warning("   Try 'gemini-pro' or 'gemini-1.5-pro' model instead")
            return 0, 1
            
    except ImportError:
        print_check("Gemini library installed", False)
        print_warning("   Install with: pip install google-generativeai")
        return 0, 1
    except Exception as e:
        print_check("Gemini API is working", False)
        print_warning(f"   Error: {str(e)[:100]}")
        return 0, 1

def check_file_structure():
    """Check if required files exist"""
    print("\n" + "="*60)
    print("📁 Checking File Structure")
    print("="*60)
    
    required_files = {
        ".env": "Environment variables",
        "main.py": "Backend API",
        "telegram_bot.py": "Telegram bot",
        "requirements.txt": "Dependencies list"
    }
    
    checks_passed = 0
    total_checks = len(required_files)
    
    for file, description in required_files.items():
        exists = os.path.exists(file)
        print_check(f"{file} - {description}", exists)
        if exists:
            checks_passed += 1
    
    return checks_passed, total_checks

def main():
    """Run all checks"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                                                            ║")
    print("║           🤰 MatruRaksha AI Setup Verification 🤰          ║")
    print("║                                                            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    total_passed = 0
    total_checks = 0
    
    # Run all checks
    checks = [
        check_file_structure(),
        check_environment(),
        check_dependencies(),
        check_supabase_connection(),
        check_telegram_bot(),
        check_gemini_api()
    ]
    
    for passed, total in checks:
        total_passed += passed
        total_checks += total
    
    # Print summary
    print("\n" + "="*60)
    print("📊 Summary")
    print("="*60)
    
    percentage = (total_passed / total_checks * 100) if total_checks > 0 else 0
    
    print(f"\nTotal Checks Passed: {total_passed}/{total_checks} ({percentage:.1f}%)")
    
    if percentage == 100:
        print(f"\n{Colors.GREEN}🎉 All checks passed! Your setup is ready!{Colors.END}")
        print(f"\n{Colors.BLUE}Next steps:{Colors.END}")
        print("  1. Run: python main.py")
        print("  2. Open Telegram and message your bot: /start")
        print("  3. Register and start uploading medical reports")
    elif percentage >= 80:
        print(f"\n{Colors.YELLOW}⚠️  Most checks passed, but some optional features may not work{Colors.END}")
        print(f"\n{Colors.BLUE}You can still run the application with:{Colors.END}")
        print("  python main.py")
    else:
        print(f"\n{Colors.RED}❌ Several checks failed. Please fix the issues above.{Colors.END}")
        print(f"\n{Colors.BLUE}Common fixes:{Colors.END}")
        print("  1. Create .env file with required credentials")
        print("  2. Install dependencies: pip install -r requirements.txt")
        print("  3. Run SQL schema in Supabase SQL Editor")
    
    print("\n" + "="*60 + "\n")
    
    return 0 if percentage >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())