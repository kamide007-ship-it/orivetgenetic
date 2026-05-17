"""kb_en.py — DISEASE_KB / TRAIT_KB の英語翻訳オーバーレイ

⚠️ **重要な免責事項**:
このファイルの英訳は AI モデル (Claude) が日本語版から自動生成したものです。
獣医遺伝学者による監修を経ていません。Orivet 名で公開する前に専門家のレビューが必須です。

構造:
    DISEASE_EN[slug] = {
        "title": "...",
        "summary": "...",
        "mechanism": "...",
        "symptoms": "...",
        "inheritance": "...",
        "advice": "...",
        "reviewed": True/False,      # 獣医監修済フラグ（既定 False）
        "reviewer": "Dr. Name",      # 監修者名（任意）
        "reviewed_date": "YYYY-MM-DD", # 監修日（任意）
        "reviewer_notes": "..."      # 監修コメント（任意・公開しない）
    }

監修ワークフロー:
    1. 獣医チームが kb_en.py を編集
    2. 監修したエントリに reviewed=True を追加
    3. オプションで reviewer / reviewed_date を記録
    4. 未監修エントリはアプリ UI に『⚠️ AI 翻訳（未監修）』バッジが表示される

poodle_genetics.py 側で SLUG_INDEX に _en としてマージされる。
部分英訳でも問題ない（unmatched entries は日本語にフォールバック）。
"""

# 重症度ラベル英訳
SEVERITY_LABELS_EN = {
    "high":   {"label": "High risk",   "emoji": "🔴"},
    "medium": {"label": "Medium risk", "emoji": "🟡"},
    "low":    {"label": "Low risk",    "emoji": "🟢"},
}

# カテゴリラベル英訳
CATEGORY_LABELS_EN = {
    "🦴 骨格・関節系":     "🦴 Skeletal / Joint",
    "🧠 神経・脳系":       "🧠 Neurological / Brain",
    "👁 眼科系":           "👁 Ophthalmologic",
    "🩸 血液・凝固系":     "🩸 Hematologic / Coagulation",
    "🧪 代謝・内分泌系":   "🧪 Metabolic / Endocrine",
    "💪 筋・運動系":       "💪 Muscular / Movement",
    "🫘 腎・泌尿器系":     "🫘 Renal / Urinary",
    "🧴 皮膚・被毛系":     "🧴 Dermatologic / Coat",
    "🛡 免疫系":           "🛡 Immune",
    "🫃 消化器系":         "🫃 Gastrointestinal",
    "🌱 発達・内分泌系":   "🌱 Developmental / Endocrine",
    "📋 その他":           "📋 Other",
}

# 症状カテゴリ英訳
SYMPTOM_LABELS_EN = {
    "hindlimb":  "🦵 Hindlimb paralysis / gait abnormality",
    "vision":    "👁 Vision impairment / blindness",
    "bleeding":  "🩸 Bleeding tendency / clotting issues",
    "neuro":     "🧠 Seizures / neurological symptoms",
    "kidney":    "🫘 Polyuria / renal dysfunction",
    "skin":      "🧴 Skin abnormalities / hair loss",
    "skeletal":  "🦴 Skeletal / joint abnormalities",
    "metabolic": "🧪 Metabolic / growth abnormalities",
    "drug":      "💉 Drug sensitivity",
    "immune":    "🛡 Immune dysfunction / recurrent infection",
}


