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
CM_MANNUAL = "usermanual_CM.md"          # USER MANUAL CM MARKDOWN
manualcontent = """"""
with open(CM_MANNUAL,'r',encoding='utf-8') as f:
	manualcontent = f.read()
	f.close()


MYLOCALIP = socket.gethostbyname(socket.gethostname()) if not socket.gethostname().startswith("localhost") else "127.0.0.1"

# ======================
# GRADIO INTERFACE
# ======================
with gr.Blocks(
    title="📔 USER MANUAL - CM System Admin",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="orange")
) as demo:
    
    gr.Markdown("# 📔 USER MANUAL - CM System Admin")
    gr.Markdown("---")
    gr.Markdown(manualcontent)
    gr.Markdown("")

    # FOOTER
    with gr.Row():
        with gr.Column(scale=1):
            gr.Image("logo.png", height=40, container=False, buttons=[])
        with gr.Column(scale=2):
            gr.Markdown("**All rights reserved (C)**\n"
                       "created by fabio.matricardi@key-solution.eu for NGUYA FLNG Project\n"
                       f"visit [Key Solution SRL](https://key-solution.eu) | Network IP: http://{MYLOCALIP}:7960")    

# ======================
# LAUNCH
# ======================
if __name__ == "__main__":
    print("\n" + "= "*70)
    print("📔 USER MANUAL - MAINTENANCE SYSTEM ADMIN CONSOLE")
    print("= "*70)
    print(f"\n🌐 ACCESS PANEL AT:")
    print(f"   • Local: http://localhost:7960")
    print(f"   • Network: http://{MYLOCALIP}:7960")
    print("\n⚠️ REQUIREMENTS:")
    print("   • pandas and openpyxl must be installed (`pip install pandas openpyxl`)")
    print("   • Main CM app must be running first to generate cmlogs-db.json")
    print("= "*70 + "\n")
    
    demo.launch()