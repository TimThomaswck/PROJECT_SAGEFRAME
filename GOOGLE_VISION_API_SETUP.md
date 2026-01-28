# Google Vision API Setup Instructions

This guide will help you configure your own Google Vision API key for document OCR (Optical Character Recognition) in SageFrame.

## Prerequisites
- Google Cloud Platform (GCP) account
- Access to GCP Console
- Internet connection

---

## Step 1: Create or Select a GCP Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the **Project Selector** dropdown at the top
3. Either:
   - **Create a new project**: Click "NEW PROJECT"
     - Enter a project name (e.g., "SageFrame")
     - Click "CREATE"
   - **Use existing project**: Select one from the list

---

## Step 2: Enable the Vision API

1. In the Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for **"Cloud Vision API"**
3. Click on **Cloud Vision API** from the results
4. Click the **ENABLE** button
5. Wait for the service to be enabled (may take a few seconds)

---

## Step 3: Create Service Account or OAuth Credentials

### Option A: Service Account (Recommended for automated use)

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → Select **Service Account**
3. Fill in the service account details:
   - **Service account name**: `sageframe-vision`
   - **Service account ID**: (auto-populated)
   - Click **CREATE AND CONTINUE**
4. Grant permissions:
   - Click **SELECT A ROLE**
   - Search for and select **"Basic"** → **"Viewer"** (or "Editor" if needed)
   - Click **CONTINUE** → **DONE**
5. Back in Credentials page, click the newly created service account
6. Go to **KEYS** tab
7. Click **ADD KEY** → **Create new key**
8. Choose **JSON** format
9. Click **CREATE** - a JSON file will download
10. Extract the `private_key` field from the JSON file

### Option B: API Key (Simpler)

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → Select **API Key**
3. The API key will be displayed
4. Copy the API key value

---

## Step 4: Set Up Billing (Required)

⚠️ **Important**: Google Vision API requires billing to be enabled, even for free tier usage.

1. Go to **Billing** in Google Cloud Console
2. Click **CREATE BILLING ACCOUNT**
3. Fill in your billing details (name, country, address)
4. Add a payment method (credit/debit card)
5. Accept terms and click **START MY FREE TRIAL**
6. Link the billing account to your project:
   - Go to **Billing** → **My Projects**
   - Find your project and click the menu (⋮)
   - Select **Change Billing Account**
   - Choose the billing account you just created

---

## Step 5: Configure API Key in SageFrame

After obtaining your API key, configure it in SageFrame using one of these methods:

### Method 1: Using the Configuration Script (Recommended)

1. Open a PowerShell terminal in the SageFrame project directory:
   ```powershell
   cd C:\Users\YOUR_USERNAME\Documents\PROJECT_SAGEFRAME\sageframe_desktop
   ```

2. Run this command (replace with your API key):
   ```powershell
   & "..\.venv\Scripts\python.exe" -c "
   import keyring
   api_key = 'YOUR_API_KEY_HERE'
   keyring.set_password('sageframe_file_ingestion', 'google_vision', api_key)
   print('Google Vision API key configured successfully!')
   print(f'Stored in: Windows Credential Manager')
   "
   ```

3. Paste your API key in place of `YOUR_API_KEY_HERE`
4. Press Enter to execute
5. You should see: **"Google Vision API key configured successfully!"**

### Method 2: Manual Windows Credential Manager (Alternative)

1. Open **Credential Manager** on Windows:
   - Press `Win + R`
   - Type `credentialManager` and press Enter
   - Or: Settings → Accounts → Credential Manager

2. Click **Windows Credentials**

3. Click **Add a generic credential**

4. Fill in:
   - **Internet or network address**: `sageframe_file_ingestion/google_vision`
   - **Username**: `google_vision`
   - **Password**: `YOUR_API_KEY_HERE`

5. Click **OK**

---

## Step 6: Verify Configuration

1. Restart SageFrame application
2. Go to **File → Import Document**
3. Select a PDF or image file
4. The extraction should work without errors

If you see API errors, check:
- API key is correct (no extra spaces)
- Vision API is enabled in GCP
- Billing is active on your GCP project
- Credentials are properly stored

---

## Troubleshooting

### Error: "Google Vision API key not configured"
- Run the configuration script from Step 5 again
- Ensure the keyring value is stored correctly

### Error: "403 PERMISSION_DENIED"
- Vision API is not enabled - Go back to Step 2

### Error: "403 BILLING_DISABLED"
- Billing is not enabled - Go back to Step 4
- Enable billing on your GCP project

### Error: "401 UNAUTHENTICATED"
- API key is incorrect or expired
- Generate a new API key from GCP Console

### Error: "QUOTA_EXCEEDED"
- Free tier quota has been reached (20 requests/minute)
- Wait a few minutes or upgrade your billing account

---

## API Quotas and Limits

**Free Tier:**
- 20 requests per minute
- 1,000 requests per day

**Pricing (after free tier):**
- First 1,000 requests/month: Free
- Additional requests: $1.50 per 1,000 requests

---

## Security Notes

⚠️ **Important**:
- Never commit API keys to version control
- Dont share your API key publicly
- Keys are stored securely in Windows Credential Manager
- Use service account keys for production systems
- Rotate keys regularly

---

## Additional Resources

- [Google Vision API Documentation](https://cloud.google.com/vision/docs)
- [GCP Pricing Calculator](https://cloud.google.com/products/calculator)
- [Authentication Documentation](https://cloud.google.com/docs/authentication)

---

## Getting Help

If you encounter issues:
1. Check the terminal output for specific error messages
2. Verify your API key in GCP Console
3. Ensure all steps above are completed
4. Check GCP Service Status: https://status.cloud.google.com/

