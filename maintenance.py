import gradio as gr
import json
import os
import datetime
import socket
import tempfile
import re
import CM_send, expert_panel, upload, usermannual


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


with gr.Blocks(title="🔧 Corrective Maintenance Log System") as demo:
    CM_send.demo.render()
with demo.route("📧 Expert Email panel and Exports"):
    expert_panel.demo.render()
with demo.route("📲 Mobile Upload photo/documents"):
    upload.demo.render()
with demo.route("📔 USER MANUAL"):
    usermannual.demo.render()

if __name__ == "__main__":
    # Auto-detect LAN IP address
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            if local_ip.startswith("127.") or ":" in local_ip:
                local_ip = "YOUR_LOCAL_IP"
        except:
            local_ip = "YOUR_LOCAL_IP"    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7960,
        inbrowser=True,
        js=JS_CODE)