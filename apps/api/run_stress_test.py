import asyncio
from app.services.export_service import ExportService
from app.models.schemas import ProposalData

async def main():
    import os
    debug = os.environ.get("STRESS_TEST_DEBUG", "0") == "1"
    session_dir = None
    if debug:
        # Remove old output PDFs before regenerating
        from pathlib import Path
        session_dir = Path(os.path.dirname(__file__)).parent / "data" / "sessions" / "STRESS_TEST"
        for fname in ["invoice.pdf", "invoice_overlay.pdf", "invoice_template.pdf"]:
            f = session_dir / fname
            if f.exists():
                f.unlink()
                print(f"[DEBUG] deleted old file: {os.path.abspath(f)}")
    export_service = ExportService()
    proposal_data = ProposalData()  # STRESS_TEST block overrides fields
    path = await export_service.export_document(
        "STRESS_TEST",
        proposal_data,
        format="pdf",
        document_type="invoice"
    )
    import os
    print("Generated file path:", path)
    print("Absolute path:", path.resolve())
    print("Exists on disk:", path.exists())
    assert path.exists() and os.path.getsize(path) > 0, f"invoice.pdf not written or empty: {path}"
    print(f"File size: {os.path.getsize(path)} bytes")
    # If debug, print overlay/template info too
    debug = os.environ.get("STRESS_TEST_DEBUG", "0") == "1"
    if debug:
        session_dir = path.parent
        overlay_path = session_dir / "invoice_overlay.pdf"
        template_path = session_dir / "invoice_template.pdf"
        for p in [template_path, overlay_path]:
            if p.exists():
                print(f"Debug PDF: {os.path.abspath(p)} | Size: {os.path.getsize(p)} bytes")
    print("STRESS_TEST invoice generated successfully.")

if __name__ == "__main__":
    asyncio.run(main())
