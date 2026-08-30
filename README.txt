NWN:EE AI ROLEPLAY CLIENT
==========================

WHAT IT DOES
------------
1. You double-click START_NWN_AI.bat.
2. The program waits for:
   C:\Users\User\Documents\Neverwinter Nights\logs\nwclientLog1.txt
3. Start Neverwinter Nights: Enhanced Edition normally.
4. The program tails the log while NWN is writing to it.
5. It parses structured [Talk], [Whisper], [Party], [Tell], [Shout], and [DM] lines.
6. It ignores the duplicate "[CHAT WINDOW TEXT]" version of chat.
7. It keeps recent conversation context for ChatGPT.
8. F9 generates an in-character reply and pastes it into the normal NWN chat box.

FIRST RUN
---------
You need Python 3 installed.

Double-click:
    START_NWN_AI.bat

The batch file creates a local .venv folder and installs the required Python
packages. It does not install them system-wide.

The program asks for your OpenAI API key if OPENAI_API_KEY is not already
defined. The key typed at the prompt is used for that run and is not stored
by this program.

HOTKEYS
-------
F6   Pause/resume listening
F7   Keyboard test: opens chat and types test text, but DOES NOT send it
F8   Generate a draft but DO NOT send it
F9   Generate and send one response to NWN
F10  Toggle automatic replies
F11  Clear conversation context
F12  Quit

RECOMMENDED USE
---------------
Leave automatic replies OFF initially.

Use F8 to see what the AI would say.
Use F9 when you want it to actually speak.

Once you are happy with the parser and behavior you can try F10, but ambient
NPC dialogue is common on roleplay servers, so automatic mode can sometimes
respond when you would prefer silence. The prompt tells the model to use
<NO_REPLY> when no response is appropriate.

CONFIGURATION
-------------
Edit settings.json with Notepad.

Important fields:

"log_path"
    Already set to:
    C:\Users\User\Documents\Neverwinter Nights\logs\nwclientLog1.txt

"character_name"
    Used to recognize your own character's messages.

"model"
    OpenAI model to use.

"window_title_contains"
    Text used to locate the NWN window before sending chat.

"focus_game_before_typing"
    If true, the program tries to focus NWN before pressing Enter / Ctrl+V /
    Enter. If Windows refuses the focus request, click NWN manually and press
    F9 again.

CHARACTER PERSONALITY
---------------------
Edit character_prompt.txt to describe the character in as much detail as you
want. This text is included with each AI request.

LOG BEHAVIOR
------------
The program initially opens an existing log at EOF so it will not process an
old session.

If NWN truncates or replaces the log when the game starts, the program detects
that and begins reading the new log from the beginning.

The supplied example log contains duplicate chat representations. The bot
intentionally ignores lines beginning with:

    [CHAT WINDOW TEXT]

and uses the structured copy such as:

    [fMlNM2u] Lora Thendry: [Talk] ...

It also filters bracketed conversation menu choices such as:

    [Leave Conversation]

because those are logged as Talk but are not roleplayed speech.

SECURITY / SERVER BEHAVIOR
--------------------------
This program does not modify NWN memory, forge network packets, or grant DM
privileges. It reads a local text log and sends ordinary keyboard input to the
normal NWN client.

Check the rules of the multiplayer server you use. Some servers prohibit
automated or AI-controlled roleplay even when it uses normal client input.

TROUBLESHOOTING
---------------
If START_NWN_AI.bat says Python is missing:
    Install Python 3 and enable "Add Python to PATH" during installation.

If no chat appears in the console:
    Confirm NWN client chat logging is enabled and that settings.json points
    to the file NWN is currently updating.

If F9 generates text but does not send:
    Click the NWN window and press F9 again.
    You can also set "focus_game_before_typing" to false and manually keep NWN
    focused.

If the wrong character is treated as YOU:
    Change "character_name" in settings.json.

FILES
-----
nwn_ai_bot.py         Main program
START_NWN_AI.bat      Double-click launcher / first-run installer
settings.json         Configuration
character_prompt.txt  Character personality / roleplay instructions
requirements.txt      Python dependencies
README.txt            This file


SENDINPUT UPDATE
----------------
This version replaces the previous PyAutoGUI Enter/Ctrl+V/Enter sequence with
the Windows SendInput API for NWN chat entry.

Press F7 after NWN is running. The bot will:
    1. Focus the Neverwinter Nights window.
    2. Send Enter to open the NWN chat entry bar.
    3. Type a test sentence using Windows SendInput.
    4. Deliberately NOT press the final Enter.

