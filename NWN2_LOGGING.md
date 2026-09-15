# NWN2 chat logging

Role Weaver needs the **client log currently receiving your character's chat**.
Do not select a server log, crash report, old session copy or combat-only log.
Editions and launchers can use different folders and INI copies.

## Enable file logging

1. Exit NWN2 and its launcher so settings are not overwritten while editing.
2. Find the active **nwn2player.ini**, normally in your user Documents folder
   under **Neverwinter Nights 2**. Back it up before editing.
3. Under the existing [Game Options] section, add or update these entries:

       [Game Options]
       ClientChatLogging=1
       ClientEntireChatWindowLogging=1

   Do not add a second section or duplicate existing keys. Save as
   nwn2player.ini, not nwn2player.ini.txt. The second option includes the
   complete chat window, including combat/system text which Role Weaver filters.
4. Start your normal game/launcher, enter a session and type a distinctive test
   sentence. Locate the file containing it and confirm new messages appear
   **while the game is running**.

The NWN2 server Amdir documents these keys in its
[client setup guide](https://wiki.amdir.de/index.php?title=NWN2_Client_Tipps%26Tricks).
It also describes an installation-directory INI copy for older setups. If the
Documents copy has no effect, check which copy your launcher uses; back up and
edit that copy instead. Do not change every INI on your computer.

### Original NWN2 and modded original installations

Start with Documents/Neverwinter Nights 2/nwn2player.ini. Older/custom installs
may use their installation-directory copy as noted above. Look for nwclientLog1.txt
under %LOCALAPPDATA%/Temp/NWN2/LOGS or %TEMP%/NWN2/LOGS.

### NWN2 Enhanced Edition, including 64-bit

Locate the active nwn2player.ini for the EE launcher. If several copies exist,
change an ordinary in-game setting, exit normally, and inspect which file's
modified time changed. Apply the logging keys to that file's Game Options section
and perform the live-message check. INI behavior may vary with EE patches; if
no live chat is written, consult your build's logging options rather than assuming
that creating an empty file enables logging.

The maintainer confirmed these EE paths and filenames:

- %LOCALAPPDATA%/Temp/NWN2 EE/nwclientLog1.txt
- %LOCALAPPDATA%/Temp/NWN2 EE/nwn2client64Log1.txt

Role Weaver checks corresponding %TEMP% paths, optional LOGS subfolders, and
numbered files too. The 64-bit filename needs no separate game selection.

### NWN2 with Client Extender

Launch through the installed extension as its instructions require.
Its chat logging can be separate from base-game INI logging. Look under
Documents/Neverwinter Nights 2/Logs, including character/chat subfolders and dated
files. Prefer the **chat** file. Consult your installed extender's README for
logging controls; the INI keys above configure the base client, not every
extension's logger. See the
[author's project](https://www.neverwintervault.org/project/nwn2/other/nwn2-client-extension).
Do not assume an original-game extension works with every EE build.

### Linux Wine / Proton

Edit the INI in the Windows user Documents folder **inside the prefix used by
your game**. Temp logs are inside that prefix too, for example:
<prefix>/drive_c/users/steamuser/AppData/Local/Temp/NWN2 EE/

For classic NWN2 the suffix is usually NWN2/LOGS. The username may differ.
Use your launcher to locate custom prefixes or external Steam libraries.
These NWN2 INI instructions do not apply to native NWN:EE.

## Select and verify in Role Weaver

1. Choose **Game Version**, then open **Server / Log**.
2. **Browse** to the exact file verified by your live test.
3. Select world and character, then **Start**.
4. Make another new chat message. Role Weaver tails new lines rather than
   replaying old contents at Start.
5. If messages stop, check whether the game switched to another numbered,
   daily or character-specific log. Stop, select that active file and Start again.

Paste %LOCALAPPDATA%/Temp into File Explorer's address bar to reach the hidden
folder. Sort logs by Date modified, then inspect their contents. A recent
timestamp alone does not prove that a file contains client chat.
