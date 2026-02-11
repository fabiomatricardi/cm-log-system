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
MYLOCALIP = socket.gethostbyname(socket.gethostname()) if not socket.gethostname().startswith("localhost") else "127.0.0.1"


# Reuse your existing CSS for perfect visual consistency
CUSTOM_CSS = """
#success-banner { background-color: #ecfdf5; border-left: 4px solid #10b981; padding: 15px; border-radius: 0 8px 8px 0; margin: 15px 0; font-weight: 500; }
.footer-note { background-color: #f0f9ff; padding: 12px; border-radius: 6px; margin-top: 15px; font-size: 0.92em; border-left: 3px solid #3b82f6; }
.gradio-container { max-width: 950px !important; margin: 0 auto !important; }
.required::after { content: " *"; color: #ef4444; font-weight: bold; }
.section-box { border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; margin: 15px 0; background: #f8fafc; }
.save-btn { background: linear-gradient(to right, #1e40af, #1d4ed8) !important; color: white !important; }
.export-btn { background: linear-gradient(to right, #b45309, #92400e) !important; color: white !important; }
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
    """Export cmlogs-db.json to timestamped Excel file"""
    try:
        if not os.path.exists(DB_FILE):
            return "❌ Database file not found. Run main CM app first to create logs.", None
        
        with open(DB_FILE, 'r') as f:
            data = json.load(f)
        
        if not data:
            return "⚠️ Database is empty. No logs to export.", None
        
        # Process data for Excel
        df = pd.DataFrame(data)
        
        # Handle list columns (original_filenames)
        if 'original_filenames' in df.columns:
            df['original_filenames'] = df['original_filenames'].apply(
                lambda x: ', '.join(x) if isinstance(x, list) else x
            )
        
        # Format ID for display
        if 'ID_db' in df.columns:
            df['ID'] = df['ID_db'].apply(lambda x: f"CM-{x:05d}")
            df.drop('ID_db', axis=1, inplace=True)
        
        # Reorder columns for readability
        cols = ['ID', 'TAGNAME', 'DESCRIPTION', 'reported_by', 'timestamp', 'attachment_count', 'original_filenames']
        df = df[[c for c in cols if c in df.columns]]
        
        # Generate filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_path = os.path.join(EXPORT_DIR, f"cmlogs_export_{timestamp}.xlsx")
        
        # Export to Excel with formatting
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Maintenance Logs', index=False)
            worksheet = writer.sheets['Maintenance Logs']
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2) * 1.1
                worksheet.column_dimensions[column_letter].width = min(adjusted_width, 50)
        
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
        gr.Markdown(f"Exports all entries from `{DB_FILE}` to formatted Excel file with auto-sized columns")
        export_btn = gr.Button("📤 Export to Excel", variant="secondary", elem_classes=["export-btn"])
        with gr.Row():
            export_status = gr.Markdown()
            export_file = gr.File(label="Download Exported Excel", interactive=False, visible=False)
    
    gr.Markdown("""

> 🔒 Security: All files remain on your local server<br>
> 💡 Tip: Valid emails must contain '@' symbol. Comments start with #<br>
> 📁 Exports saved to: `exports/cmlogs_export_YYYYMMDD_HHMMSS.xlsx`

    """)

    gr.Markdown("")

    # FOOTER
    with gr.Row():
        with gr.Column(scale=1):
            gr.Image("logo.png", height=40, container=False, buttons=[])
        with gr.Column(scale=2):
            gr.Markdown("**All rights reserved (C)**\n"
                       "created by fabio.matricardi@key-solution.eu for NGUYA FLNG Project\n"
                       f"visit [Key Solution SRL](https://key-solution.eu) | Network IP: {MYLOCALIP}")

    # ===== EVENT HANDLERS =====

    # ===== AUTHENTICATION HANDLER =====
    auth_btn.click(
        fn=authenticate_user,
        inputs=[auth_user, auth_pass],
        outputs=[gr.State(), auth_status]  # Temporary state holder
    ).success(
        fn=get_editor_visibility,
        inputs=gr.State(True),
        outputs=[inst_section, icss_section, auth_panel, auth_pass]
    ).failure(
        fn=lambda: (gr.update(), gr.update(), gr.update(), gr.update(value="")),
        outputs=[inst_section, icss_section, auth_panel, auth_pass]
    )


    # ===== EMAIL SAVE HANDLERS (UNCHANGED) =====
    inst_save_btn.click(
        fn=save_email_file,
        inputs=[gr.State(CM_EMAILS_FILE), inst_editor],
        outputs=inst_status
    ).then(
    fn=lambda: load_email_file(CM_EMAILS_FILE), 
    outputs=inst_editor)
    
    icss_save_btn.click(
        fn=save_email_file,
        inputs=[gr.State(ICSS_EMAILS_FILE), icss_editor],
        outputs=icss_status
    ).then(
    fn=lambda: load_email_file(CM_EMAILS_FILE), 
    outputs=icss_editor)
    
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
    print("= "*70 + "\n")
    
    demo.launch()