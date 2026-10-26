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

            // Mods' assets are all loaded by now, so this includes sounds from other mods.
            Sounds = capi.Assets.AllAssets
                .Where(p => (p.Key.Category == AssetCategory.sounds || p.Key.Category == AssetCategory.music) && p.Key.Path.EndsWith(".ogg"))
                .Select(p => p.Key)
                .GroupBy(SoundKeys.KeyFor)
                .Select(g => g.First())
                .Select(Describe)
                .OrderBy(e => e.Display, StringComparer.OrdinalIgnoreCase)
                .ToList();

            Tree = SoundTree.Build(Sounds, combos, out var rules);
            VolumeConfig.SetRules(rules);
            dialog?.Refresh();
            capi.Logger.Notification("[volumesliders] Loaded {0} sounds ({1} major) in {2} groups.", Sounds.Count, Sounds.Count(s => s.Major), Tree.Count);
        }

        SoundEntry Describe(AssetLocation loc)
        {
            string key = SoundKeys.KeyFor(loc);
            string langKey = "volumesliders:sound-" + key;
            string display = Lang.HasTranslation(langKey, false, false)
                ? Lang.Get(langKey)
                : SoundKeys.CategoryFor(loc) + ": " + SoundKeys.NameFor(loc);
            return new SoundEntry { Key = key, Display = display, Search = (display + " " + key).ToLowerInvariant(), Location = loc,
                HasLangName = Lang.HasTranslation(langKey, false, false),
                Major = majorKeys.Contains(key) || majorPrefixes.Any(p => key.StartsWith(p)) };
        }

        public override void Dispose()
        {
            harmony?.UnpatchAll(HarmonyId);
            dialog?.Dispose();
        }
    }
}
