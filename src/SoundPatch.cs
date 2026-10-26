using System;
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
    }
}
