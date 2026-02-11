import gradio as gr
import json
import os
import datetime
import socket
import tempfile
import re
import CM_send, expert_panel, upload, usermannual

with gr.Blocks() as demo:
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
        )