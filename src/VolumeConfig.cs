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
    /// Flat so Integrated Mod Manager can bind a slider to each key. Missing key = 100 (default volume).
    /// </summary>
    public static class VolumeConfig
    {
        public const int Max = 100;

        static string path = "";
        static ILogger? log;
        static DateTime lastKnownWrite;

        /// <summary>Set when the config file has OpenWindow:true (the IMM "open full window" checkbox). The mod clears it after acting.</summary>
        public static bool OpenWindowRequested;

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

        /// <summary>0..1 multiplier. Never above 1, so a sound can't exceed its default maximum.</summary>
        public static float Factor(string key) => Math.Clamp(Get(key), 0, Max) / (float)Max;

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
                    lastKnownWrite = File.GetLastWriteTimeUtc(path);
                    var obj = JObject.Parse(File.ReadAllText(path));
                    OpenWindowRequested = obj["OpenWindow"]?.Type == JTokenType.Boolean && obj["OpenWindow"]!.Value<bool>();
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

        /// <summary>Writes every known key (default 100) so IMM's sliders show 100 rather than an empty value.</summary>
        public static void Save(IEnumerable<string> allKeys)
        {
            try
            {
                var obj = new JObject();
                var keys = new SortedSet<string>(allKeys, StringComparer.Ordinal);
                foreach (var k in volumes.Keys) keys.Add(k);
                obj["OpenWindow"] = false;
                foreach (var k in keys) obj[k] = Get(k);
                Directory.CreateDirectory(Path.GetDirectoryName(path)!);
                File.WriteAllText(path, obj.ToString(Newtonsoft.Json.Formatting.Indented));
                lastKnownWrite = File.GetLastWriteTimeUtc(path);
            }
            catch (Exception e)
            {
                log?.Error("[volumesliders] Could not write {0}: {1}", path, e.Message);
            }
        }

        /// <summary>True (and reloads) if something else, such as IMM, changed the file since we last touched it.</summary>
        public static bool ReloadIfChangedExternally()
        {
            try
            {
                if (!File.Exists(path) || File.GetLastWriteTimeUtc(path) == lastKnownWrite) return false;
                Load();
                return true;
            }
            catch { return false; }
        }
    }
}
