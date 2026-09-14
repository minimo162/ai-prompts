using System;
using System.Collections.Generic;
using System.Text;
using PadClipboard;

public static class PadClipboardLeaseTests {
    sealed class Fake : IClipboard {
        public bool locked, busy, unsupported, changeDuringRead, failWrite, failReadAll, failReadText, partialWrite;
        public uint seq = 1;
        public int writes, closes, blockedWriters;
        public Dictionary<uint, byte[]> data = new Dictionary<uint, byte[]> {
            {13, Encoding.Unicode.GetBytes("original\0")}, {0xC001, new byte[] {1,2,3}}
        };
        public bool Open() { if(busy || locked) return false; locked=true; return true; }
        public void Close() { Check(locked); locked=false; closes++; }
        public uint Sequence { get { Check(locked); return seq; } }
        public Dictionary<uint, byte[]> ReadAll() {
            Check(locked);
            if(failReadAll) throw new InvalidOperationException("capture read failed");
            if(unsupported) throw new InvalidOperationException("unsupported");
            var copy = new Dictionary<uint, byte[]>();
            foreach(var item in data) copy.Add(item.Key, (byte[])item.Value.Clone());
            return copy;
        }
        public string ReadText() {
            Check(locked);
            if(failReadText) throw new InvalidOperationException("text read failed");
            if(changeDuringRead) seq++;
            return Encoding.Unicode.GetString(data[13]).TrimEnd('\0');
        }
        public bool ExternalWrite() {
            if(locked) {blockedWriters++; return false;}
            data = new Dictionary<uint, byte[]> {{13,Encoding.Unicode.GetBytes("newer\0")}};
            seq++; return true;
        }
        public void Write(Dictionary<uint, byte[]> values) {
            Check(locked);
            // Attempt a competing writer at exactly the old check/write gap.
            Check(!ExternalWrite());
            if(partialWrite) { data.Clear(); writes++; throw new InvalidOperationException("partial write failed"); }
            if(failWrite) throw new InvalidOperationException("write failed");
            data = new Dictionary<uint, byte[]>(values); writes++; seq++;
        }
    }
    static void Check(bool value) { if(!value) throw new Exception("Assertion failed"); }
    static void Reject(Action action) {
        bool rejected=false;
        try { action(); } catch(InvalidOperationException) { rejected=true; }
        Check(rejected);
    }
    public static int RunFailurePaths() {
        var a=new Fake(); a.failReadAll=true;
        Reject(()=>Lease.Begin(a,"paste")); Check(!a.locked && a.writes==0 && a.data.Count==2);
        a=new Fake(); var lease=Lease.Begin(a,"paste"); a.failReadText=true;
        Reject(()=>lease.Restore()); Check(!a.locked && a.writes==1);
        a=new Fake(); lease=Lease.Begin(a,"paste"); a.partialWrite=true;
        Reject(()=>lease.Restore()); Check(!a.locked && a.writes==2 && a.data.Count==0);
        Reject(()=>lease.Restore()); Check(a.writes==2);
        // Standard-format classification uses no native call. Registered format
        // names are reviewed in source, not queried from the OS in this test.
        var supported=typeof(NativeClipboard).GetMethod("Supported",System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static);
        foreach(uint id in new uint[]{1,4,5,6,7,8,10,11,12,13,15,16,17}) Check((bool)supported.Invoke(null,new object[]{id}));
        foreach(uint id in new uint[]{0,2,3,9,14,0x80,0x81,0x200,0x300}) Check(!(bool)supported.Invoke(null,new object[]{id}));
        return 4;
    }
    public static int Run() {
        var a=new Fake(); var lease=Lease.Begin(a,"paste");
        Check(lease.Restore()=="restored_supported_native_formats");
        Check(a.data.Count==2 && a.data[0xC001][2]==3 && a.writes==2 && a.blockedWriters==2 && !a.locked);
        Reject(()=>lease.Restore()); Check(a.writes==2);

        a=new Fake(); lease=Lease.Begin(a,"paste"); Check(a.ExternalWrite());
        Check(lease.Restore()=="newer_clipboard_preserved" && a.writes==1 && !a.locked);

        a=new Fake(); lease=Lease.Begin(a,"paste"); a.changeDuringRead=true;
        Check(lease.Restore()=="newer_clipboard_preserved" && a.writes==1 && !a.locked);

        a=new Fake(); lease=Lease.Begin(a,"paste");
        a.data[13]=Encoding.Unicode.GetBytes("different\0");
        Check(lease.Restore()=="newer_clipboard_preserved" && a.writes==1);

        a=new Fake(); a.unsupported=true; Reject(()=>Lease.Begin(a,"paste"));
        Check(a.writes==0 && !a.locked && a.data.Count==2);

        a=new Fake(); a.busy=true; Reject(()=>Lease.Begin(a,"paste")); Check(a.writes==0);
        a=new Fake(); lease=Lease.Begin(a,"paste"); a.busy=true;
        Reject(()=>lease.Restore()); Check(a.writes==1); Reject(()=>lease.Restore());

        a=new Fake(); lease=Lease.Begin(a,"paste"); a.failWrite=true;
        Reject(()=>lease.Restore()); Check(!a.locked); Reject(()=>lease.Restore());

        a=new Fake(); a.data.Clear(); lease=Lease.Begin(a,"paste");
        Check(lease.Restore()=="restored_supported_native_formats" && a.data.Count==0);
        return 10;
    }
}
