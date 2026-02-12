import gradio as gr
import json
import os
import datetime
import pandas as pd  # Required: pip install pandas openpyxl
from pathlib import Path
import socket

# ======================
# CONFIGURATION
# ======================
CM_EMAILS_FILE = "CMemails.txt"          # INST recipients
ICSS_EMAILS_FILE = "CM-ICSS-emails.txt"  # ICSS recipients
DB_FILE = "cmlogs-db.json"
EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

# Improved IP detection (avoids 127.0.0.1 trap)
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

MYLOCALIP = get_local_ip()

# Reuse your existing CSS for perfect visual consistency
CUSTOM_CSS = """
#success-banner { background-color: #ecfdf5; border-left: 4px solid #10b981; padding: 15px; border-radius: 0 8px 8px 0; margin: 15px 0; font-weight: 500; }
.footer-note { background-color: #f0f9ff; padding: 12px; border-radius: 6px; margin-top: 15px; font-size: 0.92em; border-left: 3px solid #3b82f6; }
.gradio-container { max-width: 950px !important; margin: 0 auto !important; }
.required::after { content: " *"; color: #ef4444; font-weight: bold; }
.section-box { border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin: 15px 0; background: #f8fafc; }
.save-btn { background: linear-gradient(to right, #1e40af, #1d4ed8) !important; color: white !important; }
.export-btn { background: linear-gradient(to right, #b45309, #92400e) !important; color: white !important; }
.status-sent { background-color: #fff3e0 !important; }
.status-ongoing { background-color: #fff9c4 !important; }
.status-completed { background-color: #e8f5e9 !important; }
"""

# ======================
# CORE FUNCTIONS
# ======================
def load_email_file(filename):
    """Safely load email file content (preserve comments/formatting)"""
    try:
        if not os.path.exists(filename):
            return f"# {filename}\n# Add one email per line below\n# Lines starting with # are comments\n"
        with open(filename, 'r') as f:
            return f.read()
    except Exception as e:
        return f"# ERROR loading {filename}: {str(e)}\n"

def save_email_file(filename, content):
    """Save edited content to email file with validation"""
    try:
        # Basic validation: check for at least one valid email
        valid_emails = [line.strip() for line in content.split('\n')
                        if line.strip() and not line.startswith('#') and '@' in line]
        if not valid_emails:
            return f"⚠️ Warning: No valid emails found in {filename}. File saved but emails may not receive notifications."
        
        with open(filename, 'w') as f:
            f.write(content)
        return f"✅ Successfully saved {len(valid_emails)} recipient(s) to **{filename}**"
    except Exception as e:
        return f"❌ Save failed for {filename}: {str(e)}"

def export_db_to_excel():
    """Export cmlogs-db.json to timestamped Excel file with ALL columns"""
    try:
        if not os.path.exists(DB_FILE):
            return "❌ Database file not found. Run main CM app first to create logs.", None
        
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        
        if not data:
            return "⚠️ Database is empty. No logs to export.", None
        
        # Process data for Excel - handle ALL fields including new ones
        processed_data = []
        for entry in data:
            # Format ID with leading zeros (CM-XXXXX)
            formatted_id = f"CM-{entry.get('ID_db', 0):05d}"
            
            # Handle list fields safely (join with commas)
            orig_files = entry.get('original_filenames', [])
            stored_files = entry.get('stored_filenames', [])
            
            processed_data.append({
                'ID': formatted_id,
                'TAGNAME': entry.get('TAGNAME', ''),
                'DESCRIPTION': entry.get('DESCRIPTION', ''),
                'reported_by': entry.get('reported_by', ''),
                'timestamp': entry.get('timestamp', ''),
                'status': entry.get('status', 'sent').capitalize(),  # New field with default
                'attachment_count': entry.get('attachment_count', 0),
                'original_filenames': ', '.join(orig_files) if isinstance(orig_files, list) else orig_files,
                'stored_filenames': ', '.join(stored_files) if isinstance(stored_files, list) else stored_files,
                'last_edited': entry.get('last_edited', ''),
                'edited_by': entry.get('edited_by', '')
            })
        
        # Create DataFrame with explicit column ordering for readability
        df = pd.DataFrame(processed_data)
        
        # Define optimal column order (workflow-focused)
        column_order = [
            'ID', 'TAGNAME', 'DESCRIPTION', 'reported_by', 'timestamp', 
            'status', 'attachment_count', 'original_filenames', 
            'stored_filenames', 'last_edited', 'edited_by'
        ]
        
        # Only include columns that exist in the data
        existing_cols = [col for col in column_order if col in df.columns]
        df = df[existing_cols]
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_path = os.path.join(EXPORT_DIR, f"cmlogs_export_{timestamp}.xlsx")
        
        # Export to Excel with professional formatting
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Maintenance Logs', index=False)
            worksheet = writer.sheets['Maintenance Logs']
            
            # Auto-adjust column widths with sensible limits
            for idx, column in enumerate(worksheet.columns, 1):
                max_length = 0
                column_letter = worksheet.cell(row=1, column=idx).column_letter
                
                for cell in column:
                    try:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    except:
                        pass
                
                # Set width with padding, capped at 60 characters
                adjusted_width = min((max_length + 2) * 1.1, 60)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Freeze header row for scrolling
            worksheet.freeze_panes = 'A2'
        
        return f"✅ Exported {len(df)} log(s) to **{os.path.basename(excel_path)}**", excel_path

    except ImportError:
        return "❌ Missing dependencies: Install with `pip install pandas openpyxl`", None
    except Exception as e:
        return f"❌ Export failed: {str(e)}", None

