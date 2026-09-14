using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;

namespace PadClipboard {
    // The same open interval MUST cover the check and every write. The test
    // backend models exclusion without accessing the native clipboard.
    public interface IClipboard {
        bool Open();
        void Close();
        uint Sequence { get; }
        Dictionary<uint, byte[]> ReadAll();
        string ReadText();
        void Write(Dictionary<uint, byte[]> formats);
    }

    public sealed class Lease {
        readonly IClipboard clipboard;
        readonly Dictionary<uint, byte[]> snapshot;
        readonly string text;
        readonly uint sequence;
        bool finished;
        Lease(IClipboard clipboard, Dictionary<uint, byte[]> snapshot, string text, uint sequence) {
            this.clipboard = clipboard; this.snapshot = snapshot;
            this.text = text; this.sequence = sequence;
        }
        public static Lease Begin(IClipboard clipboard, string text) {
            if (text == null || text.IndexOf('\0') >= 0) throw new ArgumentException("Invalid clipboard text");
            if (!clipboard.Open()) throw new InvalidOperationException("PAD_CLIPBOARD: busy; paste not started");
            try {
                uint before = clipboard.Sequence;
                var snapshot = clipboard.ReadAll(); // Unsupported format fails BEFORE mutation.
                if (clipboard.Sequence != before) throw new InvalidOperationException("PAD_CLIPBOARD: changed during capture");
                var replacement = new Dictionary<uint, byte[]> { { 13, Encoding.Unicode.GetBytes(text + "\0") } };
                try { clipboard.Write(replacement); }
                catch {
                    // Still exclusively open: no newer writer can be overwritten.
                    clipboard.Write(snapshot);
                    throw;
                }
                return new Lease(clipboard, snapshot, text, clipboard.Sequence);
            } finally { clipboard.Close(); }
        }
        public string Restore() {
            if (finished) throw new InvalidOperationException("PAD_CLIPBOARD: lease already finalized");
            finished = true; // Never retry a potentially partial mutation.
            if (!clipboard.Open()) throw new InvalidOperationException("PAD_CLIPBOARD: busy; restoration not performed");
            try {
                if (clipboard.Sequence != sequence) return "newer_clipboard_preserved";
                if (!String.Equals(clipboard.ReadText(), text, StringComparison.Ordinal) || clipboard.Sequence != sequence)
                    return "newer_clipboard_preserved";
                clipboard.Write(snapshot); // No Close/Open, OLE or managed Clipboard call in between.
                return "restored_supported_native_formats";
            } finally { clipboard.Close(); }
        }
    }

