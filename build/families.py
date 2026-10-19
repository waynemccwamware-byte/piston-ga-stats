import re
BRAND={'CESSNA':'Cessna','TEXTRON':'Cessna','REIMS':'Cessna','PIPER':'Piper','NEW PIPER':'Piper',
 'BEECH':'Beech','BEECHCRAFT':'Beech','RAYTHEON':'Beech','HAWKER':'Beech','MOONEY':'Mooney',
 'CIRRUS':'Cirrus','DIAMOND':'Diamond','COLUMBIA':'Cessna','LANCAIR':None}
def brand(mfr):
    m=mfr.upper()
    if re.search(r'^(CESSNA|TEXTRON AVIATION|REIMS)',m): return 'Cessna'
    if re.search(r'^(NEW )?PIPER(?! ?/| -|-[A-Z])',m) and 'CUB CRAFTERS' not in m: return 'Piper'
    if re.search(r'^(BEECH(?!ER)|BEECHCRAFT|RAYTHEON AIRCRAFT|HAWKER BEECHCRAFT|HAWKER$)',m): return 'Beech'
    if re.search(r'^MOONEY( AIRCRAFT| AIRPLANE| INTERNATIONAL|$)',m): return 'Mooney'
    if m.startswith('CIRRUS'): return 'Cirrus'
    if re.search(r'^DIAMOND( AIRCRAFT|$)',m): return 'Diamond'
    return None
# (brand, family label, regex on normalized model)  first match wins
FAM=[
 ('Cirrus','SR20',r'^SR ?20'),('Cirrus','SR22T',r'^SR ?22 ?T'),('Cirrus','SR22',r'^SR ?22'),
 ('Diamond','DA20',r'^DA ?20'),('Diamond','DA40 NG',r'^DA ?40 ?(NG|D)\b|^DA ?40 ?NG|^DA40D'),('Diamond','DA40',r'^DA ?40'),('Diamond','DA42',r'^DA ?42'),('Diamond','DA62',r'^DA ?62'),
 ('Cessna','120/140',r'^(120|140)'),('Cessna','150/152',r'^(F|A|FA)?15[02]'),('Cessna','170',r'^170'),
 ('Cessna','172RG',r'^172 ?RG'),('Cessna','172 Hawk XP',r'^(F?R172|R172)'),('Cessna','172',r'^(F|P)?172'),('Cessna','175',r'^175'),
 ('Cessna','177/Cardinal',r'^177'),('Cessna','180/185',r'^(A)?18[05]'),('Cessna','182',r'^(F|R|T|TR|FR)?182'),('Cessna','195',r'^19[05]'),
 ('Cessna','205/206/207',r'^(P|T|U|TU|TP)?20[567]|^210-5'),('Cessna','210',r'^(P|T)?210'),
 ('Cessna','350/400 (Columbia)',r'^(LC4[012]|T240|400|350)'),
 ('Cessna','310/320',r'^T?-?3[12]0'),('Cessna','335/340',r'^3(35|40)'),('Cessna','336/337',r'^(M|T|P|F)?33[67]'),
 ('Cessna','401-421 twins',r'^4(01|02|11|14|21)'),
 ('Piper','J-3 Cub',r'^J-?3'),('Piper','PA-18 Super Cub',r'^PA-?18'),('Piper','PA-22 Tri-Pacer/Colt',r'^PA-?22'),
 ('Piper','PA-28R Arrow',r'^PA-?28R'),('Piper','PA-28 Cherokee/Warrior/Archer',r'^PA-?28-'),('Piper','PA-28 Cherokee/Warrior/Archer',r'^PA-?28$'),
 ('Piper','PA-32 Cherokee Six/Saratoga',r'^PA-?32'),('Piper','PA-24 Comanche',r'^PA-?24'),('Piper','PA-46 Malibu/Mirage',r'^PA-?46'),
 ('Piper','PA-23 Apache/Aztec',r'^PA-?23'),('Piper','PA-30/39 Twin Comanche',r'^PA-?(30|39)'),('Piper','PA-34 Seneca',r'^PA-?34'),
 ('Piper','PA-38 Tomahawk',r'^PA-?38'),('Piper','PA-44 Seminole',r'^PA-?44'),('Piper','PA-31 Navajo',r'^PA-?31'),('Piper','PA-12 Super Cruiser',r'^PA-?12'),
 ('Beech','Bonanza 35 (V-tail)',r'^[A-Z]?35(?!-)[A-Z]?$|^[A-Z]35[AB]?$|^35$'),('Beech','Bonanza 33',r'^(35-)?[A-Z]?33[A-Z]?$|^35-[A-Z]?33'),
 ('Beech','Bonanza 36',r'^[A-Z]?36'),('Beech','Musketeer/Sundowner/Sierra',r'^[A-Z]?(19|23|24)([A-Z]?$|-|R$)'),
 ('Beech','Baron 55/58',r'^(95-)?[A-Z]?-?55|^[A-Z]?58'),('Beech','Travel Air 95',r'^[A-Z]?95'),('Beech','Duchess 76',r'^76'),('Beech','Skipper 77',r'^77$'),
 ('Mooney','M20 (C/E/F/G/J)',r'^M-?20[CDEFGJ]'),('Mooney','M20K/M/R/S/TN/V',r'^M-?20(K|M|R|S|TN|V|U)'),('Mooney','M20 early (A/B)',r'^M-?20[AB]?$'),
]
FAMC=[(b,l,re.compile(r)) for b,l,r in FAM]
def norm_model(m):
    m=m.upper().strip()
    m=re.sub(r'^(CESSNA|PIPER|BEECH|MOONEY|CIRRUS|DIAMOND)\s+','',m)
    m=m.replace('PA ','PA-')
    return m
def family(mfr,model):
    b=brand(mfr)
    if not b: return None,None
    m=norm_model(model)
    for bb,l,r in FAMC:
        if bb==b and r.search(m): return b,l
    return b,None
