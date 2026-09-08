# Nexus Mods Submission Notes

## Suggested title
Role Weaver - AI Roleplay and Persistent Character Continuity

## Short description
AI-assisted roleplay companion for Neverwinter Nights: Enhanced Edition with editable dialogue, persistent character/NPC memory, continuity, relationships, NPC briefings and DM campaign management.

## Tester notice (place first)

## Suggested description
Role Weaver is a Windows companion utility for Neverwinter Nights: Enhanced Edition. It reads the NWN client log, builds roleplay context, and uses the AI provider selected by the user to produce editable character-consistent dialogue and emotes.

The player/DM remains in control: F9 pastes a generated reply into NWN but deliberately leaves it unsent for review and editing. Role Weaver can maintain persistent character memory, relationships, knowledge, emotional continuity, story threads, correction learning and player-approved character development.

For DMs, persistent NPC memory is complemented by NPC Briefings and a Campaign Manager with campaign description, current situation, ordered story beats, objectives/open questions, important locations, player/party DM notes, session logs and Campaign Briefings.

### Requirements
- Windows
- Neverwinter Nights: Enhanced Edition
- One AI provider: Google Gemini API key, OpenAI API key, or a locally running LM Studio model

### Installation
1. Download the Role Weaver Nexus ZIP.
2. Extract the entire ZIP to a folder.
3. Run RoleWeaver.exe.
4. Select an AI provider and configure it.
5. Press Test AI Connection.
6. Create/select a character profile, select the NWN server profile, confirm the client-log path and press Start.

### Gemini setup
Create an API key in Google AI Studio (https://aistudio.google.com/), then select Google Gemini in Role Weaver, paste the key, and press Test AI Connection.

### OpenAI setup
Create a secret API key in the OpenAI API Platform (https://platform.openai.com/). Configure API billing/credits if required. ChatGPT subscriptions are separate from API billing. Select OpenAI in Role Weaver, paste the key, choose an available API model, and press Test AI Connection.

Never share an API key. Role Weaver does not ship with provider keys.

### Network disclosure
Role Weaver communicates over the internet when an online AI provider such as Gemini or OpenAI is selected because sending roleplay context and receiving generated text is essential to that mode of operation. LM Studio can be used with a locally hosted model instead.

Source code is publicly available at https://github.com/RoleWeaver/roleweaver and the project is MIT licensed.

## Nexus categorisation / disclosure
Role Weaver's core function uses generative AI for dialogue generation. Apply Nexus Mods' current **AI-Generated Content** tag and any applicable utility/gameplay categories. Do not represent the application as AI-free.

## Recommended file
Upload the GitHub Actions artifact named:
`RoleWeaver-Nexus-v1.2.1.zip`

The Nexus archive should contain the unpacked portable application plus `NEXUSMODS_README.txt`. Do not put another ZIP/archive inside it.

## Important Nexus network-tool requirement
Nexus Mods' current File Submission Guidelines say utilities that communicate over the internet may be moderated unless network access is crucial to their function, and instruct authors to contact Nexus Mods staff/support with the reasoning and source code. Role Weaver's Gemini/OpenAI modes require network access to call the selected AI API, so contact Nexus Mods support before/when submitting.

Suggested support message:

> Hello, I am preparing Role Weaver, an open-source MIT-licensed companion utility for Neverwinter Nights: Enhanced Edition. Its source is available at https://github.com/RoleWeaver/roleweaver. The program reads the user's local NWN client log and, when the user selects Google Gemini or OpenAI, sends relevant roleplay context to that provider's API and receives generated dialogue. This network communication is essential to those hosted-AI modes; users can alternatively use LM Studio locally. The program does not use an auto-updater. I would like to distribute the portable Windows build on Nexus Mods and wanted to provide the requested explanation/source in advance. Please let me know if you need any additional information.
