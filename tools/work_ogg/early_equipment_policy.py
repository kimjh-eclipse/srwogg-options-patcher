"""Independent chapter-three native machines and two equippable weapons."""
FLAG=(59,7)
UNITS=[(1222,'빌트팔켄 타입 L'),(1052,'아슈세이버'),(1209,'휴케바인 Mk-3 타입 R')]
WEAPONS=[(3510,'그라비톤 런처'),(3500,'G 임팩트 스테이크')]
STORY_ALLOCATION=0x1adc0000

def script(blob):
 from story_scripts_25 import rebuild_logo,records,command,NONE
 from campaign_bonus_scripts import insert_commands
 point=next(i for i,r in enumerate(records(blob)) if r[0]==0x93 and r[2:5]==[0x100c1,63,7])
 lines=[('카이','빌트팔켄 L, 아슈세이버, 휴케바인 Mk-3 R을 한 기씩 지급한다. 기체만이다.'),
        ('카이','그라비톤 런처와 G 임팩트 스테이크도 하나씩 준비했다. 편성과 환장 때 활용해라.')]
 out,note=rebuild_logo(blob,point,lines,{'카이':1090},FLAG)
 stop=next(i for i,r in enumerate(records(out)) if r[0]==0xba and r[2:5]==[0x100c1,*FLAG])
 grants=[command(0x5f,key,NONE,NONE,NONE) for key,name in UNITS]+[command(0x64,key,0) for key,name in WEAPONS]
 return insert_commands(out,stop,grants),note