    public sealed class NativeClipboard : IClipboard, IDisposable {
        readonly NativeWindow owner = new NativeWindow();
        bool opened;
        public NativeClipboard() {
            // Own hidden HWND, never borrow a PAD or other process's window.
            owner.CreateHandle(new CreateParams());
        }
        public bool Open() {
            if (opened) throw new InvalidOperationException("Already open");
            opened = OpenClipboard(owner.Handle);
            return opened;
        }
        public void Close() {
            if (!opened) return;
            if (!CloseClipboard()) throw new Win32Exception();
            opened = false;
        }
        public uint Sequence { get { RequireOpen(); return GetClipboardSequenceNumber(); } }
        void RequireOpen() { if (!opened) throw new InvalidOperationException("Clipboard lock required"); }
        static bool Supported(uint id) {
            // GDI/metafile, owner-display and private handle formats have other
            // ownership rules. Reject the whole capture rather than drop them.
            if (id >= 0xC000) {
                // OLE/private formats may embed live pointers even in HGLOBAL.
                // Only known, self-contained registered text formats are safe.
                var name = new StringBuilder(256);
                if (GetClipboardFormatName(id, name, name.Capacity) == 0) return false;
                string value = name.ToString();
                return value == "HTML Format" || value == "Rich Text Format" ||
                    value == "Rich Text Format Without Objects" || value == "CSV";
            }
            return id == 1 || (id >= 4 && id <= 8) || (id >= 10 && id <= 13) ||
                (id >= 15 && id <= 17);
        }
        byte[] ReadBytes(uint id) {
            IntPtr handle = GetClipboardData(id);
            if (handle == IntPtr.Zero) throw new InvalidOperationException("PAD_CLIPBOARD: unreadable format");
            ulong size = GlobalSize(handle).ToUInt64();
            if (size == 0 || size > Int32.MaxValue) throw new InvalidOperationException("PAD_CLIPBOARD: unsupported format storage");
            IntPtr address = GlobalLock(handle);
            if (address == IntPtr.Zero) throw new Win32Exception();
            try { var bytes = new byte[(int)size]; Marshal.Copy(address, bytes, 0, bytes.Length); return bytes; }
            finally { GlobalUnlock(handle); }
        }
        public Dictionary<uint, byte[]> ReadAll() {
            RequireOpen();
            var result = new Dictionary<uint, byte[]>();
            uint id = 0;
            while (true) {
                SetLastError(0);
                id = EnumClipboardFormats(id);
                if (id == 0) {
                    if (Marshal.GetLastWin32Error() != 0) throw new Win32Exception();
                    break;
                }
                if (!Supported(id)) throw new InvalidOperationException("PAD_CLIPBOARD: unsupported native format; paste refused");
                result.Add(id, ReadBytes(id));
            }
            return result;
        }
        public string ReadText() {
            RequireOpen();
            var bytes = ReadBytes(13);
            if (bytes.Length % 2 != 0) throw new InvalidOperationException("Invalid Unicode clipboard data");
            int end = 0;
            while (end + 1 < bytes.Length && (bytes[end] != 0 || bytes[end + 1] != 0)) end += 2;
            if (end == bytes.Length) throw new InvalidOperationException("Unterminated Unicode clipboard data");
            return Encoding.Unicode.GetString(bytes, 0, end);
        }
        public void Write(Dictionary<uint, byte[]> formats) {
            RequireOpen();
            var handles = new Dictionary<uint, IntPtr>();
            try {
                // Allocate every format before emptying the clipboard.
                foreach (var item in formats) {
                    IntPtr handle = GlobalAlloc(0x42, new UIntPtr((uint)item.Value.Length));
                    if (handle == IntPtr.Zero) throw new OutOfMemoryException();
                    handles.Add(item.Key, handle);
                    IntPtr address = GlobalLock(handle);
                    if (address == IntPtr.Zero) throw new Win32Exception();
                    try { Marshal.Copy(item.Value, 0, address, item.Value.Length); }
                    finally { GlobalUnlock(handle); }
                }
                if (!EmptyClipboard()) throw new Win32Exception();
                foreach (var id in new List<uint>(handles.Keys)) {
                    if (SetClipboardData(id, handles[id]) == IntPtr.Zero) throw new Win32Exception();
                    handles[id] = IntPtr.Zero; // Windows now owns it.
                }
            } finally {
                foreach (var handle in handles.Values) if (handle != IntPtr.Zero) GlobalFree(handle);
            }
        }
        public void Dispose() { Close(); owner.DestroyHandle(); }
        [DllImport("user32.dll", SetLastError=true)] static extern bool OpenClipboard(IntPtr hwnd);
        [DllImport("user32.dll", SetLastError=true)] static extern bool CloseClipboard();
        [DllImport("user32.dll")] static extern uint GetClipboardSequenceNumber();
        [DllImport("user32.dll", SetLastError=true)] static extern uint EnumClipboardFormats(uint format);
        [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern int GetClipboardFormatName(uint format, StringBuilder name, int capacity);
        [DllImport("user32.dll", SetLastError=true)] static extern IntPtr GetClipboardData(uint format);
        [DllImport("user32.dll", SetLastError=true)] static extern bool EmptyClipboard();
        [DllImport("user32.dll", SetLastError=true)] static extern IntPtr SetClipboardData(uint format, IntPtr handle);
        [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr GlobalAlloc(uint flags, UIntPtr bytes);
        [DllImport("kernel32.dll", SetLastError=true)] static extern UIntPtr GlobalSize(IntPtr handle);
        [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr GlobalLock(IntPtr handle);
        [DllImport("kernel32.dll")] static extern bool GlobalUnlock(IntPtr handle);
        [DllImport("kernel32.dll")] static extern IntPtr GlobalFree(IntPtr handle);
        [DllImport("kernel32.dll")] static extern void SetLastError(uint error);
    }
}
