# -*- coding: utf-8 -*-
"""补充药材 第三批 (9味) - 为解锁经典方剂所需,含禁忌演示相关"""
HERBS_EXTRA_C = {
    "羌活": {
        "name": "羌活", "pinyin": "Qiang Huo", "latin": "Notopterygii Rhizoma et Radix",
        "property": "辛、苦，温", "meridian": "归膀胱、肾经",
        "functions": "解表散寒，祛风胜湿，止痛",
        "indications": "风寒感冒，头痛项强，风湿痹痛，肩背酸痛",
        "dosage": "3～10g",
        "precautions": "血虚痹痛、阴虚头痛者慎用",
        "modernResearch": "含挥发油等成分，具有解热、镇痛、抗炎等作用",
        "description": "羌活为伞形科植物羌活或宽叶羌活的干燥根茎和根，善治上半身风寒湿痹。"
    },
    "葛根": {
        "name": "葛根", "pinyin": "Ge Gen", "latin": "Puerariae Lobatae Radix",
        "property": "甘、辛，凉", "meridian": "归脾、胃、肺经",
        "functions": "解肌退热，生津止渴，透疹，升阳止泻，通经活络，解酒毒",
        "indications": "外感发热头痛，项背强痛，口渴消渴，麻疹不透，热痢泄泻，高血压颈项强痛",
        "dosage": "10～15g",
        "precautions": "胃寒者慎用；表虚多汗者不宜大量使用",
        "modernResearch": "含葛根素、大豆苷元等黄酮类，具有扩张血管、解热、降血糖等作用",
        "description": "葛根为豆科植物野葛的干燥根，为解肌退热、生津止渴要药，善治项背强痛。"
    },
    "滑石": {
        "name": "滑石", "pinyin": "Hua Shi", "latin": "Talcum",
        "property": "甘、淡，寒", "meridian": "归膀胱、肺、胃经",
        "functions": "利尿通淋，清热解暑，收湿敛疮",
        "indications": "热淋石淋，尿热涩痛，暑湿烦渴，湿热水泻；外治湿疹湿疮，痱子",
        "dosage": "10～20g，包煎",
        "precautions": "脾虚气弱、精滑及热病津伤者不宜使用；孕妇慎用",
        "modernResearch": "主含硅酸镁，具有吸附、保护肠黏膜等作用",
        "description": "滑石为硅酸盐类矿物滑石族滑石，善清膀胱热结、通利水道。"
    },
    "天麻": {
        "name": "天麻", "pinyin": "Tian Ma", "latin": "Gastrodiae Rhizoma",
        "property": "甘，平", "meridian": "归肝经",
        "functions": "息风止痉，平抑肝阳，祛风通络",
        "indications": "小儿惊风，癫痫抽搐，破伤风，头痛眩晕，肢体麻木，半身不遂，风湿痹痛",
        "dosage": "3～10g",
        "precautions": "气血两虚者不宜单独使用",
        "modernResearch": "含天麻素等成分，具有镇静、抗惊厥、降压等作用",
        "description": "天麻为兰科植物天麻的干燥块茎，为治肝阳上亢眩晕、风痰抽搐之要药。"
    },
    "浮小麦": {
        "name": "浮小麦", "pinyin": "Fu Xiao Mai", "latin": "Tritici Fructus Levis",
        "property": "甘，凉", "meridian": "归心经",
        "functions": "固表止汗，益气，除热",
        "indications": "自汗，盗汗，骨蒸劳热",
        "dosage": "15～30g",
        "precautions": "表邪未解、汗出过多者慎用",
        "modernResearch": "含淀粉、蛋白质及B族维生素，具敛汗作用",
        "description": "浮小麦为禾本科植物小麦的干瘪轻浮的颖果，善敛虚汗、退虚热。"
    },
    "吴茱萸": {
        "name": "吴茱萸", "pinyin": "Wu Zhu Yu", "latin": "Euodiae Fructus",
        "property": "辛、苦，热；有小毒", "meridian": "归肝、脾、胃、肾经",
        "functions": "散寒止痛，降逆止呕，助阳止泻",
        "indications": "厥阴头痛，寒疝腹痛，寒湿脚气，经行腹痛，脘腹胀痛，呕吐吞酸，五更泄泻",
        "dosage": "2～5g；外用适量",
        "precautions": "不宜过量久服；阴虚有热者忌用；孕妇慎用",
        "modernResearch": "含吴茱萸碱、挥发油等，具有镇痛、止呕、降压等作用",
        "description": "吴茱萸为芸香科植物吴茱萸的干燥近成熟果实，善暖肝止痛、降逆止呕。"
    },
    "神曲": {
        "name": "神曲", "pinyin": "Shen Qu", "latin": "Massa Medicata Fermentata",
        "property": "甘、辛，温", "meridian": "归脾、胃经",
        "functions": "消食和胃",
        "indications": "饮食停滞，脘腹胀满，食少纳呆，肠鸣腹泻",
        "dosage": "6～15g",
        "precautions": "胃阴虚、无食积者慎用",
        "modernResearch": "含酵母菌及多种消化酶，具助消化作用",
        "description": "神曲为面粉和多种药物混合经发酵而成的加工品，善消食化积、健脾和胃。"
    },
    "山楂": {
        "name": "山楂", "pinyin": "Shan Zha", "latin": "Crataegi Fructus",
        "property": "酸、甘，微温", "meridian": "归脾、胃、肝经",
        "functions": "消食健胃，行气散瘀，化浊降脂",
        "indications": "肉食积滞，胃脘胀满，泻痢腹痛，瘀血经闭，产后瘀阻，心腹刺痛，高脂血症",
        "dosage": "9～12g",
        "precautions": "胃酸分泌过多者慎用；孕妇慎用",
        "modernResearch": "含山楂酸、黄酮类及维生素C，具有助消化、降血脂等作用",
        "description": "山楂为蔷薇科植物山里红或山楂的干燥成熟果实，善消一切饮食积滞，尤善消肉积。"
    },
    "莱菔子": {
        "name": "莱菔子", "pinyin": "Lai Fu Zi", "latin": "Raphani Semen",
        "property": "辛、甘，平", "meridian": "归肺、脾、胃经",
        "functions": "消食除胀，降气化痰",
        "indications": "饮食停滞，脘腹胀痛，大便秘结，积滞泻痢，痰壅喘咳",
        "dosage": "5～12g",
        "precautions": "气虚及无食积痰滞者慎用；不宜与人参同用",
        "modernResearch": "含莱菔子素、脂肪油等，具有促进消化、降压等作用",
        "description": "莱菔子为十字花科植物萝卜的干燥成熟种子，善消食除胀、降气化痰。"
    },
}
