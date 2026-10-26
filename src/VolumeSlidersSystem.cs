using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;

namespace VolumeSliders
{
    public class SoundEntry
    {
        public string Key = "";
        public string Display = "";
        public string Search = "";
        public AssetLocation Location = null!;
    }

    public class VolumeSlidersSystem : ModSystem
    {
        const string HarmonyId = "volumesliders";

        Harmony? harmony;
        ICoreClientAPI capi = null!;
        VolumeDialog? dialog;

        public List<SoundEntry> Sounds { get; private set; } = new List<SoundEntry>();

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

            // IMM edits the config file directly; pick those edits up without a restart.
            api.Event.RegisterGameTickListener(_ =>
            {
                if (VolumeConfig.ReloadIfChangedExternally()) dialog?.Refresh();
            }, 1500);
        }

        void OnLevelFinalize()
        {
            // Mods' assets are all loaded by now, so this includes sounds from other mods.
            Sounds = capi.Assets.AllAssets
                .Where(p => (p.Key.Category == AssetCategory.sounds || p.Key.Category == AssetCategory.music) && p.Key.Path.EndsWith(".ogg"))
                .Select(p => p.Key)
                .GroupBy(SoundKeys.KeyFor)
                .Select(g => g.First())
                .Select(Describe)
                .OrderBy(e => e.Display, StringComparer.OrdinalIgnoreCase)
                .ToList();

            // Write every key so IMM's sliders start at 100 instead of empty.
            VolumeConfig.Save(Sounds.Select(s => s.Key));
            dialog?.Refresh();
            capi.Logger.Notification("[volumesliders] Loaded {0} sounds.", Sounds.Count);
        }

        SoundEntry Describe(AssetLocation loc)
        {
            string key = SoundKeys.KeyFor(loc);
            string display = Lang.GetIfExists("volumesliders:sound-" + key)
                ?? SoundKeys.CategoryFor(loc) + ": " + SoundKeys.NameFor(loc);
            return new SoundEntry { Key = key, Display = display, Search = (display + " " + key).ToLowerInvariant(), Location = loc };
        }

        public override void Dispose()
        {
            harmony?.UnpatchAll(HarmonyId);
            dialog?.Dispose();
        }
    }
}
