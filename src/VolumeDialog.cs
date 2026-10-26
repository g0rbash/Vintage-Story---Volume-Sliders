using System;
using System.Collections.Generic;
using System.Linq;
using Cairo;
using Vintagestory.API.Client;
using Vintagestory.API.Common;
using Vintagestory.API.Config;

namespace VolumeSliders
{
    /// <summary>
    /// Searchable, openable list of volume sliders in the standard dialog style. Groups show "&gt;" (closed) or
    /// "v" (open) and hold a slider that scales everything inside. Only RowCount rows exist; scrolling re-points
    /// them at a different slice of the visible list, so 800 sounds cost no more than 12.
    /// </summary>
    public class VolumeDialog : GuiDialog
    {
        const int RowCount = 12;
        const double RowHeight = 34;
        const double Width = 700;
        const double NameWidth = 410;   // the name column; the slider starts just after it
        const long RecentMs = 30_000;

        class Row
        {
            public SoundNode Node = null!;
            public int Depth;
            public bool Header;
            public bool Open;
            public int Leaves;
        }

        readonly VolumeSlidersSystem system;
        readonly HashSet<string> openGroups = new HashSet<string>();
        List<Row> rows = new List<Row>();
        string search = "";
        bool recentOnly;
        bool showAll;
        int offset;
        int soundsShown;
        ElementBounds? listBounds;

        public override string ToggleKeyCombinationCode => "volumesliders";

        public VolumeDialog(ICoreClientAPI capi, VolumeSlidersSystem system) : base(capi)
        {
            this.system = system;
        }

        public override bool TryOpen()
        {
            if (!base.TryOpen()) return false;
            Compose();
            return true;
        }

        public bool ToggleDialog()
        {
            if (IsOpened()) TryClose(); else TryOpen();
            return true;
        }

        /// <summary>Rebuilds the list after the sounds changed underneath an open dialog.</summary>
        public void Refresh()
        {
            if (IsOpened()) { BuildRows(); FillRows(); }
        }

        void Compose()
        {
            ElementBounds dialogBounds = ElementStdBounds.AutosizedMainDialog.WithAlignment(EnumDialogArea.CenterMiddle);
            ElementBounds bgBounds = ElementBounds.Fill.WithFixedPadding(GuiStyle.ElementToDialogPadding);
            bgBounds.BothSizing = ElementSizing.FitToChildren;

            ElementBounds searchLabel = ElementBounds.Fixed(0, 40, 70, 30);
            ElementBounds searchInput = ElementBounds.Fixed(75, 38, 330, 30);
            ElementBounds recentLabel = ElementBounds.Fixed(425, 42, 170, 30);
            ElementBounds recentSwitch = ElementBounds.Fixed(600, 40, 30, 30);
            ElementBounds allLabel = ElementBounds.Fixed(425, 77, 170, 30);
            ElementBounds allSwitch = ElementBounds.Fixed(600, 75, 30, 30);

            double listTop = 120;
            ElementBounds listArea = ElementBounds.Fixed(0, listTop, Width - 20, RowCount * RowHeight);
            listBounds = listArea;
            ElementBounds scrollBounds = ElementBounds.Fixed(Width - 10, listTop, 20, RowCount * RowHeight);

            var comp = capi.Gui.CreateCompo("volumesliders", dialogBounds)
                .AddShadedDialogBG(bgBounds)
                .AddDialogTitleBar(Lang.Get("volumesliders:title"), () => TryClose())
                .BeginChildElements(bgBounds)
                    .AddStaticText(Lang.Get("volumesliders:search"), CairoFont.WhiteSmallText(), searchLabel)
                    .AddTextInput(searchInput, OnSearchChanged, CairoFont.TextInput(), "search")
                    .AddStaticText(Lang.Get("volumesliders:recent"), CairoFont.WhiteSmallText(), recentLabel)
                    .AddSwitch(on => { recentOnly = on; offset = 0; BuildRows(); FillRows(); }, recentSwitch, "recent")
                    .AddStaticText(Lang.Get("volumesliders:all-sounds"), CairoFont.WhiteSmallText(), allLabel)
                    .AddSwitch(on => { showAll = on; offset = 0; BuildRows(); FillRows(); }, allSwitch, "all")
                    .AddInset(listArea.ForkBoundingParent(2, 2, 2, 2), 4);

            for (int i = 0; i < RowCount; i++)
            {
                double y = listTop + i * RowHeight;
                int row = i;
                // The caret and the name are clickable text: the composer calls their click handler directly.
                comp.AddInteractiveElement(new ClickableText(capi, CairoFont.WhiteSmallText(), ElementBounds.Fixed(8, y + 5, 20, 28), () => ToggleRow(row)), "caret" + i)
                    .AddInteractiveElement(new ClickableText(capi, CairoFont.WhiteSmallText(), ElementBounds.Fixed(28, y + 5, NameWidth - 30, 28), () => ToggleRow(row)), "name" + i)
                    .AddSlider(v => OnSliderChanged(row, v), ElementBounds.Fixed(NameWidth + 5, y + 4, 175, 26), "slider" + i)
                    .AddSmallButton(Lang.Get("volumesliders:play"), () => PlayPreview(row), ElementBounds.Fixed(NameWidth + 185, y + 3, 56, 28), EnumButtonStyle.Normal, "play" + i);
            }

            comp.AddVerticalScrollbar(OnScroll, scrollBounds, "scroll")
                .AddSmallButton(Lang.Get("volumesliders:reset-shown"), OnResetShown, ElementBounds.Fixed(0, listTop + RowCount * RowHeight + 12, 160, 30), EnumButtonStyle.Normal)
                .AddDynamicText("", CairoFont.WhiteDetailText(), ElementBounds.Fixed(180, listTop + RowCount * RowHeight + 18, 460, 24), "count")
                .EndChildElements();

            SingleComposer = comp.Compose();
            SingleComposer.GetTextInput("search").SetValue(search);
            SingleComposer.GetSwitch("recent").SetValue(recentOnly);
            SingleComposer.GetSwitch("all").SetValue(showAll);
            BuildRows();
            FillRows();
        }

