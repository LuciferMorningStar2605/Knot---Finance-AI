import os
import sys
import json
import uuid
import logging
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core_agent import run_agent
from agent.escalation_engine import calculate_days_overdue, determine_stage
from audit.logger import get_all_records, export_to_excel, export_to_pdf, export_to_word, init_db, clear_all_records, resolve_invoice
from data.loader import load_invoices
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize DB on startup
init_db()

# ─────────────────────────────────────────────
# PAGE ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────────────────────────
# API: DASHBOARD STATS
# ─────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    records = get_all_records()
    if not records:
        return jsonify({
            "total_invoices": 0, "emails_sent": 0,
            "legal_flags": 0, "failures": 0,
            "total_value_at_risk": 0, "recovery_rate": 0
        })

    df = pd.DataFrame([r.model_dump() for r in records])
    latest = df.sort_values("timestamp").groupby("invoice_no").last().reset_index()

    total = len(latest)
    sent  = int(latest["send_status"].isin(["SENT","DRY_RUN_LOGGED"]).sum())
    legal = int((latest["send_status"] == "LEGAL_ESCALATION").sum())
    fail  = int((latest["send_status"] == "GENERATION_FAILED").sum())
    risk  = float(latest["amount_due"].sum())
    rate  = round((sent / total * 100) if total else 0, 1)

    stage_dist = latest["stage"].value_counts().to_dict()

    return jsonify({
        "total_invoices": total,
        "emails_sent": sent,
        "legal_flags": legal,
        "failures": fail,
        "total_value_at_risk": risk,
        "recovery_rate": rate,
        "stage_distribution": {str(k): int(v) for k, v in stage_dist.items()}
    })


# ─────────────────────────────────────────────
# API: INVOICE QUEUE
# ─────────────────────────────────────────────

@app.route("/api/invoices")
def api_invoices():
    records = get_all_records()
    if not records:
        return jsonify([])
    df = pd.DataFrame([r.model_dump() for r in records])
    latest = df.sort_values("timestamp").groupby("invoice_no").last().reset_index()
    latest = latest[latest["send_status"] != "RESOLVED"] # Filter out resolved invoices
    latest = latest.sort_values("days_overdue", ascending=False)
    return jsonify(latest.to_dict(orient="records"))


# ─────────────────────────────────────────────
# API: RUN AGENT
# ─────────────────────────────────────────────

@app.route("/api/run", methods=["POST"])
def api_run():
    dry_run = request.form.get("dry_run", "true").lower() == "true"
    settings.DRY_RUN_MODE = dry_run

    if "file" in request.files and request.files["file"].filename:
        f = request.files["file"]
        os.makedirs(settings.DATA_DIR, exist_ok=True)
        filepath = os.path.join(settings.DATA_DIR, f.filename)
        f.save(filepath)
    else:
        filepath = os.path.join(settings.DATA_DIR, "sample_invoices.csv")

    try:
        summary = run_agent(filepath)
        return jsonify({
            "success": True,
            "total": summary.total_processed,
            "sent": summary.emails_sent,
            "dry_run": summary.dry_run_logged,
            "legal": summary.legal_flags,
            "failed": summary.generation_failed,
            "run_id": summary.run_id,
            "timestamp": summary.run_timestamp
        })
    except Exception as e:
        logger.error(f"Agent run error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────
# API: AUDIT TRAIL
# ─────────────────────────────────────────────

@app.route("/api/audit")
def api_audit():
    limit = int(request.args.get("limit", 100))
    records = get_all_records()
    data = [r.model_dump() for r in records[:limit]]
    return jsonify(data)


@app.route("/api/audit/export")
def api_audit_export():
    fmt = request.args.get("format", "xlsx")
    os.makedirs("output", exist_ok=True)
    
    if fmt == "pdf":
        path = "output/audit_export.pdf"
        export_to_pdf(path)
        mimetype = "application/pdf"
        ext = "pdf"
    elif fmt == "docx":
        path = "output/audit_export.docx"
        export_to_word(path)
        mimetype = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ext = "docx"
    else:
        path = "output/audit_export.xlsx"
        export_to_excel(path)
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ext = "xlsx"
        
    return send_file(path, as_attachment=True, mimetype=mimetype,
                     download_name=f"Knot_Audit_{datetime.now().strftime('%Y%m%d')}.{ext}")


# ─────────────────────────────────────────────
# API: EMAIL PREVIEW
# ─────────────────────────────────────────────

@app.route("/api/email/<invoice_no>")
def api_email_preview(invoice_no):
    records = get_all_records()
    for r in records:
        if r.invoice_no == invoice_no and r.subject:
            return jsonify(r.model_dump())
    return jsonify({"error": "Email not found"}), 404


# ─────────────────────────────────────────────
# API: PREVIEW CSV
# ─────────────────────────────────────────────

@app.route("/api/preview", methods=["POST"])
def api_preview():
    """Preview CSV without running the agent — just returns parsed invoices with stage calculation."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f = request.files["file"]
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    filepath = os.path.join(settings.DATA_DIR, f.filename)
    f.save(filepath)

    try:
        invoices = load_invoices(filepath)
        results = []
        for inv in invoices:
            days = calculate_days_overdue(inv.due_date)
            stage = determine_stage(days)
            results.append({
                "invoice_no": inv.invoice_no,
                "client_name": inv.client_name,
                "client_email": inv.client_email,
                "amount_due": inv.amount_due,
                "currency": inv.currency,
                "due_date": str(inv.due_date),
                "days_overdue": days,
                "stage": stage.value if stage else 0,
                "status": "legal" if stage and stage.value == 5 else ("action" if stage else "current")
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────
# API: DATA MANAGEMENT
# ─────────────────────────────────────────────

@app.route("/api/data/clear", methods=["POST"])
def api_data_clear():
    """Wipes the database."""
    clear_all_records()
    return jsonify({"success": True})

@app.route("/api/resolve/<invoice_no>", methods=["POST"])
def api_resolve(invoice_no):
    """Marks an invoice as resolved so it disappears from the active queue."""
    resolve_invoice(invoice_no)
    return jsonify({"success": True})


# ─────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)
