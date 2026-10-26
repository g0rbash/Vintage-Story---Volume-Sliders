<p align="center"><img src="docs/images/description.png" alt="Volume Sliders, a 0 to 100 volume slider for every sound in Vintage Story 1.22.7. The full text is below." width="920"></p>

<details><summary><b>Text version</b> (the same content as the image above)</summary>

*This project was done with the help of Claude (Claude Sonnet 5.5).*

Some sounds in Vintage Story you'll love for a hundred hours, and some will wear you down: the helve hammer through a long smithing session, the rapids beside your base, the cicadas, a rainstorm that won't quit. The base game only gives you a few master volume sliders. This mod gives the individual sounds their own slider, from 0 to 100, so you can turn down just the ones that bother you and leave the rest alone.

### What You Get

- **0 to 100 per sound.** 100 is the game's normal volume for that sound, and no slider can go above it.
- **Clear names.** "Water: Rapids", "Thunder: Near", "Anvil & Helve Hammer: Hit 2". Sounds that come in several versions get a slider for each version.
- **A searchable window** in the same style as the game's own settings.
- **Heard in the last 30 seconds.** One switch lists only the sounds that just played, so you can find the one that is bugging you right now.
- **Changes apply immediately**, including sounds that are already playing, like a river loop.
- **Preview button** beside every slider.
- **Other mods' sounds** show up in the window automatically.

### The Sounds

The window opens on the sounds people most often want quieter, and can show all 813 of the game's own. IMM gets the 91 marked below.

| Group | Includes | IMM sliders |
|---|---|---|
| **Anvil & Helve Hammer** | The anvil hit, which is also the helve hammer's sound | 4 |
| **Water** | Rapids, creek, waterfall, waves, underwater, splashes, waterwheel, wading, swimming | 15 |
| **Boat** | Water against the raft, idle and moving | 2 |
| **Rain** | Rain on leafy and bare trees, hail, rain on windows | 4 |
| **Wind** | Ambient wind, wind in leafy and bare trees | 3 |
| **Thunder** | Distant, near, very near, overhead, and the low rumbles | 7 |
| **Fire** | Flames, fireplace | 2 |
| **Lava** | Lava ambience | 1 |
| **Mobs** | In IMM: Drifter, Shiver, Bowtorn, Locust, and Bell sounds. In the window: every creature sound: wolves, bears, goats, chickens, and the rest. | 36 in IMM |
| **Insects** | Cicadas, grasshoppers, coqui frogs | 4 |
| **Bees** | Hives, swarms, stings | 4 |
| **Temporal** | Stability warnings, rifts, rift wards | 5 |
| **Bells** | The deep bell | 1 |
| **Machines** | Quern, gears, bellows | 3 |

### Using It

- **The window.** Press **Ctrl+Shift+V** (you can rebind it in the controls settings), or type **.volumesliders** in chat. It opens on the sounds most people want quieter plus every creature sound; the *Show every sound* switch lists all of them, including other mods'.
- **Integrated Mod Manager.** Open it, choose *Volume Sliders*, and move the sliders. IMM can't draw a list of hundreds of settings, so it shows the major sounds above; tick *Open the full searchable window* and press *Apply* to jump to the full window.
- **Both are the same settings.** Whichever you use, the values live in **ModConfig/volumesliders.json**, and edits made in one show up in the other while the game is running.

### Compatibility

- **Vintage Story 1.22.7.** Client-side only: single player, or any server, with nothing to install on the server.
- **Integrated Mod Manager.** The sliders appear in its config window.
- **Accessibility Tweaks.** Its Sound Effects screen scales sounds too. The two multipliers stack, so a sound set to 50% in each plays at 25%.
- **Other mods.** Their sounds get sliders in the full window. Sounds that a mod plays through its own audio code instead of the game's sound engine can't be reached.

### Installation

1. Drop **volumesliders_0.1.0.zip** into your Mods folder.
2. Start the game. The first run writes **ModConfig/volumesliders.json** with every sound at 100.
3. To reset everything, delete that file, or use *Reset Shown to 100* in the window.

### Credits

- **G0rbash** design, testing, and the Vintage Story 1.22.7 build.
- **YangWenLi** for [Integrated Mod Manager](https://mods.vintagestory.at/integratedmodmanager), which this mod plugs into.
- **ApacheTech Solutions** for [Accessibility Tweaks](https://mods.vintagestory.at/accessibilitytweaks), whose Sound Effects feature showed the way to scale a single sound.

### A Note from G0rbash

I have not coded in C# since 1996 and don't have time to relearn that skill while also learning skill for my #dayjob. I tested and reviewed the code to the best of my ability. I do not condone the unethical training and use of "AI" coding tools, but there is value for small projects like this that improve the happy times we have playing video games.

Thank you,  
G0rbash

</details>

**Links:** [Integrated Mod Manager](https://mods.vintagestory.at/integratedmodmanager) · [Accessibility Tweaks](https://mods.vintagestory.at/accessibilitytweaks)

**Building from source:** see [BUILDING.md](BUILDING.md).
