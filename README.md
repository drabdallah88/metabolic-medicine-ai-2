# Metabolic Medicine Reference Assistant

Free Streamlit research-reference discovery prototype.

## Publish without code
1. Create a free GitHub account at https://github.com/signup.
2. Create a **private** repository and upload `app.py`, `requirements.txt`, and `README.md` to its root using **Add file → Upload files**.
3. Visit https://share.streamlit.io/ and sign in with GitHub.
4. Choose **Create app** / **Deploy app**, select your repository, main branch and `app.py` as the main file, then deploy.
5. Share the Streamlit app URL if your source and book permissions allow it. Set app access appropriately. Note: Streamlit Community Cloud may have restrictions on private repositories and app visibility.

Optional: Add `ACCESS_PASSWORD` as an app secret/environment variable to gate access. This is a shared password, **not multi-user authentication**.

## Limitations
- PDF books are kept in the browser's active Streamlit session; no durable library.
- Only searchable PDFs work; scanned documents require OCR.
- PDF page is the file's page position, not necessarily the printed page number.
- Source PDFs are downloaded so readers can navigate to the cited page in their PDF viewer.
- PubMed and GeneReviews are bibliographic search; Orphanet is an external link.
- No generative AI, clinical validation, or verified claim-level citations.
- This prototype is not suitable for patient-identifiable information or regulated clinical use.
- Free hosting has compute, storage, and uptime limits.
