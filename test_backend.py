import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import app
from agent.core_agent import run_agent
from audit.logger import get_all_records, clear_all_records

class TestKnotBackend(unittest.TestCase):
    def setUp(self):
        # Force local SQLite test database
        os.environ["DATABASE_URL"] = ""
        os.environ["POSTGRES_URL"] = ""
        clear_all_records()

    @patch('agent.core_agent.generate_email')
    def test_pipeline_and_api(self, mock_generate_email):
        # Mock the email generator return value directly using the proper Pydantic schemas
        from models.schemas import GeneratedEmail, PersonalizationCheck
        
        mock_email = GeneratedEmail(
            invoice_no="INV-TEST-001",
            subject="Overdue Payment Notice: INV-TEST-001",
            body="Dear Alice Smith, your payment of ₹50,000.00 is overdue by 3 days.",
            tone_used="Friendly Reminder",
            stage=1,
            personalization_check=PersonalizationCheck(
                client_name_present=True,
                invoice_no_present=True,
                amount_present=True,
                due_date_present=True,
                days_overdue_present=True,
                payment_link_present=True
            )
        )
        mock_generate_email.return_value = mock_email

        # 1. Generate a temporary test CSV file with dynamic dates relative to today
        import csv
        from datetime import datetime, timedelta
        
        today = datetime.now().date()
        due_stage1 = today - timedelta(days=3) # 3 days overdue -> Stage 1 (1-7 days)
        due_stage5 = today - timedelta(days=40) # 40 days overdue -> Stage 5 (30+ days)
        
        test_csv = "data/temp_test_invoices.csv"
        os.makedirs("data", exist_ok=True)
        with open(test_csv, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["invoice_no", "client_name", "client_email", "amount_due", "due_date", "follow_up_count", "currency", "payment_link", "finance_manager", "company_name", "notes"])
            writer.writerow(["INV-TEST-001", "Alice Smith", "alice@example.com", "50000.00", due_stage1.strftime("%Y-%m-%d"), "0", "INR", "https://pay.example.com/inv1", "Priya Sharma", "TechSolutions Pvt Ltd", "Stage 1 Test"])
            writer.writerow(["INV-TEST-002", "Bob Jones", "bob@example.com", "120000.00", due_stage5.strftime("%Y-%m-%d"), "4", "INR", "https://pay.example.com/inv2", "Priya Sharma", "TechSolutions Pvt Ltd", "Legal Flag Test"])
            
        try:
            summary = run_agent(test_csv)
        finally:
            if os.path.exists(test_csv):
                os.remove(test_csv)
        
        print("\nAgent Run Summary:")
        print(f"Total Processed: {summary.total_processed}")
        print(f"Emails Sent: {summary.emails_sent}")
        print(f"Dry Run Logged: {summary.dry_run_logged}")
        print(f"Failures: {summary.generation_failed}")
        
        self.assertGreater(summary.total_processed, 0)
        self.assertEqual(summary.generation_failed, 0)

        # 2. Verify database records
        records = get_all_records()
        self.assertGreater(len(records), 0)
        print(f"Database contains {len(records)} audit records.")

        # 3. Test Flask Endpoints via Flask test client
        with app.test_client() as client:
            # Test /
            res = client.get('/')
            self.assertEqual(res.status_code, 200)

            # Test /api/stats
            res = client.get('/api/stats')
            self.assertEqual(res.status_code, 200)
            stats = res.get_json()
            print("Stats Endpoint Output:", stats)
            self.assertGreater(stats["total_invoices"], 0)

            # Test /api/invoices
            res = client.get('/api/invoices')
            self.assertEqual(res.status_code, 200)
            invoices = res.get_json()
            self.assertGreater(len(invoices), 0)

            # Test /api/audit
            res = client.get('/api/audit')
            self.assertEqual(res.status_code, 200)
            audit = res.get_json()
            self.assertGreater(len(audit), 0)

        print("\n🎉 ALL BACKEND TESTS PASSED SUCCESSFULLY!\n")

if __name__ == '__main__':
    unittest.main()
