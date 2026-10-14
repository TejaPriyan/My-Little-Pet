# My Little Pet 🐾 (formerly Teja Pet)

## Windows download and mobile companion

The 1.1.0 Windows installer is in `../my-little-pet-site/dist/downloads/`.
It installs a self-contained app for Windows 10/11 x64; Python is bundled.
Installed copies save separately in `%LOCALAPPDATA%/MyLittlePet/save` so
updates and uninstalling do not delete a pet. Source checkouts continue using
their existing `save/` folder. `MY_LITTLE_PET_SAVE_DIR` overrides the save path
for isolated tests. Only one running Windows instance may use a save folder.

First launch accepts both an owner name and a pet name. Existing saves remain
compatible. Open **Menu → Owner + Pet Names** to rename either without losing
progress. The pet greets its owner by name. The pixel font supports 12 ASCII
letters/numbers/spaces/hyphens per name.

The website is in `../my-little-pet-site/dist/`; `/app/` is the installable
Android/iPhone web app. Mobile and desktop saves are currently independent.

A cozy pixel-art desktop virtual pet. Your pet lives in a small room, wanders
around on its own, eats, plays, sleeps, follows your mouse, levels up and
remembers everything between sessions.

* Python 3.12 (tested) and **pygame 2.6.1+** — nothing else
* Fully offline: no API key, no database, no internet
* Art and sound are generated procedurally if no files are present, so it
  always runs; real PNG/WAV files are included and can be swapped out

## Run

Install the requirements in a Python virtual environment, then run `python main.py`.
The parent folder's Windows launcher uses an available Python installation.
It is a convenience source launcher, not the self-contained Windows installer.

**Launch Desktop Pet.cmd** opens directly in desktop mode. You can also use
`python main.py --desktop` with an existing named pet.

```bash
pip install -r requirements.txt
python main.py
```

First launch asks you to name your pet. Progress is stored in
`save/save_data.json` (written atomically every 30 s, on every important
action, and on close).

## Controls

| Input | Action |
|---|---|
| Arrow keys | Walk the pet (hold **Shift** to run, diagonals supported) |
| `H` / `F` / `P` / `S` / `E` | Home / Feed / Play / Sleep / Pet |
| `G` | **Catch the Bug** Mini-Game |
| `T` | **Pet Journal** (Stats & Achievements) |
| `C` | Toggle **Follow** mode (pet trails your mouse) |
| `B` | Shop |
| `D` | Windows desktop companion mode |
| `Q` | Quiet mode (mutes music, effects, and voices) |
| `Esc` | Settings |
| `F11` | Fullscreen |
| `N` | Cycle time of day: real clock → fast cycle → day → night |
| Click the pet | Pet it |
| Click furniture | Bowl = feed, bed = sleep, ball = play, water bowl = drink, door/window/plant/table/picture/clock/shelf/cushion = visit |
| Click the floor | Pet walks there |

Arrow keys always take over from whatever the pet is doing; after you let go it
waits a few seconds before going back to its own routine.

## Gameplay

* **Needs** (0–100): Hunger (100 = full), Happiness, Energy. They drain slowly
  (a full tummy lasts about half an hour). Energy refills while sleeping.
* **Actions**: Feed (+20 hunger, +5 happy) · Play (+20 happy, −10 energy) ·
  Pet (+4 happy) · Sleep (restores energy until ~92) · Home (walks to its bed area).
* **XP**: Feed +5, Play +10, Pet +3, Sleep +5, Explore +5. Level-ups give a
  celebration and +20 coins. XP needed = `40 + 20 × (level − 1)`.
* **Coins**: earned from actions and mini-games. The **Shop** offers:
  * **Treat**: Bigger next meal (+15 extra hunger)
  * **Squeaky Toy**: Permanent play happiness bonus (+5 happy)
  * **Fancy Bow**: Cute wearable pet accessory
  * **Cozy Blanket**: Sleep restores energy 25% faster
  * **Catnip Candy**: Instant happiness boost (+35) and zoomies!
* **Mini-Game (Catch the Bug)**: A fast-paced 30-second mini-game (`G` key).
  Click fluttering bugs and rare golden fireflies to rack up combos, coins, XP, and happiness!
* **Pet Journal (Stats & Achievements)**: Press `T` to see full stats tracking
  (play time, feeds, pettings, explore distance, mini-game records) plus 10 unlockable achievements with coin rewards!
* **Weather & Atmosphere**: Dynamic weather (clear sky, rain with window sill splashes, or gentle snowfall)
  visible through the window with atmospheric sky lighting.
* **Personality**: each pet is rolled with Curiosity, Playfulness, Sleepiness
  and Friendliness, which weight its random choices (wander / play / nap / greet).
* **Autonomy**: it wanders, sits, looks around, visits landmarks, plays with the
  ball and drinks by itself. When hungry it walks to its bowl and begs
  ("FEED ME!"); when exhausted it puts itself to bed.
* **Day/night**: window sky, sun/moon, light shaft, soft tint and twinkling
  string lights follow the time of day. At night the pet is sleepier. The room
  never goes fully dark.
* **While you're away**: needs keep ageing at 10 % speed (capped at 12 h and
  floored so you never come back to a miserable pet).

## Settings (Esc)

Sound · Music · Volume · FPS (30/60/120) · Fullscreen · Time of day · Reset Pet
(with confirmation). Stored in `save/settings.json`.

