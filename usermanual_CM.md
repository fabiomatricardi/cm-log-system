# Corrective Maintenance (CM) Log System  
## User Manual  
*Version 1.0 • NGUYA FLNG Project*

---

### 📌 Table of Contents
1. [System Overview](#system-overview)  
2. [Accessing the System](#accessing-the-system)  
3. [Submitting a Maintenance Report](#submitting-a-maintenance-report)  
4. [Mobile Document Capture](#mobile-document-capture)  
5. [Admin Functions (Expert Panel)](#admin-functions-expert-panel)  
6. [Email Configuration](#email-configuration)  
7. [Security & Data Handling](#security--data-handling)  
8. [Troubleshooting](#troubleshooting)  
9. [Support Contact](#support-contact)  

---

## 1. System Overview <a name="system-overview"></a>

The Corrective Maintenance (CM) Log System is a secure, local-first application for reporting equipment issues at the NGUYA FLNG facility. It enables technicians to:

✅ Submit maintenance reports with photo/PDF attachments  
✅ Route reports to **INST** (Instrumentation) or **ICSS** (Integrated Control & Safety Systems) teams  
✅ Generate sequential IDs (CM-XXXXX format) for tracking  
✅ View recent logs in a searchable table  
✅ Export complete logs to Excel for analysis  

**Key Features:**  
- Works on desktops, tablets, and mobile phones (no app install required)  
- All data remains on your local network (no cloud storage)  
- Dual routing paths for departmental workflows  
- Automatic email notifications to assigned teams  

---

## 2. Accessing the System <a name="accessing-the-system"></a>

### 🌐 Network Access
Open a browser and navigate to:  
```
http://<SERVER_IP>:7960
```
*Replace `<SERVER_IP>` with your facility's server address (e.g., `192.168.10.45`)*

### 🔑 Interface Tabs
The system has three tabs accessible via the top navigation bar:

| Tab | Purpose | Access Level |
|-----|---------|--------------|
| **Main CM Log** | Submit maintenance reports | All personnel |
| **📧 Expert Email panel and Exports** | Manage recipients & export logs | Admin only (`admin`/`admin`) |
| **📲 Mobile Upload photo/documents** | Capture/save documents from mobile | All personnel |

> 💡 **Tip:** Bookmark the main URL for quick access. Mobile users should use the dedicated "Mobile Upload" tab for camera capture.

---

## 3. Submitting a Maintenance Report <a name="submitting-a-maintenance-report"></a>

### Step-by-Step Guide

1. **Open the Main CM Log tab** (`http://<SERVER_IP>:7960`)

2. **Attach Documentation** (Optional but recommended):
   - Click *📎 Attach Documentation*
   - Select files from your device **OR**
   - On mobile: Tap upload area → Select **"Camera"** → Capture photo → Confirm
   - *Max 10 files allowed (PDF, JPG, PNG, BMP, WEBP)*

3. **Complete Required Fields** (marked with *):
   - **TAGNAME***: Equipment identifier (e.g., `PUMP-205`, `VALVE-B3`)
   - **REPORTED BY***: Your full name and role (e.g., `John Doe, Maintenance Tech`)

4. **Add Description** (Optional but recommended):
   - Describe symptoms, safety concerns, location details
   - Be specific: *"Vibration noise near bearing housing, oil leak observed"*

5. **Route to Correct Team**:
   - 🧰 **SAVE & SEND to INST** → For instrumentation/electrical issues
   - 🎛️ **SAVE & SEND to ICSS** → For control system/DCS issues

6. **Confirmation**:
   - Green banner shows: `✅ SUCCESS! Report saved with ID: CM-00123`
   - Email sent to assigned team(s) with attachments
   - Report appears instantly in the "Recent Logs" table below

### 📋 Recent Logs Table
View the last 20 reports with columns:
- **ID**: Sequential CM number (e.g., CM-00123)
- **Tagname**: Equipment identifier
- **Description**: First 50 characters of issue description
- **Reported By**: Technician name
- **Timestamp**: Submission date/time (Congo FLNG Time)
- **Attachments**: Number of files attached

> ⚠️ **Critical**: Always verify the correct routing button (INST vs ICSS) before submission. Reports cannot be re-routed after submission.

---

## 4. Mobile Document Capture <a name="mobile-document-capture"></a>

### For Android/iOS Phones & Tablets

1. Open browser → Navigate to `http://<SERVER_IP>:7960` → Select **"📲 Mobile Upload"** tab

2. **To capture new photos**:
   - Tap *📸 Capture from Camera*
   - Allow camera permission when prompted
   - Take photo → Confirm → Tap **💾 SAVE ALL FILES**

3. **To upload existing files**:
   - Tap *📎 Upload Documents*
   - Select photos/PDFs from gallery → Tap **💾 SAVE ALL FILES**

4. **Confirmation**:
   - Green banner shows saved file paths (e.g., `attachments/20240211_143022_a1b2c3_photo.jpg`)
   - Files are immediately available for attachment in main CM form

> 📱 **Mobile Tips**  
> - Works on Chrome (Android) and Safari (iOS)  
> - For best results: Use Chrome on Android → Site Settings → Allow camera for this IP address  
> - Files save to server's `attachments/` folder – no storage used on your device  
> - *Camera may not work over HTTP on some networks – file uploads always work*

---

## 5. Admin Functions (Expert Panel) <a name="admin-functions-expert-panel"></a>

*Requires admin credentials (`admin` / `admin`)*

### 🔒 Accessing Admin Panel
1. Navigate to `http://<SERVER_IP>:7961` **OR**  
   Use the **"📧 Expert Email panel and Exports"** tab in main app
2. Enter credentials → Click *"🔓 Unlock Email Editors"*

### 📧 Managing Email Recipients
Two recipient lists control email routing:

| File | Purpose | Edit Location |
|------|---------|---------------|
| `CMemails.txt` | INST team recipients | "INST Recipients" section |
| `CM-ICSS-emails.txt` | ICSS team recipients | "ICSS Recipients" section |

**Editing Rules:**
- One email per line (e.g., `john.doe@nguya-flng.com`)
- Lines starting with `#` are comments (ignored by system)
- At least one valid email required per file
- Click **💾 Save** after edits → Changes apply immediately

### 📤 Exporting Logs to Excel
1. Click **"📤 Export to Excel"** button
2. System generates timestamped file: `exports/cmlogs_export_YYYYMMDD_HHMMSS.xlsx`
3. Click download link to save locally
4. Excel file includes:
   - All CM logs with full descriptions
   - Original attachment filenames preserved
   - Auto-sized columns for readability
   - ID formatted as CM-XXXXX

> ⚠️ **Admin Note**: Requires `pandas` and `openpyxl` installed on server (`pip install pandas openpyxl`)

---

## 6. Email Configuration <a name="email-configuration"></a>

### Prerequisites
Email notifications require:
1. Valid Gmail account configured for **App Passwords** (2FA required)
2. `secret.json` file on server containing:
```json
{
  "secret_code": "your_gmail_app_password_here"
}
```
3. Recipient files (`CMemails.txt` / `CM-ICSS-emails.txt`) with at least one valid email

### Email Content Includes:
- Sequential CM ID (e.g., CM-00123)
- Equipment TAGNAME and description
- Reporter name and timestamp
- All attached files (original filenames preserved)
- Confidentiality notice

> 🔒 **Security Note**: Emails are sent via Gmail SMTP but **all attachments and logs remain on your local server**. No data leaves your facility except the email notification itself.

---

## 7. Security & Data Handling <a name="security--data-handling"></a>

| Aspect | Implementation |
|--------|----------------|
| **Data Location** | 100% local storage – no cloud/sync |
| **Attachments** | Saved to server's `attachments/` folder |
| **Database** | `cmlogs-db.json` (human-readable JSON) |
| **Network Access** | HTTP only (no encryption) – use within facility LAN |
| **Admin Access** | Hardcoded credentials (`admin`/`admin`) – change in code if needed |
| **File Safety** | Filenames sanitized to prevent path traversal attacks |

> ⚠️ **Critical Security Practices**  
> - Only access system within NGUYA FLNG facility network  
> - Never expose port 7960/7961 to public internet  
> - Change default admin password in `expert_panel.py` for production use  
> - Regularly backup `cmlogs-db.json` and `attachments/` folder  

---

## 8. Troubleshooting <a name="troubleshooting"></a>

| Issue | Solution |
|-------|----------|
| ❌ *"Email auth failed"* | Verify `secret.json` contains valid Gmail App Password (not account password) |
| ❌ *"No recipients found"* | Check `CMemails.txt`/`CM-ICSS-emails.txt` exist and contain emails (not just comments) |
| 📱 Camera won't open on mobile | Use Chrome → Site Settings → Allow camera for server IP; or use file upload instead |
| 📁 *"File save error"* | Ensure `attachments/` folder has write permissions on server |
| 🔒 Can't access Expert Panel | Verify credentials are `admin`/`admin` (case-sensitive); panel runs on port 7961 |
| 📊 Table not updating | Click browser refresh – logs update automatically after submission |
| 🌐 Can't connect to server | Confirm server is running; check IP address with facility IT team |

> 💡 **Pro Tip**: All operations work without internet except email sending. Reports save locally even if email fails.

---

## 9. Support Contact <a name="support-contact"></a>

For system issues or configuration changes:

📧 **Email**: fabio.matricardi@key-solution.eu  
🌐 **Company**: Key Solution SRL ([https://key-solution.eu](https://key-solution.eu))  
📍 **Project**: NGUYA FLNG Maintenance Systems  

> ℹ️ This system is property of NGUYA FLNG Project. Unauthorized modification or distribution prohibited.  
> © 2026 Key Solution SRL – All rights reserved

---

### Appendix: System Architecture Diagram
```
[Technician Device] 
        ↓ (HTTP)
[CM Log System @ Port 7960]
├── Main Interface → Save to cmlogs-db.json → Email via Gmail SMTP
├── Mobile Upload → Save to attachments/ folder
└── Expert Panel @ Port 7961 → Manage recipients / Export to Excel
        ↓
[Local Server Storage]
├── cmlogs-db.json (database)
├── attachments/ (all files)
├── CMemails.txt (INST recipients)
└── CM-ICSS-emails.txt (ICSS recipients)
```

*Document Version: 1.0 • Last Updated: February 2026*