DISEASE_EN = {
    # ============================================================
    # 骨格・関節系
    # ============================================================
    "chondrodystrophy": {
        "title": "Chondrodystrophy + IVDD (CDDY+IVDD)",
        "summary": "An inherited disease in which abnormal intervertebral disc cartilage predisposes the dog to intervertebral disc herniation.",
        "mechanism": "Caused by a retroviral insertion in the FGF4 gene. The nucleus pulposus undergoes premature degeneration and calcification, making it vulnerable to rupture under minor impact, compressing the spinal cord.",
        "symptoms": "Hindlimb weakness, pain, gait difficulty. Severe cases may show complete paralysis or urinary dysfunction.",
        "inheritance": "Autosomal (incomplete) dominant. One copy raises risk; two copies increase it further.",
        "advice": "Strongly avoid P/P × P/P crosses. Affected dogs should have weight management and avoid stair-climbing or rough play.",
    },
    "osteochondrodysplasia": {
        "title": "Osteochondrodysplasia (SLC13A1)",
        "summary": "An inherited disorder of bone and cartilage development causing limb shortening and joint abnormalities.",
        "mechanism": "Mutation in SLC13A1 disrupts mineral metabolism, impairing normal skeletal development.",
        "symptoms": "Limb shortening, joint deformity, restricted movement. Reported in Scottish Folds and Miniature Poodles.",
        "inheritance": "Autosomal recessive. P/N × P/N crosses risk 25% affected offspring.",
        "advice": "Avoid P/N × P/N matings. Affected dogs benefit from regular orthopedic consultation.",
    },
    "cdpa": {
        "title": "Chondrodysplasia (CDPA — Short Leg Gene)",
        "summary": "A gene producing short limbs, defining the 'short-legged' breeds like Dachshunds and Corgis.",
        "mechanism": "Duplication of the FGF4 gene alters cartilage formation, shortening the limbs. Unlike CDDY, this is a breed-defining trait, not a disease per se.",
        "symptoms": "Typically asymptomatic. Short limbs are accepted as breed standard.",
        "inheritance": "Incomplete dominance. Most short-legged breeds are P/P or P/N.",
        "advice": "Carrier status is common in short-legged breeds. Often tested together with CDDY but distinct.",
    },
    "osteogenesis-imperfecta": {
        "title": "Osteogenesis Imperfecta (SERPINH1, COL1A1, COL1A2)",
        "summary": "An inherited disorder causing brittle bones that fracture easily from minor impacts.",
        "mechanism": "Mutations in collagen-related genes (SERPINH1, COL1A1, COL1A2) result in structurally abnormal collagen.",
        "symptoms": "Repeated fractures from a young age, dental abnormalities, joint laxity. Reported in Dachshunds and Beagles.",
        "inheritance": "Autosomal recessive (depending on subtype).",
        "advice": "Affected dogs require activity restriction and fracture prevention. Calcium and collagen nutrition is important.",
    },

    # ============================================================
    # 神経・脳系
    # ============================================================
    "degenerative-myelopathy": {
        "title": "Degenerative Myelopathy (DM / SOD1)",
        "summary": "A late-onset hereditary neurological disease causing progressive hindlimb paralysis.",
        "mechanism": "Mutation in SOD1 leads to abnormal protein accumulation in neurons, similar to human ALS.",
        "symptoms": "Hindlimb ataxia onset around 8–14 years, progressing to paralysis. Generally painless. Eventually affects forelimbs.",
        "inheritance": "Autosomal recessive (incomplete penetrance). Not all P/P dogs develop disease; rates vary by breed.",
        "advice": "Avoid P/P × P/P crosses. Affected dogs maintain QOL with physical therapy and mobility aids.",
    },
    "gm1-gangliosidosis": {
        "title": "GM1 Gangliosidosis (GLB1)",
        "summary": "A severe inherited metabolic disorder causing GM1 ganglioside accumulation in neurons and progressive neurological deterioration.",
        "mechanism": "Mutation in GLB1 causes deficiency of β-galactosidase enzyme. GM1 accumulates in neurons. Reported in Shibas, Akitas, Beagles, Spaniels.",
        "symptoms": "Onset at young age with progressive ataxia, seizures, vision loss. Most die by 2–3 years.",
        "inheritance": "Autosomal recessive. 25% of offspring from carrier × carrier crosses are affected.",
        "advice": "Strictly avoid P/N × P/N matings. Prognosis for affected dogs is poor.",
    },
    "gm2-gangliosidosis": {
        "title": "GM2 Gangliosidosis (HEXB)",
        "summary": "A severe inherited disorder of progressive neurological deterioration due to abnormal lipid accumulation in neurons.",
        "mechanism": "Mutation in HEXB causes deficiency of lysosomal enzyme hexosaminidase B. GM2 ganglioside accumulates in neurons. Similar to human Tay-Sachs disease.",
        "symptoms": "Young-onset progressive ataxia, seizures, vision loss. Most die within 1–2 years.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier crosses.",
        "advice": "Strictly avoid carrier × carrier matings. No curative treatment; only symptomatic care.",
    },
    "progressive-rod-cone": {
        "title": "Progressive Retinal Atrophy (prcd-PRA / PRCD)",
        "summary": "An inherited disease causing gradual degeneration of retinal photoreceptors (rods and cones), leading to eventual blindness.",
        "mechanism": "Mutation in PRCD causes progressive death of retinal cells, first affecting night vision then day vision.",
        "symptoms": "Night blindness → peripheral vision loss → complete blindness. Painless.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Since onset is typically after age 3–5, genetic testing is critical for breeding decisions. Dogs adapt well to blindness via smell and hearing.",
    },
    "neonatal-encephalopathy": {
        "title": "Neonatal Encephalopathy with Seizures (NEwS / ATF2)",
        "summary": "A severe poodle-specific neonatal neurological disease, fatal within weeks of birth.",
        "mechanism": "Mutation in ATF2 disrupts neurological development. Reported in Standard Poodles.",
        "symptoms": "Onset at 4–6 weeks with ataxia, seizures, failure to thrive. Most die by weaning.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Avoid P/N × P/N matings in Poodle breeding. Carrier frequency in Standard Poodles is a few percent.",
    },
    "neuronal-ceroid-lipofuscinosis": {
        "title": "Neuronal Ceroid Lipofuscinosis (NCL)",
        "summary": "A group of disorders causing abnormal accumulation of ceroid lipofuscin in brain cells, resulting in progressive neurodegeneration.",
        "mechanism": "Multiple gene mutations (CLN5, CLN6, CLN8, CTSD, etc.) impair lysosomal function. Many subtypes exist; causative gene varies by breed.",
        "symptoms": "Juvenile form: 1–3 years onset with behavioral abnormalities, ataxia, vision loss leading to death. Adult-onset forms exist.",
        "inheritance": "Most are autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Prognosis is poor; no curative treatment. Pre-breeding genetic testing is essential.",
    },
    "late-onset-ataxia": {
        "title": "Late-Onset Ataxia (LOA / CAPN1)",
        "summary": "A cerebellar ataxia beginning in young adulthood, gradually progressing.",
        "mechanism": "Mutation in CAPN1 causes degeneration of cerebellar Purkinje cells. Reported in Jack Russell Terriers.",
        "symptoms": "Gait ataxia, head tremor, balance difficulties. Painless.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Symptomatic treatment only. QOL becomes challenging when severe.",
    },
    "spinocerebellar-ataxia": {
        "title": "Spinocerebellar Ataxia (SCA)",
        "summary": "An inherited disease causing progressive degeneration of spinal cord and cerebellum, with movement and balance impairment.",
        "mechanism": "Multiple causative genes (including KCNJ10) impair neuronal function.",
        "symptoms": "Gait ataxia, abnormal posture, progressive movement disorder.",
        "inheritance": "Autosomal recessive.",
        "advice": "Only symptomatic treatment available. Pre-breeding testing is key to prevention.",
    },
    "multidrug-resistance": {
        "title": "Multidrug Resistance (MDR1 / ABCB1)",
        "summary": "A genetic mutation causing severe adverse reactions to certain drugs (ivermectin, certain anticancer drugs, antidiarrheal agents).",
        "mechanism": "Mutation in ABCB1 (formerly MDR1) impairs the drug efflux pump at the blood-brain barrier. Drugs accumulate in the brain, causing neurotoxicity. Common in collie-related breeds.",
        "symptoms": "After administration of affected drugs: severe ataxia, seizures, coma, respiratory arrest.",
        "inheritance": "Autosomal (incomplete) dominant. One copy increases risk; two copies cause severe reactions.",
        "advice": "**Always declare MDR1 status to your veterinarian before any treatment**. Particularly avoid ivermectin, loperamide, and vincristine.",
    },
    "necrotizing-meningoencephalitis": {
        "title": "Necrotizing Meningoencephalitis (NME / Pug Encephalitis)",
        "summary": "A severe inherited autoimmune disease causing necrotizing inflammation of the brain. Common in Pugs and Maltese.",
        "mechanism": "Autoimmune reaction associated with MHC class II gene polymorphisms forms necrotic lesions in the brain and meninges.",
        "symptoms": "Onset at age 1–7 with seizures, behavioral abnormality, ataxia, blindness. Most dogs die within weeks to months.",
        "inheritance": "Polygenic genetic predisposition + environmental factors. Risk-genotype dogs show high disease incidence.",
        "advice": "Immunosuppressive therapy may slow progression but prognosis is poor. Reconsider breeding risk-genotype dogs.",
    },
    "lafora": {
        "title": "Lafora Disease (NHLRC1)",
        "summary": "A severe inherited neurological disease causing progressive myoclonic epilepsy from young adulthood.",
        "mechanism": "Mutation in NHLRC1 causes Lafora bodies (polyglucosan inclusions) to accumulate in neurons. Reported in Miniature Dachshunds, Basset Hounds.",
        "symptoms": "Onset at 5–10 years with brief myoclonic jerks → progressive seizures, cognitive decline.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Antiepileptic drugs may slow progression. Pre-breeding testing is the key to prevention.",
    },
    "narcolepsy": {
        "title": "Narcolepsy (HCRTR2)",
        "summary": "An inherited sleep disorder causing sudden loss of muscle tone and sleep attacks.",
        "mechanism": "Mutation in HCRTR2 impairs orexin receptor function, disrupting wake-sleep regulation. Reported in Dobermans.",
        "symptoms": "Sudden collapse and sleep attacks triggered by excitement or eating (cataplexy). Consciousness is preserved.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "CNS stimulants or tricyclic antidepressants can alleviate symptoms. Life prognosis is good.",
    },
    "neuroaxonal-dystrophy": {
        "title": "Neuroaxonal Dystrophy (NAD / PLA2G6)",
        "summary": "An inherited disease causing progressive axonal degeneration in central and peripheral nerves, leading to movement disorders.",
        "mechanism": "Mutation in PLA2G6 impairs lipid metabolism of nerve axon membranes. Reported in Spinones and Papillons.",
        "symptoms": "Onset at age 1–4 with progressive ataxia, falls, proprioceptive abnormalities.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Symptomatic care only. Physical therapy maintains QOL.",
    },
    "spongiform-leukoencephalomyelopathy": {
        "title": "Spongiform Leukoencephalomyelopathy (SLEM)",
        "summary": "A severe juvenile-onset hereditary disease causing vacuolar degeneration of brain and spinal cord white matter.",
        "mechanism": "Mitochondrial dysfunction causes degeneration of axonal myelin in central nervous system. Reported in Silky Terriers.",
        "symptoms": "Onset within weeks of birth with ataxia, seizures, growth arrest. Most die within months.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Prognosis is grave. Pre-breeding testing is essential.",
    },
    "globoid-cell-leukodystrophy": {
        "title": "Globoid Cell Leukodystrophy (Krabbe / GALC)",
        "summary": "A severe inherited metabolic disease causing abnormal myelin formation in central and peripheral nerves.",
        "mechanism": "Mutation in GALC causes galactocerebrosidase enzyme deficiency. Myelin degradation products accumulate, causing neurodegeneration.",
        "symptoms": "Onset at 1–6 months of age with movement abnormalities, seizures, failure to thrive. Most die within 1–2 years.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Bone marrow transplant research is ongoing; not yet practical. Pre-breeding testing is essential.",
    },
    "polyneuropathy": {
        "title": "Polyneuropathy (NDRG1, ARHGEF10)",
        "summary": "An inherited disease causing simultaneous dysfunction of multiple peripheral nerves, resulting in ataxia and muscle atrophy.",
        "mechanism": "Mutations in NDRG1 or ARHGEF10 impair peripheral nerve function. Reported in Greyhounds and Alaskan Malamutes.",
        "symptoms": "Young-onset hindlimb weakness, gait abnormality, muscle atrophy.",
        "inheritance": "Varies by breed (most are autosomal recessive).",
        "advice": "Symptomatic care only. Physical therapy and assistive devices maintain QOL.",
    },
    "episodic-falling": {
        "title": "Episodic Falling Syndrome (EFS / BCAN)",
        "summary": "An inherited disease causing episodic muscle stiffening and collapse triggered by excitement or exercise. Common in Cavalier King Charles Spaniels.",
        "mechanism": "Mutation in BCAN disrupts neuronal signaling, causing episodes during exertion.",
        "symptoms": "Episodes of muscle stiffness and falling triggered by excitement, exercise, or heat. Consciousness preserved. Recovery within seconds to minutes.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Avoid triggers (excitement, heat). Some cases respond to anticonvulsants.",
    },
    "l-2-hydroxyglutaric-aciduria": {
        "title": "L-2-Hydroxyglutaric Aciduria (L2HGA / L2HGDH)",
        "summary": "A rare inherited metabolic disease causing abnormal accumulation of metabolites and neurological symptoms. Reported in Staffordshire breeds.",
        "mechanism": "Mutation in L2HGDH causes deficiency of L-2-hydroxyglutaric acid degradation enzyme.",
        "symptoms": "Young-onset ataxia, seizures, behavioral abnormality, cognitive impairment.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Symptomatic care only. Common in Staffordshire Bull Terriers and American Staffordshire Terriers.",
    },
    "cerebellar-abiotrophy": {
        "title": "Cerebellar Abiotrophy",
        "summary": "An inherited neurological disease in which cerebellar Purkinje cells degenerate postnatally, causing ataxia.",
        "mechanism": "Causative genes vary by breed (GRM1, SPTBN2, etc.). Selective death of Purkinje cells.",
        "symptoms": "Onset at 3–12 months with gait wobbliness, head tremor, falls. Progressive.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Symptomatic care only. Calm environment helps maintain QOL.",
    },
    "sensory-neuropathy": {
        "title": "Sensory Neuropathy (SN / FAM134B)",
        "summary": "An inherited disease causing degeneration of peripheral sensory nerves, leading to loss of pain sensation and self-mutilation behavior.",
        "mechanism": "Mutation in FAM134B causes peripheral sensory nerve degeneration. Reported in Border Collies.",
        "symptoms": "Loss of sensation in extremities → self-mutilation → ulceration and infection. Motor function intact.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Affected dogs need prevention of self-mutilation (e.g., E-collar) and infection management.",
    },
    "myotonia-congenita": {
        "title": "Myotonia Congenita (CLCN1)",
        "summary": "An inherited myopathy in which muscles fail to relax after contraction.",
        "mechanism": "Mutation in CLCN1 impairs chloride channels in muscle cell membranes. Abnormal sustained electrical activity.",
        "symptoms": "Stiffness at onset of movement, falls, difficulty walking. Improves with continued exercise (warm-up phenomenon).",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Symptomatic care only. Avoid cold; warm up sufficiently.",
    },

    # ============================================================
    # 眼科系
    # ============================================================
    "cord1": {
        "title": "PRA - cord1 type (RPGRIP1)",
        "summary": "A PRA subtype with early cone degeneration (day vision affected first).",
        "mechanism": "Mutation in RPGRIP1 causes retinal photoreceptor dysfunction. Reported in Miniature Longhaired Dachshunds.",
        "symptoms": "Day vision abnormality from age 1–2 → progressive blindness.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Pre-symptom genotype identification is important. Dogs adapt well to blindness via other senses.",
    },
    "rcd3": {
        "title": "PRA - rcd3 type (PDE6A)",
        "summary": "An early-onset rapidly progressive PRA subtype, affecting puppies.",
        "mechanism": "Mutation in PDE6A causes early degeneration of rod photoreceptors.",
        "symptoms": "Night blindness from 6 months of age → complete blindness by 1–2 years.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Severe; early testing and breeding selection important.",
    },
    "cngb1-pra": {
        "title": "PRA - CNGB1 type",
        "summary": "A late-onset PRA subtype with relatively slow progression.",
        "mechanism": "Mutation in CNGB1 impairs retinal rod function.",
        "symptoms": "Night blindness from middle age, gradually involving day vision.",
        "inheritance": "Autosomal recessive.",
        "advice": "Slower progression allows good QOL with early detection.",
    },
    "rcd1": {
        "title": "PRA - rcd1 type (PDE6B)",
        "summary": "A severe early-onset PRA reported in Irish Setters; causes complete blindness in puppies.",
        "mechanism": "Mutation in PDE6B causes rapid degeneration of rod photoreceptors.",
        "symptoms": "Night blindness from few months of age → complete blindness by 1 year.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Severe PRA with poor prognosis. Pre-breeding testing essential.",
    },
    "rcd2": {
        "title": "PRA - rcd2 type (RD3)",
        "summary": "An early-onset PRA reported in collies and related breeds.",
        "mechanism": "Mutation in RD3 causes retinal photoreceptor degeneration.",
        "symptoms": "Night blindness from 6–12 weeks → progressive blindness.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Severe early-onset PRA. Pre-breeding testing essential.",
    },
    "cone-rod-dystrophy": {
        "title": "Cone-Rod Dystrophy (crd4 / RPGRIP1)",
        "summary": "A PRA subtype in which cones (day vision) degenerate first, followed by rods (night vision).",
        "mechanism": "Mutation in RPGRIP1 causes photoreceptor dysfunction. Reported in Poodles and Miniature Longhaired Dachshunds.",
        "symptoms": "Daytime vision abnormality from young age → night blindness → complete blindness. Painless.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Quality of life can be maintained after blindness. Pre-breeding testing important.",
    },
    "achromatopsia": {
        "title": "Achromatopsia / Day Blindness (CNGA3)",
        "summary": "A retinal disorder in which cone photoreceptors fail to function, causing impaired vision in bright environments.",
        "mechanism": "Mutation in CNGA3 prevents cone photoreceptor function. Color vision is lost; bright-light vision is impaired.",
        "symptoms": "Squinting in bright places, bumping into objects. Relatively preserved vision in dim light (rod function maintained).",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Unlike full blindness, dim-light environments preserve QOL.",
    },
    "collie-eye-anomaly": {
        "title": "Collie Eye Anomaly (CEA / NHEJ1)",
        "summary": "An inherited eye disease caused by abnormal development of retina, choroid, and sclera. Common in collies.",
        "mechanism": "Mutation in NHEJ1 disrupts eye development. Severity is a continuous spectrum from mild to severe.",
        "symptoms": "Mild: asymptomatic to mild vision impairment. Severe: hemorrhage, retinal detachment, blindness.",
        "inheritance": "Autosomal recessive (variable penetrance). 25% affected from carrier × carrier.",
        "advice": "Testing is essential for collies and Shelties. Severity varies widely between individuals.",
    },
    "hereditary-cataract": {
        "title": "Hereditary Cataract (HSF4)",
        "summary": "An inherited disease causing early lens opacity, leading to vision loss or blindness.",
        "mechanism": "Mutation in HSF4 disrupts lens protein formation. Reported in Boston Terriers and Staffies.",
        "symptoms": "Cataract progression from young age (months to years). Vision impairment to blindness.",
        "inheritance": "Varies by breed (recessive to dominant).",
        "advice": "Early detection allows surgical vision recovery in some cases. Consult an ophthalmology specialist.",
    },
    "glaucoma": {
        "title": "Primary Glaucoma (ADAMTS10, ADAMTS17, etc.)",
        "summary": "An inherited eye disease in which abnormally elevated intraocular pressure compresses the optic nerve, causing blindness.",
        "mechanism": "Anterior chamber angle obstruction or impaired aqueous humor drainage raises IOP. ADAMTS10/17 mutations involved. Common in Beagles, Cockers, Shih Tzus.",
        "symptoms": "Eye redness, corneal opacity, pupil dilation, pain, vision loss. Acute attacks are emergencies.",
        "inheritance": "Varies by breed and gene. Many are autosomal recessive or incomplete dominant.",
        "advice": "**Acute attacks require ophthalmologic intervention within 24 hours to preserve vision**. Regular tonometry is recommended.",
    },
    "congenital-stationary-night-blindness": {
        "title": "Congenital Stationary Night Blindness (CSNB / RPE65)",
        "summary": "An inherited eye disease causing congenital lack of night vision. Day vision is normal.",
        "mechanism": "Mutation in RPE65 impairs retinal rod cell visual cycle. Reported in Briards.",
        "symptoms": "Night blindness from birth, difficulty in dim light. Non-progressive (stationary).",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "QOL is maintained with sufficient night lighting. Gene therapy research is progressing.",
    },
    "cone-degeneration": {
        "title": "Cone Degeneration (CNGB3)",
        "summary": "A retinal disorder in which cone photoreceptors degenerate, impairing day vision and color perception.",
        "mechanism": "Mutation in CNGB3 causes degeneration of cone photoreceptors. Reported in Alaskan Malamutes.",
        "symptoms": "Day-vision difficulty from a few months of age, color vision loss. Night vision preserved.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "'Day blindness' distinct from full blindness. QOL preserved in dim environments.",
    },
    "stargardt": {
        "title": "Stargardt Disease (STGD1 / ABCA4)",
        "summary": "An inherited eye disease causing degeneration of the macular region of the retina from young age.",
        "mechanism": "Mutation in ABCA4 causes lipofuscin accumulation in the retinal pigment epithelium. Reported in Labradors.",
        "symptoms": "Central vision decline from age 1–2, progressive.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Pre-symptom genetic testing is important for breeding selection.",
    },
    "multifocal-retinopathy": {
        "title": "Canine Multifocal Retinopathy (CMR / BEST1)",
        "summary": "An inherited eye disease with multiple retinal elevations and detachments. Often slowly progressive.",
        "mechanism": "Mutation in BEST1 impairs retinal pigment epithelium function. Reported in Mastiff and Pyrenees breeds.",
        "symptoms": "Initially asymptomatic. Patchy retinal lesions visible from middle age. Vision impairment often mild.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Slowly progressive; early management maintains good QOL. Regular ophthalmologic exams recommended.",
    },

    # ============================================================
    # 血液・凝固系
    # ============================================================
    "willebrand-type-1": {
        "title": "von Willebrand Disease Type I (vWD1)",
        "summary": "An inherited disorder in which the von Willebrand factor is reduced, leading to prolonged bleeding.",
        "mechanism": "Mutation in vWF gene reduces the platelet-adhesion protein. Severity ranges from mild (Type I) to severe (Type II, III). Common in Dobermans.",
        "symptoms": "Difficulty stopping bleeding from trauma, nosebleeds, prolonged bleeding after dental work, bloody stools.",
        "inheritance": "Autosomal (incomplete) dominant. One copy = mild; two copies = more severe.",
        "advice": "Always declare to your veterinarian before surgery or extractions. Avoid aspirin and other antiplatelet drugs.",
    },
    "willebrand-type-2": {
        "title": "von Willebrand Disease Type II (vWD2)",
        "summary": "A moderate-to-severe form of vWD with more pronounced bleeding tendency than Type I.",
        "mechanism": "Qualitative mutation in vWF gene — the factor is present but dysfunctional.",
        "symptoms": "Prolonged bleeding after trauma or extractions, risk of spontaneous bleeding.",
        "inheritance": "Autosomal recessive (incomplete penetrance).",
        "advice": "Always inform veterinarian before surgery. Fresh-frozen plasma or vWF concentrate may be needed for bleeding.",
    },
    "willebrand-type-3": {
        "title": "von Willebrand Disease Type III (vWD3)",
        "summary": "The most severe form of vWD; life-threatening bleeding that cannot be controlled.",
        "mechanism": "Complete deficiency of vWF protein. Reported in Scottish Terriers.",
        "symptoms": "Severe bleeding from infancy. Dental procedures and trauma may be fatal.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "P/P dogs have very high surgical risk. Blood products must be prepared in advance.",
    },
    "factor-vii": {
        "title": "Factor VII Deficiency (F7)",
        "summary": "A mild-to-moderate coagulation disorder due to deficiency of clotting factor VII.",
        "mechanism": "Mutation in F7 reduces coagulation factor VII. Most cases are mild but problematic during surgery.",
        "symptoms": "Usually asymptomatic. Difficulty stopping bleeding during trauma or surgery.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Always perform clotting tests and declare before surgery. Fresh-frozen plasma for bleeding events.",
    },
    "prekallikrein": {
        "title": "Prekallikrein Deficiency (KLKB1)",
        "summary": "A coagulation system disorder showing abnormal APTT test values; rarely symptomatic.",
        "mechanism": "Mutation in KLKB1 delays the first stage of intrinsic coagulation pathway. Mostly asymptomatic.",
        "symptoms": "Usually asymptomatic. APTT prolongation may be seen on preoperative testing.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Suspect this when preoperative APTT is prolonged. Clinical impact is minimal.",
    },
    "pyruvate-kinase": {
        "title": "Pyruvate Kinase Deficiency (PK / PKLR)",
        "summary": "An inherited red blood cell metabolic disorder causing chronic hemolytic anemia.",
        "mechanism": "Mutation in PKLR reduces energy production in red blood cells. Cells are destroyed prematurely.",
        "symptoms": "Chronic anemia, lethargy, exercise intolerance, splenomegaly. Most severe by 2–5 years.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Bone marrow transplant is the only curative option. Transfusion and supportive care maintain QOL.",
    },
    "macrothrombocytopenia": {
        "title": "Congenital Macrothrombocytopenia (β1-tubulin)",
        "summary": "An inherited disorder of large platelets with reduced platelet counts. Often asymptomatic but requires caution during surgery.",
        "mechanism": "Mutation in TUBB1 (β1-tubulin) causes abnormal platelet formation. Common in Cavalier King Charles Spaniels.",
        "symptoms": "Mostly asymptomatic. Low platelet count on routine bloodwork, but function is usually preserved.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Notify veterinarian before surgery. Avoid misdiagnosis as thrombocytopenia.",
    },
    "methemoglobinemia": {
        "title": "Congenital Methemoglobinemia (CYB5R3)",
        "summary": "An inherited disease in which blood hemoglobin is unable to transport oxygen.",
        "mechanism": "Mutation in CYB5R3 deficiency of the enzyme that reduces oxidized hemoglobin (methemoglobin). Causes chronic cyanosis.",
        "symptoms": "Bluish-purple skin and mucous membranes (cyanosis), exercise intolerance, fatigue.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Affected dogs require veterinary monitoring with regular testing. Special caution during anesthesia.",
    },

    # ============================================================
    # 代謝・内分泌系
    # ============================================================
    "hyperuricosuria": {
        "title": "Hyperuricosuria (HUU / SLC2A9)",
        "summary": "An inherited disease causing abnormally elevated urinary uric acid, predisposing to urate stones.",
        "mechanism": "Mutation in SLC2A9 disrupts hepatic uric acid metabolism. Common in Dalmatians, Bulldogs.",
        "symptoms": "Frequent urination, hematuria, dysuria, kidney stones. Severe cases may cause urinary obstruction or renal failure.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Affected dogs need low-purine diet, increased water intake, regular urinalysis.",
    },
    "cobalamin-malabsorption": {
        "title": "Cobalamin Malabsorption (AMN, CUBN)",
        "summary": "An inherited disease causing impaired intestinal absorption of vitamin B12 (cobalamin), leading to neurological and hematologic disorders.",
        "mechanism": "Mutation in AMN or CUBN impairs cobalamin receptor function in the ileum.",
        "symptoms": "Failure to thrive, anemia, neurological signs (ataxia, seizures). Reported in Giant Schnauzers and others.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "**Cobalamin (B12) injection can improve symptoms** — treatable disease, so diagnosis is critical.",
    },
    "glycogen-storage-disease": {
        "title": "Glycogen Storage Disease (GSD / Various Types)",
        "summary": "A severe metabolic disorder in which glycogen cannot be broken down and accumulates. Symptoms vary by subtype.",
        "mechanism": "Mutations in GAA (Type II), GBE1 (Type IV), etc. cause glycogen metabolism enzyme deficiency.",
        "symptoms": "Type II: cardiac and skeletal muscle damage. Type IV: liver cirrhosis and neurological signs. Most severe in young dogs.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Prognosis for P/P is grave. Early diagnosis and supportive care.",
    },
    "mucopolysaccharidosis": {
        "title": "Mucopolysaccharidosis (MPS)",
        "summary": "A severe metabolic disease in which mucopolysaccharides cannot be degraded and accumulate in tissues, causing skeletal and organ abnormalities.",
        "mechanism": "Genetic deficiency of lysosomal enzymes results in accumulation of glycosaminoglycans. Multiple subtypes (MPS I/VI/VII, etc.).",
        "symptoms": "Facial deformity, joint abnormalities, growth retardation, cardiac problems, vision impairment. Poor life expectancy.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Prognosis for P/P is poor. Pre-breeding testing is essential.",
    },
    "copper-toxicosis": {
        "title": "Copper Toxicosis (COMMD1, ATP7A/B)",
        "summary": "An inherited disease causing abnormal accumulation of copper in the liver, leading to chronic hepatitis and cirrhosis.",
        "mechanism": "Mutations in COMMD1 / ATP7A / ATP7B impair copper excretion. Reported in Bedlington Terriers, Labradors.",
        "symptoms": "Anorexia, weight loss, ascites, jaundice. Progressive liver failure.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Low-copper diet and copper-chelating drugs can slow progression. Early diagnosis is important.",
    },
    "hyperphosphatemia": {
        "title": "Familial Hyperphosphatemia (FGF23)",
        "summary": "An inherited endocrine disorder of abnormally elevated serum phosphate.",
        "mechanism": "FGF23-related gene mutation disrupts phosphate metabolism. Causes abnormal mineralization of bones and soft tissues.",
        "symptoms": "Growth abnormalities, skeletal deformity, renal dysfunction. Severe cases have poor prognosis.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Affected dogs require low-phosphate diet and phosphate binders to slow progression.",
    },

    # ============================================================
    # 筋・運動系
    # ============================================================
    "exercise-induced-collapse": {
        "title": "Exercise-Induced Collapse (EIC / DNM1)",
        "summary": "An inherited disease in which the dog suddenly loses muscle tone and collapses after strenuous exercise. Reported in Labradors and others.",
        "mechanism": "Mutation in DNM1 transiently impairs neuronal synaptic transmission during exercise.",
        "symptoms": "After 5–15 minutes of strenuous exercise, hindlimb weakness and inability to walk. Consciousness preserved; usually recovers in 5–25 minutes.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Affected dogs should avoid strenuous exercise; consult veterinarian for participation in dog sports.",
    },
    "centronuclear-myopathy": {
        "title": "Centronuclear Myopathy (CNM / PTPLA)",
        "summary": "An inherited myopathy causing muscle weakness from young age. Also known as Labrador idiopathic myopathy.",
        "mechanism": "Mutation in PTPLA causes abnormal muscle cell architecture.",
        "symptoms": "Onset within months of birth with exercise intolerance, muscle weakness, gait abnormality. Worse in cold.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Symptomatic care only. Avoid strenuous exercise and cold environments.",
    },
    "limb-girdle-muscular-dystrophy": {
        "title": "Limb-Girdle Muscular Dystrophy (LGMD)",
        "summary": "An inherited myopathy causing progressive atrophy of limb-girdle muscles (shoulder and pelvis).",
        "mechanism": "Mutations in dystrophin-associated proteins (DMD, SGCD, etc.) cause abnormal muscle cell membrane structure.",
        "symptoms": "Young-onset shoulder and pelvic muscle atrophy, exercise intolerance, gait difficulty.",
        "inheritance": "X-linked recessive or autosomal recessive (depending on subtype).",
        "advice": "Symptomatic care only. Physical therapy and assistive devices maintain QOL.",
    },
    "skeletal-dysplasia-2": {
        "title": "Skeletal Dysplasia 2 (SD2 / COL11A2)",
        "summary": "A Labrador-specific inherited disorder of limb shortening and skeletal dysplasia.",
        "mechanism": "Mutation in COL11A2 disrupts collagen formation. Causes limb shortening and forelimb bowing.",
        "symptoms": "Onset within months of birth with limb shortening, forelimb bowing, joint abnormalities.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Orthopedic management and activity restriction maintain QOL.",
    },
    "myasthenia-gravis": {
        "title": "Congenital Myasthenia Gravis (CMG / CHRNE)",
        "summary": "An inherited disease causing muscle weakness due to neuromuscular junction dysfunction.",
        "mechanism": "Mutation in CHRNE impairs acetylcholine receptor function, disrupting signaling.",
        "symptoms": "Young-onset exercise intolerance, limb weakness, dysphagia.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Anticholinesterase drugs improve symptoms. Early diagnosis and treatment are key.",
    },

    # ============================================================
    # 腎・泌尿器系
    # ============================================================
    "cystinuria": {
        "title": "Cystinuria (SLC3A1, SLC7A9)",
        "summary": "An inherited disease causing excessive cystine excretion in urine, predisposing to cystine stones.",
        "mechanism": "Mutations in SLC3A1 / SLC7A9 impair renal tubular cystine reabsorption. Cystine stones form.",
        "symptoms": "Frequent urination, hematuria, dysuria, urinary obstruction. Severe in male dogs.",
        "inheritance": "Autosomal recessive or X-linked (depending on subtype).",
        "advice": "Affected dogs need low-protein diet, urinary alkalinization drugs, increased water intake. Males prone to obstruction.",
    },
    "familial-nephropathy": {
        "title": "Familial Nephropathy (COL4A4)",
        "summary": "An inherited disease causing progressive renal failure from young age. Reported in Cocker Spaniels and others.",
        "mechanism": "Mutation in COL4A4 weakens glomerular basement membrane, causing progressive renal decline.",
        "symptoms": "Polyuria-polydipsia → anorexia, vomiting → end-stage renal failure. Most onset between 6–24 months.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "P/P prognosis is poor. Early diagnosis with dietary and supportive therapy extends life.",
    },
    "renal-cystadenocarcinoma": {
        "title": "Renal Cystadenocarcinoma + Nodular Dermatofibrosis (RCND / FLCN)",
        "summary": "An inherited tumor syndrome with multiple kidney tumors and skin nodules. Specific to German Shepherd Dogs.",
        "mechanism": "Mutation in FLCN abolishes tumor-suppressor function, causing tumors in kidneys and skin.",
        "symptoms": "Multiple skin nodules from middle age → later renal tumors → renal failure.",
        "inheritance": "Autosomal dominant. One copy raises disease risk.",
        "advice": "Regular renal function tests and abdominal imaging are key to early detection.",
    },
    "x-linked-hereditary-nephropathy": {
        "title": "X-Linked Hereditary Nephropathy (XLHN / COL4A5)",
        "summary": "An inherited nephropathy with severe disease in male dogs. Reported in Samoyeds.",
        "mechanism": "Mutation in COL4A5 on X chromosome weakens the glomerular basement membrane.",
        "symptoms": "Males: polyuria-polydipsia from 3–6 months → progressive renal failure. Females: mild symptoms.",
        "inheritance": "X-linked recessive. Males affected with 1 copy; females are carriers.",
        "advice": "Male P/Y prognosis is poor. Early detection with dietary and supportive care.",
    },

    # ============================================================
    # 皮膚・被毛系
    # ============================================================
    "hnpk": {
        "title": "Hereditary Nasal Parakeratosis (HNPK / SUV39H2)",
        "summary": "An inherited skin disease in which the nasal skin becomes abnormally thickened, fissured, and crusted.",
        "mechanism": "Mutation in SUV39H2 causes hyperkeratosis of nasal skin. Common in Labradors.",
        "symptoms": "Hardening, crusting, fissures, bleeding of the nose tip. Painful.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Ointments and moisturizers maintain QOL. Not curable.",
    },
    "ichthyosis": {
        "title": "Ichthyosis (PNPLA1)",
        "summary": "An inherited skin disease in which skin sheds like fish scales.",
        "mechanism": "Mutations in PNPLA1 and other genes disrupt the skin's keratinization process. Common in Golden Retrievers.",
        "symptoms": "Whitish scaling all over the body, dryness, pruritus, abnormal sebum production.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Shampoo therapy and moisturizers control symptoms. Not curable.",
    },
    "coat-color-dilution-alopecia": {
        "title": "Coat Color Dilution Alopecia (CDA)",
        "summary": "An inherited alopecia occurring in dogs with diluted coat colors (Blue, Lilac, etc.).",
        "mechanism": "Abnormal melanin granule accumulation damages hair follicles. Develops in some dogs carrying the dilute gene (dd) and MLPH variant.",
        "symptoms": "Alopecia and crusting on dilute-colored areas from age 6 months to 2 years, with secondary infection. Non-dilute areas are normal.",
        "inheritance": "Develops in some dd carriers (polygenic).",
        "advice": "Skin care and antibiotics manage symptoms. Reconsider breeding affected dogs.",
    },
    "footpad-hyperkeratosis": {
        "title": "Hereditary Footpad Hyperkeratosis (HFH / FAM83G)",
        "summary": "An inherited skin disease causing abnormal thickening, hardening, and fissuring of the footpads.",
        "mechanism": "Mutation in FAM83G causes footpad hyperkeratosis. Reported in Irish Terriers and Dogue de Bordeaux.",
        "symptoms": "Young-onset hardening, fissuring, pain of all footpads. May cause difficulty walking.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Ointments and moisturizers maintain QOL. Not curable.",
    },

    # ============================================================
    # 免疫系
    # ============================================================
    "trapped-neutrophil-syndrome": {
        "title": "Trapped Neutrophil Syndrome (TNS / VPS13B)",
        "summary": "A disease in which neutrophils (white blood cells) cannot migrate from the bone marrow into the bloodstream, causing chronic immunodeficiency.",
        "mechanism": "Mutation in VPS13B impairs neutrophil migration. Common in Border Collies.",
        "symptoms": "Recurrent infections, fever, failure to thrive. Most die within 1 year.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "P/P prognosis is poor. Pre-breeding testing is the key to prevention.",
    },
    "severe-combined-immunodeficiency": {
        "title": "Severe Combined Immunodeficiency (SCID)",
        "summary": "A lethal inherited disease in which T cells and B cells fail to function, causing severe immunodeficiency.",
        "mechanism": "Mutations in RAG1/RAG2, DCLRE1C, and other genes block T/B cell development. Reported in Basset Hounds, Jack Russell Terriers.",
        "symptoms": "Recurrent severe infections from weeks of age, failure to thrive. Most die young without bone marrow transplant.",
        "inheritance": "Autosomal recessive or X-linked. 25% affected from carrier × carrier.",
        "advice": "Bone marrow transplant is the only curative option. Pre-breeding testing essential.",
    },
    "recurrent-inflammatory-pulmonary-disease": {
        "title": "Recurrent Inflammatory Pulmonary Disease (RIPD / AKNA)",
        "summary": "A Rottweiler-specific inherited immune disorder of recurrent pneumonia and bronchitis.",
        "mechanism": "Mutation in AKNA reduces airway mucosal immune function.",
        "symptoms": "Young-onset recurrent lung infections, respiratory distress, exercise intolerance.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Antibiotics and bronchodilators for symptomatic care. Severe cases require long-term management.",
    },

    # ============================================================
    # 発達・内分泌系
    # ============================================================
    "pituitary-dwarfism": {
        "title": "Pituitary Dwarfism (LHX3)",
        "summary": "An inherited disease of pituitary dysfunction with reduced growth hormone production, causing extreme stunted growth.",
        "mechanism": "Mutation in LHX3 disrupts development of the anterior pituitary. Reported in German Shepherds.",
        "symptoms": "Failure to grow, small body, hair coat abnormalities, hypothyroidism.",
        "inheritance": "Autosomal recessive. 25% affected from carrier × carrier.",
        "advice": "Growth hormone and thyroid hormone replacement therapy can improve QOL.",
    },
    "persistent-mullerian-duct-syndrome": {
        "title": "Persistent Müllerian Duct Syndrome (PMDS / AMHR2)",
        "summary": "An inherited developmental disorder in which male dogs retain female internal genitalia (uterus, oviducts). Outward appearance is male.",
        "mechanism": "Mutation in AMHR2 abolishes anti-Müllerian hormone action, preventing regression of female internal genitalia. Reported in Miniature Schnauzers.",
        "symptoms": "Outwardly male but reduced fertility, urinary tract infections, prostatic problems.",
        "inheritance": "Autosomal recessive. X-linked inheritance.",
        "advice": "Some affected dogs require surgical intervention. Pre-breeding testing is the key to prevention.",
    },

    # ============================================================
    # 消化器系
    # ============================================================
    "gastric-and-intestinal-polyposis": {
        "title": "Gastric and Intestinal Polyposis (GP)",
        "summary": "An inherited disease with multiple polyps in stomach and intestine, increasing risk of bleeding and obstruction.",
        "mechanism": "Hereditary tendency for polyp formation. Reported in Jack Russell Terriers.",
        "symptoms": "Recurrent gastrointestinal symptoms, bloody stools, weight loss, vomiting.",
        "inheritance": "Autosomal recessive or dominant.",
        "advice": "Regular endoscopy for polyp management. Risk of malignancy exists.",
    },
}


