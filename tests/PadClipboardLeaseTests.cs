using System;
using System.Collections.Generic;
using System.Text;
using PadClipboard;

public static class PadClipboardLeaseTests {
    sealed class Fake : IClipboard {
        public bool locked, busy, unsupported, changeDuringRead, failWrite;
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
            if(unsupported) throw new InvalidOperationException("unsupported");
            var copy = new Dictionary<uint, byte[]>();
            foreach(var item in data) copy.Add(item.Key, (byte[])item.Value.Clone());
            return copy;
        }
        public string ReadText() {
            Check(locked);
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
