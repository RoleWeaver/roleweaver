# AI Provider Setup

> **Need help?** Testers and new users can contact **roleweaverinfo@gmail.com** with setup questions or feedback.

Role Weaver needs one AI provider. It supports **Google Gemini**, **OpenAI**, and **LM Studio**. Role Weaver does not include an API key; hosted-provider keys belong to the user and must be kept private.

## Google Gemini

### Create the key
1. Go to Google AI Studio: https://aistudio.google.com/
2. Sign in with your Google account.
3. Open **API Keys**.
4. If a usable key is not already present, choose **Create API key** and follow the project/key dialog.
5. Copy the new key. New keys created in AI Studio use Google's current authorization-key system.

### Install the key in Role Weaver
1. Launch Role Weaver.
2. In **AI Provider**, select **Google Gemini**.
3. Paste the key into the **API Key** field.
4. Choose a model if desired, or leave the application's recommended/default selection.
5. Press **Test AI Connection**.
6. If the test succeeds, continue with your character setup.

Official Google documentation:
- https://ai.google.dev/gemini-api/docs/get-started
- https://ai.google.dev/gemini-api/docs/api-key

Google may offer free and paid usage tiers depending on the model and account. Quotas, billing and model availability can change, so use Google's current documentation rather than relying on old screenshots or model lists.

## OpenAI

**Important:** ChatGPT subscriptions and OpenAI API billing are separate. A ChatGPT Plus/Pro subscription does not itself provide Role Weaver with API credit.

### Create the key
1. Go to the OpenAI API Platform: https://platform.openai.com/
2. Sign in or create an API Platform account.
3. Open the API-key area and create a new **secret API key**.
4. Copy the key when it is displayed and store it securely.
5. Configure API billing/credits if required for the model and account you intend to use.

### Install the key in Role Weaver
1. Launch Role Weaver.
2. In **AI Provider**, select **OpenAI**.
3. Paste the secret key into the **API Key** field.
4. Select an OpenAI model available to your API account.
5. Press **Test AI Connection**.
6. If the test succeeds, continue with your character setup.

Official OpenAI quickstart:
- https://platform.openai.com/docs/quickstart

Model availability and API prices change. Role Weaver documentation intentionally does not promise a particular current model or price; check the OpenAI API Platform for current options.

## LM Studio — local models

LM Studio can run an LLM on your own computer and expose a local OpenAI-compatible server to Role Weaver.

1. Install LM Studio from https://lmstudio.ai/
2. Download and load a model suitable for your hardware.
3. Start LM Studio's local API server.
4. In Role Weaver select **LM Studio**.
5. Confirm the local server address and model selection.
6. Press **Test AI Connection**.

Local model quality depends strongly on the model and computer. Hosted Gemini/OpenAI models may be more capable for long context, subtle character voice and complex continuity, while LM Studio offers local processing and no per-request hosted API charge.

## API-key safety

Treat API keys like passwords:
- Never include them in character profiles, campaign files or lore.
- Never commit them to GitHub.
- Never post them in Discord, forums, download sites, screenshots or bug reports.
- Do not email your key to Role Weaver support.
- If a key is exposed, revoke/delete it with the provider and create a replacement.

After **Test AI Connection** succeeds, continue with **CHARACTER_PROFILE_GUIDE.md** and **FIRST_RUN.md**.
