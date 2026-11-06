"""Original dialogue bridges; native plot outcomes and recruitment stay intact."""

# Locate existing boxes by speaker and a short normalized fragment. Keep the
# sister scene: Eccellen is not Lemon's actual sibling in this world.
REPLACEMENTS={
 3:[('카이','시험장 밖','실제 구조 신호다. 기지 밖 기체, 응답하라.'),
    ('린','그쪽의 나를','그쪽의 나는 살아 있군. 그 사람의 삶을 대신할 생각은 없어.')],
 4:[('카이','이 교도대','구조 신호는…… 카와이 대령님?')],
 8:[('레첼','소피아 박사는','소피아 박사의 생존은 확인했다. 신원 대조 뒤 직접 만나게 하지.'),
    ('가루인','이번에는','통신 들리나…… 내 뜻으로 출격한다.')],
 19:[('라투니','이 반응','통신의 기체…… 언니야?')],
 20:[('비안','자네들이 지켜','이곳의 나는 죽었다 들었네. 자네들이 지킨 미래를 보았군.'),
     ('비안','내가 맡긴 미래','총수로 돌아올 생각은 없네. 지금의 지휘를 따르지.')],
 21:[('잉그램','마지막에 자아','내 세계에서 자아를 되찾았다. 기체는 이미 붕괴하고 있었다.')],
 23:[('류네','아버지……','화면 속 아버지…… 정말?')],
 24:[('레몬','네 장비를','출격 장비를 또 확인했어. 널 잃을까 겁이 나서.'),
     ('액셀렌','내 삶과','걱정은 받을게. 그래도 어디서 싸울지는 내가 고르게 해 줘.')],
 28:[('레몬','이제 명령부터','라미아 구출을 방해하지 마. 네 지휘를 받으러 모인 게 아니야.'),
     ('길리엄','XN 전이부','XN 전이부는 격리한다. 구출 작전의 지휘는 쿄스케와 액셀에게 맡긴다.'),
     ('액셀렌','그럼 교대 엄호','라미아의 퇴로를 지키자. 언니도 혼자 앞서지 않기!'),
     ('에키드나','보호 명령','대위. 이번에는 내 뜻으로 W17의 퇴로를 지키겠다.')],
 29:[('액셀렌','이 싸움이 끝나면','폴카의 대결을 지켜 주자. 우린 퇴로를 지키는 거야.'),
     ('레몬','전쟁이 없는','차 약속도 함께 돌아와야 지키겠지.'),
     ('액셀렌','그럴 때 같이','끝나면 평범한 오후에 마시자, 언니.')],
 34:[('길리엄','전이 기록을','전이 기록이 이곳의 교란과 닮았다. 다만 같은 원인인지는 아직 가설이다.'),
     ('린','누군가를 골라','원하는 사람을 부르는 기술은 아니야. 우리도 귀환 좌표를 찾지 못했어.'),
     ('길리엄','이제 틈이','우선 미잘을 막는다. 전이 조사는 본대 작전을 방해하지 않는 범위로 한다.')],
 35:[('레몬','만약 돌아오지','만들어진 생명도 버려선 안 돼. 저 아이도 살아야 해.'),
     ('액셀렌','작별 대신','라울과 미즈호가 건넨 손을 지켜 주자, 언니.'),
     ('레몬','내가 책임질','그래. 이번에는 살아갈 자리를 지킬게.'),
     ('잉그램','누군가의 시험','창조주의 뜻으로 삶을 끝낼 이유는 없다. 본대의 엄호를 맡겠다.'),
     ('워단','검을 휘두른','돌아올 곳이 필요한 것은 저 아이도 같군. 퇴로를 지킨다.')],
 36:[('레첼','전투가 끝나도','별도 통신이다. 종전 뒤의 조사와 증언도 남아 있다. 약속을 잊지 마라.'),
     ('린','돌아갈 길은','본사의 린에게 안부를 전해 줘. 난 이곳에서 귀환 연구를 계속할게.')]
}

# Move only the existing guarded scene; the native conversation remains intact.
MOVES={
 28:{'after_native_sid':254,'reason':'Complete Axel/Fiona introductions and the Lamia rescue briefing first.'},
 35:{'before_native_sid':194,'reason':'Let Raul and Mizuho save Despinis before the allied-clone response.'},
 36:{'before_native_sid':712,'reason':'Keep the original final lines about the children and their world last.'}
}

FINAL_RESPONSE=[
 ('비안','슈우, 이곳은 내가 총수로 돌아갈 세계가 아니네. 그래도 파멸을 지켜볼 수는 없지.'),
 ('잉그램','과거에 너희를 도구로 삼았다. 오늘은 누구의 시험도 아닌 너희의 싸움을 돕겠다.'),
 ('레몬','이곳에서 얻은 삶을 또 전쟁의 도구로 쓰지는 않겠어. 돌아갈 길을 함께 지킬게.')
]
FINAL_RESPONSE_FLAG=(62,6)
FINAL_RESPONSE_BEFORE_SID=146

# Story-on only: the temptation is now about a remembered person rather than
# claiming the parallel survivor beside the party is still missing.
NATIVE_TEXT={
 35:{366:('비렛타','비렛타：그 기억까지 미끼로…！')},
 36:{169:('슈우','슈우：퇴장할 시간입니다. 이 세계의 비안 박사가 발할라에서 기다립니다.')}
}