        // ---------------------------------------------------------------- what is visible

        /// <summary>Flattens the tree into the rows to show, applying the search, "recent", and "every sound" filters.</summary>
        void BuildRows()
        {
            string[] terms = search.ToLowerInvariant().Split(' ', StringSplitOptions.RemoveEmptyEntries);
            bool filtering = terms.Length > 0 || recentOnly;
            long now = Environment.TickCount64;

            bool Passes(SoundNode n)
            {
                if (!showAll && !n.Major) return false;
                if (terms.Length > 0 && !terms.All(t => n.Search.Contains(t))) return false;
                if (recentOnly && !n.Members.Any(m => VolumeConfig.LastHeard.TryGetValue(m.Key, out long t) && now - t < RecentMs)) return false;
                return true;
            }

            // Returns the rows for n and how many sounds they cover; empty if nothing under n passes.
            (List<Row>, int) Visit(SoundNode n, int depth)
            {
                if (!n.IsGroup) return Passes(n) ? (new List<Row> { new Row { Node = n, Depth = depth } }, 1) : (new List<Row>(), 0);

                var inner = new List<Row>();
                int leaves = 0;
                foreach (var c in n.Children)
                {
                    var (r, l) = Visit(c, depth + 1);
                    inner.AddRange(r);
                    leaves += l;
                }
                if (leaves == 0) return (inner, 0);

                // While searching, groups open by themselves so the matches are visible.
                bool open = filtering || openGroups.Contains(n.ConfigKey);
                var list = new List<Row> { new Row { Node = n, Depth = depth, Header = true, Open = open, Leaves = leaves } };
                if (open) list.AddRange(inner);
                return (list, leaves);
            }

            rows = new List<Row>();
            soundsShown = 0;
            foreach (var root in system.Tree)
            {
                var (r, leaves) = Visit(root, 0);
                rows.AddRange(r);
                soundsShown += leaves;
            }
            offset = Math.Clamp(offset, 0, Math.Max(0, rows.Count - RowCount));
        }

        void FillRows()
        {
            if (SingleComposer == null) return;

            var scroll = SingleComposer.GetScrollbar("scroll");
            scroll.SetHeights((float)(RowCount * RowHeight), (float)(Math.Max(rows.Count, RowCount) * RowHeight));
            scroll.CurrentYPosition = (float)(offset * RowHeight);

            for (int i = 0; i < RowCount; i++)
            {
                int idx = offset + i;
                bool has = idx < rows.Count;
                var row = has ? rows[idx] : null;

                SingleComposer.GetDynamicText("caret" + i).SetNewText(row == null || !row.Header ? "" : row.Open ? "v" : ">");
                string name = row == null ? "" : new string(' ', row.Depth * 4) + row.Node.Name + RowNote(row);
                SingleComposer.GetDynamicText("name" + i).SetNewText(name);

                var slider = SingleComposer.GetSlider("slider" + i);
                slider.SetValues(row == null ? 0 : VolumeConfig.Get(row.Node.ConfigKey), 0, VolumeConfig.Max, 1, "%");
                slider.Enabled = has;
            }
            SingleComposer.GetDynamicText("count").SetNewText(Lang.Get("volumesliders:count", soundsShown, system.Sounds.Count));
        }

