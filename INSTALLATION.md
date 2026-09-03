# Role Weaver Installation Guide

Role Weaver currently targets **Windows** and **Neverwinter Nights: Enhanced Edition**. It can be used by a normal player roleplaying their own character or by a Dungeon Master portraying NPCs.

This guide covers installing from source. A future GitHub Releases build can package the same application as a standalone Windows executable.

## Required first-time setup after installation

Before pressing **Start**, every user must complete these steps in this order:

1. **Get a Gemini/OpenAI API key or set up LM Studio.** Follow `AI_PROVIDER_SETUP.md` and make sure **Test AI Connection** succeeds.
2. **Create a character description.** Follow `CHARACTER_PROFILE_GUIDE.md` and start from the included player-character or DM-NPC example.
3. Configure the NWN server/log and select that character.
4. Press Start.


## 1. Download Role Weaver

From the Role Weaver GitHub repository, either:

- use **Code → Download ZIP**, then extract it to a normal writable folder such as `C:\RoleWeaver`, or
- clone the repository with Git.

Do not run the program directly from inside a ZIP archive.

## 2. Install Python

Install a current 64-bit Python 3 release for Windows. During installation, enable the option that makes Python available from the command line.

Open **Command Prompt** in the Role Weaver folder and confirm:

```bat
python --version
```

If your Windows installation uses the Python launcher instead, this is also fine:

```bat
py --version
```

## 3. Create a virtual environment

From the Role Weaver folder:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Using a virtual environment keeps Role Weaver's Python packages separate from the rest of your system.

## 4. Start Neverwinter Nights once

Role Weaver reads the NWN client log. The usual Windows location is:

```text
%USERPROFILE%\Documents\Neverwinter Nights\logs\nwclientLog1.txt
```

If your installation stores the file elsewhere, use **Server / Log → Browse** inside Role Weaver and select the correct log file.

## 5. Start Role Weaver

With the virtual environment active:

```bat
python nwn_ai_gui.py
```

You can also use the included `RoleWeaver.bat` launcher after the environment has been created.

A short Role Weaver splash screen should appear, followed by the main client.

## 6. Choose a server and character

Open the **Server / Log** settings and select the appropriate server profile.

For a normal NWN server that does not have custom parsing rules, choose:

```text
Custom / Other NWN Server
```

Character profiles live in:

```text
Characters\<server>\
```

The release candidate includes two profile examples: `character_Kaelen_Marr_Player_Character.txt` for a player's own character and `character_Captain_Veyra_DM_NPC.txt` for a recurring DM-controlled NPC. Copy the example closest to your use case and rename the copy.

Example:

```text
Characters\CUSTOM\character_Captain_Veyra.txt
```

Edit the profile in a text editor. Keep a clear `Character Name:` or `Name:` line so Role Weaver can identify the character. Players should describe the voice, beliefs, background, goals, and boundaries of their own character. DMs can use the same structure for recurring NPCs.

## 7. Configure an AI provider

Role Weaver supports:

- **OpenAI**
- **Google Gemini**
- **LM Studio** for local models

Select the provider in the **AI Provider** settings and use **Test AI Connection** before starting the log listener.

For OpenAI or Gemini, enter your API key in the application or use the provider's supported environment variable. Role Weaver is designed not to save the API key in its normal settings files.

For LM Studio, start LM Studio's local server first and enter the server URL shown by LM Studio.

AI model names and provider availability change over time. If a model has been retired, choose a currently available model for your account/provider.

## 8. Add campaign lore

Put plain-text campaign references in:

```text
Lore\
```

Good examples include:

```text
Lore\Kingdom_of_Asterfall.txt
Lore\Cult_of_the_Black_Sun.txt
Lore\Captain_Veyra_Background.txt
```

Keep files focused. Role Weaver retrieves a few references that appear relevant to the current conversation.

Prefix a file with `always_` only when it should be included for every generation:

```text
Lore\always_campaign_ground_rules.txt
```

## 9. Start the listener

In Role Weaver:

1. Confirm the **Server**, **Character**, **AI Provider**, and **Log Path**.
2. Click **Start**.
3. Enter or observe chat in NWN.
4. Use the Activity panel to confirm Role Weaver is seeing the conversation.

