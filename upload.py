import gradio as gr
import shutil
import uuid
import datetime
from pathlib import Path
import os
import sys
import socket


MYLOCALIP = socket.gethostbyname(socket.gethostname()) if not socket.gethostname().startswith("localhost") else "127.0.0.1"


# CRITICAL FIX 1: Use ABSOLUTE path for attachments directory
SCRIPT_DIR = Path(__file__).parent.resolve()
ATTACHMENTS_DIR = SCRIPT_DIR / "attachments"
ATTACHMENTS_DIR.mkdir(exist_ok=True)

def save_files(uploaded_files, webcam_image):
    saved_paths = []
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # Process uploaded files
        if uploaded_files:
            for file_obj in uploaded_files:
                if not file_obj or not hasattr(file_obj, 'name'):
                    continue
                
                # Get safe filename
                original_name = Path(file_obj.name).name
                safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in original_name)
                unique_name = f"{timestamp}_{uuid.uuid4().hex[:8]}_{safe_name}"
                dest_path = ATTACHMENTS_DIR / unique_name
                
                # Copy file using absolute paths
                shutil.copy2(file_obj.name, dest_path)
                # Store DISPLAY path (relative to project) - NO PATH COMPUTATION
                saved_paths.append(f"attachments/{unique_name}")

        # Process webcam image
        if webcam_image and hasattr(webcam_image, 'name'):
            ext = Path(webcam_image.name).suffix.lower()
            if not ext or ext not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
                ext = ".jpg"
            
            unique_name = f"webcam_{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
            dest_path = ATTACHMENTS_DIR / unique_name
            
            shutil.copy2(webcam_image.name, dest_path)
            saved_paths.append(f"attachments/{unique_name}")

        # Generate feedback WITHOUT path resolution
        if saved_paths:
            path_list = "\n".join([f"- `{p}`" for p in saved_paths])
            success_msg = (
                f"✅ **Success!** Saved {len(saved_paths)} file(s):\n\n"
                f"{path_list}\n\n"
                f"📁 Location: `{ATTACHMENTS_DIR}`"
            )
            return success_msg, None, None
        else:
            return "⚠️ No files to save. Please upload documents or capture an image first.", None, None
            
    except Exception as e:
        error_detail = str(e)
        # Mask sensitive path info in error messages
        if "attachments" in error_detail.lower():
            error_detail = "File path resolution error (network access issue)"
        return f"❌ **Error saving files:**\n`{error_detail}`\n\n💡 Tip: Access app via localhost for full functionality", None, None

# CRITICAL FIX 2: Camera warning for network access
CAMERA_WARNING = """⚠️ **Camera Access works like File pick**    
✅ **HOW TO:**  
1. 📱 Mobile Tip: For camera access on phone select CAMERA for the sources.  
• works on both 👾Android/🍏iOS
"""

CUSTOM_CSS = """
.camera-warning {
    background-color: #fffbeb;
    border-left: 4px solid #f59e0b;
    padding: 12px;
    border-radius: 0 6px 6px 0;
    margin: 10px 0 15px;
    font-size: 0.95em;
}
#success-banner { 
    background-color: #ecfdf5; 
    border-left: 4px solid #10b981;
    padding: 15px;
    border-radius: 0 8px 8px 0;
    margin: 20px 0;
}
.footer-note {
    background-color: #f0f9ff;
    padding: 10px;
    border-radius: 6px;
    margin-top: 15px;
    font-size: 0.9em;
}
.gradio-container { max-width: 900px !important; margin: 0 auto !important; }
@media (max-width: 768px) {
    .gr-button { width: 100% !important; padding: 14px !important; font-size: 1.1em !important; }
}
"""

with gr.Blocks(
    title="📱 Mobile Document Capture & Save",
    theme=gr.themes.Soft(primary_hue="emerald"),
    css=CUSTOM_CSS
) as demo:
    gr.Markdown(
        f"""# 📎 Document Capture & Save with 📱 Mobile phone
        Upload PDFs/images **or** capture photos directly from your device camera. 

        All files are saved to the `attachments` directory.
        🌐 NETWORK ACCESS: http://{MYLOCALIP}:7960"""
    )
    
    # Network access warning banner
    gr.Markdown(CAMERA_WARNING,
        elem_classes=["footer-note"]
    )
    
    with gr.Row():
        with gr.Column():
            file_upload = gr.File(
                label="📎 Upload Documents (PDF/Images)",
                file_types=[".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".webp"],
                file_count="multiple",
                type="filepath"
            )
            gr.Markdown("<small>✅ Works over network • Max 10 files</small>")
        
        with gr.Column():
            webcam = gr.File(
                label="📸 Capture from Camera",
                file_types=[".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".webp"],
                file_count="single",
                type="filepath"
            )
            # CRITICAL: Visible camera warning
           # gr.Markdown(CAMERA_WARNING, elem_classes=["camera-warning"])
    
    save_btn = gr.Button("💾 SAVE ALL FILES", variant="primary", size="lg")
    output_msg = gr.Markdown(elem_id="success-banner")
    
    gr.Markdown(
        f"""
        <div class="footer-note">
        <strong>📁 Storage:</strong> {ATTACHMENTS_DIR}<br>
        <strong>📱 Mobile Tip:</strong> For camera access on phone select CAMERA for the sources.<br>
        • works on both Androind/iOS
        </div>
        """,
        elem_classes=["footer-note"]
    )
    
    save_btn.click(
        fn=save_files,
        inputs=[file_upload, webcam],
        outputs=[output_msg, file_upload, webcam],
        show_progress="full"
    )

if __name__ == "__main__":
    # CRITICAL FIX 3: Launch instructions for network access
    print("\n" + "="*70)
    print("🚀 LAUNCH INSTRUCTIONS")
    print("="*70)
    print(f"✅ Attachments directory: {ATTACHMENTS_DIR}")
    print("\n🔒 FOR FULL FUNCTIONALITY (INCLUDING CAMERA):")
    print("   Option 1 (Recommended): Access via http://localhost:7860 on server machine")
    print("   Option 2 (Network): Set up SSL certificates for HTTPS:")
    print("      demo.launch(ssl_certfile='cert.pem', ssl_keyfile='key.pem')")
    print("\n⚠️  CAMERA LIMITATION:")
    print("   Browsers block camera over HTTP on networks. File uploads work fine over network.")
    print("   For intranet camera access: Use Chrome mobile → Site Settings → Allow camera for this IP")
    print("="*70 + "\n")
    
    # Launch with network-friendly settings
    demo.launch(css=CUSTOM_CSS)
