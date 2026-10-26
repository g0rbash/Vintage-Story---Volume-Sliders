# Volume Sliders

Version 0.1.0 · Vintage Story 1.22.7 · client side

*This project was done with the help of Claude (Claude Sonnet 5.5).*

Some sounds in Vintage Story you'll love for a hundred hours, and some will wear you down: the helve hammer through a long smithing session, the rapids beside your base, the cicadas, a rainstorm that won't quit. The base game only gives you a few master volume sliders. This mod gives the individual sounds their own slider, so you can turn down just the ones that bother you and leave the rest alone.

<details>
<summary><b>Screenshots</b></summary>

<img src="docs/images/screenshots/window.png" width="700" alt="The window, opened with Ctrl+Shift+V. A group marked with &gt; opens to show its sounds.">

*The window, opened with Ctrl+Shift+V. A group marked with > opens to show its sounds.*

<img src="docs/images/screenshots/mods-section.png" width="700" alt="Sounds from other mods are listed under Mods, one group per mod.">

*Sounds from other mods are listed under Mods, one group per mod.*

</details>

## What you get

- **A slider for every sound.** 100 is the game's normal volume for that sound, and no slider can go above it.
- **Clear names.** "Water: Rapids", "Thunder: Near", "Drifter: Idle 2". Sounds that come in several versions get a slider for each version.
- **Groups that open.** Related sounds sit under a group marked with a **>**. Open it to see each sound; the group's own slider turns the whole group up or down. Mobs are grouped by creature: Drifter, Bear, Bowtorn, and so on.
- **One slider for the helve hammer.** Everything the helve hammer plays is a single slider, instead of a handful of near-identical hits.
- **A searchable window** in the same style as the game's own settings.
- **Recently heard.** One switch lists only the sounds that played in the last 30 seconds, so you can find the one that is bugging you right now.
- **Changes apply immediately**, including sounds that are already playing, like a river loop.
- **Preview button** beside every slider.
- **Mod sounds too.** Sounds that other mods add get sliders under **Mods**, grouped by mod. Salty's Temporal Symphony, for example, has a **Temporal Storm** group for its storm rumbles, warnings, and thunder.
- **Changes are marked.** When a mod replaces one of the game's own sounds, that slider shows the mod's name beside it, and its group counts how many of its sounds were changed.

## The sounds

The window opens on these sounds, the ones people most often want quieter, and can show all 813 of the game's own, plus the sounds of any mods you have.

- **Helve Hammer** (3): One slider for everything the helve hammer plays. Hammering at an anvil by hand plays the same hits, so it quiets those too.
- **Anvil** (1): The weld hit
- **Water** (15): Rapids, creek, waterfall, waves, underwater, splashes, waterwheel, wading, swimming
- **Boat** (2): Water against the raft, idle and moving
- **Rain** (4): Rain on leafy and bare trees, hail, rain on windows
- **Wind** (3): Ambient wind, wind in leafy and bare trees
- **Thunder** (7): Distant, near, very near, overhead, and the low rumbles
- **Fire** (2): Flames, fireplace
- **Lava** (1): Lava ambience
- **Mobs** (271): Every creature sound, grouped by creature: drifters, shivers, bowtorn, locusts, wolves, bears, goats, chickens, and the rest
- **Insects** (4): Cicadas, grasshoppers, coqui frogs
- **Bees** (4): Hives, swarms, stings
- **Temporal** (5): Stability warnings, rifts, rift wards
- **Bells** (1): The deep bell
- **Machines** (3): Quern, gears, bellows
- **Mods**: Sounds added by other mods, grouped by mod. Temporal Symphony's temporal storm, thunder, and creature sounds are one example.

## Using it

- Press **Ctrl+Shift+V** (you can rebind it in the controls settings), or type **.volumesliders** in chat.
- Click a group, or its **>**, to open or close it. The group's slider scales everything inside, and each sound keeps its own slider too. They multiply, so a group at 50% and a sound at 50% plays at 25%.
- The window opens on the sounds most people want quieter, plus every creature sound. Flip *Show every sound* to list every sound, including mods' quieter ones.
- Your settings are saved in **ModConfig/volumesliders.json**.

## Compatibility

- **Vintage Story 1.22.7.** Client-side only.
- **Accessibility Tweaks.** Its Sound Effects screen scales sounds too. The two multipliers stack, so a sound set to 50% in each plays at 25%.
- **Other mods.** Their sounds get sliders under Mods, and a game sound a mod replaces is marked with the mod's name. If a mod has its own volume setting, it still applies on top of these sliders. A mod that plays sound through its own audio code, instead of the game's sound engine, may not respond.

## Installation

1. Drop **volumesliders_0.1.0.zip** into your Mods folder.
2. Start the game. The first run writes **ModConfig/volumesliders.json** with every sound at 100.
3. To reset everything, delete that file, or use *Reset Shown to 100* in the window.

## Credits

- **G0rbash** design, testing, and the Vintage Story 1.22.7 build.
- **ApacheTech Solutions** for [Accessibility Tweaks](https://mods.vintagestory.at/accessibilitytweaks), whose Sound Effects feature showed the way to scale a single sound.

## A note from G0rbash

I have not coded in C# since 1996 and don't have time to relearn that skill while also learning skill for my #dayjob. I tested and reviewed the code to the best of my ability. I do not condone the unethical training and use of "AI" coding tools, but there is value for small projects like this that improve the happy times we have playing video games.

Thank you,  
G0rbash

---

Building from source: see [BUILDING.md](BUILDING.md).