TRAIT_EN = {
    "e-locus": {
        "title": "E Locus (MC1R) — Eumelanin Master Switch",
        "summary": "The 'master switch' determining whether the coat produces black/brown pigment (eumelanin).",
        "mechanism": "When MC1R is active, the dog produces eumelanin. In e/e homozygotes (recessive), MC1R is inactive, so the coat is only red/yellow/cream/white (skin and footpad pigment is unaffected).",
        "phenotype": "E/E, E/e: Coat can express black/brown pigment (subject to K and A loci).\nee: Coat is cream–apricot–red (KITLG determines shade).",
        "advice": "Even ee dogs may have black or brown nose, paws, and eye rims, depending on the B locus.",
    },
    "k-locus": {
        "title": "K Locus (CBD103) — Dominant Black",
        "summary": "Determines whether the coat is solid (one color) or shows agouti patterns.",
        "mechanism": "KB (dominant) in one copy suppresses A locus expression, producing solid coat. ky/ky allows A locus patterns (sable, tan point, etc.). kbr causes brindle.",
        "phenotype": "KB/_ : Solid (black, brown, or diluted depending on E and B).\nky/ky : A locus patterns (sable, tan point, etc.)\nkbr/_  : Brindle",
        "advice": "Maintain KB to preserve solid coat. Cross ky/ky × ky/ky to express patterns.",
    },
    "a-locus": {
        "title": "A Locus (ASIP) — Agouti Pattern",
        "summary": "Determines coat pattern when K locus is ky/ky.",
        "mechanism": "Dominance order: ay > aw > at > a. ay=sable, aw=wild sable, at=tan point, a=recessive black.",
        "phenotype": "ay/_ : Fawn/Sable\naw/_ : Wild Sable\nat/_ : Black-and-Tan/Tricolor (Doberman-like)\na/a : Recessive Black (solid black)",
        "advice": "Visible coat pattern depends on A locus + K locus + E locus combination.",
    },
    "b-locus": {
        "title": "B Locus (TYRP1) — Brown Pigment",
        "summary": "Determines whether eumelanin appears as black or is converted to brown.",
        "mechanism": "When TYRP1 function is lost (bb homozygous), all black pigment is converted to brown. In ee dogs, B does not affect coat color since there is no eumelanin in coat; only affects nose and footpad pigment.",
        "phenotype": "B/_ : Normal black pigment\nbb : All black converted to brown (chocolate/liver). With ee, coat is cream-apricot but nose is brown.",
        "advice": "bb is required to maintain chocolate color.",
    },
    "d-locus": {
        "title": "D Locus (MLPH) — Dilute",
        "summary": "A gene that dilutes pigment concentration. Black → Blue, Brown → Lilac/Isabella, Yellow → Champagne.",
        "mechanism": "Loss of MLPH function (dd homozygous) prevents uniform distribution of melanin granules, resulting in lighter color.",
        "phenotype": "D/_ : Normal\ndd : Diluted. Black→Blue, Brown→Lilac/Isabella, Yellow→Champagne",
        "advice": "Weimaraner's gray and French Bulldog's blue are due to dd.",
    },
    "m-locus": {
        "title": "M Locus (PMEL17) — Merle Pattern",
        "summary": "A gene producing irregular spotted patches (merle) on the coat. M/M (double merle) carries serious health risks.",
        "mechanism": "Mutation in PMEL17 partially disrupts melanocyte function, producing mottled patterns. M/M carries high risk of blindness and deafness.",
        "phenotype": "m/m : No merle\nM/m : Merle phenotype\nM/M : Double merle (more white area, high risk of visual/auditory impairment)",
        "advice": "**M/m × M/m crosses are strictly prohibited**. 25% of offspring will be double merle.",
    },
    "s-locus": {
        "title": "S Locus (MITF) — Piebald/Parti",
        "summary": "Determines presence of white patches on the coat.",
        "mechanism": "Promoter mutation in MITF restricts melanocyte distribution, producing white coat regions.",
        "phenotype": "S/S : No or minimal white\nS/sp : Mild white markings\nsp/sp : Piebald/Parti (high white percentage)",
        "advice": "Parti-poodles are sp/sp. Other genes (Irish spotting, etc.) also influence white expression.",
    },
    "g-locus": {
        "title": "G Locus (Greying / PMEL17) — Progressive Greying",
        "summary": "A gene causing puppies born with color to gradually fade as they mature. Cause of silver Poodles and similar.",
        "mechanism": "G_ causes progressive melanin loss in coat hair after birth. Greying typically progresses by 1–2 years.",
        "phenotype": "g/g: No greying\nG/g or G/G: Adult fading\n  Black + G_  → Silver\n  Brown + G_  → Silver Beige\n  Blue + G_   → Silver (lighter)",
        "advice": "Silver Poodles are born black. Greying gradually develops over the first 1–2 years. M locus (Merle) is a different gene despite both involving PMEL17.",
    },
    "furnishings": {
        "title": "Furnishings (RSPO2)",
        "summary": "A gene producing furnished facial hair (eyebrows, beard, mustache).",
        "mechanism": "Insertion mutation in RSPO2 increases facial hair density.",
        "phenotype": "F/F or F/N: Furnished (terrier, doodle types)\nN/N: Smooth-coated",
        "advice": "Strongly affects appearance of doodle breeds (Labradoodle, etc.).",
    },
    "curly-coat": {
        "title": "Curly Coat (KRT71)",
        "summary": "Determines whether the coat is straight or curly.",
        "mechanism": "Mutation in KRT71 produces curly hair.",
        "phenotype": "C/C or C/N: Curly coat\nN/N: Straight coat",
        "advice": "Poodles and Bichons Frise are C/C homozygous. Combined with Furnishings (F locus), produces various coat types.",
    },
    "l-locus": {
        "title": "L Locus (FGF5) — Hair Length",
        "summary": "Determines short hair vs long hair. Long hair is recessive.",
        "mechanism": "Mutation in FGF5 alters hair cycle. L/L is short, l/l is long.",
        "phenotype": "L/L: Short coat\nL/l: Short coat (carrier)\nl/l: Long coat",
        "advice": "Poodles, Yorkshire Terriers, Papillons are l/l homozygous. Combines with KRT71 (Curly) and RSPO2 (Furnishings) for diverse coat types.",
    },
    "shedding": {
        "title": "SD Locus (MC5R) — Shedding",
        "summary": "Determines amount of coat shedding. Most breeds carry 1 or 2 alleles.",
        "mechanism": "Mutations in MC5R affect coat-shedding cycle. SD/SD homozygous = heavy shedding; N/N = minimal shedding.",
        "phenotype": "SD/SD: Heavy shedding\nSD/N: Moderate\nN/N: Minimal shedding",
        "advice": "Poodles and doodles are N/N with minimal shedding (sometimes called 'hypoallergenic'; not 100% hair-free).",
    },
    "bob-tail": {
        "title": "BT Locus (Brachyury / T Gene) — Natural Bob Tail",
        "summary": "A gene producing a naturally short tail. BT/BT homozygotes are embryonic lethal.",
        "mechanism": "Mutation in Brachyury (T) gene shortens tail development. Homozygotes are embryonic lethal.",
        "phenotype": "BT/BT: Embryonic lethal (not born)\nBT/N: Natural bob tail\nN/N: Normal tail length",
        "advice": "**BT/BT × BT/BT crosses are strictly prohibited** — embryos are not born. Common in Welsh Corgis, Bobtails, Boxers.",
    },
    "em-locus": {
        "title": "Em Locus (MC1R) — Melanistic Mask",
        "summary": "A gene producing a black mask on the face. A specific MC1R variant.",
        "mechanism": "The Em variant of the E locus (MC1R) is dominant, concentrating black pigment on the face. Different mutation from E locus itself.",
        "phenotype": "Em/Em or Em/E: Mask present\nE/E (no Em): No mask",
        "advice": "Typical in German Shepherds, Pugs, Boxers. Not expressed in ee dogs (no eumelanin in coat).",
    },
}