        /// <summary>What follows a row's name: a group's size, and which mod changed a sound.</summary>
        static string RowNote(Row row)
        {
            if (row.Header)
            {
                string n = "  (" + row.Leaves + ")";
                return row.Node.ModdedCount > 0 ? n + "  [" + row.Node.ModdedCount + " changed by mods]" : n;
            }
            return row.Node.Note != null ? "  [" + row.Node.Note + "]" : "";
        }

        // ---------------------------------------------------------------- input

        void OnSearchChanged(string text)
        {
            search = text;
            offset = 0;
            BuildRows();
            FillRows();
        }

        void OnScroll(float y)
        {
            int newOffset = (int)Math.Round(y / RowHeight);
            if (newOffset == offset) return;
            offset = newOffset;
            FillRows();
        }

        bool OnSliderChanged(int row, int value)
        {
            int idx = offset + row;
            if (idx >= rows.Count) return true;

            var node = rows[idx].Node;
            VolumeConfig.Set(node.ConfigKey, value);
            var affected = new HashSet<string>(node.Members.Select(m => m.Key));
            SoundPatch.RefreshPlaying(affected.Contains);
            SaveSoon();
            return true;
        }

        bool PlayPreview(int row)
        {
            int idx = offset + row;
            var sound = idx < rows.Count ? rows[idx].Node.Preview : null;
            if (sound != null)
            {
                // Plays through the normal pipeline, so the slider values apply to the preview too.
                capi.World.PlaySoundAt(sound.Location, capi.World.Player.Entity, null, false, 16f, 1f);
            }
            return true;
        }

        bool OnResetShown()
        {
            var affected = new HashSet<string>();
            foreach (var r in rows)
            {
                foreach (string k in r.Node.ResetKeys()) VolumeConfig.Set(k, VolumeConfig.Max);
                foreach (var m in r.Node.Members) affected.Add(m.Key);
            }
            SoundPatch.RefreshPlaying(affected.Contains);
            SaveSoon();
            FillRows();
            return true;
        }

        /// <summary>Opens or closes the group shown on a row; rows that are single sounds ignore the click.</summary>
        void ToggleRow(int row)
        {
            int idx = offset + row;
            if (idx < 0 || idx >= rows.Count || !rows[idx].Header) return;

            string key = rows[idx].Node.ConfigKey;
            if (!openGroups.Remove(key)) openGroups.Add(key);
            BuildRows();
            FillRows();
        }

        public override void OnMouseWheel(MouseWheelEventArgs args)
        {
            // Same as clicks: the base class would mark the wheel handled before we saw it.
            if (!args.IsHandled && SingleComposer != null && listBounds != null && IsOpened()
                && listBounds.PointInside(capi.Input.MouseX, capi.Input.MouseY))
            {
                offset = Math.Clamp(offset - Math.Sign(args.deltaPrecise) * 2, 0, Math.Max(0, rows.Count - RowCount));
                FillRows();
                args.SetHandled();
                return;
            }
            base.OnMouseWheel(args);
        }

        long saveListener;

        /// <summary>Sliders fire on every step while dragging; write the file once the drag settles.</summary>
        void SaveSoon()
        {
            if (saveListener != 0) capi.Event.UnregisterCallback(saveListener);
            saveListener = capi.Event.RegisterCallback(_ =>
            {
                saveListener = 0;
                VolumeConfig.Save();
            }, 400);
        }

        public override void OnGuiClosed()
        {
            base.OnGuiClosed();
            VolumeConfig.Save();
        }
    }

    /// <summary>Text that can be changed with SetNewText and runs a callback when clicked.</summary>
    public class ClickableText : GuiElementDynamicText
    {
        readonly Action onClick;

        public ClickableText(ICoreClientAPI capi, CairoFont font, ElementBounds bounds, Action onClick) : base(capi, "", font, bounds)
        {
            this.onClick = onClick;
        }

        public override void OnMouseDownOnElement(ICoreClientAPI api, MouseEvent args)
        {
            base.OnMouseDownOnElement(api, args);
            if (args.Button == EnumMouseButton.Left) onClick();
        }
    }
}
