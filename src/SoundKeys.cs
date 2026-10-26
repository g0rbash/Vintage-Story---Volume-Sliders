using System.Text;
using Vintagestory.API.Common;

namespace VolumeSliders
{
    /// <summary>
    /// Turns asset locations into the stable config keys stored in volumesliders.json, and into readable names.
    /// tools/generate.py must produce identical keys for the vanilla sounds it writes into imm.json.
    /// </summary>
    public static class SoundKeys
    {
        static readonly string[] VanillaDomains = { "game", "survival", "creative" };

        /// <summary>"game:sounds/walk/wood1.ogg" -> "walk_wood1"; "music/x" -> "music_x"; other domains are prefixed.</summary>
        public static string KeyFor(AssetLocation loc)
        {
            string path = loc.Path;
            if (path.EndsWith(".ogg")) path = path.Substring(0, path.Length - 4);
            if (path.StartsWith("sounds/")) path = path.Substring(7);

            var sb = new StringBuilder();
            if (loc.Domain != null && System.Array.IndexOf(VanillaDomains, loc.Domain) < 0)
            {
                sb.Append(loc.Domain).Append('_');
            }
            foreach (char c in path)
            {
                sb.Append(char.IsLetterOrDigit(c) ? char.ToLowerInvariant(c) : '_');
            }
            return sb.ToString();
        }

        /// <summary>First folder of the sound, title-cased: "walk/wood1" -> "Walk".</summary>
        public static string CategoryFor(AssetLocation loc)
        {
            string path = loc.Path;
            if (path.StartsWith("sounds/")) path = path.Substring(7);
            int slash = path.IndexOf('/');
            string cat = slash < 0 ? "General" : path.Substring(0, slash);
            return TitleCase(cat);
        }

        /// <summary>Readable name from the file: "weather/lightning-near1" -> "Lightning Near 1".</summary>
        public static string NameFor(AssetLocation loc)
        {
            string path = loc.Path;
            if (path.EndsWith(".ogg")) path = path.Substring(0, path.Length - 4);
            string file = path.Substring(path.LastIndexOf('/') + 1);

            // Folders below the category help when file names repeat (e.g. "tracks/rain-leafy").
            string folder = path.Contains("/") ? path.Substring(0, path.LastIndexOf('/')) : "";
            if (folder.StartsWith("sounds/")) folder = folder.Substring(7);
            int firstSlash = folder.IndexOf('/');
            string sub = firstSlash < 0 ? "" : folder.Substring(firstSlash + 1).Replace('/', ' ');

            string name = TitleCase(file);
            return sub.Length > 0 ? TitleCase(sub) + " " + name : name;
        }

        /// <summary>"lightning-near1" -> "Lightning Near 1".</summary>
        public static string TitleCase(string s)
        {
            var sb = new StringBuilder();
            for (int i = 0; i < s.Length; i++)
            {
                char c = s[i];
                if (c == '-' || c == '_' || c == ' ' || c == '.')
                {
                    if (sb.Length > 0 && sb[sb.Length - 1] != ' ') sb.Append(' ');
                    continue;
                }
                bool boundary = sb.Length > 0 && sb[sb.Length - 1] != ' ' &&
                    ((char.IsDigit(c) && !char.IsDigit(s[i - 1])) || (char.IsUpper(c) && char.IsLower(s[i - 1])));
                if (boundary) sb.Append(' ');
                sb.Append(sb.Length == 0 || sb[sb.Length - 1] == ' ' ? char.ToUpperInvariant(c) : c);
            }
            return sb.ToString();
        }
    }
}
