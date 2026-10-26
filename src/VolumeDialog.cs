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
    /// Searchable list of per-sound sliders in the standard dialog style. Only RowCount rows exist; scrolling
    /// re-points them at a different slice of the filtered list, so 700+ sounds cost no more than 12.
    /// </summary>
    public class VolumeDialog : GuiDialog
    {
        const int RowCount = 12;
        const double RowHeight = 34;
        const double Width = 700;
        const long RecentMs = 30_000;

        readonly VolumeSlidersSystem system;
        List<SoundEntry> filtered = new List<SoundEntry>();
        string search = "";
        bool recentOnly;
        bool showAll;
        int offset;

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

        /// <summary>Re-reads values after the config or sound list changed underneath an open dialog.</summary>
        public void Refresh()
        {
            if (IsOpened()) { ApplyFilter(); FillRows(); }
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
            ElementBounds scrollBounds = ElementBounds.Fixed(Width - 10, listTop, 20, RowCount * RowHeight);

            var comp = capi.Gui.CreateCompo("volumesliders", dialogBounds)
                .AddShadedDialogBG(bgBounds)
                .AddDialogTitleBar(Lang.Get("volumesliders:title"), () => TryClose())
                .BeginChildElements(bgBounds)
                    .AddStaticText(Lang.Get("volumesliders:search"), CairoFont.WhiteSmallText(), searchLabel)
                    .AddTextInput(searchInput, OnSearchChanged, CairoFont.TextInput(), "search")
                    .AddStaticText(Lang.Get("volumesliders:recent"), CairoFont.WhiteSmallText(), recentLabel)
                    .AddSwitch(on => { recentOnly = on; offset = 0; ApplyFilter(); FillRows(); }, recentSwitch, "recent")
                    .AddStaticText(Lang.Get("volumesliders:all-sounds"), CairoFont.WhiteSmallText(), allLabel)
                    .AddSwitch(on => { showAll = on; offset = 0; ApplyFilter(); FillRows(); }, allSwitch, "all")
                    .AddInset(listArea.ForkBoundingParent(2, 2, 2, 2), 4);

            for (int i = 0; i < RowCount; i++)
            {
                double y = listTop + i * RowHeight;
                int row = i;
                comp.AddDynamicText("", CairoFont.WhiteSmallText(), ElementBounds.Fixed(8, y + 7, 360, 24), "name" + i)
                    .AddSlider(v => OnSliderChanged(row, v), ElementBounds.Fixed(375, y + 4, 215, 26), "slider" + i)
                    .AddSmallButton("▶", () => PlayPreview(row), ElementBounds.Fixed(600, y + 3, 40, 28), EnumButtonStyle.Normal, "play" + i);
            }

            comp.AddVerticalScrollbar(OnScroll, scrollBounds, "scroll")
                .AddSmallButton(Lang.Get("volumesliders:reset-shown"), OnResetShown, ElementBounds.Fixed(0, listTop + RowCount * RowHeight + 12, 160, 30), EnumButtonStyle.Normal)
                .AddDynamicText("", CairoFont.WhiteDetailText(), ElementBounds.Fixed(180, listTop + RowCount * RowHeight + 18, 460, 24), "count")
                .EndChildElements();

            SingleComposer = comp.Compose();
            SingleComposer.GetTextInput("search").SetValue(search);
            SingleComposer.GetSwitch("recent").SetValue(recentOnly);
            SingleComposer.GetSwitch("all").SetValue(showAll);
            ApplyFilter();
            FillRows();
        }

        void ApplyFilter()
        {
            string[] terms = search.ToLowerInvariant().Split(' ', StringSplitOptions.RemoveEmptyEntries);
            IEnumerable<SoundEntry> q = showAll ? system.Sounds : system.Sounds.Where(s => s.Major);
            if (terms.Length > 0) q = q.Where(s => terms.All(t => s.Search.Contains(t)));

            if (recentOnly)
            {
                long now = Environment.TickCount64;
                q = q.Where(s => VolumeConfig.LastHeard.TryGetValue(s.Key, out long t) && now - t < RecentMs)
                     .OrderByDescending(s => VolumeConfig.LastHeard[s.Key]);
            }
            filtered = q.ToList();
            offset = Math.Clamp(offset, 0, Math.Max(0, filtered.Count - RowCount));
        }

        void FillRows()
        {
            if (SingleComposer == null) return;

            var scroll = SingleComposer.GetScrollbar("scroll");
            scroll.SetHeights((float)(RowCount * RowHeight), (float)(Math.Max(filtered.Count, RowCount) * RowHeight));
            scroll.CurrentYPosition = (float)(offset * RowHeight);

            for (int i = 0; i < RowCount; i++)
            {
                int idx = offset + i;
                bool has = idx < filtered.Count;
                SingleComposer.GetDynamicText("name" + i).SetNewText(has ? filtered[idx].Display : "");
                var slider = SingleComposer.GetSlider("slider" + i);
                slider.SetValues(has ? VolumeConfig.Get(filtered[idx].Key) : 0, 0, VolumeConfig.Max, 1, "%");
                slider.Enabled = has;
            }
            SingleComposer.GetDynamicText("count").SetNewText(Lang.Get("volumesliders:count", filtered.Count, system.Sounds.Count));
        }

        void OnSearchChanged(string text)
        {
            search = text;
            offset = 0;
            ApplyFilter();
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
            if (idx >= filtered.Count) return true;
            string key = filtered[idx].Key;
            VolumeConfig.Set(key, value);
            SoundPatch.RefreshPlaying(k => k == key);
            SaveSoon();
            return true;
        }

        bool PlayPreview(int row)
        {
            int idx = offset + row;
            if (idx < filtered.Count)
            {
                // Plays through the normal pipeline, so the slider value applies to the preview too.
                capi.World.PlaySoundAt(filtered[idx].Location, capi.World.Player.Entity, null, false, 16f, 1f);
            }
            return true;
        }

        bool OnResetShown()
        {
            foreach (var s in filtered) VolumeConfig.Set(s.Key, VolumeConfig.Max);
            var shown = new HashSet<string>(filtered.Select(s => s.Key));
            SoundPatch.RefreshPlaying(shown.Contains);
            SaveSoon();
            FillRows();
            return true;
        }

        long saveListener;

        /// <summary>Sliders fire on every step while dragging; write the file once the drag settles.</summary>
        void SaveSoon()
        {
            if (saveListener != 0) capi.Event.UnregisterCallback(saveListener);
            saveListener = capi.Event.RegisterCallback(_ =>
            {
                saveListener = 0;
                VolumeConfig.Save(system.Sounds.Select(s => s.Key));
            }, 400);
        }

        public override void OnMouseWheel(MouseWheelEventArgs args)
        {
            base.OnMouseWheel(args);
            if (args.IsHandled || SingleComposer == null) return;
            offset = Math.Clamp(offset - Math.Sign(args.deltaPrecise) * 2, 0, Math.Max(0, filtered.Count - RowCount));
            FillRows();
            args.SetHandled();
        }

        public override void OnGuiClosed()
        {
            base.OnGuiClosed();
            VolumeConfig.Save(system.Sounds.Select(s => s.Key));
        }
    }
}
