using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace VolumeSliders
{
    /// <summary>A sound that has its own slider.</summary>
    public class SoundEntry
    {
        public string Key = "";
        public string Display = "";   // "Water: Rapids"
        public string Search = "";    // lower case
        public Vintagestory.API.Common.AssetLocation Location = null!;
        public bool Major;
        public bool HasLangName;      // Display came from lang/en.json ("Group: Name") rather than the file name
        public string? ModName;       // set when the sound's file comes from a mod rather than the game
        public bool Replaced;         // ...and that mod replaced one of the game's own sound files
    }

    /// <summary>One of the "combo" sliders from config/combined.json: several sounds, one slider.</summary>
    public class CombinedDef
    {
        public string id = "";
        public string name = "";
        public string[] keys = new string[0];
    }

    /// <summary>How the audio thread scales one sound: its own slider (unless folded into a combo) times each group above it.</summary>
    public class SoundRule
    {
        public string[] Groups = new string[0];
        public bool IgnoreOwn;
    }

    /// <summary>A row in the window: a single sound, a combined slider, or a group that opens to show more.</summary>
    public class SoundNode
    {
        public string ConfigKey = "";                 // sound key, "group:mobs/drifter", or "combo:helvehammer"
        public string Name = "";
        public string Search = "";                    // lower case, leaves and combos only
        public SoundNode? Parent;
        public string? Note;                          // shown beside a sound a mod has replaced
        public int ModdedCount;                       // how many sounds at or under this row a mod has replaced
        public List<SoundNode> Children = new List<SoundNode>();
        public bool IsGroup;
        public bool Major;
        public SoundEntry? Sound;                     // leaf only
        public List<SoundEntry> Members = new List<SoundEntry>();   // every sound this slider affects
        public int LeafCount => IsGroup ? Children.Sum(c => c.LeafCount) : 1;

        public SoundEntry? Preview => Sound ?? Members.FirstOrDefault();

        /// <summary>Config keys to set back to 100 when this row is reset: its own and everything beneath it.</summary>
        public IEnumerable<string> ResetKeys()
        {
            yield return ConfigKey;
            foreach (var c in Children) foreach (var k in c.ResetKeys()) yield return k;
        }
    }

    /// <summary>
    /// Groups the flat sound list into the openable tree the window shows, and works out the per-sound rules.
    /// No game or UI types beyond AssetLocation, so it can be tested on its own.
    /// </summary>
    public static class SoundTree
    {
        static readonly HashSet<string> GenericFolders = new HashSet<string> { "animal", "mammal", "hooved", "large", "medium", "small", "bird", "birds", "generic", "strange" };

        public static List<SoundNode> Build(IEnumerable<SoundEntry> sounds, IEnumerable<CombinedDef> combos, out Dictionary<string, SoundRule> rules)
        {
            var roots = new List<SoundNode>();
            var groups = new Dictionary<string, SoundNode>();
            var comboOf = new Dictionary<string, SoundNode>();

            foreach (var def in combos)
            {
                var node = new SoundNode { ConfigKey = "combo:" + def.id, Name = def.name };
                foreach (var k in def.keys) comboOf[k] = node;
            }

            SoundNode Group(string name, SoundNode? parent)
            {
                string path = (parent == null ? "" : parent.ConfigKey.Substring("group:".Length) + "/") + name.ToLowerInvariant();
                if (!groups.TryGetValue(path, out var g))
                {
                    g = new SoundNode { ConfigKey = "group:" + path, Name = name, IsGroup = true, Parent = parent };
                    groups[path] = g;
                    (parent?.Children ?? roots).Add(g);
                }
                return g;
            }

            var usedCombos = new HashSet<SoundNode>();
            foreach (var s in sounds)
            {
                if (comboOf.TryGetValue(s.Key, out var combo))
                {
                    combo.Members.Add(s);
                    combo.Major |= s.Major;
                    if (usedCombos.Add(combo)) roots.Add(combo);
                    continue;
                }

                Classify(s, out string group, out List<string> subs, out string leafName);
                var parent = Group(group, null);
                foreach (string sub in subs) parent = Group(sub, parent);
                parent.Children.Add(new SoundNode
                {
                    ConfigKey = s.Key, Name = leafName, Sound = s, Major = s.Major, Parent = parent, Members = { s },
                    Note = s.Replaced ? ShortName(s.ModName) : null, ModdedCount = s.Replaced ? 1 : 0,
                    Search = (group + " " + string.Join(" ", subs) + " " + leafName + " " + s.Display + " " + s.Key + " " + (s.Replaced ? s.ModName : "")).ToLowerInvariant(),
                });
            }
            foreach (var c in usedCombos)
            {
                c.Search = (c.Name + " " + string.Join(" ", c.Members.Select(m => m.Display + " " + m.Key))).ToLowerInvariant();
            }

            for (int i = 0; i < roots.Count; i++) roots[i] = Tidy(roots[i]);
            roots.Sort((a, b) => NaturalCompare(a.Name, b.Name));

            rules = new Dictionary<string, SoundRule>();
            foreach (var r in roots) Describe(r, new List<string>(), rules);
            return roots;
        }

        /// <summary>
        /// A group with a single sound is not worth a caret: it becomes a plain row named "Group: Sound".
        /// Everything else gets its children sorted and its totals filled in.
        /// </summary>
        static SoundNode Tidy(SoundNode n)
        {
            if (!n.IsGroup) return n;
            for (int i = 0; i < n.Children.Count; i++) n.Children[i] = Tidy(n.Children[i]);

            if (n.LeafCount == 1 && n.Children.Count == 1 && !n.Children[0].IsGroup)
            {
                var leaf = n.Children[0];
                leaf.Name = n.Name + ": " + leaf.Name;
                leaf.Parent = n.Parent;
                return leaf;
            }
            n.Children.Sort((a, b) => NaturalCompare(a.Name, b.Name));
            foreach (var c in n.Children)
            {
                c.Parent = n;
                n.Members.AddRange(c.Members);
                n.Major |= c.Major;
                n.ModdedCount += c.ModdedCount;
            }
            return n;
        }

        static void Describe(SoundNode n, List<string> groupKeys, Dictionary<string, SoundRule> rules)
        {
            if (n.IsGroup)
            {
                var next = new List<string>(groupKeys) { n.ConfigKey };
                foreach (var c in n.Children) Describe(c, next, rules);
            }
            else if (n.Sound == null)
            {
                // A combo: its members answer to the combo's slider and nothing else.
                foreach (var m in n.Members)
                    rules[m.Key] = new SoundRule { Groups = groupKeys.Concat(new[] { n.ConfigKey }).ToArray(), IgnoreOwn = true };
            }
            else if (groupKeys.Count > 0)
            {
                rules[n.Sound.Key] = new SoundRule { Groups = groupKeys.ToArray() };
            }
        }

        /// <summary>A mod's name as it fits beside a slider.</summary>
        public static string ShortName(string? name)
        {
            name = (name ?? "a mod").Trim();
            return name.Length <= 36 ? name : name.Substring(0, 35).TrimEnd() + "...";
        }

        /// <summary>Which group (and, for mobs, which creature and folder) a sound lists under, and what to call it there.</summary>
        public static void Classify(SoundEntry s, out string group, out List<string> subs, out string leafName)
        {
            subs = new List<string>();
            var loc = s.Location;
            bool fromMod = s.ModName != null && !s.Replaced;   // a replaced vanilla sound stays in its vanilla group

            if (fromMod)
            {
                // Mods > <mod> > <the mod's own group, or the sound's folder> > sound
                group = "Mods";
                subs.Add(ShortName(s.ModName));
                if (s.HasLangName)
                {
                    int colon = s.Display.IndexOf(": ", StringComparison.Ordinal);
                    if (colon >= 0) { subs.Add(s.Display.Substring(0, colon)); leafName = s.Display.Substring(colon + 2); return; }
                    leafName = s.Display;
                    return;
                }
                string cat = SoundKeys.FolderOf(loc);
                leafName = SoundKeys.NameFor(loc);
                if (cat.Length == 0) return;
                if (cat == "creature") { subs.Add("Mobs"); ClassifyCreature(loc, subs, out leafName); return; }
                subs.Add(SoundKeys.TitleCase(cat));
                return;
            }

            if (s.HasLangName)
            {
                int colon = s.Display.IndexOf(": ", StringComparison.Ordinal);
                group = colon < 0 ? "Other" : s.Display.Substring(0, colon);
                leafName = colon < 0 ? s.Display : s.Display.Substring(colon + 2);
                return;
            }

            group = SoundKeys.CategoryFor(loc);
            leafName = SoundKeys.NameFor(loc);
            if (group != "Creature") return;

            group = "Mobs";
            ClassifyCreature(loc, subs, out leafName);
        }

        /// <summary>Adds the creature (and first folder) a creature sound belongs to, and names the sound within it.</summary>
        static void ClassifyCreature(Vintagestory.API.Common.AssetLocation loc, List<string> subs, out string leafName)
        {
            string path = loc.Path;
            if (path.EndsWith(".ogg")) path = path.Substring(0, path.Length - 4);
            if (path.StartsWith("sounds/")) path = path.Substring(7);
            var segs = path.Split('/').Skip(1).ToList();                    // drop "creature"
            string? firstGeneric = null;   // 'hooved' for hooved/small/callsmall1: the creature family stands in for the name
            while (segs.Count > 1 && GenericFolders.Contains(segs[0])) { firstGeneric ??= segs[0]; segs.RemoveAt(0); }

            string file = segs[segs.Count - 1];
            string mob = segs.Count > 1 ? segs[0] : (firstGeneric ?? FirstWord(file));
            var folders = segs.Count > 2 ? segs.Skip(1).Take(segs.Count - 2).ToList() : new List<string>();

            subs.Add(SoundKeys.TitleCase(mob));
            var named = new List<string> { mob };            // words the groups above already say
            named.AddRange(folders);
            if (folders.Count > 0)
            {
                subs.Add(SoundKeys.TitleCase(folders[0]));
                folders.RemoveAt(0);
            }

            // Leaf: leftover folders plus the file's words, minus any word a group above already says.
            // "bear/footsteps/dirt/bear-footstep-dirt1" under Bear > Footsteps becomes "Dirt 1".
            var folderWords = SoundKeys.TitleCase(string.Join(" ", folders)).Split(' ', StringSplitOptions.RemoveEmptyEntries);
            var fileWords = SoundKeys.TitleCase(file).Split(' ', StringSplitOptions.RemoveEmptyEntries)
                .Where(w => char.IsDigit(w[0]) || !IsCovered(w, named));
            var words = folderWords.Concat(fileWords).ToList();
            leafName = words.Any(w => !char.IsDigit(w[0])) ? string.Join(" ", words) : SoundKeys.TitleCase(file);
        }

        /// <summary>True if a group above already says this word (a loose match, so "footstep" is covered by "footsteps").</summary>
        static bool IsCovered(string word, List<string> named)
        {
            string w = word.ToLowerInvariant();
            if (w.Length < 3) return false;
            foreach (string n in named)
                foreach (string part in SoundKeys.TitleCase(n).Split(' ', StringSplitOptions.RemoveEmptyEntries))
                {
                    string p = part.ToLowerInvariant();
                    if (p.Length >= 3 && (p.StartsWith(w) || w.StartsWith(p))) return true;
                }
            return false;
        }

        static string FirstWord(string file)
        {
            int cut = file.IndexOfAny(new[] { '-', '_' });
            string w = cut < 0 ? file : file.Substring(0, cut);
            return w.TrimEnd('0', '1', '2', '3', '4', '5', '6', '7', '8', '9');
        }

        /// <summary>Case-insensitive, with numbers compared as numbers, so "Hit 2" comes before "Hit 10".</summary>
        public static int NaturalCompare(string a, string b)
        {
            int i = 0, j = 0;
            while (i < a.Length && j < b.Length)
            {
                if (char.IsDigit(a[i]) && char.IsDigit(b[j]))
                {
                    int si = i, sj = j;
                    while (i < a.Length && char.IsDigit(a[i])) i++;
                    while (j < b.Length && char.IsDigit(b[j])) j++;
                    string na = a.Substring(si, i - si).TrimStart('0'), nb = b.Substring(sj, j - sj).TrimStart('0');
                    if (na.Length != nb.Length) return na.Length - nb.Length;
                    int c = string.CompareOrdinal(na, nb);
                    if (c != 0) return c;
                }
                else
                {
                    int c = char.ToLowerInvariant(a[i]).CompareTo(char.ToLowerInvariant(b[j]));
                    if (c != 0) return c;
                    i++; j++;
                }
            }
            return (a.Length - i) - (b.Length - j);
        }
    }
}
