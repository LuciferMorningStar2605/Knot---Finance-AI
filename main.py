import argparse
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.core_agent import run_agent
from config.settings import settings
from audit.logger import init_db

def main():
    parser = argparse.ArgumentParser(description="Enterprise Finance Follow-Up Agent")
    parser.add_argument("--file", type=str, default="data/sample_invoices.csv", help="Path to invoice CSV/Excel")
    parser.add_argument("--live", action="store_true", help="Disable dry-run mode and send real emails")
    parser.add_argument("--force", action="store_true", help="Skip confirmation (for CI/CD)")
    
    args = parser.parse_args()
    
    init_db()
    
    # Handle Live Mode
    if args.live:
        if not args.force:
            confirm = input("⚠️ LIVE MODE — emails will be sent to real addresses. Proceed? (y/n): ")
            if confirm.lower() != 'y':
                print("Aborted.")
                return
        settings.DRY_RUN_MODE = False
        print("🚀 RUNNING IN LIVE MODE")
    else:
        # Default to env setting or True
        settings.DRY_RUN_MODE = os.getenv("DRY_RUN_MODE", "true").lower() == "true"
        if settings.DRY_RUN_MODE:
            print("🛡️ RUNNING IN DRY RUN MODE")
        else:
            print("🚀 RUNNING IN LIVE MODE (from env)")

    print(f"📂 Processing file: {args.file}")
    summary = run_agent(args.file)
    
    print("\n" + "="*30)
    print("      AGENT RUN SUMMARY")
    print("="*30)
    print(f"Total Records:  {summary.total_processed}")
    print(f"Success/Sent:   {summary.emails_sent + summary.dry_run_logged}")
    print(f"Legal Flags:    {summary.legal_flags}")
    print(f"Failures:       {summary.generation_failed}")
    print("="*30 + "\n")

if __name__ == "__main__":
    main()