# ======================
# AUTHENTICATION FUNCTIONS
# ======================
def authenticate_user(username, password):
    """Validate credentials - hardcoded per requirement"""
    if username.strip() == "admin" and password.strip() == "admin":
        return True, "✅ Authentication successful! Email editors unlocked."
    return False, "❌ Invalid credentials. Access denied to email management."

def get_editor_visibility(is_authenticated):
    """Return visibility states for protected components"""
    return (
        gr.update(visible=is_authenticated),  # INST section
        gr.update(visible=is_authenticated),  # ICSS section
        gr.update(visible=not is_authenticated),  # Login panel
        gr.update(value="")  # Clear password field
    )

# ======================
# GRADIO INTERFACE
# ======================
with gr.Blocks(
    title="👨‍🔧 Expert Panel - CM System Admin",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="orange"),
    css=CUSTOM_CSS
) as demo:
    
    gr.Markdown("# 👨‍🔧 Expert Panel - Maintenance System Admin")
    gr.Markdown("Manage recipient lists and export maintenance logs. *Changes apply immediately to main CM app.*")
    gr.Markdown("---")
    
    # ===== AUTHENTICATION PANEL (VISIBLE BY DEFAULT) =====
    with gr.Group(elem_classes=["section-box"], visible=True) as auth_panel:
        gr.Markdown("## 🔒 Email Management Authentication")
        gr.Markdown("Enter admin credentials to edit recipient lists")
        auth_user = gr.Textbox(label="Username", placeholder="admin")
        auth_pass = gr.Textbox(label="Password", type="password", placeholder="admin")
        auth_btn = gr.Button("🔓 Unlock Email Editors", variant="primary")
        auth_status = gr.Markdown()
    
    gr.Markdown("---")
    
    # ===== INST EMAILS SECTION =====
    with gr.Group(elem_classes=["section-box"], visible=False) as inst_section:
        gr.Markdown("## 📧 INST Recipients (`CMemails.txt`)")
        gr.Markdown("Edit email list for **🧰 SAVE & SEND to INST** button in main app")
        inst_editor = gr.Textbox(
            value=load_email_file(CM_EMAILS_FILE),
            lines=10,
            max_lines=25,
            label="Email List Content",
            placeholder="Format:\n# Comments start with #\njohn@company.com\njane@company.com",
            show_label=False
        )
        with gr.Row():
            inst_save_btn = gr.Button("💾 Save INST Emails", variant="primary", elem_classes=["save-btn"])
            inst_status = gr.Markdown()
    
    # ===== ICSS EMAILS SECTION =====
    with gr.Group(elem_classes=["section-box"], visible=False) as icss_section:
        gr.Markdown("## 📧 ICSS Recipients (`CM-ICSS-emails.txt`)")
        gr.Markdown("Edit email list for **🎛️ SAVE & SEND to ICSS** button in main app")
        icss_editor = gr.Textbox(
            value=load_email_file(ICSS_EMAILS_FILE),
            lines=10,
            max_lines=25,
            label="Email List Content",
            placeholder="Format:\n# Comments start with #\nsupport@icss.com\nlead@icss.com",
            show_label=False
        )
        with gr.Row():
            icss_save_btn = gr.Button("💾 Save ICSS Emails", variant="primary", elem_classes=["save-btn"])
            icss_status = gr.Markdown()
    
    # ===== EXPORT SECTION =====
    with gr.Group(elem_classes=["section-box"]):
        gr.Markdown("## 📤 Export Maintenance Logs to Excel")
        gr.Markdown(f"Exports **ALL fields** from `{DB_FILE}` including status workflow and audit trail to formatted Excel file")
        export_btn = gr.Button("📤 Export to Excel", variant="secondary", elem_classes=["export-btn"])
        with gr.Row():
            export_status = gr.Markdown()
            export_file = gr.File(label="Download Exported Excel", interactive=False, visible=False)
    
    gr.Markdown("""
🔒 Security: All files remain on your local server  
💡 Tip: Valid emails must contain '@' symbol. Comments start with #  
📁 Exports saved to: `exports/cmlogs_export_YYYYMMDD_HHMMSS.xlsx`  
📊 Export includes: ID, Tagname, Description, Reporter, Timestamp, **Status**, Attachments, Original/Stored Filenames, Edit History
""")
    
    gr.Markdown(" ")
    
    # FOOTER
    with gr.Row():
        with gr.Column(scale=1):
            try:
                gr.Image("logo.png", height=40, container=False, buttons=[])
            except:
                gr.Markdown("NGUYA FLNG", elem_classes=["footer-note"])
        with gr.Column(scale=2):
            gr.Markdown("**All rights reserved (C)**\n"
                        "created by fabio.matricardi@key-solution.eu for NGUYA FLNG Project\n"
                       f"visit [Key Solution SRL](https://key-solution.eu) | Network IP: {MYLOCALIP}")

    # ===== EVENT HANDLERS =====
    
    # ===== AUTHENTICATION HANDLER =====
    def handle_auth(username, password):
        success, msg = authenticate_user(username, password)
        return (
            gr.update(visible=success),
            gr.update(visible=success),
            gr.update(visible=not success),
            gr.update(value=""),
            msg
        )
    
    auth_btn.click(
        fn=handle_auth,
        inputs=[auth_user, auth_pass],
        outputs=[inst_section, icss_section, auth_panel, auth_pass, auth_status]
    )
    
    # ===== EMAIL SAVE HANDLERS =====
    def save_inst_emails(content):
        result = save_email_file(CM_EMAILS_FILE, content)
        return result, load_email_file(CM_EMAILS_FILE)
    
    inst_save_btn.click(
        fn=save_inst_emails,
        inputs=[inst_editor],
        outputs=[inst_status, inst_editor]
    )
    
    def save_icss_emails(content):
        result = save_email_file(ICSS_EMAILS_FILE, content)
        return result, load_email_file(ICSS_EMAILS_FILE)
    
    icss_save_btn.click(
        fn=save_icss_emails,
        inputs=[icss_editor],
        outputs=[icss_status, icss_editor]
    )
    
    # ===== EXPORT HANDLER =====
    export_btn.click(
        fn=export_db_to_excel,
        inputs=None,
        outputs=[export_status, export_file]
    ).then(
        fn=lambda x: gr.update(visible=True) if x else gr.update(visible=False),
        inputs=export_file,
        outputs=export_file
    )

