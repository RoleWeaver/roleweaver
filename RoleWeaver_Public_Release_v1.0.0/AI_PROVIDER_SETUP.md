# AI Provider Setup

After installing Role Weaver, **setting up an AI provider is the first configuration step**. Role Weaver needs a Large Language Model (LLM) to generate replies. You only need one provider.

## Quick recommendation

| Provider | Cost | Setup | Typical RP quality | Best reason to choose it |
| --- | --- | --- | --- | --- |
| Google Gemini | Free tier available | Easy | Very good | Start without buying API credit |
| OpenAI / GPT-5.6 Luna | Low-cost API | Easy | Very good | Fast, inexpensive hosted model |
| LM Studio | No per-message API fee | Moderate | Depends heavily on model/hardware | Run the LLM locally |

For most new users: start with **Gemini** if you want a free option; use **OpenAI GPT-5.6 Luna** if you want an inexpensive hosted option; try **LM Studio** if you specifically want local inference.

## Google Gemini — free-tier starting option

Google's Gemini API has a **free tier** for supported models, with lower quotas/rate limits than paid tiers.

1. Open Google AI Studio: https://aistudio.google.com/
2. Sign in with your Google account.
3. Open the API Keys page.
4. New users may already have a project/key. Otherwise choose **Create API key**.
5. Copy the key.
6. In Role Weaver choose **Google Gemini** and paste the key.
7. Press **Test AI Connection**.

Official getting-started guide: https://ai.google.dev/gemini-api/docs/get-started

The free tier is an excellent way to start Role Weaver without paying. Its limits are more restrictive, however. During busy periods you may encounter rate/capacity limits, retries, or slower availability. Role Weaver includes Gemini fallback behavior to help when a configured model is temporarily unavailable. Google also offers paid Gemini tiers with higher limits.

## OpenAI — inexpensive hosted option

OpenAI API billing is separate from a ChatGPT subscription. Having ChatGPT Plus or Pro does not itself provide prepaid API usage.

1. Open the OpenAI API Platform: https://platform.openai.com/
2. Sign in or create an account.
3. Create a secret API key and copy it when shown.
4. Open API Billing and add a payment method.
5. Purchase API credit.
6. In Role Weaver choose **OpenAI**, paste the key, select a model, and press **Test AI Connection**.

API overview: https://openai.com/api/

API key help: https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key

### Suggested starting credit and model

A practical starting amount is **about US$10**. OpenAI currently allows prepaid API purchases beginning at US$5, with US$10 as the default initial purchase amount. Review the auto-recharge option if you do not want automatic top-ups.

Prepaid billing help: https://help.openai.com/en/articles/8264644-what-is-prepaid-billi

**GPT-5.6 Luna** is a good starting model for Role Weaver because it is a lower-cost GPT-5.6 model and Role Weaver usually generates relatively short conversational output. At the time this guide was prepared, OpenAI listed GPT-5.6 Luna at $0.20 per million input tokens and $1.20 per million output tokens. Prices/model availability can change, so check the current API page.

For ordinary Role Weaver use, $10 should provide a substantial amount of dialogue generation, but actual usage depends on context size, candidate generation, summaries, response length, and frequency.

## LM Studio — run the LLM locally

LM Studio lets Role Weaver use an LLM running **on your own computer** rather than an online provider.

Download: https://lmstudio.ai/download

Documentation: https://lmstudio.ai/docs/app

1. Install LM Studio for Windows.
2. Find and download an LLM in LM Studio.
3. Load the model.
4. Start LM Studio's local API server.
5. In Role Weaver choose **LM Studio**.
6. Leave Model on `auto` initially or select the model reported by LM Studio.
7. Confirm the local server address and press **Test AI Connection**.

LM Studio can serve local models through OpenAI-compatible endpoints that Role Weaver can use.

### Local-model quality trade-off

A local model does **not** automatically match the quality of large hosted Gemini/OpenAI models. Small and medium local models can work well for straightforward RP, but may be less consistent at distinctive voice, complicated Guidance, long histories, subtle relationships, knowledge boundaries, and varied candidate replies.

Very large local models can improve results, but require substantially more RAM/VRAM, storage, and computing power. On many ordinary PCs, a hosted Gemini or OpenAI model will therefore produce better RP than the local model that comfortably fits the machine.

LM Studio is especially attractive if you value local processing, have powerful hardware, want to experiment with open models, or want to avoid per-request API charges.

## API key safety

**Never share your Gemini or OpenAI API key.** Do not put it in a character profile, Lore file, GitHub repository, Discord message, screenshot, forum post, or bug report. If a key is exposed, revoke it and create a new one.

## Next step

Once **Test AI Connection** succeeds, do **not** press Start yet. Your next step is to create your character description.

Continue with **CHARACTER_PROFILE_GUIDE.md**.
