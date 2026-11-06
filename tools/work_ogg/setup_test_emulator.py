"""Prepare a separate portable PCSX2 directory; do not edit the user's setup."""
from pathlib import Path
import shutil,re
ROOT=Path(__file__).resolve().parent
src=Path('C:/Emul/Pcsx2-v1.7');dst=ROOT/'test_emulator'
dst.mkdir(exist_ok=True)
for p in src.iterdir():
 if p.is_file() and (p.suffix.lower()=='.dll' or p.name in ('pcsx2-qt.exe','qt.conf','portable.ini')):
  if not (dst/p.name).exists():shutil.copy2(p,dst/p.name)
for folder in ('QtPlugins','resources','translations'):
 shutil.copytree(src/folder,dst/folder,dirs_exist_ok=True)
(dst/'inis').mkdir(exist_ok=True)
ini=(src/'inis/PCSX2.ini').read_text(encoding='utf-8-sig')
for key,value in {'Bios':str(src/'bios'),'EnableCheats':'false','EnablePINE':'true','Slot':'28012','EnableWideScreenPatches':'false','EnableNoInterlacingPatches':'false','StartFullscreen':'false','ConfirmShutdown':'false','Enable':'false'}.items():
 if key=='Enable':continue
 if key=='Slot':continue
 ini=re.sub(r'^'+re.escape(key)+r'\s*=.*$',key+' = '+value.replace('\\','/'),ini,flags=re.M)
ini=re.sub(r'^PINESlot\s*=.*$','PINESlot = 28012',ini,flags=re.M)
ini=re.sub(r'\[PINE\][\s\S]*?(?=\n\[|\Z)','[PINE]\nEnabled = true\nSlot = 28012\n',ini)
if '[PINE]' not in ini:ini+='\n[PINE]\nEnabled = true\nSlot = 28012\n'
for key in ['Slot1_Enable','Slot2_Enable']:ini=re.sub(r'^'+key+r'\s*=.*$',key+' = false',ini,flags=re.M)
(dst/'inis/PCSX2.ini').write_text(ini,encoding='utf-8')
print(dst/'pcsx2-qt.exe')