If the test sentence appears in NWN's chat entry field, keyboard injection is
working. Press Escape to discard the test.

F9 and F10 use the same sequence but press Enter at the end to send the reply.

If F7 still does nothing, check whether NWN is running as Administrator. If it
is, try running START_NWN_AI.bat as Administrator as well, since Windows can
prevent a lower-privileged process from injecting input into an elevated one.


SENDINPUT FIX - VERSION 3
-------------------------
The previous build had an incorrectly sized Windows INPUT structure. On
64-bit Windows that can cause:

    [SEND ERROR] [WinError 0] The parameter is incorrect.

This build defines the complete Win32 INPUT union (mouse, keyboard, hardware),
which gives SendInput the correct structure size.

It now uses:
    SendInput Enter
    Clipboard Ctrl+V for the text
    SendInput Enter

Clipboard paste is the default because it tends to be more reliable for long
NWN roleplay messages than issuing one Unicode keyboard event per character.

You can change:
    "input_method": "clipboard"

to:
    "input_method": "unicode"

in settings.json if you want to test direct Unicode SendInput typing.

F7 remains the safest diagnostic. It opens NWN chat, enters test text, and
leaves it unsent.

During a send you should now see a line such as:
    [SEND] SendInput structure size: 40 bytes (64-bit Python)

On a normal 64-bit Python/Windows installation, 40 bytes is expected.


DIAGNOSTIC BUILD
----------------
This build adds console commands so testing no longer depends on F7/F9 being
visible to the Python hotkey listener.

After starting the program, type one of these commands into its console:

    test
        Test the configured keyboard method (default: pynput).

    tests
        Step through four keyboard methods:
        1. pynput
        2. pyautogui
        3. sendinput
        4. postmessage

    speak
        Generate and send one AI reply.

    draft
        Generate a draft only.

    auto
        Toggle automatic replies.

    quit
        Exit.

The test command focuses NWN, presses Enter, pastes a test sentence, and
deliberately does NOT press the final Enter. If the sentence appears in NWN's
chat entry field, that keyboard method works.

The console now also prints the actual foreground window title after trying
to focus NWN. This tells us whether the problem is keyboard injection or
Windows refusing to give the NWN window focus.

If F7 is detected, the console prints:
    [HOTKEY] F7 detected

If that line never appears, the function key itself is being swallowed or
hidden from the global listener. Use the console command "test" instead.

You can set the preferred method in settings.json:
    "keyboard_method": "pynput"

Other values:
    "pyautogui"
    "sendinput"
    "postmessage"


DIAGNOSTIC FIX 2
----------------
Fixed a ctypes pointer mismatch in the SendInput wrapper. The previous
build passed ctypes.byref(INPUT); this build passes ctypes.pointer(INPUT),
which matches the declared LP_INPUT argument type exactly.


DIRECT SENDINPUT FIX
--------------------
The prior diagnostic build still passed through pynput for the default "test"
command. On some Python/Windows combinations pynput itself can raise:

    TypeError: expected LP_INPUT instance instead of pointer to INPUT

This build removes pynput and PyAutoGUI from the actual NWN chat keystroke path.

The default test now uses this program's own Win32 SendInput wrapper directly.
The second SendInput argument is declared as c_void_p, which avoids ctypes
pointer-type identity mismatches while still passing the actual INPUT buffer.

The native send sequence is now:

    Win32 SendInput: Enter
    Windows clipboard: copy text
    Win32 SendInput: Ctrl+V
    (test stops here)
    Win32 SendInput: Enter   [F9/F10 only]

If "test" still does not open chat, type:

    tests

The build will step through:
    sendinput
    keybd_event
    postmessage

The keybd_event option uses the older Win32 keyboard injection API and can
sometimes work with games that reject SendInput.


SCANCODE / MANUAL-FOCUS BUILD
-----------------------------
This build adds a lower-level scan-code keyboard method. Many games read
keyboard input through DirectInput/SDL-style paths and respond better to
scan-code SendInput than to virtual-key events.

The new default is:

    "keyboard_method": "scancode"

Most useful diagnostic command:

    manualtest

After typing "manualtest" in the bot console, you get a 5-second countdown.
During the countdown, CLICK THE NWN GAME WINDOW and leave it focused.

At the end of the countdown the bot does NOT try to switch windows. It sends:

    scan-code Enter
    scan-code Ctrl+V

and intentionally stops before the final Enter.

This separates "Windows refused to focus NWN" from "NWN rejected synthetic
keyboard input."

If manualtest works, F9/F10 can use the same scan-code method normally.

