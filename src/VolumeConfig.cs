using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using Newtonsoft.Json.Linq;
using Vintagestory.API.Common;

namespace VolumeSliders
{
    /// <summary>
    /// ModConfig/volumesliders.json: a flat { "walk_wood1": 40, ... } map of sound key -> 0..100.
    /// Only sounds turned below 100 are stored; a missing key means 100 (default volume).
    /// </summary>
    public static class VolumeConfig
    {
        public const int Max = 100;

        static string path = "";
        static ILogger? log;

        // Replaced wholesale on load so the audio thread never sees a half-updated dictionary.
        static Dictionary<string, int> volumes = new Dictionary<string, int>();

        /// <summary>Sound key -> last time (Environment.TickCount64) it started or changed volume. Feeds the "recently heard" filter.</summary>
        public static readonly ConcurrentDictionary<string, long> LastHeard = new ConcurrentDictionary<string, long>();

        public static void Init(string configDir, ILogger logger)
        {
            log = logger;
            path = Path.Combine(configDir, "volumesliders.json");
            Load();
        }

        public static int Get(string key) => volumes.TryGetValue(key, out int v) ? v : Max;

        // Keys of the game's own sounds. Anything else (a mod's sound, or a vanilla sound a mod replaced) is never touched.
        static HashSet<string> vanilla = new HashSet<string>();

        public static void SetVanilla(HashSet<string> keys) => vanilla = keys;

        public static bool IsVanilla(string key) => vanilla.Contains(key);

        // Sound key -> the group/combo sliders it answers to. Replaced wholesale once the sound list is known.
        static Dictionary<string, SoundRule> rules = new Dictionary<string, SoundRule>();

        public static void SetRules(Dictionary<string, SoundRule> newRules) => rules = newRules;

        static float Unit(string key) => Math.Clamp(Get(key), 0, Max) / (float)Max;

        /// <summary>
        /// 0..1 multiplier: the sound's own slider times every group slider above it (a combo slider replaces the
        /// sound's own). Each part is at most 1, so a sound can never exceed its default maximum.
        /// </summary>
        public static float Factor(string key)
        {
            if (!rules.TryGetValue(key, out var rule)) return Unit(key);
            float f = rule.IgnoreOwn ? 1f : Unit(key);
            foreach (string g in rule.Groups) f *= Unit(g);
            return f;
        }

        public static void Set(string key, int value)
        {
            var copy = new Dictionary<string, int>(volumes);
            copy[key] = Math.Clamp(value, 0, Max);
            volumes = copy;
        }

        public static void Load()
        {
            try
            {
                var loaded = new Dictionary<string, int>();
                if (File.Exists(path))
                {
                    var obj = JObject.Parse(File.ReadAllText(path));
                    foreach (var p in obj.Properties())
                    {
                        if (p.Value.Type == JTokenType.Integer || p.Value.Type == JTokenType.Float)
                        {
                            loaded[p.Name] = Math.Clamp((int)Math.Round(p.Value.Value<double>()), 0, Max);
                        }
                    }
                }
                volumes = loaded;
            }
            catch (Exception e)
            {
                log?.Error("[volumesliders] Could not read {0}: {1}", path, e.Message);
            }
        }

        public static void Save()
        {
            try
            {
                var obj = new JObject();
                foreach (var kv in new SortedDictionary<string, int>(volumes, StringComparer.Ordinal))
                {
                    if (kv.Value != Max) obj[kv.Key] = kv.Value;
                }
                Directory.CreateDirectory(Path.GetDirectoryName(path)!);
                File.WriteAllText(path, obj.ToString(Newtonsoft.Json.Formatting.Indented));
            }
            catch (Exception e)
            {
                log?.Error("[volumesliders] Could not write {0}: {1}", path, e.Message);
            }
        }
    }
}
