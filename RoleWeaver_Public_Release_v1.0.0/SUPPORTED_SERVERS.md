# Supported Neverwinter Nights Servers

Role Weaver includes explicit server selections and tested chat parsers for:

- **Custom / Other NWN Server**
- **The Dragon's Neck (TDN)**
- **Arelith**
- **Ravenloft: Prisoners of the Mist**
- **Cormyr and the Dalelands**
- **Star Wars: Legends of the Old Republic**
- **Haze: Saltborne**

## Parsing approach

NWN persistent-world client logs often contain two copies of the same chat message: a `[CHAT WINDOW TEXT]` display copy followed by a structured record containing the speaker, channel, and message. Role Weaver ignores the display copy and parses the structured record. This prevents duplicate conversation entries and preserves speaker/account identifiers where the server supplies them.

Supported structured channels are Talk, Whisper, Party, Tell, Shout, and DM. Bracket-only dialog/menu selections such as `[Continue]`, `[Confirm]`, or `[Leave.]` are normally excluded from RP context.

## Ravenloft: Prisoners of the Mist

Verified against the supplied Ravenloft client log. Ravenloft's `<< You have entered the area: ... >>` records are also recognized as area transitions.

## Cormyr and the Dalelands

Verified against the supplied Cormyr and the Dalelands client log, including structured Talk records and server color/control formatting.

## Star Wars: Legends of the Old Republic

Verified against the supplied Legends of the Old Republic client log. It supports NPC/player Talk records, player/account prefixes, and server color/control formatting.

## Haze: Saltborne

Verified against the supplied Haze client log. Both Talk and Tell records were observed and are supported. Tell messages continue to use Role Weaver's separate private-conversation context handling. Haze can use descriptive character identities; Role Weaver uses the speaker name NWN writes to the structured chat record.

## Other servers

Choose **Custom / Other NWN Server** if a server is not listed. Many NWN:EE persistent worlds use the same structured log format and may work immediately.
