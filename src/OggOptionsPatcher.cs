using System;
using System.IO;
using System.IO.Compression;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Text;
using System.Drawing;
using System.Threading;
using System.Windows.Forms;

internal static class OggOptionsPatcher
{
    const string ExpectedPackSha = "__PACK_SHA__";
    const string Version = "v20261107.1";
    sealed class Region { public long Offset; public byte[] Original, Zero; }
    sealed class Edit { public long Offset; public byte[] Data; }
    sealed class Pack {
        public long Size; public byte[] SourceHash; public string[] Names, Descriptions;
        public List<Region> Regions = new List<Region>();
        public List<Edit>[] Features; public byte[][] Profiles;
        public Dictionary<string,int> Known = new Dictionary<string,int>();
    }
    sealed class Inspection { public byte[][] Actual; public string ActualHash, Signature; public int Mask; }
    static string Hex(byte[] b) { return BitConverter.ToString(b).Replace("-", "").ToLowerInvariant(); }
    static byte[] Sha(byte[] b) { using (SHA256 h=SHA256.Create()) return h.ComputeHash(b); }
    static byte[] ReadExact(BinaryReader r,int n) { byte[] b=r.ReadBytes(n); if(b.Length!=n) throw new InvalidDataException("파일이 잘렸습니다."); return b; }
    static byte[] Blob(BinaryReader r) { int n=r.ReadInt32(); if(n<0 || n>256*1024*1024) throw new InvalidDataException("패치 데이터 크기 오류"); return ReadExact(r,n); }
    static byte[] Inflate(byte[] z,int length) {
        using(MemoryStream input=new MemoryStream(z)) using(DeflateStream d=new DeflateStream(input,CompressionMode.Decompress)) {
            byte[] b=new byte[length]; int p=0,n; while(p<length && (n=d.Read(b,p,length-p))>0) p+=n;
            if(p!=length || d.ReadByte()!=-1) throw new InvalidDataException("압축 데이터가 손상되었습니다."); return b;
        }
    }
    static byte[] Deflate(byte[] b) { using(MemoryStream m=new MemoryStream()) { using(DeflateStream d=new DeflateStream(m,CompressionMode.Compress,true)) d.Write(b,0,b.Length); return m.ToArray(); } }
    static Pack Load() {
        string path=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"OGG_options.bin");
        byte[] raw=File.ReadAllBytes(path); if(Hex(Sha(raw))!=ExpectedPackSha) throw new InvalidDataException("OGG_options.bin의 검증값이 다릅니다. 같은 ZIP의 파일들을 함께 사용해 주세요.");
        Pack p=new Pack(); using(BinaryReader r=new BinaryReader(new MemoryStream(raw),Encoding.UTF8)) {
            if(Encoding.ASCII.GetString(ReadExact(r,8))!="OGGOPT01" || r.ReadInt32()!=1) throw new InvalidDataException("패치 형식 오류");
            p.Size=r.ReadInt64(); p.SourceHash=ReadExact(r,32); int count=r.ReadInt32(); if(count!=11) throw new InvalidDataException("옵션 수 오류");
            p.Names=new string[count]; p.Descriptions=new string[count]; p.Features=new List<Edit>[count];
            for(int i=0;i<count;i++) { p.Names[i]=Encoding.UTF8.GetString(Blob(r)); p.Descriptions[i]=Encoding.UTF8.GetString(Blob(r)); }
            int regions=r.ReadInt32(); if(regions<1 || regions>100000) throw new InvalidDataException("구간 수 오류"); long end=0;
            for(int i=0;i<regions;i++) { long at=r.ReadInt64(); int n=r.ReadInt32(); if(at<end || n<1 || at>p.Size-n) throw new InvalidDataException("구간 범위 오류");
                Region x=new Region { Offset=at, Original=Inflate(Blob(r),n), Zero=Inflate(Blob(r),n) }; p.Regions.Add(x); end=at+n; }
            for(int i=0;i<count;i++) { p.Features[i]=new List<Edit>(); int n=r.ReadInt32(); if(n<0 || n>100000) throw new InvalidDataException("옵션 구간 오류");
                for(int j=0;j<n;j++) { long at=r.ReadInt64(); int length=r.ReadInt32(); if(length<1 || length>p.Size || at<0 || at>p.Size-length) throw new InvalidDataException("옵션 범위 오류"); p.Features[i].Add(new Edit { Offset=at, Data=ReadExact(r,length) }); } }
            int profiles=r.ReadInt32(); if(profiles!=(1<<count)) throw new InvalidDataException("조합 수 오류"); p.Profiles=new byte[profiles][];
            for(int i=0;i<profiles;i++) { if(r.ReadInt32()!=i) throw new InvalidDataException("조합 순서 오류"); p.Profiles[i]=ReadExact(r,32); p.Known.Add(Hex(p.Profiles[i]),i); }
            p.Known[Hex(ReadExact(r,32))]=-1; int legacy=r.ReadInt32(); if(legacy<0 || legacy>4096) throw new InvalidDataException("이전 버전 오류");
            for(int i=0;i<legacy;i++) { string key=Hex(ReadExact(r,32)); int mask=r.ReadInt32(); p.Known[key]=mask; }
            if(r.BaseStream.Position!=r.BaseStream.Length) throw new InvalidDataException("패치 뒤에 잉여 데이터가 있습니다.");
        } return p;
    }
    static int Find(Pack p,long offset,int length) {
        int lo=0,hi=p.Regions.Count-1;
        while(lo<=hi) { int m=(lo+hi)/2; Region r=p.Regions[m]; if(offset<r.Offset) hi=m-1; else if(offset>=r.Offset+r.Zero.Length) lo=m+1; else { if(offset-r.Offset+length>r.Zero.Length) break; return m; } }
        throw new InvalidDataException("옵션이 관리 구간을 벗어났습니다.");
    }
    static byte[][] Compose(Pack p,int mask) {
        if(mask<0 || mask>=p.Profiles.Length) throw new ArgumentOutOfRangeException("mask"); byte[][] data=new byte[p.Regions.Count][];
        for(int i=0;i<data.Length;i++) data[i]=p.Regions[i].Zero;
        for(int bit=0;bit<p.Features.Length;bit++) if((mask&(1<<bit))!=0) foreach(Edit e in p.Features[bit]) { int i=Find(p,e.Offset,e.Data.Length);
            if(Object.ReferenceEquals(data[i],p.Regions[i].Zero)) data[i]=(byte[])data[i].Clone(); Buffer.BlockCopy(e.Data,0,data[i],(int)(e.Offset-p.Regions[i].Offset),e.Data.Length); }
        return data;
    }
    static string Fingerprint(Pack p,byte[][] data) {
        using(MemoryStream m=new MemoryStream()) { using(BinaryWriter w=new BinaryWriter(m,Encoding.UTF8,true)) for(int i=0;i<data.Length;i++) { w.Write(p.Regions[i].Offset); w.Write(data[i].Length); w.Write(Sha(data[i])); } return Hex(Sha(m.ToArray())); }
    }
    static bool Equal(byte[] a,byte[] b) { if(a.Length!=b.Length) return false; for(int i=0;i<a.Length;i++) if(a[i]!=b[i]) return false; return true; }
    static void Update(HashAlgorithm h,byte[] b,int n) { h.TransformBlock(b,0,n,b,0); }
    static byte[] ReadAt(FileStream f,long offset,int length) { f.Position=offset; byte[] b=new byte[length]; int p=0,n; while(p<length && (n=f.Read(b,p,length-p))>0) p+=n; if(p!=length) throw new EndOfStreamException(); return b; }
    static Inspection Inspect(Pack p,FileStream f,bool allowPartial,Action<string> log) {
        if(f.Length!=p.Size) throw new InvalidDataException("지원되는 OG외전 한글판 ISO와 파일 크기가 다릅니다.");
        log("ISO 전체와 현재 옵션을 검사하고 있습니다..."); byte[][] data=new byte[p.Regions.Count][]; byte[] buffer=new byte[4<<20]; long pos=0;
        using(SHA256 normal=SHA256.Create()) using(SHA256 actual=SHA256.Create()) {
            for(int i=0;i<p.Regions.Count;i++) { Region r=p.Regions[i]; f.Position=pos;
                while(pos<r.Offset) { int n=f.Read(buffer,0,(int)Math.Min(buffer.Length,r.Offset-pos)); if(n==0) throw new EndOfStreamException(); Update(normal,buffer,n); Update(actual,buffer,n); pos+=n; }
                data[i]=ReadAt(f,r.Offset,r.Zero.Length); Update(normal,r.Original,r.Original.Length); Update(actual,data[i],data[i].Length); pos+=data[i].Length;
            }
            f.Position=pos; int got; while((got=f.Read(buffer,0,buffer.Length))>0) { Update(normal,buffer,got); Update(actual,buffer,got); }
            normal.TransformFinalBlock(new byte[0],0,0); actual.TransformFinalBlock(new byte[0],0,0);
            if(!Equal(normal.Hash,p.SourceHash)) throw new InvalidDataException("기준 한글판과 다른 ISO이거나, 관리 구간 밖이 수정된 파일입니다. ISO는 변경하지 않았습니다.");
            string signature=Fingerprint(p,data); int mask; if(!p.Known.TryGetValue(signature,out mask)) { if(!allowPartial) throw new InvalidDataException("지원되지 않는 수정 조합입니다. ISO는 변경하지 않았습니다."); mask=-2; }
            return new Inspection { Actual=data, ActualHash=Hex(actual.Hash), Signature=signature, Mask=mask };
        }
    }
    static byte[][] ReadManaged(Pack p,FileStream f) { byte[][] data=new byte[p.Regions.Count][]; for(int i=0;i<data.Length;i++) data[i]=ReadAt(f,p.Regions[i].Offset,p.Regions[i].Zero.Length); return data; }
    static void WriteData(Pack p,FileStream f,byte[][] current,byte[][] desired) {
        for(int i=0;i<desired.Length;i++) if(!Equal(current[i],desired[i])) { f.Position=p.Regions[i].Offset; f.Write(desired[i],0,desired[i].Length); } f.Flush(true);
    }
    static void SaveBackup(Pack p,string path,Inspection inspection) {
        if(File.Exists(path)) { LoadBackup(p,path); return; }
        using(MemoryStream m=new MemoryStream()) { using(BinaryWriter w=new BinaryWriter(m,Encoding.UTF8,true)) {
            w.Write(Encoding.ASCII.GetBytes("OGGBAK01")); w.Write(p.Size); w.Write(Encoding.ASCII.GetBytes(inspection.ActualHash)); w.Write(Encoding.ASCII.GetBytes(ExpectedPackSha)); w.Write(p.Regions.Count);
            for(int i=0;i<p.Regions.Count;i++) { w.Write(p.Regions[i].Offset); w.Write(inspection.Actual[i].Length); byte[] z=Deflate(inspection.Actual[i]); w.Write(z.Length); w.Write(z); }
        } byte[] b=m.ToArray(); using(FileStream f=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.None)) { f.Write(b,0,b.Length); byte[] hash=Sha(b); f.Write(hash,0,hash.Length); f.Flush(true); } }
    }
    sealed class Backup { public string Hash; public byte[][] Data; }
    static Backup LoadBackup(Pack p,string path) {
        byte[] all=File.ReadAllBytes(path); if(all.Length<32) throw new InvalidDataException("복원 기록이 손상되었습니다."); byte[] b=new byte[all.Length-32],hash=new byte[32]; Buffer.BlockCopy(all,0,b,0,b.Length); Buffer.BlockCopy(all,b.Length,hash,0,32);
        if(!Equal(Sha(b),hash)) throw new InvalidDataException("복원 기록의 검증값이 다릅니다.");
        using(BinaryReader r=new BinaryReader(new MemoryStream(b))) {
            if(Encoding.ASCII.GetString(ReadExact(r,8))!="OGGBAK01" || r.ReadInt64()!=p.Size) throw new InvalidDataException("복원 기록 형식 오류");
            string initial=Encoding.ASCII.GetString(ReadExact(r,64)); if(Encoding.ASCII.GetString(ReadExact(r,64))!=ExpectedPackSha || r.ReadInt32()!=p.Regions.Count) throw new InvalidDataException("다른 버전의 복원 기록입니다.");
            byte[][] data=new byte[p.Regions.Count][];
            for(int i=0;i<data.Length;i++) { if(r.ReadInt64()!=p.Regions[i].Offset || r.ReadInt32()!=p.Regions[i].Zero.Length) throw new InvalidDataException("복원 범위 오류"); data[i]=Inflate(Blob(r),p.Regions[i].Zero.Length); }
            if(r.BaseStream.Position!=r.BaseStream.Length) throw new InvalidDataException("복원 데이터 길이 오류"); return new Backup { Hash=initial, Data=data };
        }
    }
    static string Apply(Pack p,string path,int mask,bool restore,Action<string> log) {
        using(FileStream f=new FileStream(path,FileMode.Open,FileAccess.ReadWrite,FileShare.None,4<<20)) {
            Inspection input=Inspect(p,f,restore,log); byte[][] desired; string expected;
            if(restore) { Backup b=LoadBackup(p,path+"."+Version+".oggbak"); desired=b.Data; expected=b.Hash; } else { desired=Compose(p,mask); expected=null; SaveBackup(p,path+"."+Version+".oggbak",input); }
            try { log(restore?"처음 상태로 복원하고 있습니다...":"선택한 옵션을 적용하고 있습니다..."); WriteData(p,f,input.Actual,desired);
                Inspection after=Inspect(p,f,false,log); if(restore ? after.ActualHash!=expected : after.Signature!=Hex(p.Profiles[mask])) throw new InvalidDataException("쓰기 후 검증 실패");
                return after.ActualHash;
            } catch { WriteData(p,f,ReadManaged(p,f),input.Actual); throw; }
        }
    }
    static string SelfTest(Pack p) {
        for(int mask=0;mask<p.Profiles.Length;mask++) if(Fingerprint(p,Compose(p,mask))!=Hex(p.Profiles[mask])) throw new InvalidDataException("옵션 조합 검증 실패: "+mask);
        return "{\"passed\":true,\"profiles\":"+p.Profiles.Length+",\"checkboxes\":"+p.Names.Length+"}";
    }
    static string Exercise(Pack p,string path,Action<string> log) {
        string backup=path+"."+Version+".oggbak"; if(File.Exists(backup)) throw new IOException("검사용 경로에 기존 .oggbak이 있습니다. 덮어쓰지 않습니다.");
        string before,after; int transitions=0;
        using(FileStream f=new FileStream(path,FileMode.Open,FileAccess.ReadWrite,FileShare.None,4<<20)) {
            Inspection input=Inspect(p,f,false,log); before=input.ActualHash; SaveBackup(p,backup,input); byte[][] current=input.Actual;
            try {
                byte[][] official=new byte[p.Regions.Count][];for(int i=0;i<official.Length;i++) official[i]=p.Regions[i].Original;
                WriteData(p,f,current,official);current=ReadManaged(p,f);
                Inspection officialInput=Inspect(p,f,false,log);
                if(officialInput.Mask!=-1 || officialInput.ActualHash!=Hex(p.SourceHash)) throw new InvalidDataException("공식 베이스 입력 검증 실패");
                for(int i=0;i<p.Profiles.Length;i++) { int mask=i^(i>>1); byte[][] desired=Compose(p,mask); WriteData(p,f,current,desired); current=ReadManaged(p,f);
                    if(Fingerprint(p,current)!=Hex(p.Profiles[mask])) throw new InvalidDataException("실제 ISO 전환 검증 실패: "+mask); transitions++; if(i%16==0) log("실제 ISO 옵션 전환 검사: "+i+" / "+p.Profiles.Length); }
                // Exercise the exact sparse-backup read/restore path as well.
                Backup b=LoadBackup(p,backup); WriteData(p,f,current,b.Data); current=b.Data;
                Inspection final=Inspect(p,f,false,log); after=final.ActualHash; if(after!=before || after!=b.Hash) throw new InvalidDataException("검사 후 원상 복원 검증 실패");
            } finally { WriteData(p,f,ReadManaged(p,f),input.Actual); }
        }
        File.Delete(backup); return "{\"passed\":true,\"real_iso_transitions\":"+transitions+",\"official_base_input_verified\":true,\"backup_restore_verified\":true,\"canonical_sha256_before\":\""+before+"\",\"canonical_sha256_after\":\""+after+"\",\"extra_full_ISOs_created\":0}";
    }
    static void Log(string message) { Console.WriteLine(message); }
    static string ReportArgument(string[] args) { for(int i=0;i<args.Length-1;i++) if(args[i]=="--report") return args[i+1]; return null; }
    [STAThread] static int Main(string[] args) {
        try {
            Pack p=Load(); string result=null; string report=ReportArgument(args);
            if(args.Length==0) { Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false); Application.Run(new Window(p)); return 0; }
            if(args[0]=="--selftest") result=SelfTest(p);
            else if(args[0]=="--verify") { using(FileStream f=new FileStream(args[1],FileMode.Open,FileAccess.Read,FileShare.None)) { Inspection i=Inspect(p,f,false,Log); result="{\"passed\":true,\"mask\":"+i.Mask+",\"sha256\":\""+i.ActualHash+"\"}"; } }
            else if(args[0]=="--exercise") result=Exercise(p,args[1],Log);
            else if(args[0]=="--patch") { int mask=0; for(int i=2;i<args.Length-1;i++) if(args[i]=="--mask") mask=Int32.Parse(args[i+1]); result="{\"passed\":true,\"mask\":"+mask+",\"sha256\":\""+Apply(p,args[1],mask,false,Log)+"\"}"; }
            else if(args[0]=="--restore") result="{\"passed\":true,\"sha256\":\""+Apply(p,args[1],0,true,Log)+"\"}";
            else if(args[0]=="--preview") { Application.EnableVisualStyles(); using(Window w=new Window(p)) { w.ShowInTaskbar=false; w.Opacity=0; w.Show(); Application.DoEvents(); w.PerformLayout(); using(Bitmap b=new Bitmap(w.Width,w.Height)) { w.DrawToBitmap(b,new Rectangle(0,0,w.Width,w.Height)); b.Save(args[1]); } } result="{\"passed\":true}"; }
            else throw new ArgumentException("지원하지 않는 명령입니다.");
            if(report!=null) File.WriteAllText(report,result,Encoding.UTF8); Console.WriteLine(result); return 0;
        } catch(Exception e) { string report=ReportArgument(args); if(report!=null) File.WriteAllText(report,"{\"passed\":false,\"error\":\""+e.Message.Replace("\\","\\\\").Replace("\"","\\\"").Replace("\r"," ").Replace("\n"," ")+"\"}",Encoding.UTF8);
            if(args.Length==0) MessageBox.Show(e.Message,"OG외전 옵션 패처",MessageBoxButtons.OK,MessageBoxIcon.Error); else Console.Error.WriteLine(e); return 1; }
    }
    sealed class Window:Form {
        readonly Pack pack; readonly TextBox path=new TextBox(),messages=new TextBox(); readonly CheckBox[] checks=new CheckBox[11]; readonly ProgressBar progress=new ProgressBar(); readonly List<Control> actions=new List<Control>(); bool busy;
        public Window(Pack p) {
            pack=p; Text="슈퍼로봇대전 OG외전 옵션 패처 "+Version; Font=new Font("맑은 고딕",10); ClientSize=new Size(900,880); MinimumSize=new Size(800,820); StartPosition=FormStartPosition.CenterScreen;
            TableLayoutPanel main=new TableLayoutPanel { Dock=DockStyle.Fill,Padding=new Padding(16),ColumnCount=1,RowCount=5 };
            main.RowStyles.Add(new RowStyle(SizeType.Absolute,60));main.RowStyles.Add(new RowStyle(SizeType.Absolute,44));main.RowStyles.Add(new RowStyle(SizeType.Percent,100));main.RowStyles.Add(new RowStyle(SizeType.Absolute,86));main.RowStyles.Add(new RowStyle(SizeType.Absolute,48)); Controls.Add(main);
            Label intro=new Label { Dock=DockStyle.Fill,Text="필요한 옵션을 선택해 한글판 ISO에 적용하세요.\n25편성 시나리오는 새 게임에서 시작해 주세요. 다른 옵션은 재부팅 후 일반 세이브로 진행할 수 있습니다.",AutoSize=false }; main.Controls.Add(intro,0,0);
            TableLayoutPanel picker=new TableLayoutPanel { Dock=DockStyle.Fill,ColumnCount=2 };picker.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));picker.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,110));path.Dock=DockStyle.Fill;path.Margin=new Padding(0,5,8,5);picker.Controls.Add(path,0,0);
            Button choose=new Button { Text="ISO 선택",Dock=DockStyle.Fill };choose.Click+=delegate { using(OpenFileDialog d=new OpenFileDialog { Filter="PS2 ISO (*.iso)|*.iso",Title="패치할 OG외전 한글판 ISO를 선택하세요" }) if(d.ShowDialog()==DialogResult.OK) path.Text=d.FileName; };picker.Controls.Add(choose,1,0);main.Controls.Add(picker,0,1);actions.Add(choose);actions.Add(path);
            FlowLayoutPanel options=new FlowLayoutPanel { Dock=DockStyle.Fill,FlowDirection=FlowDirection.TopDown,WrapContents=false,AutoScroll=true,Padding=new Padding(0,4,0,0) };
            for(int i=0;i<checks.Length;i++) { Panel row=new Panel { Width=830,Height=50,Margin=new Padding(0,0,0,2) };CheckBox box=new CheckBox { Left=0,Top=0,Width=820,Height=26,Text=(i+1)+". "+p.Names[i] };checks[i]=box;row.Controls.Add(box);row.Controls.Add(new Label { Left=24,Top=27,Width=800,Height=20,ForeColor=Color.DimGray,Font=new Font("맑은 고딕",9),Text=p.Descriptions[i] });options.Controls.Add(row);actions.Add(box); } main.Controls.Add(options,0,2);
            messages.Dock=DockStyle.Fill;messages.Multiline=true;messages.ReadOnly=true;messages.ScrollBars=ScrollBars.Vertical;messages.Text="한글 표시 수정과 추가 파일럿 정신기 조정을 적용합니다. 옵션은 모두 꺼진 상태로 시작합니다.\r\n[검사]를 누르면 현재 ISO의 옵션이 표시됩니다. 선택 후 [패치 적용]을 눌러 주세요.";main.Controls.Add(messages,0,3);
            FlowLayoutPanel bar=new FlowLayoutPanel { Dock=DockStyle.Fill,FlowDirection=FlowDirection.LeftToRight,Padding=new Padding(0,8,0,0) };
            Button verify=new Button { Text="검사",Width=100,Height=30 },apply=new Button { Text="패치 적용",Width=130,Height=30 },restore=new Button { Text="처음 상태 복원",Width=150,Height=30 };
            verify.Click+=delegate { Start(0); };apply.Click+=delegate { Start(1); };restore.Click+=delegate { Start(2); };bar.Controls.AddRange(new Control[] {verify,apply,restore});actions.Add(verify);actions.Add(apply);actions.Add(restore);progress.Width=230;progress.Height=26;progress.Margin=new Padding(16,2,0,0);bar.Controls.Add(progress);main.Controls.Add(bar,0,4);
            FormClosing+=delegate(object sender,FormClosingEventArgs e) { if(busy) { e.Cancel=true; AddLog("작업이 완료된 뒤 종료해 주세요."); } };
        }
        void AddLog(string text) { if(InvokeRequired) { BeginInvoke(new Action<string>(AddLog),text); return; } messages.AppendText("\r\n"+text); }
        void Start(int mode) {
            string file=path.Text.Trim();if(!File.Exists(file)) { AddLog("먼저 ISO 파일을 선택해 주세요.");return; } int mask=0;for(int i=0;i<checks.Length;i++) if(checks[i].Checked) mask|=1<<i;
            busy=true;foreach(Control c in actions) c.Enabled=false;progress.Style=ProgressBarStyle.Marquee;
            new Thread(delegate() { int detected=-3;try { if(mode==0) { using(FileStream f=new FileStream(file,FileMode.Open,FileAccess.Read,FileShare.None)) { Inspection input=Inspect(pack,f,false,AddLog);detected=input.Mask;AddLog(input.Mask<0?"기준 한글판으로 확인되었습니다.":"현재 적용 옵션을 확인했습니다."); } }
                    else { string hash=Apply(pack,file,mask,mode==2,AddLog);AddLog((mode==2?"복원":"적용")+" 및 ISO 전체 검증을 완료했습니다.\r\nSHA-256: "+hash+"\r\nPCSX2에서 완전히 새로 부팅해 주세요."); }
                } catch(Exception e) { AddLog("완료하지 못했습니다: "+e.Message+"\r\n파일 사용 중 오류라면 PCSX2를 종료하고 다시 실행해 주세요."); }
                finally { BeginInvoke(new Action(delegate { if(detected>=-1) for(int i=0;i<checks.Length;i++) checks[i].Checked=detected>=0 && (detected&(1<<i))!=0;busy=false;foreach(Control c in actions) c.Enabled=true;progress.Style=ProgressBarStyle.Blocks; })); }
            }) { IsBackground=true }.Start();
        }
    }
}
