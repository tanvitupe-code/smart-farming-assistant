# Smart Farming AI Decision Assistant — upgrade

## What is improved
- AI is now the main feature: structured farming decision support rather than a short generic explanation.
- Uses farm profile, weather snapshot and user-entered market prices as context.
- Provides weather considerations, crop-planning considerations, water/soil checks, budget arithmetic, market interpretation and next steps.
- Includes optional farmer question and downloadable AI advisory.
- Weather results are cached for 30 minutes.
- API errors shown without exposing full exception details in the interface.

## Run locally
1. Install Python 3.10+ and VS Code.
2. Open this folder in VS Code.
3. In the terminal run `py -m venv .venv` and activate it on Windows with `.venv\\Scripts\\activate`.
4. Run `pip install -r requirements.txt`.
5. Create a `.env` file based on `.env.example` and set `GEMINI_API_KEY`.
6. Run `streamlit run app.py`.

## Update the deployed Streamlit app
The live app must be updated through its connected GitHub repository; this assistant cannot directly modify your Streamlit deployment.
1. Open the GitHub repository connected to the current app.
2. Replace its `app.py` with this version and ensure `requirements.txt` includes `google-genai` and the other listed packages.
3. Commit the changes. Streamlit Community Cloud will redeploy from the repository.
4. In the app's Manage app → Settings → Secrets, add `GEMINI_API_KEY = "your_actual_key"` if not already configured. Keep the key private; do not put it in public code.
5. Open the app and test the AI button.

Official docs: https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