If manualtest still does nothing even though NWN is visibly focused at the
end of the countdown, the NWN client is likely filtering or ignoring
synthetic keyboard input at the game-input layer. In that case the next
practical route is an external macro layer such as AutoHotkey or a
client/plugin integration rather than more SendInput variants.


F9 EDITABLE-DRAFT UPDATE
------------------------
F9/manual replies now:
1. Generate the AI reply.
2. Give you a 2-second warning to focus NWN.
3. Open the NWN chat bar.
4. Paste the reply.
5. Stop without pressing the final Enter.

You can edit or cancel the draft, then press Enter yourself when ready.

F10/automatic replies still send normally.

The default setting is now:
    "focus_game_before_typing": false

The keyboard method remains:
    "keyboard_method": "scancode"

F9 drafts are not inserted into local AI conversation history as if they had
already been spoken. The actual edited message will be picked up from the NWN
chat log after you send it.
\n\nONE-SHOT GUIDANCE FOR F9/F10\n----------------------------\nBefore generating the next reply, type a guidance command in the bot console:\n\n    guide be suspicious of this person and keep the reply brief\n\nThen press F9. The guidance is included with the recent NWN conversation for\nthe next AI-generated reply only. It is cleared automatically after a\nsuccessful response is generated.\n\nOther examples:\n\n    guide politely decline without explaining why\n    guide ask about the missing shipment\n    guide mostly emote and say very little\n    guide do not reveal that Lora already knows the answer\n\nCommands:\n\n    guide <text>   Set one-shot guidance for the next generated reply.\n    guide?         Show currently queued guidance.\n    guide clear    Remove queued guidance.\n\nThe guidance is not typed into NWN chat. F9 remains an editable draft: it\npastes the generated response but does not press the final Enter. F10/auto\ncontinues to send automatically. If guidance is queued, whichever mode\ngenerates the next response will consume it.\n

GUIDANCE WINDOW UPDATE
----------------------
START_NWN_AI.bat now opens a small separate window named:

    NWN AI - Next Reply Guidance

Workflow:
1. Type an instruction in the Guidance window.
2. Click "Set Guidance" (or press Ctrl+Enter).
3. Return to NWN and press F9.
4. The instruction is included only with the next AI generation.
5. After a successful generation, the bot clears the one-shot guidance and
   the Guidance window automatically notices and clears itself.

Examples:
    Be suspicious of this person and keep the answer brief.
    Politely decline, but do not explain why.
    Ask about the shipment before agreeing to anything.
    Mostly use an emote and say very little.

The "Keep on top" checkbox is enabled by default so the small window remains
easy to reach while playing. Turn it off if it gets in the way.

The original console commands still work:
    guide <text>
    guide?
    guide clear

Both the console and the Guidance window use the same next_guidance.txt file,
so they stay synchronized.

Closing the Guidance window does NOT erase guidance you already queued.


UNICODE PUNCTUATION NORMALIZATION
---------------------------------
Before text is pasted into NWN chat, the bot now converts common smart
punctuation to plain ASCII equivalents.

Examples:
    ’  ->  '
    ‘  ->  '
    “  ->  "
    ”  ->  "
    –  ->  -
    —  ->  -
    …  ->  ...

This prevents apostrophes and similar punctuation from appearing as question
marks in the NWN chat entry field on clients that do not handle those Unicode
characters correctly.


FULL UI VERSION
---------------
The bot is now controlled from one Windows UI instead of the terminal.

Launch:
    START_NWN_AI.bat

The main window contains:
- Start / Stop
- Pause / Resume listening
- Auto Reply ON/OFF
- Draft in Activity Log (F8)
- Draft into NWN Chat (F9)
- Clear Conversation (F11)
- Keyboard Test
- One-shot Guidance text box
- OpenAI API key field (only needed if OPENAI_API_KEY is not already set)
- Current area, status, context count, and activity/conversation display

F9 still uses the known-working behavior:
1. Generate the response.
2. Wait 2 seconds.
3. You click/focus NWN.
4. The bot opens the NWN chat field.
5. It pastes the response.
6. It does NOT press the final Enter, so you can edit the text.

The global F6/F8/F9/F10/F11/F12 hotkeys remain available while the UI is
running.

Guidance is now built into the same main window. Type guidance and click
Set Guidance, or simply edit the guidance box and click an AI-generation
button; changed guidance is saved automatically before generation.

One-shot guidance is cleared after a successful AI generation.

The Activity / Conversation pane replaces the normal terminal output for
routine use.

For troubleshooting only:
    START_NWN_AI_DEBUG.bat

opens the same GUI while leaving a console visible for Python startup errors.
