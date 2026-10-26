using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;

namespace VolumeSliders
{
    public class VolumeSlidersSystem : ModSystem
    {
        const string HarmonyId = "volumesliders";

        Harmony? harmony;
        ICoreClientAPI capi = null!;
        VolumeDialog? dialog;

        public List<SoundEntry> Sounds { get; private set; } = new List<SoundEntry>();
        public List<SoundNode> Tree { get; private set; } = new List<SoundNode>();

        // assets/volumesliders/config/major.json, written by tools/generate.py.
        HashSet<string> majorKeys = new HashSet<string>();
        string[] majorPrefixes = new string[0];

        class MajorList { public string[] keys = new string[0]; public string[] prefixes = new string[0]; }

        public override bool ShouldLoad(EnumAppSide forSide) => forSide == EnumAppSide.Client;

        public override void StartClientSide(ICoreClientAPI api)
        {
            capi = api;
            VolumeConfig.Init(GamePaths.ModConfig, api.Logger);

            harmony = new Harmony(HarmonyId);
            harmony.PatchAll(typeof(VolumeSlidersSystem).Assembly);

            api.Event.LevelFinalize += OnLevelFinalize;

            dialog = new VolumeDialog(api, this);
            api.Input.RegisterHotKey("volumesliders", Lang.Get("volumesliders:hotkey"), GlKeys.V, HotkeyType.GUIOrOtherControls, ctrlPressed: true, shiftPressed: true);
            api.Input.SetHotKeyHandler("volumesliders", _ => dialog.ToggleDialog());

            api.ChatCommands.Create("volumesliders")
                .WithDescription(Lang.Get("volumesliders:command-description"))
                .HandleWith(_ => { dialog.TryOpen(); return TextCommandResult.Success(); });
        }

        void OnLevelFinalize()
        {
            var majorAsset = capi.Assets.TryGet(new AssetLocation("volumesliders", "config/major.json"));
            var major = majorAsset?.ToObject<MajorList>();
            if (major != null)
            {
                majorKeys = new HashSet<string>(major.keys);
                majorPrefixes = major.prefixes;
            }

            var combos = capi.Assets.TryGet(new AssetLocation("volumesliders", "config/combined.json"))?.ToObject<CombinedDef[]>()
                ?? new CombinedDef[0];

            // Every sound file, from the game and from mods. Which mod a file comes from is found by matching the file's
            // origin against each loaded mod's folders. A zipped mod is unpacked into a cache folder when the game starts,
            // and that folder (ModContainer.FolderPath), not the zip, is where its files are read from.
            var mods = capi.ModLoader.Mods
                .Select(m => (Mod: m, Roots: new[] { (m as Vintagestory.Common.ModContainer)?.FolderPath, m.SourcePath }
                    .Where(r => !string.IsNullOrEmpty(r)).ToList()))
                .ToList();
            string? ModFor(string originPath) => mods
                .FirstOrDefault(m => m.Roots.Any(r => SoundKeys.IsInside(originPath, r!)))
                .Mod?.Info?.Name;

            Sounds = capi.Assets.AllAssets
                .Where(p => (p.Key.Category == AssetCategory.sounds || p.Key.Category == AssetCategory.music) && p.Key.Path.EndsWith(".ogg"))
                .GroupBy(p => SoundKeys.KeyFor(p.Key))
                .Select(g => Describe(g.First().Key, g.First().Value, ModFor))
                .OrderBy(e => e.Display, StringComparer.OrdinalIgnoreCase)
                .ToList();
            VolumeConfig.SetKnown(new HashSet<string>(Sounds.Select(e => e.Key)));

            Tree = SoundTree.Build(Sounds, combos, out var rules);
            VolumeConfig.SetRules(rules);
            dialog?.Refresh();
            capi.Logger.Notification("[volumesliders] {0} sounds ({1} major) in {2} groups; {3} come from mods, {4} of those replace a game sound.",
                Sounds.Count, Sounds.Count(s => s.Major), Tree.Count, Sounds.Count(s => s.ModName != null), Sounds.Count(s => s.Replaced));
        }

        SoundEntry Describe(AssetLocation loc, IAsset asset, System.Func<string, string?> modFor)
        {
            string key = SoundKeys.KeyFor(loc);
            string langKey = "volumesliders:sound-" + key;
            bool hasName = Lang.HasTranslation(langKey, false, false);
            string display = hasName ? Lang.Get(langKey) : SoundKeys.CategoryFor(loc) + ": " + SoundKeys.NameFor(loc);

            // A file that isn't in the game's assets folder came from a mod. If the game has a file at the same path,
            // the mod replaced it; otherwise the mod added it.
            string origin = asset.Origin?.OriginPath ?? "";
            string? mod = null;
            bool replaced = false;
            if (!SoundKeys.IsInside(origin, GamePaths.AssetsPath))
            {
                // The mod whose folder holds the file; failing that, the mod that owns the sound's domain (domain = mod id).
                mod = modFor(origin)
                    ?? (loc.Domain != null ? capi.ModLoader.GetMod(loc.Domain)?.Info?.Name : null)
                    ?? SoundKeys.TitleCase(loc.Domain ?? "mod");
                replaced = System.IO.File.Exists(System.IO.Path.Combine(GamePaths.AssetsPath, loc.Domain ?? "game", loc.Path));
            }

            return new SoundEntry
            {
                Key = key, Display = display, Search = (display + " " + key).ToLowerInvariant(), Location = loc, HasLangName = hasName,
                ModName = mod, Replaced = replaced,
                // A mod's own sounds show up by default; a replaced game sound is major only if the game's own would be.
                Major = majorKeys.Contains(key) || majorPrefixes.Any(p => key.StartsWith(p)) || (mod != null && !replaced),
            };
        }

        public override void Dispose()
        {
            harmony?.UnpatchAll(HarmonyId);
            dialog?.Dispose();
        }
    }
}
