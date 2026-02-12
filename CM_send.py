import gradio as gr
import shutil
import uuid
import datetime
import json
from pathlib import Path
import os
import socket
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import mimetypes
import sys

# ======================
# CONFIGURATION (FIXED)
# ======================
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
CMLOGS_DB_FNAME = "cmlogs-db.json"
SECRETFILE = "secret.json"
INST_RECIPIENTS_FILE = "CMemails.txt"
ICSS_RECIPIENTS_FILE = "CM-ICSS-emails.txt"
SENDER_EMAIL = "fabio.matricardi@gmail.com"
ATTACHMENTS_DIR = "attachments"
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)
VALID_STATUSES = ['sent', 'ongoing', 'completed']  # Centralized validation

# Load Gmail password securely
GMAIL_APP_PASSWORD = None
try:
    with open(SECRETFILE) as f:
        GMAIL_APP_PASSWORD = json.load(f)['secret_code']
except Exception as e:
    print(f"⚠️ Secret file error: {e}. Email functionality disabled.")

# Initialize database if missing
if not os.path.exists(CMLOGS_DB_FNAME):
    with open(CMLOGS_DB_FNAME, 'w') as f:
        json.dump([], f)
    print(f"✅ Created new log database: {CMLOGS_DB_FNAME}")

# ======================
# CORE FUNCTIONS (ENHANCED WITH STATUS)
# ======================
def generate_next_id():
    """Safely generate next sequential ID from database"""
    try:
        with open(CMLOGS_DB_FNAME, 'r') as f:
            db = json.load(f)
        return max((entry.get('ID_db', 0) for entry in db), default=0) + 1
    except Exception as e:
        print(f"⚠️ ID generation error: {e}. Using timestamp-based ID.")
        return int(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))

def load_recipients(filename):
    """Load valid emails from specified file (skip comments/empty lines)"""
    recipients = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                email = line.strip()
                if email and not email.startswith('#') and '@' in email:
                    recipients.append(email)
        return recipients
    except FileNotFoundError:
        raise FileNotFoundError(f"Recipient file '{filename}' not found. Create it with one email per line.")
    except Exception as e:
        raise Exception(f"Error reading recipients from '{filename}': {str(e)}")

def save_to_database(entry):
    """Append new entry to JSON database"""
    try:
        with open(CMLOGS_DB_FNAME, 'r') as f:
            db = json.load(f)
    except:
        db = []
    db.append(entry)
    with open(CMLOGS_DB_FNAME, 'w') as f:
        json.dump(db, f, indent=2)

def load_all_logs():
    """Load ALL logs for search/edit operations (not truncated)"""
    try:
        with open(CMLOGS_DB_FNAME, 'r') as f:
            return json.load(f)
    except:
        return []

def load_logs_for_display(search_query=None):
    """
    Load logs with optional search filtering including status field
    search_query: string to search across all fields including status
    """
    try:
        with open(CMLOGS_DB_FNAME, 'r') as f:
            db = json.load(f)
        
        # Apply search filter if query exists
        if search_query and search_query.strip():
            query = search_query.lower().strip()
            filtered = []
            for entry in db:
                # Search across ALL fields including status (with safe defaults)
                search_text = " ".join([
                    f"CM-{entry.get('ID_db', 0):05d}",
                    entry.get('TAGNAME', ''),
                    entry.get('DESCRIPTION', ''),
                    entry.get('reported_by', ''),
                    entry.get('status', 'sent'),  # INCLUDE STATUS IN SEARCH
                    str(entry.get('ID_db', ''))
                ]).lower()
                if query in search_text:
                    filtered.append(entry)
            db = filtered
        
        # Sort descending + truncate description
        entries = sorted(db, key=lambda x: x.get('ID_db', 0), reverse=True)[:20]
        return [
            [
                f"CM-{e['ID_db']:05d}",                          # ID
                e.get('TAGNAME', ''),                            # Tagname
                (e.get('DESCRIPTION', '')[:47] + '...') if len(e.get('DESCRIPTION', '')) > 50 else e.get('DESCRIPTION', ''), # Description
                e.get('reported_by', ''),                        # Reported By
                e.get('timestamp', ''),                          # Timestamp
                e.get('attachment_count', 0),                    # Attachments
                e.get('status', 'sent').capitalize(),            # STATUS (NEW COLUMN, capitalized for display)
                "✅" if e.get('last_edited') else ""             # Edited indicator
            ]
            for e in entries
        ]
    except Exception as e:
        print(f"⚠️ Table load error: {e}")
        return []

