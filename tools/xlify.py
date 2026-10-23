"""Make Pixel War XL's game files from Pixel War's.

Pixel War XL is Pixel War with a fixed set of changes: its own name,
storage and multiplayer rooms, up to 15 nations, five more colours, maps
twice the size and a leaderboard that lists everyone. This script copies
game.js, style.css and index.html from a Pixel War checkout and reapplies
those changes, so every Pixel War update can be brought across exactly.

Usage:
    python3 tools/xlify.py ~/Claude/pixel-war

It stops with an error if Pixel War has changed a line it expects to edit.
The XL version number (APP_VERSION) and the service worker are left alone.
"""

import re
import sys
from pathlib import Path

GAME = [
    (" * Pixel War: a territory-conquest game", " * Pixel War XL: a territory-conquest game"),
    ("  const TARGET_CELLS = 16000;     // approximate number of cells on a random map",
     "  const TARGET_CELLS = 64000;     // approximate number of cells on a random map"),
    ("  const SLOT = 10;                // stride for the attacker/target lookup table",
     "  const SLOT = 16;                // stride for the attacker/target lookup table (more than MAX_FACTIONS)"),
    ("  const BASE_WIDTH = { world: 420, europe: 260 };",
     "  // XL maps are drawn twice as wide as Pixel War's but keep its unit sizes\n"
     "  // (ranges, blasts, starting land), so there is 4x the room.\n"
     "  const BASE_WIDTH = { world: 840, europe: 520 };"),
    ("    { name: 'White', rgb: [236, 238, 242] },", "    { name: 'Magenta', rgb: [217, 70, 239] },"),
    ("    { name: 'Bronze', rgb: [150, 98, 52] },\n  ];",
     "    { name: 'Bronze', rgb: [150, 98, 52] },\n"
     "    { name: 'Sky', rgb: [56, 189, 248] },\n"
     "    { name: 'Gold', rgb: [250, 204, 21] },\n"
     "    { name: 'Indigo', rgb: [67, 56, 202] },\n"
     "    { name: 'Maroon', rgb: [127, 29, 29] },\n"
     "    { name: 'Olive', rgb: [101, 121, 40] },\n  ];"),
    ("  const MAX_FACTIONS = 6;", "  const MAX_FACTIONS = 15;"),
    ("localStorage.getItem('pixelwar.' + key)", "localStorage.getItem('pixelwarxl.' + key)"),
    ("localStorage.setItem('pixelwar.' + key", "localStorage.setItem('pixelwarxl.' + key"),
    ("Object.assign({ opponents: 3, allies: 0,", "Object.assign({ opponents: 8, allies: 0,"),
    ("    G.minSpawnDist = Math.max(gw, gh) * (G.real ? 0.12 : count > 4 ? 0.22 : 0.28);",
     "    G.minSpawnDist = Math.max(gw, gh) * (G.real ? (count > 8 ? 0.09 : 0.12) : count > 10 ? 0.15 : count > 4 ? 0.22 : 0.28);"),
    ("        .sort((a, b) => share(b) - share(a) || a.id - b.id)\n        .slice(0, 6)\n        .map((f) => {",
     "        .sort((a, b) => share(b) - share(a) || a.id - b.id);\n"
     "      // Every nation still standing; rows tighten up in big games.\n"
     "      $('board').classList.toggle('many', rows.length > 8);\n"
     "      $('board').innerHTML = rows.map((f) => {"),
    ("        });\n      $('board').innerHTML = rows.join('');", "        }).join('');"),
    ("'<b>Welcome to Pixel War!</b>", "'<b>Welcome to Pixel War XL!</b>"),
    ("  const PEER_PREFIX = 'pixelwar-v1-';", "  const PEER_PREFIX = 'pixelwarxl-v1-';"),
    ("'Friends open Pixel War on any", "'Friends open Pixel War XL on any"),
    ("+ 'Update Pixel War (reload", "+ 'Update Pixel War XL (reload"),
    ("different map. Update Pixel War'", "different map. Update Pixel War XL'"),
]

STYLE = [
    ("  font-size: 11px;\n  pointer-events: none;\n  z-index: 4;\n}",
     "  font-size: 11px;\n  pointer-events: none;\n  z-index: 4;\n"
     "  /* All 15 nations fit; on a short screen the list scrolls above the controls. */\n"
     "  max-height: calc(100vh - env(safe-area-inset-top) - 66px - 120px);\n"
     "  overflow-y: auto;\n  overscroll-behavior: contain;\n}\n"
     "#board.many { gap: 0; font-size: 10.5px; }\n#board.many li { padding: 1.5px 0; }"),
    (".logo span { color: var(--danger); text-shadow: 3px 3px 0 #7f1d1d; margin-left: 0.2em; }\n",
     ".logo span { color: var(--danger); text-shadow: 3px 3px 0 #7f1d1d; margin-left: 0.2em; }\n"
     ".logo span.xl { color: #fbbf24; text-shadow: 3px 3px 0 #78350f; }\n"),
]

HTML = [
    ('content="Pixel War: a territory-conquest', 'content="Pixel War XL: a territory-conquest'),
    ('<title>Pixel War</title>', '<title>Pixel War XL</title>'),
    ('<h1 class="logo">PIXEL<span>WAR</span></h1>', '<h1 class="logo">PIXEL<span>WAR</span> <span class="xl">XL</span></h1>'),
    ('          <button data-v="1">1</button>\n          <button data-v="2">2</button>\n'
     '          <button data-v="3">3</button>\n          <button data-v="4">4</button>\n'
     '          <button data-v="5">5</button>',
     '          <button data-v="2">2</button>\n          <button data-v="5">5</button>\n'
     '          <button data-v="8">8</button>\n          <button data-v="11">11</button>\n'
     '          <button data-v="14">14</button>'),
    ('          <button data-v="2">2</button>\n          <button data-v="3">3</button>\n        </div>',
     '          <button data-v="2">2</button>\n          <button data-v="4">4</button>\n'
     '          <button data-v="6">6</button>\n        </div>'),
]


def apply(text: str, edits: list[tuple[str, str]], name: str) -> str:
    """Apply each (old, new) edit exactly once, or stop with an error."""
    for old, new in edits:
        count = text.count(old)
        if count != 1:
            sys.exit(f'{name}: expected 1 match, found {count}:\n{old}')
        text = text.replace(old, new)
    return text


def main() -> None:
    """Copy Pixel War's game files into this checkout with the XL changes."""
    src = Path(sys.argv[1]).expanduser()
    dst = Path(__file__).resolve().parent.parent
    version = re.search(r"const APP_VERSION = '([^']+)';", (dst / 'game.js').read_text()).group(1)
    game = apply((src / 'game.js').read_text(), GAME, 'game.js')
    game = re.sub(r"const APP_VERSION = '[^']+';", f"const APP_VERSION = '{version}';", game, count=1)
    (dst / 'game.js').write_text(game)
    (dst / 'style.css').write_text(apply((src / 'style.css').read_text(), STYLE, 'style.css'))
    (dst / 'index.html').write_text(apply((src / 'index.html').read_text(), HTML, 'index.html'))
    print(f'XL files rebuilt from {src} (APP_VERSION {version} kept)')


if __name__ == '__main__':
    main()
