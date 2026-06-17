"""embark_diseases_variants.py — Embark の breed-specific variant 別エントリ

Embark DNA テストは多くの疾患について breed-specific variant（特定の犬種で
固定された特定エクソンの変異）を別検査として提供している。本ファイルでは
それらを個別の SEO 個別ページとして辞書化し、品種別の検査結果と直接対応
できるようにする。

各エントリは _source="embark" フラグが poodle_genetics.py 側で自動付与される。
"""

from urllib.parse import quote_plus as _qp


def _g(q: str) -> str:
    return "https://www.google.com/search?q=" + _qp(q + " 犬 遺伝子")


EMBARK_VARIANT_DISEASES = [
    # ============================================================
    # GM1 ガングリオシドーシス — 品種別バリアント
    # ============================================================
    {
        "match": ["gm1 portuguese water dog", "glb1 exon 2", "gm1 pwd"],
        "title": "GM1 ガングリオシドーシス (Portuguese Water Dog / GLB1 Exon 2)",
        "summary": "Portuguese Water Dog 特有の GLB1 エクソン 2 変異による致死性蓄積症。GM1 ガングリオシドーシスの品種別バリアント。",
        "mechanism": "GLB1 遺伝子エクソン 2 の変異により β-ガラクトシダーゼが完全欠損し、GM1 ガングリオシドが神経細胞に蓄積する。",
        "symptoms": "生後数か月からの運動失調・けいれん・視力低下。多くは 2 歳までに死亡。",
        "inheritance": "常染色体劣性。",
        "advice": "Portuguese Water Dog ブリーダーは繁殖前検査必須。P/N × P/N 交配は厳禁。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("GM1 Portuguese Water Dog GLB1")},
        ],
    },
    {
        "match": ["gm1 alaskan husky", "glb1 alaskan husky"],
        "title": "GM1 ガングリオシドーシス (Alaskan Husky / GLB1 Exon 15)",
        "summary": "Alaskan Husky の GLB1 エクソン 15 変異による GM1 ガングリオシドーシス。Shiba 変異とは別系統の同遺伝子変異。",
        "mechanism": "GLB1 遺伝子エクソン 15 の変異により β-ガラクトシダーゼ機能が欠損する。",
        "symptoms": "若齢からの運動失調・けいれん・視力低下。",
        "inheritance": "常染色体劣性。",
        "advice": "Alaskan Husky ブリーダーは繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("GM1 Alaskan Husky GLB1 Exon 15")},
        ],
    },

    # ============================================================
    # Cobalamin Malabsorption — 品種別バリアント
    # ============================================================
    {
        "match": ["cobalamin beagle", "cubn exon 8", "imerslund beagle"],
        "title": "コバラミン吸収不良症 (Beagle / CUBN Exon 8)",
        "summary": "Beagle 特有の CUBN エクソン 8 変異によるビタミン B12 吸収不全症。月 1〜2 回の B12 注射で完全コントロール可能。",
        "mechanism": "CUBN（キュビリン）エクソン 8 の変異により回腸の B12-内因子複合体受容体が機能不全となる。",
        "symptoms": "若齢期からの元気消失・成長不良・貧血・神経症状。B12 投与で速やかに改善。",
        "inheritance": "常染色体劣性。",
        "advice": "Beagle ブリーダーの繁殖前検査推奨。発症犬は生涯にわたる B12 注射が必要だが予後良好。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Cobalamin Beagle CUBN Exon 8")},
        ],
    },
    {
        "match": ["cobalamin border collie", "cubn exon 53", "imerslund border collie"],
        "title": "コバラミン吸収不良症 (Border Collie / CUBN Exon 53)",
        "summary": "Border Collie 特有の CUBN エクソン 53 変異による B12 吸収不全症。",
        "mechanism": "CUBN エクソン 53 の変異により B12-内因子複合体の受容体機能が破綻する。",
        "symptoms": "若齢期からの元気消失・成長不良・蛋白尿。B12 注射で改善。",
        "inheritance": "常染色体劣性。",
        "advice": "Border Collie ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Cobalamin Border Collie CUBN Exon 53")},
        ],
    },
    {
        "match": ["cobalamin komondor", "cubn komondor", "cobalamin proteinuria"],
        "title": "コバラミン吸収不良 + 蛋白尿 (Komondor / CUBN)",
        "summary": "Komondor で報告される、B12 吸収不全に持続性蛋白尿を伴う症候群。",
        "mechanism": "CUBN 遺伝子変異により回腸と腎尿細管でのキュビリン-アムニオンレス複合体機能が同時に障害される。",
        "symptoms": "若齢期からの成長不良・貧血・持続性蛋白尿。",
        "inheritance": "常染色体劣性。",
        "advice": "発症犬は B12 注射と腎ケア食。Komondor の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Cobalamin Komondor CUBN proteinuria")},
        ],
    },

    # ============================================================
    # Cystinuria — タイプ別
    # ============================================================
    {
        "match": ["cystinuria type i-a", "cystinuria type 1a", "newfoundland cystinuria"],
        "title": "シスチン尿症 I-A 型 (Newfoundland / SLC3A1)",
        "summary": "Newfoundland 特有の重症型シスチン尿症。若齢から再発性尿路結石を起こす。",
        "mechanism": "SLC3A1 遺伝子変異により近位尿細管でのシスチン再吸収が破綻し、尿中シスチン濃度が上昇する。",
        "symptoms": "若齢期からの繰り返す尿路結石・血尿・尿閉。重症例で腎不全。",
        "inheritance": "常染色体劣性。",
        "advice": "発症犬は低タンパク食・尿アルカリ化・チオール製剤投与。Newfoundland ブリーダー必須検査。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Cystinuria Type I-A Newfoundland SLC3A1")},
        ],
    },
    {
        "match": ["cystinuria type ii-a", "cystinuria type 2a", "australian cattle dog cystinuria"],
        "title": "シスチン尿症 II-A 型 (Australian Cattle Dog / SLC3A1)",
        "summary": "Australian Cattle Dog の SLC3A1 別変異による中等症型シスチン尿症。",
        "mechanism": "SLC3A1 の別の変異により尿細管シスチントランスポーター機能が部分的に低下する。",
        "symptoms": "中年期から尿路結石。男性犬で症状が出やすい（性ホルモン依存）。",
        "inheritance": "常染色体劣性。",
        "advice": "発症犬は予防的食事療法。Australian Cattle Dog の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Cystinuria Type II-A ACD SLC3A1")},
        ],
    },
    {
        "match": ["cystinuria type ii-b", "cystinuria type 2b", "miniature pinscher cystinuria"],
        "title": "シスチン尿症 II-B 型 (Miniature Pinscher / SLC7A9)",
        "summary": "Miniature Pinscher で報告される SLC7A9 変異によるシスチン尿症。",
        "mechanism": "SLC7A9 遺伝子変異により尿細管シスチン再吸収の補助サブユニットが機能不全となる。",
        "symptoms": "中年期からの尿路結石。",
        "inheritance": "常染色体劣性（女性犬でも発症しうる）。",
        "advice": "Miniature Pinscher の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Cystinuria Type II-B Miniature Pinscher SLC7A9")},
        ],
    },

    # ============================================================
    # Congenital Hypothyroidism — 品種別バリアント
    # ============================================================
    {
        "match": ["hypothyroidism rat terrier", "tpo rat terrier", "tpo hairless terrier"],
        "title": "先天性甲状腺機能低下症 (Rat Terrier / TPO)",
        "summary": "Rat Terrier・Toy Fox Terrier・Hairless Terrier で報告される TPO 変異による先天性甲状腺機能低下症。",
        "mechanism": "TPO（甲状腺ペルオキシダーゼ）遺伝子変異により甲状腺ホルモン合成が障害される。",
        "symptoms": "新生子期からの発達遅延・低身長・巨大舌・慢性便秘・毛量減少。",
        "inheritance": "常染色体劣性。",
        "advice": "早期診断で甲状腺ホルモン補充療法により発達は正常化する。Rat Terrier・Toy Fox Terrier の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Congenital Hypothyroidism Rat Terrier TPO")},
        ],
    },
    {
        "match": ["hypothyroidism tenterfield", "tpo tenterfield"],
        "title": "先天性甲状腺機能低下症 (Tenterfield Terrier / TPO)",
        "summary": "Tenterfield Terrier 特有の TPO 別変異による先天性甲状腺機能低下症。",
        "mechanism": "TPO 遺伝子の異なる変異により甲状腺ホルモン合成が同様に障害される。",
        "symptoms": "新生子期からの発達遅延・低身長・代謝低下症状。",
        "inheritance": "常染色体劣性。",
        "advice": "早期診断とホルモン補充療法で正常発達。Tenterfield Terrier の繁殖前検査必須。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Congenital Hypothyroidism Tenterfield TPO")},
        ],
    },
    {
        "match": ["hypothyroidism french bulldog", "tpo french bulldog", "goiter french bulldog"],
        "title": "先天性甲状腺機能低下症 + 甲状腺腫 (French Bulldog / TPO Intron 13)",
        "summary": "French Bulldog で報告される、甲状腺腫を伴う先天性甲状腺機能低下症。",
        "mechanism": "TPO イントロン 13 のスプライス変異により甲状腺ホルモン合成と甲状腺発達が異常化する。",
        "symptoms": "新生子期からの発達遅延と肉眼で確認できる甲状腺腫。",
        "inheritance": "常染色体劣性。",
        "advice": "早期発見でホルモン補充療法。French Bulldog ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Congenital Hypothyroidism French Bulldog TPO")},
        ],
    },
    {
        "match": ["hypothyroidism shih tzu", "slc5a5 shih tzu", "nis shih tzu"],
        "title": "先天性甲状腺機能低下症 + 甲状腺腫 (Shih Tzu / SLC5A5)",
        "summary": "Shih Tzu で報告される SLC5A5（NIS）変異による甲状腺腫を伴う甲状腺機能低下症。",
        "mechanism": "SLC5A5（ナトリウム-ヨウ素シンポーター）遺伝子変異により甲状腺へのヨウ素取り込みが障害される。",
        "symptoms": "新生子期からの発達遅延、巨大舌、甲状腺腫。",
        "inheritance": "常染色体劣性。",
        "advice": "早期診断とホルモン補充療法。Shih Tzu の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Congenital Hypothyroidism Shih Tzu SLC5A5")},
        ],
    },

    # ============================================================
    # Congenital Myasthenic Syndrome — 品種別バリアント
    # ============================================================
    {
        "match": ["cms labrador", "colq labrador", "myasthenic labrador"],
        "title": "先天性筋無力症候群 (Labrador / COLQ)",
        "summary": "Labrador で報告される、神経筋接合部のコリンエステラーゼ係留異常による先天性筋無力症候群。",
        "mechanism": "COLQ 遺伝子変異により神経筋接合部のアセチルコリンエステラーゼ係留が異常化する。",
        "symptoms": "若齢期からの運動誘発性脱力、易疲労性。",
        "inheritance": "常染色体劣性。",
        "advice": "コリンエステラーゼ阻害薬は禁忌。3,4-DAP（ジアミノピリジン）で対応。Labrador の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("CMS Labrador COLQ")},
        ],
    },
    {
        "match": ["cms golden", "colq golden", "myasthenic golden"],
        "title": "先天性筋無力症候群 (Golden Retriever / COLQ)",
        "summary": "Golden Retriever で報告される COLQ 変異による先天性筋無力症候群。",
        "mechanism": "Labrador 型と類似の COLQ 変異による神経筋接合部機能異常。",
        "symptoms": "若齢期からの運動不耐性、運動誘発性脱力。",
        "inheritance": "常染色体劣性。",
        "advice": "Golden Retriever ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("CMS Golden Retriever COLQ")},
        ],
    },
    {
        "match": ["cms old danish", "chat old danish", "myasthenic pointing dog"],
        "title": "先天性筋無力症候群 (Old Danish Pointing Dog / CHAT)",
        "summary": "Old Danish Pointing Dog 特有の CHAT 変異によるアセチルコリン合成障害。",
        "mechanism": "CHAT（コリンアセチルトランスフェラーゼ）遺伝子変異によりアセチルコリン合成が低下する。",
        "symptoms": "若齢期からの運動不耐性、易疲労性。",
        "inheritance": "常染色体劣性。",
        "advice": "対症療法、Old Danish Pointing Dog ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("CMS Old Danish Pointing Dog CHAT")},
        ],
    },
    {
        "match": ["cms jack russell", "chrne jack russell", "myasthenic jrt"],
        "title": "先天性筋無力症候群 (Jack Russell Terrier / CHRNE)",
        "summary": "Jack Russell Terrier 特有の CHRNE 変異による神経筋接合部疾患。",
        "mechanism": "CHRNE（アセチルコリン受容体 ε サブユニット）遺伝子変異により受容体構造が異常化する。",
        "symptoms": "若齢期からの運動誘発性脱力。",
        "inheritance": "常染色体劣性。",
        "advice": "コリンエステラーゼ阻害薬で改善することが多い。JRT ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("CMS Jack Russell Terrier CHRNE")},
        ],
    },

    # ============================================================
    # Congenital Stationary Night Blindness — 品種別バリアント
    # ============================================================
    {
        "match": ["csnb beagle", "lrit3 beagle"],
        "title": "先天性夜盲症 (Beagle / LRIT3)",
        "summary": "Beagle で報告される、LRIT3 変異による先天性夜盲症。日中視力は保たれる。",
        "mechanism": "LRIT3 遺伝子変異により網膜双極細胞でのシナプス伝達が障害され、桿体機能が失われる。",
        "symptoms": "生後早期からの夜盲。日中の視覚は維持される。",
        "inheritance": "常染色体劣性。",
        "advice": "発症犬は明るい環境を保つことで日常生活に支障なし。Beagle の繁殖前検査推奨。",
        "severity": "low",
        "references": [
            {"label": "詳細を検索", "url": _g("CSNB Beagle LRIT3")},
        ],
    },
    {
        "match": ["csnb briard", "rpe65 briard"],
        "title": "先天性夜盲症 (Briard / RPE65)",
        "summary": "Briard 特有の RPE65 変異による先天性夜盲症。重症型で日中視力も低下することがある。",
        "mechanism": "RPE65 遺伝子変異により網膜色素上皮でのレチノイドサイクルが破綻する。",
        "symptoms": "生後早期からの夜盲、進行して日中視力も低下する場合あり。",
        "inheritance": "常染色体劣性。",
        "advice": "ヒトでは遺伝子治療（Luxturna）が承認されている疾患。Briard ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("CSNB Briard RPE65 Luxturna")},
        ],
    },

    # ============================================================
    # Day Blindness — 品種別バリアント
    # ============================================================
    {
        "match": ["day blindness malamute", "cngb3 malamute", "achromatopsia malamute"],
        "title": "昼盲症 (Alaskan Malamute / CNGB3)",
        "summary": "Alaskan Malamute 特有の CNGB3 欠失変異による錐体機能不全。明所視で著しく視力低下。",
        "mechanism": "CNGB3 遺伝子の欠失変異により錐体光受容体の機能が失われる。",
        "symptoms": "明るい場所での視力低下、暗所では比較的良好な視力。",
        "inheritance": "常染色体劣性。",
        "advice": "発症犬は屋内中心の生活で QOL を保てる。Alaskan Malamute の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Day Blindness Malamute CNGB3")},
        ],
    },
    {
        "match": ["day blindness german shepherd", "cnga3 gsd", "achromatopsia gsd"],
        "title": "昼盲症 (German Shepherd / CNGA3)",
        "summary": "German Shepherd の CNGA3 エクソン 7 変異による錐体機能不全。",
        "mechanism": "CNGA3 遺伝子エクソン 7 変異により錐体光受容体機能が失われる。",
        "symptoms": "明所での視力低下、色覚異常、暗所視は保たれる。",
        "inheritance": "常染色体劣性。",
        "advice": "German Shepherd の繁殖前検査推奨。発症犬は環境調整で対応。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Day Blindness GSD CNGA3")},
        ],
    },
    {
        "match": ["day blindness labrador", "cnga3 labrador"],
        "title": "昼盲症 (Labrador / CNGA3)",
        "summary": "Labrador での CNGA3 エクソン 7 変異による錐体機能不全。",
        "mechanism": "CNGA3 遺伝子エクソン 7 変異により錐体光受容体機能が失われる。",
        "symptoms": "明所での視力低下、暗所視は保たれる。",
        "inheritance": "常染色体劣性。",
        "advice": "Labrador の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Day Blindness Labrador CNGA3")},
        ],
    },
    {
        "match": ["day blindness gsp", "cngb3 gsp", "german shorthaired pointer day blindness"],
        "title": "昼盲症 (German Shorthaired Pointer / CNGB3)",
        "summary": "German Shorthaired Pointer の CNGB3 エクソン 6 変異による錐体機能不全。",
        "mechanism": "CNGB3 遺伝子エクソン 6 変異により錐体光受容体機能が失われる。",
        "symptoms": "明所での視力低下、暗所視は保たれる。",
        "inheritance": "常染色体劣性。",
        "advice": "GSP の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Day Blindness GSP CNGB3")},
        ],
    },

    # ============================================================
    # Hemophilia A — 品種別バリアント
    # ============================================================
    {
        "match": ["hemophilia a german shepherd 1", "f8 exon 11 gsd"],
        "title": "血友病 A (German Shepherd Variant 1 / F8 Exon 11)",
        "summary": "German Shepherd で報告される F8 エクソン 11 変異による血友病 A。",
        "mechanism": "F8 遺伝子エクソン 11 の変異により凝固第 VIII 因子が機能不全となる。X 連鎖性。",
        "symptoms": "若齢からの自然出血、関節血腫、術後出血。",
        "inheritance": "X 連鎖性劣性。",
        "advice": "GSD ブリーダーの繁殖前検査必須。手術前に第 VIII 因子製剤準備。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Hemophilia A GSD F8 Exon 11")},
        ],
    },
    {
        "match": ["hemophilia a german shepherd 2", "f8 exon 1 gsd"],
        "title": "血友病 A (German Shepherd Variant 2 / F8 Exon 1)",
        "summary": "German Shepherd の F8 エクソン 1 別変異による血友病 A。",
        "mechanism": "F8 遺伝子エクソン 1 の変異により第 VIII 因子の合成が破綻する。",
        "symptoms": "若齢からの自然出血、関節血腫。",
        "inheritance": "X 連鎖性劣性。",
        "advice": "GSD では F8 Exon 11 と併せて検査が推奨される。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Hemophilia A GSD F8 Exon 1")},
        ],
    },
    {
        "match": ["hemophilia a boxer", "f8 exon 10 boxer"],
        "title": "血友病 A (Boxer / F8 Exon 10)",
        "summary": "Boxer で報告される F8 エクソン 10 変異による血友病 A。",
        "mechanism": "F8 遺伝子エクソン 10 の変異により第 VIII 因子機能が破綻する。",
        "symptoms": "若齢からの出血傾向、関節血腫。",
        "inheritance": "X 連鎖性劣性。",
        "advice": "Boxer ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Hemophilia A Boxer F8 Exon 10")},
        ],
    },

    # ============================================================
    # Hemophilia B — 品種別バリアント
    # ============================================================
    {
        "match": ["hemophilia b terrier", "f9 terrier"],
        "title": "血友病 B (Terrier Variant / F9 Exon 7)",
        "summary": "テリア系で報告される F9 エクソン 7 変異による血友病 B。",
        "mechanism": "F9 遺伝子エクソン 7 の変異により凝固第 IX 因子が機能不全となる。",
        "symptoms": "若齢からの出血傾向、関節血腫、術後出血。",
        "inheritance": "X 連鎖性劣性。",
        "advice": "テリア系ブリーダーの繁殖前検査推奨。手術前に第 IX 因子製剤または血漿準備。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Hemophilia B Terrier F9")},
        ],
    },
    {
        "match": ["hemophilia b rhodesian ridgeback", "f9 rhodesian"],
        "title": "血友病 B (Rhodesian Ridgeback / F9 Exon 7)",
        "summary": "Rhodesian Ridgeback での F9 別変異による血友病 B。",
        "mechanism": "F9 遺伝子エクソン 7 の Rhodesian Ridgeback 特有変異により第 IX 因子機能が破綻する。",
        "symptoms": "若齢からの出血傾向。",
        "inheritance": "X 連鎖性劣性。",
        "advice": "Rhodesian Ridgeback ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Hemophilia B Rhodesian Ridgeback F9")},
        ],
    },

    # ============================================================
    # Mucopolysaccharidosis 各タイプ
    # ============================================================
    {
        "match": ["mps iiib", "sanfilippo b", "naglu", "schipperke mps"],
        "title": "ムコ多糖症 IIIB 型 / Sanfilippo B (Schipperke / NAGLU)",
        "summary": "Schipperke 特有のリソソーム酵素 α-N-アセチルグルコサミニダーゼ欠損による進行性蓄積症。",
        "mechanism": "NAGLU 遺伝子変異により α-N-アセチルグルコサミニダーゼが欠損し、ヘパラン硫酸が神経細胞に蓄積する。",
        "symptoms": "1〜2 歳からの運動失調、行動異常、進行性神経変性。",
        "inheritance": "常染色体劣性。",
        "advice": "治療法は対症療法のみ。Schipperke ブリーダーの繁殖前検査必須。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("MPS IIIB Schipperke NAGLU Sanfilippo")},
        ],
    },
    {
        "match": ["mps iiia dachshund", "sanfilippo a dachshund", "sgsh dachshund"],
        "title": "ムコ多糖症 IIIA 型 / Sanfilippo A (Dachshund / SGSH Exon 6)",
        "summary": "Dachshund で報告される SGSH 遺伝子変異による Sanfilippo A 病。",
        "mechanism": "SGSH（ヘパラン-N-スルファターゼ）遺伝子変異によりヘパラン硫酸が神経細胞に蓄積する。",
        "symptoms": "若齢期からの運動失調、進行性神経症状。",
        "inheritance": "常染色体劣性。",
        "advice": "治療法なし。Dachshund ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("MPS IIIA Dachshund SGSH Sanfilippo")},
        ],
    },
    {
        "match": ["mps iiia huntaway", "sgsh huntaway", "sanfilippo huntaway"],
        "title": "ムコ多糖症 IIIA 型 (New Zealand Huntaway / SGSH)",
        "summary": "New Zealand Huntaway 特有の SGSH 別変異による Sanfilippo A 病。",
        "mechanism": "SGSH 遺伝子の異なる変異によりヘパラン硫酸蓄積が起こる。",
        "symptoms": "若齢期からの進行性神経症状。",
        "inheritance": "常染色体劣性。",
        "advice": "Huntaway ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("MPS IIIA Huntaway SGSH")},
        ],
    },
    {
        "match": ["mps vi", "maroteaux-lamy", "arsb", "miniature pinscher mps"],
        "title": "ムコ多糖症 VI 型 / Maroteaux-Lamy (Miniature Pinscher / ARSB)",
        "summary": "Miniature Pinscher 特有のアリルスルファターゼ B 欠損による蓄積症。骨格異常を伴う。",
        "mechanism": "ARSB 遺伝子変異によりアリルスルファターゼ B が欠損し、ダーマタン硫酸が蓄積する。",
        "symptoms": "若齢期からの骨格変形、角膜混濁、進行性運動障害。",
        "inheritance": "常染色体劣性。",
        "advice": "ヒトでは酵素補充療法が承認されている。Miniature Pinscher ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("MPS VI Maroteaux-Lamy Miniature Pinscher ARSB")},
        ],
    },
    {
        "match": ["mps vii", "sly syndrome", "gusb", "german shepherd mps"],
        "title": "ムコ多糖症 VII 型 / Sly 症候群 (German Shepherd / GUSB)",
        "summary": "German Shepherd 特有の β-グルクロニダーゼ欠損による蓄積症。",
        "mechanism": "GUSB 遺伝子変異により β-グルクロニダーゼが欠損し、多種のグリコサミノグリカンが蓄積する。",
        "symptoms": "出生時から重症で、骨格異常、角膜混濁、神経症状を伴う。",
        "inheritance": "常染色体劣性。",
        "advice": "ほとんどの発症犬は新生子期に死亡。GSD ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("MPS VII Sly Syndrome GSD GUSB")},
        ],
    },

    # ============================================================
    # Canine Multifocal Retinopathy (CMR) — 3 タイプ
    # ============================================================
    {
        "match": ["cmr1", "multifocal retinopathy 1", "best1 exon 2"],
        "title": "犬多巣性網膜症 1 (CMR1 / BEST1 Exon 2)",
        "summary": "Mastiff・Bullmastiff 系で報告される、網膜に多数の局所性病変ができる遺伝性疾患。",
        "mechanism": "BEST1 遺伝子エクソン 2 の変異により網膜色素上皮の塩素イオンチャネル機能が異常化する。",
        "symptoms": "若齢期から眼底に多数の小さな剥離様病変。多くは軽症で進行は緩徐。",
        "inheritance": "常染色体劣性。",
        "advice": "軽症型は無治療で経過観察。Mastiff・Bullmastiff の繁殖前検査推奨。",
        "severity": "low",
        "references": [
            {"label": "詳細を検索", "url": _g("CMR1 BEST1 Mastiff")},
        ],
    },
    {
        "match": ["cmr2", "multifocal retinopathy 2", "coton de tulear retinopathy"],
        "title": "犬多巣性網膜症 2 (CMR2 / Coton de Tulear)",
        "summary": "Coton de Tulear 特有の BEST1 エクソン 5 変異による多巣性網膜症。",
        "mechanism": "BEST1 遺伝子エクソン 5 の変異により網膜色素上皮機能が異常化する。",
        "symptoms": "若齢期から眼底の多巣性病変。多くは軽症。",
        "inheritance": "常染色体劣性。",
        "advice": "Coton de Tulear の繁殖前検査推奨。",
        "severity": "low",
        "references": [
            {"label": "詳細を検索", "url": _g("CMR2 Coton de Tulear BEST1")},
        ],
    },
    {
        "match": ["cmr3", "multifocal retinopathy 3", "lapphund retinopathy"],
        "title": "犬多巣性網膜症 3 (CMR3 / Lapphund Variant)",
        "summary": "Finnish/Swedish Lapphund・Lapponian Herder 特有の BEST1 エクソン 10 欠失変異による網膜症。",
        "mechanism": "BEST1 遺伝子エクソン 10 欠失変異により網膜色素上皮機能が破綻する。",
        "symptoms": "若齢期から眼底の多巣性病変。",
        "inheritance": "常染色体劣性。",
        "advice": "Lapphund 系の繁殖前検査推奨。",
        "severity": "low",
        "references": [
            {"label": "詳細を検索", "url": _g("CMR3 Lapphund BEST1")},
        ],
    },

    # ============================================================
    # Multiple System Degeneration — 品種別バリアント
    # ============================================================
    {
        "match": ["msd chinese crested", "serac1 exon 4"],
        "title": "犬多系統変性症 (Chinese Crested / SERAC1 Exon 4)",
        "summary": "Chinese Crested 特有の SERAC1 エクソン 4 変異による若年発症の多系統神経変性症。",
        "mechanism": "SERAC1 遺伝子エクソン 4 の変異によりミトコンドリア機能が破綻し、複数の神経核が変性する。",
        "symptoms": "若齢期からの運動失調・歩行異常・進行性麻痺。",
        "inheritance": "常染色体劣性。",
        "advice": "対症療法のみ。Chinese Crested の繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Multiple System Degeneration Chinese Crested SERAC1")},
        ],
    },
    {
        "match": ["msd kerry blue", "serac1 exon 15"],
        "title": "犬多系統変性症 (Kerry Blue Terrier / SERAC1 Exon 15)",
        "summary": "Kerry Blue Terrier 特有の SERAC1 エクソン 15 変異による多系統変性症。",
        "mechanism": "SERAC1 遺伝子エクソン 15 の変異によりミトコンドリア機能が破綻する。",
        "symptoms": "若齢期からの運動失調・進行性麻痺。",
        "inheritance": "常染色体劣性。",
        "advice": "Kerry Blue Terrier の繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Multiple System Degeneration Kerry Blue SERAC1")},
        ],
    },

    # ============================================================
    # Myotonia Congenita — 品種別バリアント
    # ============================================================
    {
        "match": ["myotonia congenita acd", "clcn1 exon 23", "myotonia australian cattle dog"],
        "title": "先天性筋強直症 (Australian Cattle Dog / CLCN1 Exon 23)",
        "summary": "Australian Cattle Dog 特有の CLCN1 エクソン 23 変異による先天性筋強直症。",
        "mechanism": "CLCN1（塩素イオンチャネル）遺伝子エクソン 23 変異により筋細胞の興奮性が異常化する。",
        "symptoms": "若齢期からの運動開始時の筋強直、ぎこちない歩行。寒冷で悪化。",
        "inheritance": "常染色体劣性。",
        "advice": "メキシレチン等の Na チャネル遮断薬で症状緩和。Australian Cattle Dog の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Myotonia Congenita ACD CLCN1")},
        ],
    },
    {
        "match": ["myotonia congenita labrador", "clcn1 exon 19", "myotonia labrador"],
        "title": "先天性筋強直症 (Labrador / CLCN1 Exon 19)",
        "summary": "Labrador 特有の CLCN1 エクソン 19 変異による先天性筋強直症。",
        "mechanism": "CLCN1 遺伝子エクソン 19 変異により筋塩素イオンチャネル機能が破綻する。",
        "symptoms": "若齢期からの筋強直、ぎこちない歩行、運動誘発性脱力。",
        "inheritance": "常染色体劣性。",
        "advice": "Labrador の繁殖前検査推奨。対症療法で QOL を保てる。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Myotonia Congenita Labrador CLCN1")},
        ],
    },
    {
        "match": ["myotonia congenita miniature schnauzer", "clcn1 exon 7", "myotonia schnauzer"],
        "title": "先天性筋強直症 (Miniature Schnauzer / CLCN1 Exon 7)",
        "summary": "Miniature Schnauzer 特有の CLCN1 エクソン 7 変異による先天性筋強直症。",
        "mechanism": "CLCN1 遺伝子エクソン 7 変異により筋細胞興奮性が異常化する。",
        "symptoms": "若齢期からの運動開始時の筋強直、ぎこちない歩行。",
        "inheritance": "常染色体劣性。",
        "advice": "Miniature Schnauzer の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Myotonia Congenita Miniature Schnauzer CLCN1")},
        ],
    },

    # ============================================================
    # Narcolepsy — 品種別バリアント
    # ============================================================
    {
        "match": ["narcolepsy dachshund", "hcrtr2 dachshund", "hcrtr2 exon 1"],
        "title": "ナルコレプシー (Dachshund / HCRTR2 Exon 1)",
        "summary": "Dachshund 特有の HCRTR2 エクソン 1 変異によるナルコレプシー。",
        "mechanism": "HCRTR2（オレキシン受容体 2）遺伝子エクソン 1 変異によりオレキシンシグナル伝達が破綻する。",
        "symptoms": "興奮・食事をきっかけとした突然の脱力発作。意識は保たれる。",
        "inheritance": "常染色体劣性。",
        "advice": "発症犬は意識のある脱力発作のため日常生活に支障少ない。Dachshund ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Narcolepsy Dachshund HCRTR2")},
        ],
    },
    {
        "match": ["narcolepsy doberman", "hcrtr2 doberman", "hcrtr2 intron 4"],
        "title": "ナルコレプシー (Doberman / HCRTR2 Intron 4)",
        "summary": "Doberman 特有の HCRTR2 イントロン 4 変異によるナルコレプシー。",
        "mechanism": "HCRTR2 遺伝子イントロン 4 のスプライス変異によりオレキシンシグナル伝達が破綻する。",
        "symptoms": "興奮・食事をきっかけとした脱力発作。",
        "inheritance": "常染色体劣性。",
        "advice": "Doberman ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Narcolepsy Doberman HCRTR2")},
        ],
    },
    {
        "match": ["narcolepsy labrador", "hcrtr2 labrador", "hcrtr2 intron 6"],
        "title": "ナルコレプシー (Labrador / HCRTR2 Intron 6)",
        "summary": "Labrador 特有の HCRTR2 イントロン 6 変異によるナルコレプシー。",
        "mechanism": "HCRTR2 遺伝子イントロン 6 のスプライス変異によりオレキシンシグナル伝達が破綻する。",
        "symptoms": "興奮時の脱力発作。",
        "inheritance": "常染色体劣性。",
        "advice": "Labrador ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Narcolepsy Labrador HCRTR2")},
        ],
    },

    # ============================================================
    # Neuronal Ceroid Lipofuscinosis (NCL) — タイプ別
    # ============================================================
    {
        "match": ["ncl1 dachshund", "ppt1 dachshund", "ncl type 1"],
        "title": "神経セロイドリポフスチン症 1 型 (Dachshund / PPT1)",
        "summary": "Dachshund 特有の PPT1 変異による NCL タイプ 1。リソソーム酵素 PPT1 の欠損が原因。",
        "mechanism": "PPT1 遺伝子エクソン 8 変異により棕櫚化タンパクチオエステラーゼ 1 が欠損し、リポフスチン蓄積が起こる。",
        "symptoms": "若齢期からの進行性神経変性、視力低下、運動失調、けいれん。",
        "inheritance": "常染色体劣性。",
        "advice": "治療法なし。Dachshund ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("NCL1 Dachshund PPT1")},
        ],
    },
    {
        "match": ["ncl2 dachshund", "tpp1 dachshund", "ncl type 2"],
        "title": "神経セロイドリポフスチン症 2 型 (Dachshund / TPP1)",
        "summary": "Dachshund での TPP1 エクソン 4 変異による NCL タイプ 2。",
        "mechanism": "TPP1 遺伝子エクソン 4 変異によりトリペプチジルペプチダーゼ 1 が欠損する。",
        "symptoms": "若齢期からの進行性神経変性、視力低下。",
        "inheritance": "常染色体劣性。",
        "advice": "ヒトでは酵素補充療法（セルリポナーゼアルファ）が承認。Dachshund の繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("NCL2 Dachshund TPP1")},
        ],
    },
    {
        "match": ["ncl5 border collie", "cln5 border collie", "cln5 snp"],
        "title": "神経セロイドリポフスチン症 5 型 (Border Collie / CLN5 SNP)",
        "summary": "Border Collie 特有の CLN5 SNP 変異による NCL タイプ 5。",
        "mechanism": "CLN5 遺伝子の SNP 変異によりリソソーム膜タンパク機能が破綻する。",
        "symptoms": "1〜2 歳からの進行性神経変性、行動異常、視力低下、運動失調。",
        "inheritance": "常染色体劣性。",
        "advice": "Border Collie ブリーダーの繁殖前検査必須。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("NCL5 Border Collie CLN5")},
        ],
    },
    {
        "match": ["ncl5 golden", "cln5 golden", "cln5 deletion"],
        "title": "神経セロイドリポフスチン症 5 型 (Golden Retriever / CLN5 Deletion)",
        "summary": "Golden Retriever での CLN5 エクソン 4 欠失変異による NCL タイプ 5。",
        "mechanism": "CLN5 遺伝子エクソン 4 の欠失により蛋白質が完全欠損する。",
        "symptoms": "若齢期からの進行性神経変性。",
        "inheritance": "常染色体劣性。",
        "advice": "Golden Retriever の繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("NCL5 Golden Retriever CLN5")},
        ],
    },
    {
        "match": ["ncl6 australian shepherd", "cln6 aussie"],
        "title": "神経セロイドリポフスチン症 6 型 (Australian Shepherd / CLN6)",
        "summary": "Australian Shepherd 特有の CLN6 エクソン 7 変異による NCL タイプ 6。",
        "mechanism": "CLN6 遺伝子エクソン 7 変異により小胞体膜タンパク機能が破綻し、リポフスチン蓄積が起こる。",
        "symptoms": "1〜2 歳からの進行性神経変性、視力低下、けいれん。",
        "inheritance": "常染色体劣性。",
        "advice": "Australian Shepherd ブリーダーの繁殖前検査必須。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("NCL6 Australian Shepherd CLN6")},
        ],
    },
    {
        "match": ["ncl7 chihuahua", "mfsd8 chihuahua", "ncl chinese crested"],
        "title": "神経セロイドリポフスチン症 7 型 (Chihuahua, Chinese Crested / MFSD8)",
        "summary": "Chihuahua・Chinese Crested で報告される MFSD8 変異による NCL タイプ 7。",
        "mechanism": "MFSD8 遺伝子変異によりリソソーム膜輸送タンパク機能が破綻する。",
        "symptoms": "若齢期からの進行性神経変性。",
        "inheritance": "常染色体劣性。",
        "advice": "Chihuahua・Chinese Crested ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("NCL7 Chihuahua MFSD8")},
        ],
    },
    {
        "match": ["ncl8 australian shepherd", "cln8 aussie", "ncl8 aussie"],
        "title": "神経セロイドリポフスチン症 8 型 (Australian Shepherd / CLN8)",
        "summary": "Australian Shepherd 特有の CLN8 変異による NCL タイプ 8。",
        "mechanism": "CLN8 遺伝子変異により小胞体膜タンパク機能が破綻する。",
        "symptoms": "若齢期からの進行性神経変性。",
        "inheritance": "常染色体劣性。",
        "advice": "Australian Shepherd ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("NCL8 Australian Shepherd CLN8")},
        ],
    },
    {
        "match": ["ncl8 english setter", "cln8 setter"],
        "title": "神経セロイドリポフスチン症 8 型 (English Setter / CLN8 Exon 2)",
        "summary": "English Setter 特有の CLN8 エクソン 2 変異による NCL タイプ 8。",
        "mechanism": "CLN8 遺伝子エクソン 2 変異により小胞体膜タンパク機能が破綻する。",
        "symptoms": "若齢期からの進行性神経変性、視力低下。",
        "inheritance": "常染色体劣性。",
        "advice": "English Setter ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("NCL8 English Setter CLN8")},
        ],
    },
    {
        "match": ["ncl8 saluki", "cln8 saluki"],
        "title": "神経セロイドリポフスチン症 8 型 (Saluki / CLN8 Insertion)",
        "summary": "Saluki 特有の CLN8 挿入変異による NCL タイプ 8。",
        "mechanism": "CLN8 遺伝子の挿入変異により小胞体膜タンパクが構造異常化する。",
        "symptoms": "若齢期からの進行性神経変性。",
        "inheritance": "常染色体劣性。",
        "advice": "Saluki ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("NCL8 Saluki CLN8")},
        ],
    },
    {
        "match": ["late-onset ncl", "ncl12", "atp13a2"],
        "title": "遅発型神経セロイドリポフスチン症 12 (Australian Cattle Dog / ATP13A2)",
        "summary": "Australian Cattle Dog 特有の ATP13A2 変異による遅発型 NCL タイプ 12。",
        "mechanism": "ATP13A2 遺伝子変異によりリソソーム膜輸送タンパク機能が破綻する。",
        "symptoms": "中年期からの進行性神経変性、視力低下、行動異常。",
        "inheritance": "常染色体劣性。",
        "advice": "ACD ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Late-Onset NCL12 ACD ATP13A2")},
        ],
    },

    # ============================================================
    # Osteogenesis Imperfecta — 品種別バリアント
    # ============================================================
    {
        "match": ["oi beagle", "col1a2 beagle", "osteogenesis imperfecta beagle"],
        "title": "骨形成不全症 (Beagle / COL1A2)",
        "summary": "Beagle 特有の COL1A2 変異による骨脆弱症。軽い衝撃で骨折を繰り返す。",
        "mechanism": "COL1A2 遺伝子変異により I 型コラーゲン α2 鎖が構造異常化し、骨基質が脆弱化する。",
        "symptoms": "若齢期からの繰り返す骨折、関節弛緩、歯の異常。",
        "inheritance": "常染色体劣性。",
        "advice": "発症犬は外傷を避ける生活、ビスホスホネート等で骨密度改善を試みる。Beagle ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Osteogenesis Imperfecta Beagle COL1A2")},
        ],
    },
    {
        "match": ["oi dachshund", "serpinh1 dachshund", "osteogenesis imperfecta dachshund"],
        "title": "骨形成不全症 (Dachshund / SERPINH1)",
        "summary": "Dachshund での SERPINH1 変異による骨脆弱症。",
        "mechanism": "SERPINH1（HSP47）遺伝子変異によりコラーゲン折りたたみが破綻する。",
        "symptoms": "若齢期からの繰り返す骨折、骨格変形。",
        "inheritance": "常染色体劣性。",
        "advice": "Dachshund ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Osteogenesis Imperfecta Dachshund SERPINH1")},
        ],
    },
    {
        "match": ["oi golden", "col1a1 golden", "osteogenesis imperfecta golden"],
        "title": "骨形成不全症 (Golden Retriever / COL1A1)",
        "summary": "Golden Retriever 特有の COL1A1 変異による骨脆弱症。",
        "mechanism": "COL1A1 遺伝子変異により I 型コラーゲン α1 鎖が構造異常化する。",
        "symptoms": "若齢期からの繰り返す骨折。",
        "inheritance": "常染色体劣性。",
        "advice": "Golden Retriever ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Osteogenesis Imperfecta Golden COL1A1")},
        ],
    },

    # ============================================================
    # Pyruvate Kinase Deficiency — 品種別バリアント
    # ============================================================
    {
        "match": ["pk basenji", "pklr basenji", "pyruvate kinase basenji"],
        "title": "ピルビン酸キナーゼ欠損症 (Basenji / PKLR Exon 5)",
        "summary": "Basenji 特有の PKLR エクソン 5 変異による赤血球エネルギー代謝障害。",
        "mechanism": "PKLR 遺伝子エクソン 5 変異により赤血球のピルビン酸キナーゼが欠損し、エネルギー代謝が破綻して溶血する。",
        "symptoms": "若齢期からの慢性溶血性貧血、易疲労性、骨髄線維化。",
        "inheritance": "常染色体劣性。",
        "advice": "発症犬は重症例で骨髄移植が選択肢。Basenji ブリーダーの繁殖前検査必須。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Pyruvate Kinase Basenji PKLR")},
        ],
    },
    {
        "match": ["pk beagle", "pklr beagle", "pyruvate kinase beagle"],
        "title": "ピルビン酸キナーゼ欠損症 (Beagle / PKLR Exon 7)",
        "summary": "Beagle 特有の PKLR エクソン 7 変異による赤血球溶血性貧血。",
        "mechanism": "PKLR 遺伝子エクソン 7 変異によりピルビン酸キナーゼ機能が破綻する。",
        "symptoms": "若齢期からの慢性溶血性貧血。",
        "inheritance": "常染色体劣性。",
        "advice": "Beagle ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Pyruvate Kinase Beagle PKLR")},
        ],
    },
    {
        "match": ["pk terrier", "pklr terrier", "pyruvate kinase terrier"],
        "title": "ピルビン酸キナーゼ欠損症 (West Highland White Terrier / PKLR Exon 10)",
        "summary": "WHWT・Cairn Terrier 等で報告される PKLR エクソン 10 変異による溶血性貧血。",
        "mechanism": "PKLR 遺伝子エクソン 10 変異によりピルビン酸キナーゼ機能が破綻する。",
        "symptoms": "若齢期からの慢性溶血性貧血。",
        "inheritance": "常染色体劣性。",
        "advice": "WHWT・Cairn Terrier の繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Pyruvate Kinase Terrier PKLR WHWT")},
        ],
    },
    {
        "match": ["pk labrador", "pklr labrador", "pyruvate kinase labrador"],
        "title": "ピルビン酸キナーゼ欠損症 (Labrador / PKLR Exon 7)",
        "summary": "Labrador での PKLR エクソン 7 変異による溶血性貧血。",
        "mechanism": "PKLR 遺伝子エクソン 7 の Labrador 特有変異によりピルビン酸キナーゼ機能が破綻する。",
        "symptoms": "若齢期からの慢性溶血性貧血。",
        "inheritance": "常染色体劣性。",
        "advice": "Labrador ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Pyruvate Kinase Labrador PKLR")},
        ],
    },
    {
        "match": ["pk pug", "pklr pug", "pyruvate kinase pug"],
        "title": "ピルビン酸キナーゼ欠損症 (Pug / PKLR Exon 7)",
        "summary": "Pug 特有の PKLR エクソン 7 変異による溶血性貧血。",
        "mechanism": "PKLR 遺伝子エクソン 7 の Pug 特有変異によりピルビン酸キナーゼ機能が破綻する。",
        "symptoms": "若齢期からの慢性溶血性貧血。",
        "inheritance": "常染色体劣性。",
        "advice": "Pug ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Pyruvate Kinase Pug PKLR")},
        ],
    },

    # ============================================================
    # PFK Deficiency (GSD VII) — 品種別バリアント
    # ============================================================
    {
        "match": ["pfk deficiency whippet", "pfkm whippet", "pfk springer"],
        "title": "ホスホフルクトキナーゼ欠損症 (Whippet, English Springer Spaniel / PFKM)",
        "summary": "Whippet・English Springer Spaniel で報告される PFKM 変異による糖原蓄積症 VII 型。",
        "mechanism": "PFKM（筋型ホスホフルクトキナーゼ）遺伝子変異により筋糖代謝が破綻し、運動誘発性溶血と筋障害が起こる。",
        "symptoms": "運動誘発性の溶血、筋力低下、ミオグロビン尿。",
        "inheritance": "常染色体劣性。",
        "advice": "発症犬は激しい運動を避け、興奮制限。Whippet・English Springer Spaniel の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("PFK Deficiency Whippet Springer PFKM")},
        ],
    },
    {
        "match": ["pfk deficiency wachtelhund", "pfkm wachtelhund"],
        "title": "ホスホフルクトキナーゼ欠損症 (Wachtelhund / PFKM)",
        "summary": "Wachtelhund で報告される PFKM 別変異による糖原蓄積症 VII 型。",
        "mechanism": "PFKM 遺伝子変異により筋糖代謝が破綻する。",
        "symptoms": "運動誘発性の溶血、筋力低下。",
        "inheritance": "常染色体劣性。",
        "advice": "Wachtelhund ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("PFK Deficiency Wachtelhund PFKM")},
        ],
    },

    # ============================================================
    # GSD Ia — 品種別バリアント
    # ============================================================
    {
        "match": ["gsd ia german pinscher", "g6pc1 german pinscher", "von gierke pinscher"],
        "title": "糖原病 Ia 型 / Von Gierke (German Pinscher / G6PC1)",
        "summary": "German Pinscher 特有の G6PC1 変異による糖原蓄積症 Ia 型。",
        "mechanism": "G6PC1（グルコース-6-ホスファターゼ）遺伝子変異により肝糖新生が破綻する。",
        "symptoms": "新生子期からの致命的低血糖、乳酸アシドーシス、肝腫大。",
        "inheritance": "常染色体劣性。",
        "advice": "頻回給餌で低血糖を予防。German Pinscher ブリーダーの繁殖前検査必須。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("GSD Ia German Pinscher G6PC1")},
        ],
    },
    {
        "match": ["gsd ia maltese", "g6pc maltese", "von gierke maltese"],
        "title": "糖原病 Ia 型 / Von Gierke (Maltese / G6PC)",
        "summary": "Maltese 特有の G6PC 変異による糖原蓄積症 Ia 型。",
        "mechanism": "G6PC 遺伝子変異によりグルコース-6-ホスファターゼが欠損する。",
        "symptoms": "新生子期からの低血糖発作、肝腫大、成長不良。",
        "inheritance": "常染色体劣性。",
        "advice": "発症犬は頻回給餌での低血糖管理。Maltese の繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("GSD Ia Maltese G6PC")},
        ],
    },
    {
        "match": ["gsd iiia", "agl curly", "glycogen storage iiia"],
        "title": "糖原病 IIIA 型 (Curly Coated Retriever / AGL)",
        "summary": "Curly Coated Retriever 特有の AGL 変異による糖原蓄積症 IIIA 型。",
        "mechanism": "AGL 遺伝子変異により糖原脱分枝酵素が欠損し、異常構造のグリコーゲンが肝・筋に蓄積する。",
        "symptoms": "若齢期からの低血糖、肝腫大、進行性筋障害。",
        "inheritance": "常染色体劣性。",
        "advice": "Curly Coated Retriever ブリーダーの繁殖前検査推奨。発症犬は食事療法。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("GSD IIIA Curly Coated Retriever AGL")},
        ],
    },

    # ============================================================
    # SCID — 品種別バリアント
    # ============================================================
    {
        "match": ["scid terrier", "prkdc terrier", "scid jack russell"],
        "title": "重症複合免疫不全 (Jack Russell Terrier / PRKDC)",
        "summary": "Jack Russell Terrier 特有の PRKDC 変異による重症複合免疫不全症。",
        "mechanism": "PRKDC 遺伝子変異により V(D)J 再構成が破綻し、T 細胞・B 細胞ともに欠損する。",
        "symptoms": "新生子期からの重症感染症、ほとんどは離乳前に死亡。",
        "inheritance": "常染色体劣性。",
        "advice": "JRT ブリーダーの繁殖前検査必須。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("SCID Jack Russell PRKDC")},
        ],
    },
    {
        "match": ["scid wetterhoun", "rag1 wetterhoun"],
        "title": "重症複合免疫不全 (Wetterhoun / RAG1)",
        "summary": "Wetterhoun 特有の RAG1 変異による重症複合免疫不全症。",
        "mechanism": "RAG1 遺伝子変異により V(D)J 再構成が破綻する。",
        "symptoms": "新生子期からの重症感染症。",
        "inheritance": "常染色体劣性。",
        "advice": "Wetterhoun ブリーダーの繁殖前検査必須。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("SCID Wetterhoun RAG1")},
        ],
    },
    {
        "match": ["x-scid basset", "il2rg basset", "x-linked scid basset"],
        "title": "X 連鎖性重症複合免疫不全 (Basset Hound / IL2RG)",
        "summary": "Basset Hound 特有の IL2RG エクソン 1 変異による X 連鎖性重症複合免疫不全症。",
        "mechanism": "IL2RG（共通 γ 鎖）遺伝子変異により複数のサイトカイン受容体が機能不全となり、T 細胞・NK 細胞が欠損する。",
        "symptoms": "新生子期からの重症感染症、生後 4 か月以内の死亡が多い。",
        "inheritance": "X 連鎖性劣性。オスで発症、メスは保因者。",
        "advice": "Basset Hound メス繁殖前の検査必須。骨髄移植が唯一の根治療法。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("X-SCID Basset Hound IL2RG")},
        ],
    },
    {
        "match": ["x-scid corgi", "il2rg corgi", "x-linked scid corgi"],
        "title": "X 連鎖性重症複合免疫不全 (Cardigan Welsh Corgi / IL2RG)",
        "summary": "Cardigan Welsh Corgi での IL2RG 変異による X 連鎖性 SCID。",
        "mechanism": "IL2RG 遺伝子変異により T 細胞・NK 細胞が欠損する。",
        "symptoms": "新生子期からの重症感染症。",
        "inheritance": "X 連鎖性劣性。",
        "advice": "Corgi メス繁殖前の検査必須。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("X-SCID Corgi IL2RG")},
        ],
    },

    # ============================================================
    # Thrombopathia — 品種別バリアント
    # ============================================================
    {
        "match": ["thrombopathia american eskimo", "rasgrp1 american eskimo"],
        "title": "犬血小板症 (American Eskimo Dog / RASGRP1 Exon 5)",
        "summary": "American Eskimo Dog 特有の RASGRP1 エクソン 5 変異による血小板凝集障害。",
        "mechanism": "RASGRP1 遺伝子エクソン 5 変異により血小板内シグナル伝達が破綻する。",
        "symptoms": "鼻出血・歯肉出血・術後出血。",
        "inheritance": "常染色体劣性。",
        "advice": "American Eskimo Dog の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Thrombopathia American Eskimo RASGRP1")},
        ],
    },
    {
        "match": ["thrombopathia basset", "rasgrp1 basset hound"],
        "title": "犬血小板症 (Basset Hound / RASGRP1 Exon 5)",
        "summary": "Basset Hound 特有の RASGRP1 エクソン 5 変異による血小板凝集障害。",
        "mechanism": "RASGRP1 遺伝子エクソン 5 変異により血小板内シグナル伝達が破綻する。",
        "symptoms": "出血傾向、術後出血延長。",
        "inheritance": "常染色体劣性。",
        "advice": "Basset Hound の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Thrombopathia Basset Hound RASGRP1")},
        ],
    },
    {
        "match": ["thrombopathia landseer", "rasgrp1 landseer"],
        "title": "犬血小板症 (Landseer / RASGRP1 Exon 8)",
        "summary": "Landseer 特有の RASGRP1 エクソン 8 変異による血小板凝集障害。",
        "mechanism": "RASGRP1 遺伝子エクソン 8 変異により血小板内シグナル伝達が破綻する。",
        "symptoms": "出血傾向。",
        "inheritance": "常染色体劣性。",
        "advice": "Landseer の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Thrombopathia Landseer RASGRP1")},
        ],
    },

    # ============================================================
    # Familial Nephropathy — 品種別バリアント
    # ============================================================
    {
        "match": ["familial nephropathy cocker", "col4a4 exon 3 cocker"],
        "title": "家族性腎症 (Cocker Spaniel / COL4A4 Exon 3)",
        "summary": "Cocker Spaniel 特有の COL4A4 エクソン 3 変異による若年発症腎症。",
        "mechanism": "COL4A4 遺伝子エクソン 3 変異により糸球体基底膜の IV 型コラーゲンが構造異常化する。",
        "symptoms": "若齢期からの蛋白尿、進行性腎不全。",
        "inheritance": "常染色体劣性。",
        "advice": "Cocker Spaniel の繁殖前検査推奨。発症犬は腎ケア食・ACE 阻害薬。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Familial Nephropathy Cocker COL4A4")},
        ],
    },
    {
        "match": ["familial nephropathy springer", "col4a4 exon 30 springer"],
        "title": "家族性腎症 (English Springer Spaniel / COL4A4 Exon 30)",
        "summary": "English Springer Spaniel での COL4A4 エクソン 30 変異による家族性腎症。",
        "mechanism": "COL4A4 遺伝子エクソン 30 変異により糸球体基底膜が構造異常化する。",
        "symptoms": "若齢期からの蛋白尿、進行性腎不全。",
        "inheritance": "常染色体劣性。",
        "advice": "English Springer Spaniel の繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Familial Nephropathy Springer COL4A4")},
        ],
    },

    # ============================================================
    # Hereditary Ataxia — 品種別バリアント
    # ============================================================
    {
        "match": ["hereditary ataxia aussie", "pnpla8 australian shepherd"],
        "title": "遺伝性運動失調 (Australian Shepherd / PNPLA8)",
        "summary": "Australian Shepherd 特有の PNPLA8 変異による遺伝性運動失調症。",
        "mechanism": "PNPLA8（ミトコンドリアカルシウム依存性ホスホリパーゼ）遺伝子変異によりミトコンドリア機能が破綻する。",
        "symptoms": "若齢期からの進行性運動失調。",
        "inheritance": "常染色体劣性。",
        "advice": "Australian Shepherd ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Hereditary Ataxia Australian Shepherd PNPLA8")},
        ],
    },
    {
        "match": ["hereditary ataxia oes gordon", "rab24 cerebellar"],
        "title": "遺伝性小脳変性 (Old English Sheepdog, Gordon Setter / RAB24)",
        "summary": "Old English Sheepdog・Gordon Setter で報告される RAB24 変異による小脳変性症。",
        "mechanism": "RAB24（オートファジー関連 Rab GTPase）遺伝子変異により小脳プルキンエ細胞のオートファジー機能が破綻する。",
        "symptoms": "中年期からの進行性運動失調。",
        "inheritance": "常染色体劣性。",
        "advice": "OES・Gordon Setter の繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Hereditary Ataxia OES Gordon Setter RAB24")},
        ],
    },

    # ============================================================
    # Hereditary Footpad Hyperkeratosis — 品種別バリアント
    # ============================================================
    {
        "match": ["hfh terrier", "fam83g terrier", "kromfohrlander hyperkeratosis"],
        "title": "遺伝性肉球角化症 (Terrier, Kromfohrlander / FAM83G)",
        "summary": "Irish Terrier・Kromfohrlander 等で報告される、肉球の異常な肥厚と亀裂を起こす遺伝性疾患。",
        "mechanism": "FAM83G 遺伝子変異により肉球角化細胞の機能が破綻する。",
        "symptoms": "若齢期からの肉球の肥厚・亀裂・歩行時の痛み。",
        "inheritance": "常染色体劣性。",
        "advice": "発症犬は保湿クリーム・定期的なケアで管理。Terrier・Kromfohrlander の繁殖前検査推奨。",
        "severity": "low",
        "references": [
            {"label": "詳細を検索", "url": _g("Hereditary Footpad Hyperkeratosis Terrier FAM83G")},
        ],
    },
    {
        "match": ["hfh rottweiler", "dsg1 rottweiler"],
        "title": "遺伝性肉球角化症 (Rottweiler / DSG1)",
        "summary": "Rottweiler 特有の DSG1 変異による肉球の異常角化症。",
        "mechanism": "DSG1（デスモグレイン 1）遺伝子変異により角化細胞間接着が破綻し、肉球の角化が異常化する。",
        "symptoms": "若齢期からの肉球の肥厚・亀裂。",
        "inheritance": "常染色体劣性。",
        "advice": "Rottweiler ブリーダーの繁殖前検査推奨。",
        "severity": "low",
        "references": [
            {"label": "詳細を検索", "url": _g("Hereditary Footpad Hyperkeratosis Rottweiler DSG1")},
        ],
    },

    # ============================================================
    # Ichthyosis — 品種別バリアント
    # ============================================================
    {
        "match": ["ichthyosis american bulldog", "nipal4 ichthyosis"],
        "title": "魚鱗癬 (American Bulldog / NIPAL4)",
        "summary": "American Bulldog 特有の NIPAL4 変異による表皮角化異常。",
        "mechanism": "NIPAL4 遺伝子変異により表皮細胞のマグネシウム輸送が破綻し、角化過程が異常化する。",
        "symptoms": "若齢期からの全身性鱗屑、皮膚の厚化、苔癬様皮疹。",
        "inheritance": "常染色体劣性。",
        "advice": "発症犬は保湿スキンケア・抗炎症療法。American Bulldog の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Ichthyosis American Bulldog NIPAL4")},
        ],
    },
    {
        "match": ["ichthyosis german shepherd", "asprv1 ichthyosis"],
        "title": "魚鱗癬 (German Shepherd / ASPRV1)",
        "summary": "German Shepherd 特有の ASPRV1 変異による表皮角化異常。",
        "mechanism": "ASPRV1 遺伝子エクソン 2 変異により表皮プロテアーゼ機能が破綻する。",
        "symptoms": "若齢期からの全身性鱗屑・皮膚乾燥。",
        "inheritance": "常染色体劣性。",
        "advice": "GSD ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Ichthyosis GSD ASPRV1")},
        ],
    },
    {
        "match": ["ichthyosis great dane", "slc27a4 ichthyosis"],
        "title": "魚鱗癬 (Great Dane / SLC27A4)",
        "summary": "Great Dane 特有の SLC27A4 変異による表皮脂質代謝異常。",
        "mechanism": "SLC27A4 遺伝子変異により表皮脂肪酸輸送が破綻し、角質層構造が異常化する。",
        "symptoms": "若齢期からの全身性鱗屑、皮膚バリア機能低下。",
        "inheritance": "常染色体劣性。",
        "advice": "Great Dane ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Ichthyosis Great Dane SLC27A4")},
        ],
    },
    {
        "match": ["ichthyosis terrier", "krt10 epidermolytic"],
        "title": "表皮融解性魚鱗癬 (Terrier / KRT10)",
        "summary": "Terrier 系で報告される、KRT10 変異による表皮融解性魚鱗癬。",
        "mechanism": "KRT10（ケラチン 10）遺伝子変異によりサイトケラチンネットワークが脆弱化し、表皮が剥離する。",
        "symptoms": "若齢期からの皮膚水疱、剥離、過角化。",
        "inheritance": "常染色体優性。",
        "advice": "発症犬は無刺激スキンケア。Terrier 系の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Epidermolytic Ichthyosis Terrier KRT10")},
        ],
    },
    {
        "match": ["ichthyosis golden 2", "abhd5 golden", "ich2"],
        "title": "魚鱗癬 ICH2 (Golden Retriever / ABHD5)",
        "summary": "Golden Retriever の ABHD5 変異による魚鱗癬。一般的な PNPLA1 型（ICH1）とは別系統。",
        "mechanism": "ABHD5 遺伝子変異により表皮脂質代謝が破綻する。",
        "symptoms": "若齢期からの全身性鱗屑。",
        "inheritance": "常染色体劣性。",
        "advice": "Golden Retriever では PNPLA1（ICH1）と併せて検査することが標準。",
        "severity": "low",
        "references": [
            {"label": "詳細を検索", "url": _g("Ichthyosis ICH2 Golden Retriever ABHD5")},
        ],
    },

    # ============================================================
    # POAG — 品種別バリアント
    # ============================================================
    {
        "match": ["poag basset fauve", "adamts17 basset fauve"],
        "title": "原発性開放隅角緑内障 (Basset Fauve de Bretagne / ADAMTS17 Exon 11)",
        "summary": "Basset Fauve de Bretagne 特有の ADAMTS17 エクソン 11 変異による緑内障。",
        "mechanism": "ADAMTS17 遺伝子エクソン 11 変異により小柱網構造が脆弱化する。",
        "symptoms": "中年期からの眼圧上昇、進行性視神経萎縮。",
        "inheritance": "常染色体劣性。",
        "advice": "Basset Fauve de Bretagne の繁殖前検査推奨。早期発見で眼圧下降薬。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("POAG Basset Fauve ADAMTS17")},
        ],
    },
    {
        "match": ["poag beagle", "adamts10 exon 17 beagle"],
        "title": "原発性開放隅角緑内障 (Beagle / ADAMTS10 Exon 17)",
        "summary": "Beagle 特有の ADAMTS10 エクソン 17 変異による緑内障。",
        "mechanism": "ADAMTS10 遺伝子エクソン 17 変異により前眼房房水流出路の構造が異常化する。",
        "symptoms": "中年期からの緩徐な眼圧上昇、視神経萎縮。",
        "inheritance": "常染色体劣性。",
        "advice": "Beagle ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("POAG Beagle ADAMTS10")},
        ],
    },
    {
        "match": ["poag norwegian elkhound", "adamts10 exon 9 elkhound"],
        "title": "原発性開放隅角緑内障 (Norwegian Elkhound / ADAMTS10 Exon 9)",
        "summary": "Norwegian Elkhound 特有の ADAMTS10 エクソン 9 変異による緑内障。",
        "mechanism": "ADAMTS10 遺伝子エクソン 9 変異により前眼房構造が異常化する。",
        "symptoms": "中年期からの眼圧上昇、進行性視野欠損。",
        "inheritance": "常染色体劣性。",
        "advice": "Norwegian Elkhound の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("POAG Norwegian Elkhound ADAMTS10")},
        ],
    },
    {
        "match": ["poag pll shar-pei", "adamts17 exon 2 shar-pei"],
        "title": "原発性開放隅角緑内障 + 水晶体脱臼 (Chinese Shar-Pei / ADAMTS17)",
        "summary": "Chinese Shar-Pei 特有の ADAMTS17 エクソン 2 変異による緑内障と水晶体脱臼の合併症候群。",
        "mechanism": "ADAMTS17 遺伝子エクソン 2 変異により前眼房隅角と水晶体小帯両方が脆弱化する。",
        "symptoms": "中年期からの急性緑内障、水晶体脱臼、眼痛。",
        "inheritance": "常染色体劣性。",
        "advice": "Shar-Pei の繁殖前検査必須。眼科緊急時の早期対応で視覚を救える可能性あり。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("POAG PLL Shar-Pei ADAMTS17")},
        ],
    },

    # ============================================================
    # Junctional Epidermolysis Bullosa — 品種別バリアント
    # ============================================================
    {
        "match": ["jeb acd", "lama3 australian cattle dog"],
        "title": "接合部型表皮水疱症 (Australian Cattle Dog / LAMA3)",
        "summary": "Australian Cattle Dog 特有の LAMA3 エクソン 66 変異による表皮水疱症。",
        "mechanism": "LAMA3 遺伝子エクソン 66 変異によりラミニン α3 鎖が機能不全となり、表皮真皮接合部が脆弱化する。",
        "symptoms": "出生時からの全身性水疱・剥離。",
        "inheritance": "常染色体劣性。",
        "advice": "Australian Cattle Dog ブリーダーの繁殖前検査必須。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("JEB Australian Cattle Dog LAMA3")},
        ],
    },
    {
        "match": ["jeb australian shepherd", "lamb3 australian shepherd"],
        "title": "接合部型表皮水疱症 (Australian Shepherd / LAMB3)",
        "summary": "Australian Shepherd 特有の LAMB3 エクソン 11 変異による表皮水疱症。",
        "mechanism": "LAMB3 遺伝子エクソン 11 変異によりラミニン β3 鎖が機能不全となる。",
        "symptoms": "出生時からの全身性水疱・剥離。",
        "inheritance": "常染色体劣性。",
        "advice": "Australian Shepherd ブリーダーの繁殖前検査必須。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("JEB Australian Shepherd LAMB3")},
        ],
    },

    # ============================================================
    # Sensory Neuropathy — 単独
    # ============================================================
    {
        "match": ["sensory neuropathy border collie", "fam134b border collie"],
        "title": "感覚性神経障害 (Border Collie / FAM134B)",
        "summary": "Border Collie 特有の FAM134B 変異による感覚神経障害。痛覚低下による自咬リスクあり。",
        "mechanism": "FAM134B 遺伝子変異により末梢感覚神経が発達不全となる。",
        "symptoms": "若齢期からの足先・尾の感覚低下・自咬。",
        "inheritance": "常染色体劣性。",
        "advice": "発症犬は感覚低下による自傷予防に行動管理。Border Collie ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Sensory Neuropathy Border Collie FAM134B")},
        ],
    },

    # ============================================================
    # Hereditary Cataracts — 品種別バリアント
    # ============================================================
    {
        "match": ["cataract australian shepherd", "hsf4 exon 9 aussie"],
        "title": "遺伝性白内障 (Australian Shepherd / HSF4 Exon 9)",
        "summary": "Australian Shepherd 特有の HSF4 エクソン 9 変異による若年性白内障。",
        "mechanism": "HSF4 遺伝子エクソン 9 変異により水晶体細胞ストレス応答が破綻する。",
        "symptoms": "若齢期からの両眼の進行性水晶体混濁。",
        "inheritance": "常染色体優性（不完全浸透）。",
        "advice": "早期発見で手術可能。Australian Shepherd ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Cataract Australian Shepherd HSF4")},
        ],
    },
    {
        "match": ["cataract wirehaired pointing griffon", "fyco1 cataract"],
        "title": "遺伝性白内障 (Wirehaired Pointing Griffon / FYCO1)",
        "summary": "Wirehaired Pointing Griffon 特有の FYCO1 変異による白内障。",
        "mechanism": "FYCO1 遺伝子変異により水晶体細胞のオートファジー機能が破綻する。",
        "symptoms": "若齢期からの両眼の水晶体混濁。",
        "inheritance": "常染色体劣性。",
        "advice": "Wirehaired Pointing Griffon の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Cataract Wirehaired Pointing Griffon FYCO1")},
        ],
    },

    # ============================================================
    # Hereditary Nasal Parakeratosis — 品種別バリアント
    # ============================================================
    {
        "match": ["hnpk greyhound", "suv39h2 intron 4 greyhound"],
        "title": "遺伝性鼻過角化症 (Greyhound / SUV39H2 Intron 4)",
        "summary": "Greyhound 特有の SUV39H2 イントロン 4 変異による鼻の過角化症。",
        "mechanism": "SUV39H2 遺伝子イントロン 4 変異により表皮ヒストン修飾が異常化する。",
        "symptoms": "鼻先の過角化、亀裂、出血。",
        "inheritance": "常染色体劣性。",
        "advice": "Greyhound ブリーダーの繁殖前検査推奨。保湿クリームでの管理。",
        "severity": "low",
        "references": [
            {"label": "詳細を検索", "url": _g("HNPK Greyhound SUV39H2")},
        ],
    },

    # ============================================================
    # Golden Retriever PRA 1, 2
    # ============================================================
    {
        "match": ["gr-pra1", "gr pra1", "slc4a3", "golden retriever pra 1"],
        "title": "進行性網膜萎縮症 GR-PRA1 (Golden Retriever / SLC4A3)",
        "summary": "Golden Retriever 特有の SLC4A3 変異による進行性網膜萎縮症。中年期から失明が進行する。",
        "mechanism": "SLC4A3 遺伝子変異により網膜光受容体細胞の pH 恒常性が破綻し、変性が起こる。",
        "symptoms": "5〜10 歳からの夜盲、進行性視力低下、最終的に失明。",
        "inheritance": "常染色体劣性。",
        "advice": "Golden Retriever は GR-PRA1・GR-PRA2・prcd-PRA の 3 種を併せて検査するのが標準。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("GR-PRA1 Golden Retriever SLC4A3")},
        ],
    },
    {
        "match": ["gr-pra2", "gr pra2", "ttc8", "golden retriever pra 2"],
        "title": "進行性網膜萎縮症 GR-PRA2 (Golden Retriever / TTC8)",
        "summary": "Golden Retriever 特有の TTC8 変異による進行性網膜萎縮症。BBS8 関連で繊毛病に分類される。",
        "mechanism": "TTC8（BBS8）遺伝子変異により網膜光受容体細胞の繊毛機能が破綻する。",
        "symptoms": "中年期から夜盲、進行性視力低下、最終的に失明。",
        "inheritance": "常染色体劣性。",
        "advice": "GR-PRA1 と併せて Golden Retriever ブリーダーの繁殖前検査必須。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("GR-PRA2 Golden Retriever TTC8 BBS8")},
        ],
    },

    # ============================================================
    # PRA — 各種追加バリアント
    # ============================================================
    {
        "match": ["pra sag", "sag pra", "arrestin pra"],
        "title": "進行性網膜萎縮症 (SAG / S-アレスチン)",
        "summary": "SAG（S-アレスチン）遺伝子変異による桿体機能不全。複数犬種で報告。",
        "mechanism": "SAG 遺伝子変異により桿体光受容体のロドプシン脱活性化が破綻する。",
        "symptoms": "若齢〜中年期からの夜盲、進行性視力低下。",
        "inheritance": "常染色体劣性。",
        "advice": "対症療法のみ。発症犬は生活環境を一定に保つことで適応可能。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("PRA SAG arrestin")},
        ],
    },
    {
        "match": ["pra ift122", "ift122 lapphund", "ift122 lapponian"],
        "title": "進行性網膜萎縮症 (Lapponian Herder / IFT122)",
        "summary": "Lapponian Herder 特有の IFT122 エクソン 26 変異による PRA。繊毛形成タンパクの異常。",
        "mechanism": "IFT122（繊毛内輸送タンパク 122）遺伝子変異により光受容体繊毛機能が破綻する。",
        "symptoms": "中年期からの夜盲、進行性失明。",
        "inheritance": "常染色体劣性。",
        "advice": "Lapponian Herder ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("PRA Lapponian Herder IFT122")},
        ],
    },
    {
        "match": ["pra5", "necap1", "giant schnauzer pra"],
        "title": "進行性網膜萎縮症 PRA5 (Giant Schnauzer / NECAP1)",
        "summary": "Giant Schnauzer 特有の NECAP1 エクソン 6 変異による PRA。",
        "mechanism": "NECAP1 遺伝子変異により網膜細胞内の小胞輸送が異常化する。",
        "symptoms": "中年期からの夜盲、進行性失明。",
        "inheritance": "常染色体劣性。",
        "advice": "Giant Schnauzer ブリーダーの繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("PRA5 Giant Schnauzer NECAP1")},
        ],
    },
    {
        "match": ["pra cnga", "cnga1 exon 9", "cnga1 pra"],
        "title": "進行性網膜萎縮症 CNGA (CNGA1 Exon 9)",
        "summary": "CNGA1 エクソン 9 変異による桿体型 PRA。複数犬種で報告。",
        "mechanism": "CNGA1（環状ヌクレオチド依存性チャネル α サブユニット）遺伝子変異により桿体光受容体機能が破綻する。",
        "symptoms": "若齢〜中年期からの夜盲、進行性失明。",
        "inheritance": "常染色体劣性。",
        "advice": "対症療法のみ。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("PRA CNGA1 Exon 9")},
        ],
    },
    {
        "match": ["pra3", "fam161a", "pra fam161a"],
        "title": "進行性網膜萎縮症 PRA3 (FAM161A)",
        "summary": "FAM161A 遺伝子変異による PRA。Tibetan Spaniel・Tibetan Terrier 等で報告。",
        "mechanism": "FAM161A 遺伝子変異により光受容体繊毛基底部の機能が破綻する。",
        "symptoms": "中年期からの夜盲、進行性視力低下、失明。",
        "inheritance": "常染色体劣性。",
        "advice": "Tibetan Spaniel・Tibetan Terrier の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("PRA3 FAM161A Tibetan Spaniel")},
        ],
    },
    {
        "match": ["sca alpine dachsbracke", "scn8a alpine", "spinocerebellar alpine"],
        "title": "脊髄小脳失調症 (Alpine Dachsbracke / SCN8A)",
        "summary": "Alpine Dachsbracke 特有の SCN8A 変異による若齢発症の脊髄小脳失調症。",
        "mechanism": "SCN8A（電位依存性 Na チャネル Nav1.6）遺伝子変異により神経興奮性が異常化する。",
        "symptoms": "若齢期からの進行性運動失調、けいれん。",
        "inheritance": "常染色体劣性。",
        "advice": "Alpine Dachsbracke ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("SCA Alpine Dachsbracke SCN8A")},
        ],
    },
    {
        "match": ["spongy degeneration cerebellar ataxia 1", "spongy 1 kcnj10"],
        "title": "海綿状変性 + 小脳失調 1 型 (KCNJ10)",
        "summary": "KCNJ10 変異による海綿状脳変性と小脳失調を伴う疾患。複数犬種で報告。",
        "mechanism": "KCNJ10 遺伝子変異により脳内カリウムイオン恒常性が破綻し、白質に海綿状変性が起こる。",
        "symptoms": "若齢期からの進行性運動失調、けいれん。",
        "inheritance": "常染色体劣性。",
        "advice": "対症療法のみ。Belgian Shepherd・Malinois ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Spongy Degeneration KCNJ10 Belgian Shepherd")},
        ],
    },
    {
        "match": ["chondrodysplasia norwegian elkhound", "itga10 elkhound"],
        "title": "軟骨異形成症 (Norwegian Elkhound, Karelian Bear Dog / ITGA10)",
        "summary": "Norwegian Elkhound・Karelian Bear Dog 特有の ITGA10 変異による短足型軟骨異形成。",
        "mechanism": "ITGA10（インテグリン α10）遺伝子変異により軟骨成長板での細胞外マトリックス接着が破綻する。",
        "symptoms": "生後早期からの四肢の異常な短縮、関節障害。",
        "inheritance": "常染色体劣性。",
        "advice": "Norwegian Elkhound・Karelian Bear Dog の繁殖前検査推奨。",
        "severity": "medium",
        "references": [
            {"label": "詳細を検索", "url": _g("Chondrodysplasia Norwegian Elkhound ITGA10")},
        ],
    },
    {
        "match": ["ncl10 american bulldog", "ctsd american bulldog"],
        "title": "神経セロイドリポフスチン症 10 型 (American Bulldog / CTSD)",
        "summary": "American Bulldog 特有の CTSD エクソン 5 変異による NCL タイプ 10。",
        "mechanism": "CTSD（カテプシン D）遺伝子変異によりリソソームのプロテアーゼ機能が破綻する。",
        "symptoms": "若齢期からの進行性神経変性。",
        "inheritance": "常染色体劣性。",
        "advice": "American Bulldog ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("NCL10 American Bulldog CTSD")},
        ],
    },
    {
        "match": ["early onset cerebellar ataxia", "sel1l finnish hound"],
        "title": "若年発症小脳失調症 (Finnish Hound / SEL1L)",
        "summary": "Finnish Hound 特有の SEL1L 変異による若年発症の小脳失調症。",
        "mechanism": "SEL1L 遺伝子変異により小胞体関連分解（ERAD）系が破綻し、小脳プルキンエ細胞が変性する。",
        "symptoms": "若齢期からの進行性運動失調、頭部振戦。",
        "inheritance": "常染色体劣性。",
        "advice": "Finnish Hound ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("Early Onset Cerebellar Ataxia Finnish Hound SEL1L")},
        ],
    },

    # ============================================================
    # NCL4A AmStaff — 単独
    # ============================================================
    {
        "match": ["ncl4a amstaff", "arsg amstaff", "ncl cerebellar ataxia"],
        "title": "神経セロイドリポフスチン症 4A 型 + 小脳失調 (Am Staff / ARSG)",
        "summary": "American Staffordshire Terrier 特有の ARSG 変異による NCL タイプ 4A と小脳失調の合併症候群。",
        "mechanism": "ARSG（アリルスルファターゼ G）遺伝子変異によりリソソーム機能が破綻する。",
        "symptoms": "中年期からの進行性小脳失調、行動異常、視力低下。",
        "inheritance": "常染色体劣性。",
        "advice": "American Staffordshire Terrier ブリーダーの繁殖前検査推奨。",
        "severity": "high",
        "references": [
            {"label": "詳細を検索", "url": _g("NCL4A AmStaff ARSG")},
        ],
    },
]
