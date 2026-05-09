import pandas as pd
from typing import List, Tuple
from models.schemas import InvoiceRecord
import logging
import os

logger = logging.getLogger(__name__)

def load_file(filepath: str) -> pd.DataFrame:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        return pd.read_csv(filepath)
    elif ext in [".xlsx", ".xls"]:
        return pd.read_excel(filepath)
    elif ext == ".json":
        return pd.read_json(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def validate_schema(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    required_cols = [
        "invoice_no", "client_name", "client_email", "amount_due", 
        "due_date", "follow_up_count", "payment_link", 
        "finance_manager", "company_name"
    ]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        return df, [f"Missing columns: {', '.join(missing)}"]
    return df, []

def parse_to_records(df: pd.DataFrame) -> List[InvoiceRecord]:
    records = []
    for idx, row in df.iterrows():
        try:
            # Handle potential NaN or empty strings
            row_dict = row.to_dict()
            for key, val in row_dict.items():
                if pd.isna(val):
                    row_dict[key] = None
            
            # Ensure due_date is date object
            if isinstance(row_dict["due_date"], str):
                row_dict["due_date"] = pd.to_datetime(row_dict["due_date"]).date()
            elif hasattr(row_dict["due_date"], "date"):
                row_dict["due_date"] = row_dict["due_date"].date()

            record = InvoiceRecord(**row_dict)
            records.append(record)
        except Exception as e:
            logger.error(f"Failed to parse row {idx}: {e}")
    return records

def load_invoices(filepath: str) -> List[InvoiceRecord]:
    df = load_file(filepath)
    df, errors = validate_schema(df)
    if errors:
        raise ValueError("\n".join(errors))
    return parse_to_records(df)