Additional settings: desktop pet size (2x/3x/4x), pet voices, quiet mode,
weather (automatic/clear/rain/snow), desktop mode, and Help. Forced weather
stays selected until changed back to automatic. Help explains the controls.

## Desktop companion

Press **D** or click **DESK**. On Windows, your pet appears over your desktop and
other windows, with a house, food bowl, water bowl, and ball. Unpainted parts
are transparent and pass mouse clicks to the applications underneath.

* Drag the pet to move it; drop it on the house to send it home.
* Click the house to sleep; click again to wake it. **Home** also sleeps in
  both modes. A rested pet wakes automatically after at least five seconds.
* Right-click the pet or a desktop prop for care, follow, quiet, room, and quit.
* **C** toggles cursor following; arrows move the pet while its window has focus.
* Click **ROOM (ESC)** or press Escape while the pet window has focus to return.
  Keyboard controls are local to the pet, so they do not intercept typing in
  another application. Click a pet prop first if another app has focus.
* Desktop mode uses the primary monitor's work area, leaving the taskbar free.
  It is Windows-only. Multiple-monitor roaming is not implemented.
* The room position and the same pet stats are preserved across modes. Mode
  preference is saved, so reopening restores the selected mode.

## Upgrade features

The shop has **ITEMS / PETS / STYLE** tabs. Adopt a kitty, puppy, bunny, or fox;
each has three free coats. Wear a bow, flower, party hat, or crown, attached to
the animated head. This switches the active pet's appearance and shares its
progress; it does not create four separate save slots. Use More in Style for
additional accessories and room themes.

**G** opens Catch the Bug, Treat Drop, or the daily-care tracker. In Treat Drop,
move the basket with the mouse or arrow keys, catch treats and gold stars, and
avoid thorns. Both games last 30 seconds, show rewards, save best scores, and
celebrate level-ups. Escape ends a round and shows its results.

Feed three times, play twice, and finish one mini-game each local calendar day
to earn **30 coins**, once per day. Garden and Starlight room themes unlock at
levels **3 and 5**; choose them in Style. They redecorate the existing room and
keep its familiar furniture layout.

Pets blink, stretch while idle, react to care, and use synthesized species
voices (including cat purrs). Joy Candy gives 15 seconds of faster movement.
Energy Snacks restore 30 energy. Achievement coin payouts are awarded once.
Existing saves migrate to the new appearance format on load.

## Project layout

```
main.py          entry point
game.py          window, scenes, input routing, game loop
display.py       window/fullscreen + crisp integer scaling (room display)
pet.py           Pet data, needs, XP/levels, animation player
ai.py            Brain: state machine (IDLE, WANDER, WALK_TO_OBJECT, EAT, PLAY,
                 SLEEP, SIT, HAPPY, SAD, FOLLOW_PLAYER, MANUAL)
world.py         room props, collision, A* pathfinding, day/night, lighting
effects.py       particles + floating text
ui.py            HUD, buttons, bubbles, name screen, settings, shop, dialogs
sprites.py       procedural pixel-art painters (the placeholder art)
assets.py        loads PNGs, falls back to sprites.py when a file is missing
audio.py         SFX/music: loads WAVs, falls back to a tiny synthesizer
pixelfont.py     built-in 5×7 bitmap font (crisp on every OS)
save_system.py   atomic saves, validation, corrupt-file recovery
settings.py      persistent user settings
config.py        every tunable constant
assets/          sprites/pet, environment, ui, audio  (all real files)
tools/generate_assets.py   regenerate every PNG/WAV
tests/           headless end-to-end tests
```

## Replacing the art

Every sprite is a normal PNG in `assets/`. Edit or replace it, keeping the frame
size, and the game picks it up on the next launch — no code changes. Delete a
file and the built-in placeholder is used instead.

| File | Layout |
|---|---|
| `sprites/pet/*.png` | horizontal strip of **24×24** frames. `idle` and `sit` hold the normal frames followed by the same number of *blink* frames |
| `environment/food.png`, `water.png` | strip of 16 px frames (food: full, empty) |
| `environment/plant.png` | strip of 24 px frames (sway) |
| `ui/panels.png`, `ui/buttons.png` | 16×16 nine-slice (4 px corners); buttons = normal / hover / pressed |
| `environment/room.png` | 480×210 wall + floor |

Run `python tools/generate_assets.py` to reset everything to the defaults.

## Tuning

All gameplay numbers (decay rates, rewards, speeds, autosave interval, offline
rules, shop prices) live in `config.py`.

## Tests

```bash
python tests/test_game.py
python tests/test_new_features.py
python tests/test_upgrade.py
```

Runs headless (movement, collision, feeding, playing, sleeping, home
navigation, petting, follow mode, autonomy, stats, saving/loading, corrupted
saves, levelling, shop, settings, reset, missing assets, random-input soak).
Screenshots land in the system temporary folder under `teja_shots` (override with `TEJA_SHOTS`). The tests use a small PIL-based pygame
stand-in (`tests/fake_pygame.py`) so they work on machines without a display.

The upgrade suite uses real Pygame with SDL's dummy video/audio drivers and
isolated save data. It covers purchases, save migration, duplicate rewards,
weather persistence, both game results, daily goals, desktop logic, and all
species/coats/animations. Rendered previews are in the parent `upgrade-shots`
folder. The suite creates its temporary test folder automatically.

## Current limits

One active pet at a time; room themes share a layout; desktop movement is on
the primary monitor. Desktop overlays depend on the Windows compositor and
are verified on this machine, while automated headless tests cannot prove
native transparency, focus, or click-through behavior on other machines.