def update_log_entry(log_id, new_tagname, new_description, new_reported_by, new_status):
    """Update ALL editable fields with validation (status included)"""
    # VALIDATION (critical for data integrity)
    if not new_tagname or not new_tagname.strip():
        return False, "❌ TAGNAME cannot be empty"
    if not new_reported_by or not new_reported_by.strip():
        return False, "❌ 'Reported by' cannot be empty"
    if new_status not in VALID_STATUSES:
        return False, f"❌ Invalid status '{new_status}'. Must be one of: {', '.join(VALID_STATUSES)}"
    
    try:
        with open(CMLOGS_DB_FNAME, 'r') as f:
            db = json.load(f)
        
        for entry in db:
            if entry.get('ID_db') == log_id:
                # Update ALL editable fields (audit trail preserved for core metadata)
                entry['TAGNAME'] = new_tagname.strip()
                entry['DESCRIPTION'] = new_description.strip() if new_description else ""
                entry['reported_by'] = new_reported_by.strip()
                entry['status'] = new_status  # UPDATE STATUS
                entry['last_edited'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry['edited_by'] = new_reported_by.strip() if new_reported_by else "System"
                
                with open(CMLOGS_DB_FNAME, 'w') as f:
                    json.dump(db, f, indent=2)
                return True, f"✅ Log CM-{log_id:05d} updated successfully (edited {entry['last_edited']})"
        
        return False, f"❌ Log ID {log_id} not found"
    except Exception as e:
        return False, f"❌ Update failed: {str(e)}"

def delete_log_entry(log_id):
    """Delete log entry from database (attachments require manual cleanup)"""
    try:
        with open(CMLOGS_DB_FNAME, 'r') as f:
            db = json.load(f)
        
        original_count = len(db)
        db = [e for e in db if e.get('ID_db') != log_id]
        
        if len(db) == original_count:
            return False, f"❌ Log ID {log_id} not found"
        
        with open(CMLOGS_DB_FNAME, 'w') as f:
            json.dump(db, f, indent=2)
        
        warning = "⚠️ ATTACHMENTS NOT DELETED (manual cleanup required in attachments/ folder)"
        return True, f"✅ Log CM-{log_id:05d} DELETED from database\n{warning}"
    except Exception as e:
        return False, f"❌ Deletion failed: {str(e)}"

def send_email_with_exports(recipients, attachments_info, custom_note=""):
    """Send email with attachments and custom report note"""
    if not GMAIL_APP_PASSWORD:
        return "❌ EMAIL NOT CONFIGURED: Missing valid GMAIL_APP_PASSWORD in secret.json"
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        report_id = custom_note.split('ID: ')[1].split('\n')[0].strip()
        subject = f"🔧 Corrective Maintenance Notice #{report_id} - {timestamp}"
    except:
        subject = f"🔧 Corrective Maintenance Notice - {timestamp}"

    body = f"""CORRECTIVE MAINTENANCE ACTION REQUIRED
========================================
{custom_note}
⚠️ CONFIDENTIAL: Contains operational safety data.
Do not forward outside authorized Congo FLNG personnel.

System Details:
• Generated by: NGUYA CM LOG SYSTEM
• Timestamp: {timestamp} (Congo FLNG Time)
• System IP: {MYLOCALIP}
• Attachments: {len(attachments_info)} file(s)

Automated message from CM LOG SYSTEM
"""
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = SENDER_EMAIL
    
    display_recipients = ', '.join(recipients[:3])
    if len(recipients) > 3:
        display_recipients += f" +{len(recipients)-3} others"
    message['To'] = display_recipients
    message.attach(MIMEText(body, 'plain'))

    attached_names = []
    for filepath, orig_name in attachments_info:
        if not os.path.exists(filepath):
            print(f"⚠️ Skipping missing file: {filepath}")
            continue
            
        try:
            ctype, _ = mimetypes.guess_type(filepath)
            if ctype is None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            
            with open(filepath, 'rb') as fp:
                part = MIMEBase(maintype, subtype)
                part.set_payload(fp.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{orig_name}"'
            )
            message.attach(part)
            attached_names.append(orig_name)
        except Exception as e:
            print(f"⚠️ Attachment error ({orig_name}): {str(e)}")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as server:
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(message, to_addrs=recipients)
        return f"✅ Email sent to {len(recipients)} recipient(s)! Attached: {', '.join(attached_names) if attached_names else 'None'}"
    except smtplib.SMTPAuthenticationError:
        return "❌ EMAIL AUTH FAILED: Invalid GMAIL_APP_PASSWORD. Contact administrator."
    except Exception as e:
        return f"❌ Email failed: {str(e)[:150]}"

def _submit_form_core(uploaded_files, tagname, description, reported_by, recipient_file):
    """Unified handler: validate → save → email (with status='sent' default)"""
    # VALIDATION
    errors = []
    if not tagname or not tagname.strip():
        errors.append("• TAGNAME is mandatory")
    if not reported_by or not reported_by.strip():
        errors.append("• 'Reported by' is mandatory")
    if uploaded_files and len(uploaded_files) > 10:
        errors.append("• Maximum 10 files allowed")
    if errors:
        return "❌ CORRECTION REQUIRED:\n" + "\n".join(errors)
    
    # PROCESS FILES
    attachments_info = []
    stored_filenames = []
    if uploaded_files:
        for temp_path in uploaded_files:
            orig_name = os.path.basename(temp_path)
            safe_name = re.sub(r'[^\w\-_\.]', '_', orig_name)
            storage_name = f"{uuid.uuid4().hex}_{safe_name}"
            dest_path = os.path.join(ATTACHMENTS_DIR, storage_name)
            
            try:
                shutil.copy(temp_path, dest_path)
                attachments_info.append((dest_path, orig_name))
                stored_filenames.append(storage_name)
            except Exception as e:
                return f"❌ File save error ({orig_name}): {str(e)}"

    # GENERATE ID & SAVE TO DB (WITH STATUS='sent')
    next_id = generate_next_id()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db_entry = {
        "ID_db": next_id,
        "TAGNAME": tagname.strip(),
        "DESCRIPTION": description.strip() if description else "",
        "reported_by": reported_by.strip(),
        "timestamp": timestamp,
        "attachment_count": len(attachments_info),
        "original_filenames": [orig for _, orig in attachments_info],
        "stored_filenames": stored_filenames,
        "status": "sent",  # ✅ DEFAULT STATUS FOR NEW ENTRIES
        "last_edited": None,
        "edited_by": None
    }

    try:
        save_to_database(db_entry)
    except Exception as e:
        return f"❌ Database save failed: {str(e)}"

    # GENERATE EMAIL NOTE
    custom_note = f"""ID: CM-{next_id:05d}
TAGNAME: {tagname.strip()}
DESCRIPTION: {description.strip() if description else 'None provided'}
Reported by: {reported_by.strip()}
Timestamp: {timestamp}
Status: sent
Attachments: {len(attachments_info)} file(s)"""
    if attachments_info:
        custom_note += "\n\nAttached Files:\n" + "\n".join(f"• {orig}" for _, orig in attachments_info)
    
    # SEND EMAIL
    try:
        recipients = load_recipients(recipient_file)
        if not recipients:
            return f"⚠️ Report saved (ID: **CM-{next_id:05d}**), but NO RECIPIENTS FOUND in {recipient_file}. Email not sent."
    except Exception as e:
        return f"⚠️ Report saved (ID: **CM-{next_id:05d}**), recipient file error ({recipient_file}): {str(e)}"

    email_result = send_email_with_exports(recipients, attachments_info, custom_note)

    # SUCCESS MESSAGE
    if email_result.startswith("✅"):
        return f"""✅ **SUCCESS!**  
Report saved with ID: CM-{next_id:05d}  
Status: **sent**  
{email_result}  
📁 Files archived in `{ATTACHMENTS_DIR}`"""
    else:
        return f"""⚠️ PARTIAL SUCCESS  
Report saved with ID: CM-{next_id:05d}  
Status: **sent**  
📧 Email status: {email_result} (Data safely stored locally)"""

def submit_to_inst(uploaded_files, tagname, description, reported_by):
    msg = _submit_form_core(uploaded_files, tagname, description, reported_by, INST_RECIPIENTS_FILE)
    return msg, load_logs_for_display()

def submit_to_icss(uploaded_files, tagname, description, reported_by):
    msg = _submit_form_core(uploaded_files, tagname, description, reported_by, ICSS_RECIPIENTS_FILE)
    return msg, load_logs_for_display()

# ======================
# GRADIO INTERFACE (FULLY ENHANCED)
# ======================
CUSTOM_CSS = """
#success-banner {
    background-color: #ecfdf5;
    border-left: 4px solid #10b981;
    padding: 15px;
    border-radius: 0 8px 8px 0;
    margin: 20px 0;
    font-weight: 500;
}
.footer-note {
    background-color: #f0f9ff;
    padding: 12px;
    border-radius: 6px;
    margin-top: 15px;
    font-size: 0.92em;
    border-left: 3px solid #3b82f6;
}
.edit-indicator {
    color: #dc2626;
    font-weight: bold;
    font-size: 1.1em;
}
.gradio-container { max-width: 950px !important; margin: 0 auto !important; }
.compact-text { font-size: 0.95em; color: #555; margin-top: -8px; }
.required::after {
    content: " *";
    color: #ef4444;
    font-weight: bold;
}
.inst-btn {
    background: linear-gradient(to right, #10b981, #0da271) !important;
    color: white !important;
}
.icss-btn {
    background: linear-gradient(to right, #3b82f6, #2563eb) !important;
    color: white !important;
}
.delete-btn {
    background: linear-gradient(to right, #ef4444, #b91c1c) !important;
    color: white !important;
}
.admin-section {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 15px;
    margin-top: 20px;
    background-color: #f9fafb;
}
"""

# JavaScript: Confirmation dialogs + SMART ROW HIGHLIGHTING with MutationObserver
JS_CODE = """
(function() {
    // ===== CONFIRMATION DIALOGS (UNCHANGED) =====
    document.body.addEventListener('click', function(e) {
        const instBtn = e.target.closest('.inst-btn');
        const icssBtn = e.target.closest('.icss-btn');
        const deleteBtn = e.target.closest('.delete-btn');
        
        if (instBtn && !confirm("⚠️ CONFIRM SUBMISSION\\n\\nAre you sure you want to submit this report to the INST team?\\nThis will send an email to all INST recipients and cannot be undone.")) {
            e.preventDefault(); e.stopPropagation(); return false;
        }
        if (icssBtn && !confirm("⚠️ CONFIRM SUBMISSION\\n\\nAre you sure you want to submit this report to the ICSS team?\\nThis will send an email to all ICSS recipients and cannot be undone.")) {
            e.preventDefault(); e.stopPropagation(); return false;
        }
        if (deleteBtn && !confirm("⚠️ PERMANENT DELETION\\n\\nAre you absolutely sure you want to delete this log entry?\\nAttachments will NOT be deleted (manual cleanup required in attachments/ folder).")) {
            e.preventDefault(); e.stopPropagation(); return false;
        }
    });
    
    // ===== ENTIRE ROW COLORING (ADAPTED FROM YOUR WORKING CODE) =====
    function applyStatusColors() {
        // Find ALL status cells by text content (YOUR PROVEN METHOD)
        const statusCells = Array.from(document.querySelectorAll('#log-table td, #log-table div'))
            .filter(cell => {
                const text = cell.textContent?.trim().toLowerCase();
                return text === 'sent' || text === 'ongoing' || text === 'completed';
            });
        
        statusCells.forEach(cell => {
            // Determine color and tooltip (UNCHANGED FROM YOUR WORKING CODE)
            const status = cell.textContent.trim().toLowerCase();
            let bgColor = '';
            if (status === 'sent') {
                bgColor = '#fff3e0'; // Light orange
                cell.title = 'Workflow status: Sent (Report submitted)';
            } else if (status === 'ongoing') {
                bgColor = '#fff9c4'; // Yellow
                cell.title = 'Workflow status: Ongoing (Work in progress)';
            } else if (status === 'completed') {
                bgColor = '#e8f5e9'; // Light green
                cell.title = 'Workflow status: Completed (Issue resolved)';
            }
            
            // ✅ CRITICAL FIX: COLOR THE PARENT CONTAINER (ENTIRE ROW)
            // In Gradio's DOM, the direct parent of the cell IS the row container
            if (cell.parentElement) {
                cell.parentElement.style.backgroundColor = bgColor;
                cell.parentElement.style.transition = 'background-color 0.2s';
                // Ensure child cells don't override row color
                cell.parentElement.style.background = bgColor; // Cover all bases
            }
            
            // ✅ ENHANCE STATUS CELL (with transparent bg to show row color)
            cell.style.backgroundColor = 'transparent'; // Critical: let row color show through
            cell.style.fontWeight = 'bold';
            cell.style.textAlign = 'center';
            cell.style.borderRadius = '4px';
            cell.style.padding = '2px 6px';
        });
        
        // Style edit indicators (✅) - preserve your working logic
        document.querySelectorAll('#log-table td, #log-table div').forEach(cell => {
            if (cell.textContent.trim() === '✅') {
                cell.style.color = '#dc2626';
                cell.style.fontWeight = 'bold';
                cell.style.fontSize = '1.2em';
                cell.title = 'Log has been edited';
                cell.style.backgroundColor = 'transparent'; // Show row color underneath
            }
        });
    }
    
    // ===== ROBUST INITIALIZATION (YOUR WORKING METHOD) =====
    function init() {
        applyStatusColors();
        
        // Observe entire document body for table updates (critical for virtualized tables)
        const observer = new MutationObserver(() => {
            if (document.getElementById('log-table')) {
                setTimeout(applyStatusColors, 100);
            }
        });
        
        observer.observe(document.body, { 
            childList: true, 
            subtree: true 
        });
    }
    
    // Start after DOM is fully ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
"""

with gr.Blocks(
    title="Corrective Maintenance Log",
    theme=gr.themes.Soft(primary_hue="emerald", secondary_hue="blue"),
    css=CUSTOM_CSS
) as demo:
    
    gr.Markdown(f"""# 🔧 Corrective Maintenance Log System
Submit equipment issues with supporting documentation.  
🌐 Network Access: http://{MYLOCALIP}:7960""")
    gr.Markdown("""⚠️ **Mobile Users**: Tap the upload area → Select "Camera" to capture photos directly  
(Works on Android/iOS - no app install needed)""", elem_classes=["footer-note"])
    
    # ===== ADD NEW ENTRY =====    
    with gr.Row():
        with gr.Column():
            file_upload = gr.File(
                label="📎 Attach Documentation (Photos, PDFs, etc.)",
                file_types=[".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".webp"],
                file_count="multiple",
                type="filepath",
            )
            gr.Markdown("Max 10 files. Mobile: Select 'Camera' to capture new photos")
        
        with gr.Column():
            tagname = gr.Textbox(
                label="TAGNAME",
                info="Equipment tag or location identifier",
                placeholder="e.g., PUMP-205, VALVE-B3",
                elem_classes=["required"]
            )
            reported_by = gr.Textbox(
                label="REPORTED BY",
                info="Your full name and role",
                placeholder="e.g., John Doe, Maintenance Technician",
                elem_classes=["required"]
            )
    with gr.Row():
        description = gr.Textbox(
            label="DESCRIPTION",
            info="Detailed issue description",
            placeholder="Describe the problem, symptoms, safety concerns...",
            lines=3,
            max_lines=6
        )            

    # TWO BUTTONS FOR DEPARTMENTAL ROUTING
    with gr.Row():
        save_btn_inst = gr.Button(
            "🧰 SAVE & SEND to INST", 
            variant="primary", 
            size="lg",
            elem_classes=["inst-btn"]
        )
        save_btn_icss = gr.Button(
            "🎛️ SAVE & SEND to ICSS", 
            variant="secondary", 
            size="lg",
            elem_classes=["icss-btn"]
        )

    output_msg = gr.Markdown("""\n\nSave and send operations displayed here.
Check status after submitting...""", elem_id="success-banner")

    # ===== SEARCH BAR =====
    gr.Markdown("")
    gr.Markdown("---")
    gr.Markdown("")
    with gr.Row():
        search_box = gr.Textbox(
            label="🔍 Search Logs (ID, Tagname, Description, Reported By, Status)",
            placeholder="Type to filter recent logs...",
            info="Searches across all fields including status (sent/ongoing/completed)"
        )

    # ===== LOG HISTORY TABLE (WITH STATUS COLUMN & HIGHLIGHTING) =====
    gr.Markdown("## 📋 Recent Maintenance Logs (Last 20 Entries)")
    log_table = gr.DataFrame(
        value=load_logs_for_display(),
        headers=["ID", "Tagname", "Description", "Reported By", "Timestamp", "Attachments", "Status", "Edited"],  # 8 COLUMNS
        datatype=["str", "str", "str", "str", "str", "number", "str", "str"],
        wrap=True,
        interactive=False,
        elem_classes=["log-table"],
        elem_id="log-table"  # CRITICAL FOR JS TARGETING
    )
    
    # ===== ADMIN SECTION: FULL EDIT/DELETE =====
    with gr.Accordion("🛠️ Admin Functions: Edit or Delete Existing Logs", open=False, elem_classes=["admin-section"]):
        gr.Markdown("⚠️ **Use with caution**: All fields editable except ID, timestamp, and attachments. Deletion removes database entry (attachments require manual cleanup).")
        
        with gr.Row():
            all_logs = load_all_logs()
            log_ids = [f"CM-{entry['ID_db']:05d}" for entry in sorted(all_logs, key=lambda x: x['ID_db'], reverse=True)] if all_logs else ["No logs available"]
            
            log_selector = gr.Dropdown(
                choices=log_ids,
                label="Select Log ID to Edit/Delete",
                info="Choose a log entry from the database"
            )
            load_log_btn = gr.Button("퀵 Load Log Details", variant="secondary")
        
        # TWO-COLUMN LAYOUT FOR ALL EDITABLE FIELDS
        with gr.Row():
            with gr.Column():
                edit_tagname = gr.Textbox(
                    label="🏷️ Tagname",
                    info="Equipment tag or location identifier",
                    interactive=False
                )
                edit_description = gr.Textbox(
                    label="📝 Description",
                    lines=3,
                    max_lines=6,
                    interactive=False
                )
            with gr.Column():
                edit_status = gr.Dropdown(
                    choices=VALID_STATUSES,
                    value="sent",
                    label="🚦 Status",
                    info="Workflow progress status",
                    interactive=False
                )
                edit_reported_by = gr.Textbox(
                    label="👤 Reported By",
                    interactive=False
                )
        
        with gr.Row():
            update_btn = gr.Button("💾 UPDATE Log (All Fields)", variant="primary", interactive=False)
            delete_btn = gr.Button(
                "🗑️ DELETE Log Entry", 
                variant="stop", 
                interactive=False,
                elem_classes=["delete-btn"]
            )
        
        admin_output = gr.Markdown("")
        
        # ===== EDIT/DELETE LOGIC =====
        def load_log_details(selected_id):
            if not selected_id or selected_id == "No logs available":
                return (
                    gr.update(interactive=False), gr.update(interactive=False),
                    gr.update(interactive=False), gr.update(interactive=False),
                    gr.update(interactive=False), gr.update(interactive=False), ""
                )
            
            try:
                log_id = int(selected_id.split('-')[1])
                all_logs = load_all_logs()
                for log in all_logs:
                    if log.get('ID_db') == log_id:
                        # Safe status retrieval with fallback
                        current_status = log.get('status', 'sent')
                        if current_status not in VALID_STATUSES:
                            current_status = 'sent'
                        
                        return (
                            gr.update(value=log.get('TAGNAME', ''), interactive=True),
                            gr.update(value=log.get('DESCRIPTION', ''), interactive=True),
                            gr.update(value=current_status, interactive=True),
                            gr.update(value=log.get('reported_by', ''), interactive=True),
                            gr.update(interactive=True),  # update_btn
                            gr.update(interactive=True),  # delete_btn
                            f"✅ Loaded log CM-{log_id:05d}. Edit fields below and click UPDATE."
                        )
                return (
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=False), gr.update(interactive=False),
                    "❌ Log not found"
                )
            except Exception as e:
                return (
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(interactive=False), gr.update(interactive=False),
                    f"❌ Error: {str(e)}"
                )
        
        def handle_update(selected_id, new_tagname, new_description, new_status, new_reported_by):
            if not selected_id:
                return "❌ No log selected"
            try:
                log_id = int(selected_id.split('-')[1])
                success, msg = update_log_entry(log_id, new_tagname, new_description, new_reported_by, new_status)
                return msg
            except Exception as e:
                return f"❌ Update error: {str(e)}"
        
        def handle_delete(selected_id):
            if not selected_id:
                return "❌ No log selected"
            try:
                log_id = int(selected_id.split('-')[1])
                success, msg = delete_log_entry(log_id)
                return msg
            except Exception as e:
                return f"❌ Deletion error: {str(e)}"
        
        # LOAD LOG DETAILS
        load_log_btn.click(
            load_log_details,
            inputs=[log_selector],
            outputs=[
                edit_tagname, edit_description, 
                edit_status, edit_reported_by,
                update_btn, delete_btn,
                admin_output
            ]
        )
        
        # UPDATE LOG
        update_btn.click(
            handle_update,
            inputs=[log_selector, edit_tagname, edit_description, edit_status, edit_reported_by],
            outputs=[admin_output]
        ).then(
            lambda: load_logs_for_display(),
            outputs=[log_table]
        )
        
        # DELETE LOG (with form reset)
        delete_btn.click(
            handle_delete,
            inputs=[log_selector],
            outputs=[admin_output]
        ).then(
            lambda: load_logs_for_display(),
            outputs=[log_table]
        ).then(
            lambda: (
                gr.update(value=None), gr.update(value=""), gr.update(value=""), 
                gr.update(value="sent"), gr.update(value=""),
                gr.update(interactive=False), gr.update(interactive=False), ""
            ),
            outputs=[
                log_selector, edit_tagname, edit_description,
                edit_status, edit_reported_by,
                update_btn, delete_btn, admin_output
            ]
        )
    
    # ===== SYSTEM INFO =====
    accordionTEXT = f"""📁 Storage: Attachments saved to `{ATTACHMENTS_DIR}` | Database: `{CMLOGS_DB_FNAME}`<br>
🔒 Security: All data remains on your local network. Emails require configured Gmail App Password.<br>
💡 Tip: ID format = CM-XXXXX (auto-generated after submission)<br>
📤 Routing: INST button uses `{INST_RECIPIENTS_FILE}` | ICSS button uses `{ICSS_RECIPIENTS_FILE}`<br>
✏️ Edit Policy: All fields editable except ID, timestamp, and attachments (preserves audit trail)<br>
🚦 Status Workflow: `sent` → `ongoing` → `completed` (manually updated via Admin Functions)<br>
🗑️ Delete Note: Database entry removed only; attachments require manual cleanup in `{ATTACHMENTS_DIR}`"""
    
    gr.Markdown("---")
    with gr.Accordion("📚 Read Brief Manual", open=False):
        gr.Markdown(accordionTEXT, elem_classes=["footer-note"])    
    
    # FOOTER (URL FIXED)
    with gr.Row():
        with gr.Column(scale=1):
            try:
                gr.Image("logo.png", height=40, container=False, buttons=[])
            except:
                gr.Markdown("NGUYA FLNG", elem_classes=["footer-note"])
        with gr.Column(scale=2):
            # FIXED URL: Removed trailing spaces
            gr.Markdown(f"""**All rights reserved (C)**  
created by fabio.matricardi@key-solution.eu for NGUYA FLNG Project  
visit [Key Solution SRL](https://key-solution.eu) | Network IP: {MYLOCALIP}""")

    # ===== EVENT HANDLERS =====
    search_box.change(
        load_logs_for_display,
        inputs=[search_box],
        outputs=[log_table]
    )
    
    save_btn_inst.click(
        submit_to_inst,
        inputs=[file_upload, tagname, description, reported_by],
        outputs=[output_msg, log_table],
        show_progress="full"
    )
    save_btn_icss.click(
        submit_to_icss,
        inputs=[file_upload, tagname, description, reported_by],
        outputs=[output_msg, log_table],
        show_progress="full"
    )
    

# ======================
# LAUNCH
# ======================
if __name__ == "__main__":
    print("\n" + "= "*70)
    print("🚀 CORRECTIVE MAINTENANCE LOG SYSTEM - READY")
    print("= "*70)
    print(f"✅ Attachments directory: {os.path.abspath(ATTACHMENTS_DIR)}")
    print(f"✅ Database file: {os.path.abspath(CMLOGS_DB_FNAME)}")
    print(f"✅ INST Recipients file: {os.path.abspath(INST_RECIPIENTS_FILE)}")
    print(f"✅ ICSS Recipients file: {os.path.abspath(ICSS_RECIPIENTS_FILE)}")
    print(f"\n🌐 ACCESS VIA:")
    print(f"   • Local: http://localhost:7960")
    print(f"   • Network: http://{MYLOCALIP}:7960")
    print("\n⚠️ EMAIL REQUIREMENTS:")
    print("   • secret.json must contain valid Gmail App Password")
    print("   • Recipient files must contain emails (one per line, # for comments)")
    print("\n✨ NEW FEATURES:")
    print("   • 🚦 Status field (sent/ongoing/completed) with row highlighting")
    print("   • 🔍 Enhanced search (includes status values)")
    print("   • ✏️ FULL edit capability (Tagname, Description, Reported By, Status)")
    print("   • 🗑️ Safe delete with JavaScript confirmation")
    print("   • 🌐 Fixed footer URL (no broken links)")
    print("= "*70 + "\n")
    
    demo.launch(server_port=7960, js=JS_CODE,css=CUSTOM_CSS)