# ======================
# LAUNCH
# ======================
if __name__ == "__main__":
    print("\n" + "= "*70)
    print("👨‍🔧 EXPERT PANEL - MAINTENANCE SYSTEM ADMIN CONSOLE")
    print("= "*70)
    print(f"✅ Managing recipient files:")
    print(f"   • INST: {os.path.abspath(CM_EMAILS_FILE)}")
    print(f"   • ICSS: {os.path.abspath(ICSS_EMAILS_FILE)}")
    print(f"✅ Database source: {os.path.abspath(DB_FILE)}")
    print(f"✅ Exports directory: {os.path.abspath(EXPORT_DIR)}")
    print(f"\n🌐 ACCESS PANEL AT:")
    print(f"   • Local: http://localhost:7961")
    print(f"   • Network: http://{MYLOCALIP}:7961")
    print("\n⚠️ REQUIREMENTS:")
    print("   • pandas and openpyxl must be installed (`pip install pandas openpyxl`)")
    print("   • Main CM app must be running first to generate cmlogs-db.json")
    print("\n✨ EXPORT FEATURES:")
    print("   • All 11 fields exported including new 'status' workflow field")
    print("   • Backward compatible with legacy logs (missing fields handled gracefully)")
    print("   • Auto-sized columns with frozen header row")
    print("   • Professional formatting for audit/compliance reporting")
    print("= "*70 + "\n")
    
    demo.launch(server_port=7960,css=CUSTOM_CSS)