using System;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using HarmonyLib;
using Vintagestory.API.Common;
using Vintagestory.Client;

namespace VolumeSliders
{
    /// <summary>
    /// Every volume the engine sends to OpenAL is "soundParams.Volume * GlobalVolume", so scaling the GlobalVolume
    /// getter's result scales that one sound only. The factor is 0..1, so nothing gets louder than vanilla.
    /// </summary>
    [HarmonyPatch(typeof(LoadedSoundNative), "GlobalVolume", MethodType.Getter)]
    public static class SoundPatch
    {
        // Location.ToString() allocates and this runs on every volume update, so remember the key per AssetLocation.
        static readonly ConditionalWeakTable<AssetLocation, string> keys = new ConditionalWeakTable<AssetLocation, string>();

        [HarmonyPostfix]
        public static void Postfix(LoadedSoundNative __instance, ref float __result)
        {
            var loc = __instance.Params?.Location;
            if (loc == null) return;

            if (!keys.TryGetValue(loc, out string? key))
            {
                key = SoundKeys.KeyFor(loc);
                keys.AddOrUpdate(loc, key);
            }

            VolumeConfig.LastHeard[key] = Environment.TickCount64;
            __result *= VolumeConfig.Factor(key);
        }

        static readonly System.Reflection.FieldInfo? soundList = AccessTools.Field(typeof(LoadedSoundNative), "loadedSounds");
        static readonly System.Reflection.FieldInfo? soundLock = AccessTools.Field(typeof(LoadedSoundNative), "loadedSoundsLock");

        /// <summary>
        /// Steady loops (rapids, rain, wind) only re-send their volume when it drifts, so a slider change would
        /// otherwise wait until the loop restarts. Re-send now for every playing sound whose key matches (null = all).
        /// </summary>
        public static void RefreshPlaying(System.Func<string, bool>? matches)
        {
            if (soundList?.GetValue(null) is not IEnumerable list || soundLock?.GetValue(null) is not object padlock) return;

            var playing = new List<LoadedSoundNative>();
            lock (padlock)
            {
                foreach (object o in list) if (o is LoadedSoundNative s) playing.Add(s);
            }
            foreach (var s in playing)
            {
                var loc = s.Params?.Location;
                if (loc == null || s.IsDisposed) continue;
                if (matches == null || matches(SoundKeys.KeyFor(loc))) s.SetVolume();
            }
        }
    }
}
