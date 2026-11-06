"""Role-based spirit corrections for allied clones only (step 1 of the roadmap)."""
SPIRITS={'열혈':2,'번뜩임':3,'불굴':4,'철벽':5,'집중':6,'필중':7,'감응':8,
 '가속':9,'각성':10,'근성':11,'초근성':12,'신뢰':13,'기합':16,'기백':17,
 '저격':20,'직격':21,'정찰':22,'사랑':24,'예측':35,'투지':40,'기도':42}

# Each tuple is (spirit, SP cost, learn level). Unspecified slots stay intact.
# Native low-cost Accel and Scout remain valid; no blanket SP discount is used.
POLICY={
 '잉그램':{'reason':'리바레의 명중·회피 보조. 정찰 대신 집중을 추가하고 교관용 힘조절은 유지.',
          'slots':{1:('집중',15,1)}},
 '메키보스':{'reason':'아군 운용 시 비어 있던 트윈 정신기를 보완.', 'twin':('투지',20)},
 '비가지':{'reason':'근접 중장갑 역할에 철벽을 제공하고 열혈·필중 비용을 기존 아군 범위로 조정.',
          'spirits':[('필중',20,1),('기합',30,1),('초근성',30,1),('철벽',20,10),('열혈',35,25),('직격',20,30)]},
 '스리사즈':{'reason':'돌격형. 저비용 각성·감응 대신 불굴·기합·열혈을 단계적으로 습득.',
          'spirits':[('집중',15,1),('불굴',10,8),('가속',5,12),('기합',35,20),('열혈',40,28),('직격',25,34)]},
 '안사즈':{'reason':'저격·지원형. 저격·직격·감응의 비용을 조정하고 각성은 후반에 습득.',
          'spirits':[('집중',15,1),('저격',20,8),('가속',5,12),('직격',25,20),('감응',30,28),('각성',60,38)]},
 '울즈':{'reason':'정밀 사격형. 필중·열혈을 갖추고 각성은 후반의 고비용 선택으로 유지.',
          'spirits':[('집중',15,1),('필중',15,8),('가속',5,12),('직격',25,20),('열혈',40,28),('각성',60,38)]},
 '시카로그':{'reason':'철벽 SP5를 중장갑 아군의 통상 범위로 조정.', 'slots':{0:('철벽',20,1)}},
 '아타드':{'reason':'지원용 감응의 과도한 소모를 완화. 재동과 기존 나머지 구성은 유지.',
          'slots':{1:('감응',30,1)}},
 '워단':{'reason':'아군 운용 시 비어 있던 트윈 정신기를 보완. 전율은 추가하지 않음.', 'twin':('투지',20)},
 '유리아':{'reason':'기백 SP70을 기존 아군 범위로 조정.', 'slots':{5:('기백',50,30)}},
 '이글렛':{'reason':'후방 지원형. 복사된 카티나 공격수 구성에서 신뢰·정찰·감응 중심으로 분화.',
          'spirits':[('필중',20,1),('신뢰',20,1),('정찰',1,10),('가속',5,14),('불굴',10,22),('감응',30,30)],
          'twin':('기도',20)},
 '지벨':{'reason':'원거리 포격형. 필중·저격의 과도한 소모를 낮추고 철벽·열혈을 확보.',
          'spirits':[('정찰',1,1),('필중',20,1),('저격',20,10),('가속',10,14),('철벽',20,23),('열혈',40,31)]},
 '템페스트':{'reason':'집중·사랑 비용을 기존 아군 범위로 조정하고 비어 있던 트윈을 보완.',
          'slots':{2:('집중',15,10),5:('사랑',65,38)},'twin':('예측',40)},
}

def apply_to_row(name,row):
 b=bytearray(row);policy=POLICY.get(name,{})
 slots=dict(enumerate(policy['spirits'])) if 'spirits' in policy else policy.get('slots',{})
 for i,(spirit,cost,level) in slots.items():
  assert 0<=i<6 and 0<cost<=90 and 1<=level<=99
  b[0x6c+i]=SPIRITS[spirit];b[0x72+i]=cost;b[0x78+i]=level
 if 'twin' in policy:
  spirit,cost=policy['twin'];assert SPIRITS[spirit]>=32
  b[0x7e]=SPIRITS[spirit];b[0x7f]=cost
 assert b[:0x6c]==row[:0x6c] and b[0x80:]==row[0x80:]
 return bytes(b)