Important hotkeys:

```text
F6   Pause / resume listening
F8   Generate multiple candidate drafts
F9   Generate and place an editable draft into NWN
F10  Toggle auto reply
F11  Clear current conversation context
F12  Stop Role Weaver
```

F9 intentionally does **not** press the final Enter key. Review and edit the NWN chat text before sending it.

## 10. Create a desktop shortcut

After installing the Python dependencies, right-click `Create_RoleWeaver_Desktop_Shortcut.ps1` and choose **Run with PowerShell**, or run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Create_RoleWeaver_Desktop_Shortcut.ps1
```

The shortcut uses the included Role Weaver icon.

If your organization blocks PowerShell scripts, create a shortcut manually to `RoleWeaver.bat` and choose `assets\RoleWeaver.ico` as the shortcut icon.

## Where Role Weaver stores data

Runtime continuity data is placed under:

```text
RoleWeaver_Data\<server>\<character>\
```

This can include:

- persistent character memory,
- the running summary,
- archived session summaries,
- conversation history.

Character-specific AI preferences are stored beside character profiles in `.settings.json` files.

Treat these files as campaign data. Review them before sharing them publicly.

## Updating

For source installs:

1. Stop Role Weaver.
2. Back up `Characters`, `Lore`, and `RoleWeaver_Data`.
3. Pull/download the new version.
4. Re-run:

```bat
.venv\Scripts\activate
pip install -r requirements.txt
```

5. Restore or merge your campaign data as needed.

## Troubleshooting

### Role Weaver sees no chat

Check that NWN is running and that the selected log file is receiving new lines. Use **Browse** to point Role Weaver at the correct `nwclientLog1.txt`.

### F9 generates text but nothing appears in NWN

Use the built-in keyboard test first. Make sure the NWN window is focused during the short F9 countdown.

### The AI provider changes unexpectedly

Choose the provider/model you want before pressing Start. Character-specific settings are stored per profile, so changing characters can intentionally load different AI settings.

### An API model no longer exists

Provider model catalogs change. Select another model available to your account and test the connection.

### I want to use Role Weaver with several DMs

Read [DM_GUIDE.md](DM_GUIDE.md). Share character profiles and lore through your private campaign repository. Runtime memory is local unless your group deliberately shares it.


## Player or DM?

After installation, the program itself works the same way for both.

**If you are a player:** select the profile for the character you are currently playing. Start with `PLAYER_GUIDE.md`.

**If you are a DM:** select the NPC you are currently portraying. Start with `DM_GUIDE.md`.

You can keep many player characters and NPCs in the same installation. Server-specific folders keep campaign profiles separated.


## Built-in server profiles

The server menu includes The Dragon's Neck (TDN), Arelith, Ravenloft: Prisoners of the Mist, Cormyr and the Dalelands, Star Wars: Legends of the Old Republic, Haze: Saltborne, and Custom / Other NWN Server. Each profile has its own character-profile folder and saved log path. See `SUPPORTED_SERVERS.md` for parser details.


## Character and lore editing

After selecting a server, use **New Character...** to create your first character profile. Use **Edit Selected...** to revise it later.

Use **Lore Editor...** to create or paste campaign/server information. Lore is saved under `Lore/<server>/` and only applies when that same server is selected. Server response rules are stored separately under `RoleplayRules/<server>/roleplay_rules.txt`.


## NWN draft does not paste

If F9 generates a response but the NWN chat bar does not open:

1. Wait for the message that the reply has finished generating.
2. During the 2-second countdown, click the Neverwinter Nights game window.
3. Role Weaver will use scan-code keyboard input to press Enter and Ctrl+V.
4. F9 intentionally does not press the final Enter; review/edit the text and send it yourself.

For manually selected F8 candidates, use **Paste Edited Draft into NWN** after choosing or editing the draft.

Role Weaver leaves an F9/manual draft on the Windows clipboard. If a particular
NWN/window configuration rejects the automatic Ctrl+V, you can press Ctrl+V
manually without regenerating the response.

The **Keyboard Test** button can also be used to check NWN keyboard injection.
