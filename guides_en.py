"""guides_en.py — GUIDES の英語翻訳オーバーレイ

⚠️ **重要な免責事項**:
このファイルの英訳は AI モデル (Claude) が日本語版から自動生成したものです。
獣医遺伝学者・専門編集者による監修を経ていません。Orivet 名で公開する前にレビューが必須です。

構造:
    GUIDES_EN[slug] = {
        "title": "...",
        "summary": "...",
        "category": "...",            # 表示用カテゴリ（絵文字 + 英語）
        "reading_time": "X min",
        "sections": [
            {"heading": "...", "body": "..."},
            ...
        ],
        "reviewed": True/False,       # 獣医・編集者監修済フラグ（既定 False）
        "reviewer": "...",            # 監修者名（任意）
        "reviewed_date": "YYYY-MM-DD",
    }

監修ワークフロー: kb_en.py と同じ。reviewed=True のエントリは UI で『✅ Reviewed translation』を表示。
未監修エントリは『⚠️ AI translation — pending review』を表示。

poodle_genetics.py 側の get_guides_localized() でマージされる。部分英訳でも問題ない
（未収録 slug は日本語版にフォールバック）。
"""

GUIDES_EN = {
    # ====================================================================
    # 🔰 Beginner guides
    # ====================================================================
    "how-to-read-orivet-results": {
        "title": "How to Read Your Orivet Genetic Test Results",
        "summary": "When you receive your Orivet genetic test PDF, this guide explains how to read the results, what the terms mean, and what to do next.",
        "category": "🔰 Beginner",
        "reading_time": "5 min",
        "sections": [
            {
                "heading": "📄 What is in the test PDF",
                "body": (
                    "An Orivet genetic test PDF contains two main result categories: <strong>Health conditions</strong> and <strong>Traits (coat color, etc.)</strong>. "
                    "Each item is reported as one of <strong>N/N (Normal)</strong>, <strong>P/N (Carrier)</strong>, or <strong>P/P (Affected)</strong>."
                ),
            },
            {
                "heading": "🟢 N/N — Normal (Clear)",
                "body": (
                    "Both inherited copies of the gene are normal. "
                    "There is no genetic risk of developing the condition, and the dog will not pass a mutant copy to offspring."
                ),
            },
            {
                "heading": "🟡 P/N — Carrier",
                "body": (
                    "Heterozygote — one mutant copy inherited from one parent. "
                    "For most autosomal recessive conditions the carrier <strong>does not develop the disease</strong>, but will transmit the mutant allele to ~50% of offspring. "
                    "When breeding, avoid pairing with another P/P or P/N dog to prevent producing affected puppies."
                ),
            },
            {
                "heading": "🔴 P/P — Affected (At Risk)",
                "body": (
                    "Homozygote — mutant copies inherited from both parents. "
                    "For autosomal recessive disease, this dog <strong>will develop the condition</strong>. Age of onset and severity vary by disease. "
                    "Regular veterinary health checks are recommended."
                ),
            },
            {
                "heading": "💡 What to do next",
                "body": (
                    "1. If any item is P/P, <strong>consult your veterinarian first</strong>. Many conditions allow pre-clinical intervention.<br>"
                    "2. For P/N carriers, plan breeding carefully — avoid mating two carriers of the same variant.<br>"
                    "3. To share results, use the Excel download feature to export the report.<br>"
                    "4. Visit the <strong>Glossary</strong> for detailed mechanism, inheritance pattern, and advice on each condition."
                ),
            },
        ],
    },

    "coi-basics": {
        "title": "COI (Coefficient of Inbreeding) Explained — What the Number Means",
        "summary": "What COI (Coefficient of Inbreeding) really measures, at what level it becomes risky, and intuitive comparisons to human relationships.",
        "category": "🐕 Breeding",
        "reading_time": "4 min",
        "sections": [
            {
                "heading": "📊 What is COI?",
                "body": (
                    "The Coefficient of Inbreeding (COI) is the probability that a puppy will inherit two identical copies of the same allele from a common ancestor shared by sire and dam. "
                    "Sewall Wright established this metric in 1922, and it remains the foundational measure for canine breeding decisions."
                ),
            },
            {
                "heading": "🎚 Tiers (with human-relationship equivalents)",
                "body": (
                    "<table style='width:100%;border-collapse:collapse;'>"
                    "<tr><th style='text-align:left;padding:6px 10px;background:#f3f4f6;'>COI</th><th style='text-align:left;padding:6px 10px;background:#f3f4f6;'>Human equivalent</th></tr>"
                    "<tr><td style='padding:6px 10px;color:#22c55e;'><strong>0%</strong></td><td>Completely unrelated parents</td></tr>"
                    "<tr><td style='padding:6px 10px;color:#22c55e;'><strong>~6.25%</strong></td><td>First-cousin mating — generally acceptable</td></tr>"
                    "<tr><td style='padding:6px 10px;color:#eab308;'><strong>6.25–12.5%</strong></td><td>Half-sibling mating — reduced immunity and fertility trends</td></tr>"
                    "<tr><td style='padding:6px 10px;color:#ef4444;'><strong>12.5–25%</strong></td><td>Full-sibling or parent–offspring mating — sharply increased genetic disease risk</td></tr>"
                    "<tr><td style='padding:6px 10px;color:#dc2626;'><strong>&gt;25%</strong></td><td>Repeated close inbreeding — recessive disease incidence rises exponentially</td></tr>"
                    "</table>"
                ),
            },
            {
                "heading": "⚠️ Health risks of high-COI dogs",
                "body": (
                    "In high-COI dogs, previously hidden recessive diseases are more likely to surface. Reduced immune function, fertility, and lifespan have also been reported. "
                    "Breed associations such as JKC and FCI frequently recommend keeping COI at or below 6.25%, particularly when selecting stud dogs."
                ),
            },
            {
                "heading": "🔧 Calculating COI with this tool",
                "body": (
                    "Our <strong>breeding simulator</strong> calculates Wright's COI automatically from three generations of pedigree data. "
                    "It also visualizes where and how often each common ancestor appears, so you can apply the result directly to breeding decisions."
                ),
            },
        ],
    },

    "color-genetics-basics": {
        "title": "Basics of Canine Coat Color Genetics — The Role of the 8 Loci",
        "summary": "A dog's coat color is determined by combinations of eight major loci (E / K / A / B / D / M / S / G). This guide summarizes each locus's role.",
        "category": "🎨 Coat Genetics",
        "reading_time": "6 min",
        "sections": [
            {
                "heading": "🎨 How coat color is layered",
                "body": (
                    "Coat color is not controlled by a single gene but by a combination of loci. "
                    "First, the <strong>E locus</strong> determines whether eumelanin (black-series pigment) can be produced. "
                    "The <strong>K locus</strong> then decides solid vs. patterned. "
                    "<strong>B</strong> sets black vs. brown, <strong>D</strong> controls dilution, <strong>M/S</strong> govern patterning, and <strong>G</strong> drives age-related fading."
                ),
            },
            {
                "heading": "🔌 E locus (MC1R) — Master pigment switch",
                "body": (
                    "<strong>E_</strong> allows black/brown pigment to be expressed in the coat. "
                    "<strong>e/e</strong> homozygotes show only cream / apricot / red in the coat, "
                    "but nose, pads, and eye rims still produce pigment and remain influenced by the B locus."
                ),
            },
            {
                "heading": "🎯 K locus (CBD103) — Dominant black",
                "body": (
                    "<strong>KB_</strong> produces a solid color and masks A-locus patterning. "
                    "<strong>ky/ky</strong> allows A-locus patterns (sable, tan-point, etc.) to appear. "
                    "<strong>kbr_</strong> produces brindle."
                ),
            },
            {
                "heading": "🎭 A locus (ASIP) — Agouti patterning",
                "body": (
                    "Expressed when K = ky/ky. Dominance: <strong>ay &gt; aw &gt; at &gt; a</strong>. "
                    "ay = fawn / sable, aw = wild sable, at = black-and-tan / tricolor, a/a = recessive black."
                ),
            },
            {
                "heading": "🍫 B locus (TYRP1) — Brown pigment",
                "body": (
                    "<strong>B_</strong> produces normal black pigment. <strong>bb</strong> converts all black pigment to brown (chocolate / liver). "
                    "In <strong>ee</strong> dogs, B does not affect coat color and is only visible in nose / pad pigment."
                ),
            },
            {
                "heading": "💧 D locus (MLPH) — Dilution",
                "body": (
                    "<strong>dd</strong> dilutes pigment density: Black → Blue, Brown → Lilac / Isabella, Yellow → Champagne. "
                    "Blue Weimaraners and blue French Bulldogs owe their color to this locus."
                ),
            },
            {
                "heading": "🎨 M / S / G loci",
                "body": (
                    "<strong>M locus (PMEL17)</strong>: Merle patterning. M/M (double merle) carries a high risk of vision and hearing impairment.<br>"
                    "<strong>S locus (MITF)</strong>: Piebald / parti-color.<br>"
                    "<strong>G locus (Greying)</strong>: Progressive fading with age, as seen in silver Poodles."
                ),
            },
        ],
    },

    "breeders-checklist": {
        "title": "Breeder's Checklist for Healthy Litters",
        "summary": "A checklist of items every breeder should verify before mating to produce healthy puppies.",
        "category": "🐕 Breeding",
        "reading_time": "5 min",
        "sections": [
            {
                "heading": "✅ Must-check items before breeding",
                "body": (
                    "□ Both parents have genetic test results (at least 12–14 panel items)<br>"
                    "□ Parents are not both P/P or P/N for the same variant (avoid producing affected pups for recessive disease)<br>"
                    "□ COI is within acceptable range (ideally ≤ 6.25%)<br>"
                    "□ For the M locus (Merle), avoid M/m × M/m (double merle is contraindicated)<br>"
                    "□ For the BT locus (natural bobtail), BT/BT × BT/BT is embryonically lethal<br>"
                    "□ vWD / MDR1 carrier results shared with your veterinarian<br>"
                    "□ Pedigree confirmed for 3–5 generations on both sides"
                ),
            },
            {
                "heading": "⚠️ Cases to reconsider breeding",
                "body": (
                    "<strong>1. Both parents are carriers of the same high-severity disease</strong>: 25% chance of an affected pup.<br>"
                    "<strong>2. M/m × M/m</strong>: double-merle risk — blindness and deafness.<br>"
                    "<strong>3. COI &gt; 12.5%</strong>: substantially elevated health and fertility risks.<br>"
                    "<strong>4. Parent has a serious heritable disease</strong>: high transmission probability.<br>"
                    "<strong>5. Breeding without testing</strong>: ethical concern — pups born to unknown risk."
                ),
            },
            {
                "heading": "📋 Recommended baseline panel",
                "body": (
                    "Specific recommendations vary by breed, but the following are widely important:<br>"
                    "・<strong>DM (Degenerative Myelopathy)</strong> — SOD1<br>"
                    "・<strong>CDDY + IVDD</strong> — FGF4 / intervertebral disc disease<br>"
                    "・<strong>vWD I / II / III</strong> — coagulation factors<br>"
                    "・<strong>prcd-PRA</strong> — progressive retinal atrophy<br>"
                    "・<strong>MDR1</strong> — drug sensitivity<br>"
                    "For breed-specific diseases (e.g., NEwS in Standard Poodles, CNM in Labradors), check the breed-specific entries in our <strong>Glossary</strong>."
                ),
            },
            {
                "heading": "📊 Pre-validate with the simulator",
                "body": (
                    "Our breeding simulator predicts puppy-genotype probabilities from the proposed sire / dam genotypes in advance. "
                    "Run color simulation, health risk prediction, and COI calculation together before committing to a mating."
                ),
            },
        ],
    },

    "severity-explained": {
        "title": "How Severity Grades (🔴🟡🟢) Are Assigned",
        "summary": "What criteria drive the severity badges in our glossary, and how you should interpret them.",
        "category": "🔰 Beginner",
        "reading_time": "3 min",
        "sections": [
            {
                "heading": "🚦 Three-tier severity",
                "body": (
                    "Each disease entry in the glossary and report carries one of three severity badges:<br>"
                    "🔴 <strong>High risk</strong>: poor prognosis, high mortality, or life-threatening course<br>"
                    "🟡 <strong>Medium risk</strong>: progressive or requiring symptomatic care, but quality of life can be maintained<br>"
                    "🟢 <strong>Low risk</strong>: usually asymptomatic or mild, requiring only limited attention"
                ),
            },
            {
                "heading": "🤖 How grading works",
                "body": (
                    "Grading is two-step:<br>"
                    "1. Automatic inference from KB entry text (keywords like 'poor prognosis', 'fatal').<br>"
                    "2. Entries where automatic inference was wrong are manually pinned via an explicit <code>severity</code> field (override)."
                ),
            },
            {
                "heading": "⚠️ Important disclaimer",
                "body": (
                    "Severity reflects the <strong>general tendency</strong> of a disease and does not predict the outcome for any individual dog. "
                    "Actual disease severity depends heavily on:<br>"
                    "・breed<br>"
                    "・genotype (P/N carrier vs. P/P affected)<br>"
                    "・comorbidities<br>"
                    "・environmental factors<br>"
                    "Always discuss diagnosis and treatment with your <strong>veterinarian</strong>."
                ),
            },
            {
                "heading": "🔍 Using the severity filter",
                "body": (
                    "Use the 🚦 filter on the glossary page to browse diseases by severity. "
                    "When planning breeding, we recommend prioritizing testing for <strong>high-risk diseases</strong>."
                ),
            },
        ],
    },

    # ====================================================================
    # 🐩🐕 Breed-specific guides
    # ====================================================================
    "poodle-genetic-health-guide": {
        "title": "Poodle Owner / Breeder Genetic Testing Guide",
        "summary": "A guide to the most important inherited diseases and coat-color genetics for Standard, Miniature, Toy, and Tiny Poodles.",
        "category": "🐩 Breed-specific",
        "reading_time": "7 min",
        "sections": [
            {
                "heading": "🐩 Key genetic diseases in Poodles",
                "body": (
                    "Poodles are generally healthy but have several breed-specific conditions:<br>"
                    "・<strong>NEwS (Neonatal Encephalopathy)</strong> — specific to Standard Poodles. Fatal at 4–6 weeks of age. Carrier × carrier breeding is strictly contraindicated.<br>"
                    "・<strong>prcd-PRA (Progressive Rod-Cone Degeneration)</strong> — all sizes. Mid-life blindness.<br>"
                    "・<strong>vWD1 (von Willebrand Disease Type 1)</strong> — bleeding tendency. Disclose before surgery.<br>"
                    "・<strong>HSF4 cataract</strong> — reported in some lines.<br>"
                    "・<strong>DM (Degenerative Myelopathy)</strong> — reported in larger Poodles."
                ),
            },
            {
                "heading": "🎨 Poodle coat-color genetics",
                "body": (
                    "Poodles come in a wide variety of colors. Key loci:<br>"
                    "・<strong>E locus (MC1R)</strong> — controls cream / apricot / red base<br>"
                    "・<strong>K locus (CBD103)</strong> — solid black / brown (chocolate)<br>"
                    "・<strong>B locus (TYRP1)</strong> — bb produces brown (chocolate / liver)<br>"
                    "・<strong>D locus (MLPH)</strong> — dd dilutes to blue / silver-beige<br>"
                    "・<strong>G locus (Greying)</strong> — the cause of silver Poodles. Born black, fade with age.<br>"
                    "・<strong>S locus (MITF)</strong> — sp/sp produces parti-color"
                ),
            },
            {
                "heading": "✂ Poodle-specific coat traits",
                "body": (
                    "・<strong>C/C (KRT71)</strong> — curly coat (Poodles are uniformly C/C)<br>"
                    "・<strong>F/F (RSPO2)</strong> — furnishings (eyebrows, beard, ornamental hair)<br>"
                    "・<strong>l/l (FGF5)</strong> — long coat (Poodles are uniformly l/l)<br>"
                    "・<strong>N/N (MC5R)</strong> — low shedding (the basis for the 'hypoallergenic' reputation)<br>"
                    "Together these define the Poodle's curly, long, low-shedding coat."
                ),
            },
            {
                "heading": "🐕 Notes by size variety",
                "body": (
                    "<strong>Standard Poodle</strong>: NEwS risk is breed-specific. Also watch for hip dysplasia and SARDS. Prefer low-COI lines.<br>"
                    "<strong>Miniature Poodle</strong>: predisposed to patellar luxation and epilepsy.<br>"
                    "<strong>Toy / Tiny Poodle</strong>: hypoglycemia, hydrocephalus, and dental problems are common. Avoid breeding for extreme miniaturization."
                ),
            },
            {
                "heading": "💡 Recommended breeding steps for Poodles",
                "body": (
                    "1. Run at least the 8-item <strong>standard Poodle panel</strong> on both parents.<br>"
                    "2. Maintain <strong>COI ≤ 6.25%</strong> through line selection.<br>"
                    "3. Strictly avoid P/N × P/N crosses for <strong>NEwS / prcd-PRA / vWD1</strong>.<br>"
                    "4. Never breed a Merle (M locus) dog to another merle.<br>"
                    "5. Test puppies genetically as early as possible."
                ),
            },
        ],
    },

    "labrador-genetic-health-guide": {
        "title": "Labrador Owner / Breeder Genetic Testing Guide",
        "summary": "A guide to important inherited diseases and coat-color genetics for Labrador Retrievers, including breed-specific conditions like EIC and HNPK.",
        "category": "🐕 Breed-specific",
        "reading_time": "7 min",
        "sections": [
            {
                "heading": "🐕 Key genetic diseases in Labradors",
                "body": (
                    "As a popular breed, Labradors have an unusually rich set of genetic data:<br>"
                    "・<strong>EIC (Exercise-Induced Collapse)</strong> — breed-specific. Collapse after intense exercise.<br>"
                    "・<strong>CNM (Centronuclear Myopathy)</strong> — muscle weakness from a young age.<br>"
                    "・<strong>prcd-PRA</strong> — mid-life blindness.<br>"
                    "・<strong>HNPK (Hereditary Nasal Parakeratosis)</strong> — hardening and fissures of the nose. Common in Labradors.<br>"
                    "・<strong>Copper Toxicosis (COMMD1)</strong> — abnormal hepatic copper accumulation.<br>"
                    "・<strong>HUU (Hyperuricosuria)</strong> — reported in some lines.<br>"
                    "・<strong>SD2 (Skeletal Dysplasia 2)</strong> — abnormally short limbs.<br>"
                    "・<strong>CDDY + IVDD</strong> — intervertebral disc disease risk (especially in short-legged Labs)."
                ),
            },
            {
                "heading": "🎨 The three base colors of the Labrador",
                "body": (
                    "<strong>Black (E_, B_)</strong>: standard color. Both E and B functional.<br>"
                    "<strong>Yellow (e/e)</strong>: ee homozygote prevents black / brown pigment in the coat. "
                    "Shade ranges from pale cream to deep fox red (modulated by KITLG).<br>"
                    "<strong>Chocolate (bb)</strong>: bb homozygote converts black pigment to brown.<br>"
                    "<strong>Silver / Charcoal</strong>: dilution from dd (blue / champagne). "
                    "Silver Labradors remain controversial within the AKC. The Em (mask) allele can also appear."
                ),
            },
            {
                "heading": "🦴 Labrador-specific coat and conformation traits",
                "body": (
                    "・<strong>L/L (FGF5)</strong> — short coat (all Labradors are L/L). Occasional l/l 'fuzzy' Labradors do appear.<br>"
                    "・<strong>SD/SD (MC5R)</strong> — high shedding. Labradors are heavy shedders.<br>"
                    "・<strong>No furnishings (RSPO2 N/N)</strong> — smooth coat.<br>"
                    "・<strong>Em/E (MC1R variant)</strong> — a black mask is seen in some Labradors."
                ),
            },
            {
                "heading": "💡 Recommended Labrador breeding panel",
                "body": (
                    "Minimum panel:<br>"
                    "EIC, CNM, prcd-PRA, HNPK, CDDY, HUU, Copper Toxicosis, Centronuclear Myopathy.<br>"
                    "Because Labradors carry many breed-specific conditions, take advantage of the Embark or Orivet 'Labrador panel'."
                ),
            },
        ],
    },

    "doodle-genetic-health-guide": {
        "title": "Doodle Breeds (Goldendoodle / Labradoodle, etc.) Genetic Testing Guide",
        "summary": "For Poodle × Golden/Labrador and similar mixes, both parental breed panels are required. Coat prediction is also complex.",
        "category": "🐾 Breed-specific",
        "reading_time": "7 min",
        "sections": [
            {
                "heading": "🐾 What are doodle breeds?",
                "body": (
                    "F1 / F1B / F2 mixed breeds created by crossing a Poodle with another breed:<br>"
                    "・<strong>Goldendoodle</strong> — Poodle × Golden Retriever<br>"
                    "・<strong>Labradoodle / Australian Labradoodle</strong> — Poodle × Labrador<br>"
                    "・<strong>Bernedoodle</strong> — Poodle × Bernese Mountain Dog<br>"
                    "・<strong>Sheepadoodle</strong> — Poodle × Old English Sheepdog<br>"
                    "・<strong>Cavapoo</strong> — Poodle × Cavalier King Charles Spaniel<br>"
                    "Each combination requires the disease panels appropriate to <strong>both</strong> parental breeds."
                ),
            },
            {
                "heading": "🩺 Important doodle breeding panels",
                "body": (
                    "Cover the diseases of both parental breeds comprehensively:<br>"
                    "<strong>Poodle side</strong>: prcd-PRA, NEwS (Standard), vWD1, HSF4<br>"
                    "<strong>Golden side</strong>: prcd-PRA, Ichthyosis, cardiac panels<br>"
                    "<strong>Labrador side</strong>: EIC, CNM, HNPK, HUU, Copper Toxicosis<br>"
                    "<strong>Bernese side</strong>: DM, osteosarcoma risk, histiocytic sarcoma<br>"
                    "<strong>Cavalier side</strong>: Mitral Valve Disease, Macrothrombocytopenia, EFS, DM<br>"
                    "If both parents carry the same variant at P/N, doodles still face a 25% affected risk."
                ),
            },
            {
                "heading": "🎨 Predicting coat type",
                "body": (
                    "A doodle's 'Poodle-like' coat is governed by two loci in combination:<br>"
                    "<strong>C/C (KRT71 curly)</strong>: curly<br>"
                    "<strong>C/N</strong>: wavy<br>"
                    "<strong>N/N</strong>: straight<br>"
                    "<strong>F/F (RSPO2 furnishings)</strong>: full furnishings on the face, low shedding<br>"
                    "<strong>F/N</strong>: intermediate<br>"
                    "<strong>N/N (Improper Coat)</strong>: Lab/Golden-like smooth face<br>"
                    "F1 (purebred × purebred) puppies are usually F/N × C/N, so coat type varies across the litter.<br>"
                    "<strong>For the 'hypoallergenic' look, F/F + C/C + N/N (shedding) is ideal.</strong>"
                ),
            },
            {
                "heading": "💡 Advice for doodle breeders",
                "body": (
                    "1. Test <strong>both parents</strong> — testing only one is meaningless.<br>"
                    "2. <strong>COI</strong> can rise even between different breeds if they share an ancestor (e.g., the same Poodle line).<br>"
                    "3. <strong>Coat type is a probability prediction</strong>: even F/F C/C N/N × F/F C/C N/N produces some variation in F1.<br>"
                    "4. <strong>F1B is easier to predict than F1</strong> (F1 back-crossed to a Poodle).<br>"
                    "5. Prioritize health over coat — disease panels first, coat traits second."
                ),
            },
        ],
    },

    "shiba-genetic-health-guide": {
        "title": "Shiba Inu Genetic Testing & Health Guide",
        "summary": "Important inherited diseases (GM1 gangliosidosis, etc.) and coat-color genetics for the Shiba Inu, Japan's iconic native breed. Covered by Orivet panels.",
        "category": "🐕 Breed-specific",
        "reading_time": "6 min",
        "sections": [
            {
                "heading": "🐕 Key genetic diseases in Shiba Inu",
                "body": (
                    "Shibas are relatively healthy but have specific concerns:<br>"
                    "・<strong>GM1 Gangliosidosis (GLB1)</strong> — well-established fatal neurological disease in Shibas. Carrier × carrier crosses produce 25% affected.<br>"
                    "・<strong>Glaucoma</strong> — mid-life onset risk. Routine intraocular pressure checks help prevent blindness.<br>"
                    "・<strong>Atopic dermatitis</strong> — genetic predisposition with environmental triggers.<br>"
                    "・<strong>Patellar luxation</strong> — typical risk for a small/medium breed.<br>"
                    "・<strong>GM2 Gangliosidosis</strong> — reported in some lines (less frequent than GM1)."
                ),
            },
            {
                "heading": "🎨 Shiba coat-color genetics",
                "body": (
                    "The four Shiba colors arise from combinations of:<br>"
                    "<strong>Red</strong>: ay/_ ky/ky E_ B_ (agouti / sable expression)<br>"
                    "<strong>Black-and-Tan (Kuro-Goma)</strong>: at/at ky/ky E_ B_ (tan-point)<br>"
                    "<strong>Sesame (Goma)</strong>: ay/at with individual variation producing the mixed sesame appearance<br>"
                    "<strong>Cream / White</strong>: e/e (recessive). Less common.<br>"
                    "<strong>Urajiro (white underside)</strong>: the typical urajiro pattern is governed by a separate gene from the S locus."
                ),
            },
            {
                "heading": "💡 Shiba breeding recommendations",
                "body": (
                    "・<strong>GM1 testing is essential</strong> — particularly for Japanese breeders.<br>"
                    "・Maintaining the four coat colors (red, black-and-tan, sesame, cream) requires controlled inheritance at A / E / B loci.<br>"
                    "・Avoid extreme miniaturization, which increases health problems."
                ),
            },
        ],
    },

    "akita-genetic-health-guide": {
        "title": "Akita Inu Genetic Testing & Health Guide",
        "summary": "Important inherited conditions (DM, immune-mediated disease, etc.) and breed-specific traits in the Akita Inu. Covered by Orivet panels.",
        "category": "🐕 Breed-specific",
        "reading_time": "5 min",
        "sections": [
            {
                "heading": "🐕 Key genetic diseases in Akita Inu",
                "body": (
                    "・<strong>DM (Degenerative Myelopathy)</strong> — Akitas frequently carry the SOD1 risk allele.<br>"
                    "・<strong>VKH-like syndrome</strong> — autoimmune disease (ocular and dermal depigmentation). Common in Akitas.<br>"
                    "・<strong>Progressive Retinal Atrophy (PRA)</strong> — reported in some lines.<br>"
                    "・<strong>Hip dysplasia</strong> — typical large-breed concern.<br>"
                    "・<strong>Hypothyroidism</strong> — onset in middle to advanced age."
                ),
            },
            {
                "heading": "🎨 Akita coat colors",
                "body": (
                    "<strong>Red</strong>: ay/_ with the typical urajiro underlay<br>"
                    "<strong>White</strong>: e/e cream / white<br>"
                    "<strong>Sesame</strong>: agouti-driven mixed color<br>"
                    "<strong>Brindle</strong>: kbr allele expression (more common in American Akitas than Japanese Akitas)"
                ),
            },
            {
                "heading": "💡 Akita breeding recommendations",
                "body": (
                    "・<strong>DM testing</strong> at adulthood is essential — strictly avoid P/P × P/P crosses.<br>"
                    "・Select lines that account for autoimmune predisposition.<br>"
                    "・Keep COI low (Akitas have relatively low within-breed diversity)."
                ),
            },
        ],
    },

    "shar-pei-genetic-health-guide": {
        "title": "Shar-Pei Genetic Testing & Health Guide",
        "summary": "Familial Shar-Pei Fever and other skin / inflammatory conditions in the wrinkled breed. Covered by Orivet panels.",
        "category": "🐕 Breed-specific",
        "reading_time": "5 min",
        "sections": [
            {
                "heading": "🐕 Key genetic diseases in Shar-Pei",
                "body": (
                    "・<strong>Familial Shar-Pei Fever (FSF)</strong> — periodic fevers and joint swelling. Linked to amyloidosis risk. Breed-specific.<br>"
                    "・<strong>Progressive renal amyloidosis</strong> — a long-term complication of FSF.<br>"
                    "・<strong>Entropion / Ectropion</strong> — common in heavily wrinkled breeds.<br>"
                    "・<strong>Footpad hyperkeratosis</strong> — genetically reduced skin barrier function.<br>"
                    "・<strong>POAG (Primary Open-Angle Glaucoma)</strong>"
                ),
            },
            {
                "heading": "🎨 Shar-Pei coat and color",
                "body": (
                    "<strong>Colors</strong>: black, brown, cream, red, chocolate, and more.<br>"
                    "<strong>Coat types</strong>:<br>"
                    "・Horse coat (short, harsh)<br>"
                    "・Brush coat (slightly longer)<br>"
                    "・Bear coat (long, not FCI-accepted)<br>"
                    "The bear coat is caused by l/l at the FGF5 (L) locus."
                ),
            },
            {
                "heading": "💡 Shar-Pei breeding recommendations",
                "body": (
                    "・Confirm FSF / amyloidosis family history.<br>"
                    "・Avoid breeding for extreme wrinkling (skin disease risk).<br>"
                    "・Periodic renal function testing from a young age."
                ),
            },
        ],
    },

    "chin-genetic-health-guide": {
        "title": "Japanese Chin Genetic Testing & Health Guide",
        "summary": "Important inherited conditions and traits in the Japanese Chin, a traditional Japanese toy breed. Covered by Orivet panels.",
        "category": "🐕 Breed-specific",
        "reading_time": "4 min",
        "sections": [
            {
                "heading": "🐕 Key genetic diseases in the Japanese Chin",
                "body": (
                    "・<strong>GM2 Gangliosidosis</strong> — reported in some lines. Severe neurological disease.<br>"
                    "・<strong>Brachycephalic syndrome</strong> — respiratory and ophthalmologic risks from skull conformation.<br>"
                    "・<strong>Hydrocephalus</strong> — common toy-breed concern.<br>"
                    "・<strong>Patellar luxation</strong> — common in toy breeds.<br>"
                    "・<strong>Cataract</strong> — middle age and beyond."
                ),
            },
            {
                "heading": "🎨 Chin coat colors",
                "body": (
                    "<strong>Black &amp; White</strong>: at/at + piebald (sp/sp)<br>"
                    "<strong>Red &amp; White</strong>: ay/_ + piebald<br>"
                    "Heavy white markings are a hallmark, reflecting strong sp/sp expression at the S locus."
                ),
            },
            {
                "heading": "💡 Chin breeding recommendations",
                "body": (
                    "・Breed for conformation that reduces brachycephalic respiratory burden.<br>"
                    "・Do not push miniaturization to extremes.<br>"
                    "・Run genetic testing including GM2."
                ),
            },
        ],
    },

    "dachshund-genetic-health-guide": {
        "title": "Dachshund Genetic Testing & Health Guide",
        "summary": "Intervertebral disc disease (CDDY + IVDD) and PRA are particularly important for this iconic short-legged breed.",
        "category": "🐕 Breed-specific",
        "reading_time": "6 min",
        "sections": [
            {
                "heading": "🐕 Key genetic diseases in Dachshunds",
                "body": (
                    "・<strong>CDDY + IVDD (Intervertebral Disc Disease)</strong> — the most important Dachshund concern. The breed carries CDPA for short legs plus CDDY for disc disease risk.<br>"
                    "・<strong>CORD1 / PRA</strong> — especially in Miniature Long-Haired Dachshunds. Blindness risk.<br>"
                    "・<strong>Lafora disease</strong> — progressive myoclonic epilepsy. Reported in Miniatures.<br>"
                    "・<strong>Osteogenesis Imperfecta (OI)</strong> — reported.<br>"
                    "・<strong>Epilepsy</strong> — polygenic."
                ),
            },
            {
                "heading": "🎨 Dachshund coat and color",
                "body": (
                    "<strong>Colors</strong>: black-and-tan, chocolate-and-tan, red, cream, silver dapple (Merle), piebald, and more.<br>"
                    "<strong>Coat types</strong>: smooth (short), long-haired (l/l), wire-haired (F/F + curl in combination).<br>"
                    "⚠️ <strong>Dapple × Dapple breeding is strictly contraindicated</strong> (M/M double merle: blindness, deafness)."
                ),
            },
            {
                "heading": "💡 Dachshund care and breeding recommendations",
                "body": (
                    "・<strong>Disc protection</strong>: weight management, stair restriction, no jumping.<br>"
                    "・<strong>CDDY testing</strong>: recommended for all dogs.<br>"
                    "・<strong>PRA / Lafora testing</strong>: essential for Miniature Long-Haireds.<br>"
                    "・Strictly observe dapple-breeding rules."
                ),
            },
        ],
    },

    "french-bulldog-genetic-health-guide": {
        "title": "French Bulldog Genetic Testing & Health Guide",
        "summary": "Brachycephalic syndromes, inherited diseases, and blue-related (dd) CDA in this popular breed.",
        "category": "🐕 Breed-specific",
        "reading_time": "6 min",
        "sections": [
            {
                "heading": "🐕 Key genetic diseases in French Bulldogs",
                "body": (
                    "・<strong>Brachycephalic Obstructive Airway Syndrome (BOAS)</strong> — respiratory burden, elevated anesthetic risk.<br>"
                    "・<strong>Hemivertebrae</strong> — breed-specific vertebral malformation.<br>"
                    "・<strong>CDA (Color Dilution Alopecia)</strong> — frequent in blue (dd) French Bulldogs.<br>"
                    "・<strong>HUU (Hyperuricosuria)</strong> — reported in some lines.<br>"
                    "・<strong>Multiple cartilaginous exostoses</strong><br>"
                    "・<strong>Cataract / Cherry eye</strong>"
                ),
            },
            {
                "heading": "🎨 French Bulldog colors",
                "body": (
                    "<strong>Standard colors (FCI-accepted)</strong>: fawn, brindle, pied.<br>"
                    "<strong>Non-standard colors</strong>: blue (dd), chocolate (bb), lilac (bb dd), merle (M/_).<br>"
                    "Blue lines carry CDA risk. Merle is not FCI-accepted and carries health risk (strictly avoid M/M double merle)."
                ),
            },
            {
                "heading": "💡 French Bulldog breeding recommendations",
                "body": (
                    "・Breed from dogs that have been <strong>BOAS-scored</strong>.<br>"
                    "・Use spinal radiographs to check for vertebral malformation.<br>"
                    "・Cesarean rates are high — breeders must prepare for obstetric care.<br>"
                    "・If selecting dilute (dd) colors, be aware of CDA risk."
                ),
            },
        ],
    },

    "cavalier-genetic-health-guide": {
        "title": "Cavalier King Charles Spaniel Genetic Testing & Health Guide",
        "summary": "Mitral Valve Disease (MVD), Macrothrombocytopenia, EFS, and other Cavalier-specific concerns.",
        "category": "🐕 Breed-specific",
        "reading_time": "6 min",
        "sections": [
            {
                "heading": "🐕 Key genetic diseases in Cavaliers",
                "body": (
                    "・<strong>Mitral Valve Disease (MVD)</strong> — the leading cause of death in Cavaliers. Mid-life onset. Cardiac screening is essential.<br>"
                    "・<strong>Chiari-like Malformation / Syringomyelia (SM)</strong> — skull / cervical malformation causing neurological signs. MRI screening recommended.<br>"
                    "・<strong>Episodic Falling Syndrome (EFS / BCAN)</strong> — exertion-triggered episodes. Breed-specific.<br>"
                    "・<strong>Macrothrombocytopenia (TUBB1)</strong> — large platelets, usually asymptomatic.<br>"
                    "・<strong>DM (Degenerative Myelopathy)</strong> — reported in some lines.<br>"
                    "・<strong>Cataract (HSF4)</strong>"
                ),
            },
            {
                "heading": "🎨 The four Cavalier colors",
                "body": (
                    "<strong>Blenheim (red &amp; white)</strong>: ay/_ + piebald<br>"
                    "<strong>Tricolor (black, tan, white)</strong>: at/at + piebald<br>"
                    "<strong>Ruby (red)</strong>: e/e (recessive red)<br>"
                    "<strong>Black-and-Tan</strong>: at/at"
                ),
            },
            {
                "heading": "💡 Cavalier breeding recommendations",
                "body": (
                    "・Cardiac screen for <strong>MVD</strong> at adulthood and select breeders based on heart score.<br>"
                    "・<strong>MRI screening for SM</strong> is recommended despite the cost.<br>"
                    "・Run genetic testing for EFS / Macrothrombocytopenia / DM.<br>"
                    "・Within-breed COI tends to be high in Cavaliers, so low-COI line selection is important."
                ),
            },
        ],
    },

    "border-collie-genetic-health-guide": {
        "title": "Border Collie Genetic Testing & Health Guide",
        "summary": "Why this highly intelligent herding breed needs an extensive panel, and what to include.",
        "category": "🐕 Breed-specific",
        "reading_time": "7 min",
        "sections": [
            {
                "heading": "🐕 Key genetic diseases in Border Collies",
                "body": (
                    "Border Collies have one of the most thoroughly characterized canine genetic testing portfolios:<br>"
                    "・<strong>CEA (Collie Eye Anomaly)</strong> — developmental ocular anomaly.<br>"
                    "・<strong>TNS (Trapped Neutrophil Syndrome)</strong> — severe immune deficiency, fatal in puppies.<br>"
                    "・<strong>NCL (Neuronal Ceroid Lipofuscinosis)</strong> — progressive neurodegeneration.<br>"
                    "・<strong>MDR1 (Multi-Drug Resistance)</strong> — drug hypersensitivity (ivermectin, etc.).<br>"
                    "・<strong>SN (Sensory Neuropathy / FAM134B)</strong> — risk of self-mutilation.<br>"
                    "・<strong>CL (additional Ceroid Lipofuscinosis types)</strong><br>"
                    "・<strong>DM</strong>, <strong>epilepsy</strong>"
                ),
            },
            {
                "heading": "🎨 Border Collie's diverse colors",
                "body": (
                    "<strong>Standard colors</strong>: black &amp; white, red &amp; white, tricolor, blue &amp; white.<br>"
                    "<strong>Merle</strong>: blue merle, red merle, slate merle.<br>"
                    "<strong>Rare colors</strong>: lilac, seal, brindle.<br>"
                    "⚠️ <strong>Merle × Merle breeding is strictly contraindicated</strong> (M/M double merle)."
                ),
            },
            {
                "heading": "💡 Border Collie breeding recommendations",
                "body": (
                    "<strong>Minimum panel</strong>:<br>"
                    "CEA / TNS / NCL / MDR1 / IGS (B12)<br>"
                    "<strong>Recommended panel</strong>:<br>"
                    "DM / SN / all CL subtypes / EAOD (Early Adult-Onset Deafness)<br>"
                    "<strong>Athletic-breed considerations</strong>:<br>"
                    "As a high-drive working breed, also screen joints and watch for exercise-induced collapse."
                ),
            },
        ],
    },

    "german-shepherd-genetic-health-guide": {
        "title": "German Shepherd Genetic Testing & Health Guide",
        "summary": "DM, RCND, pituitary dwarfism, and other concerns for this highly intelligent, athletic breed.",
        "category": "🐕 Breed-specific",
        "reading_time": "6 min",
        "sections": [
            {
                "heading": "🐕 Key genetic diseases in German Shepherds",
                "body": (
                    "・<strong>DM (Degenerative Myelopathy)</strong> — progressive hindlimb paralysis in middle to senior age. SOD1 risk allele is common in this breed.<br>"
                    "・<strong>RCND (Renal Cystadenocarcinoma and Nodular Dermatofibrosis / FLCN)</strong> — a breed-specific tumor syndrome.<br>"
                    "・<strong>Pituitary Dwarfism (LHX3)</strong> — growth abnormality.<br>"
                    "・<strong>Hip dysplasia</strong> — typical large-breed concern. OFA / PennHIP screening recommended.<br>"
                    "・<strong>Elbow dysplasia</strong>, <strong>epilepsy</strong><br>"
                    "・<strong>Exocrine Pancreatic Insufficiency (EPI)</strong>"
                ),
            },
            {
                "heading": "🎨 German Shepherd coat colors",
                "body": (
                    "<strong>Standard colors</strong>: black-and-tan (Em/_ mask), sable.<br>"
                    "<strong>Rare colors</strong>: solid black (a/a), solid white (e/e + depigmentation), panda.<br>"
                    "The classic black-and-tan combines agouti at/at with an Em mask."
                ),
            },
            {
                "heading": "💡 German Shepherd breeding recommendations",
                "body": (
                    "・Run <strong>DM testing</strong> at adulthood — strictly avoid P/P × P/P.<br>"
                    "・<strong>Hip radiographs</strong> after 12 months of age.<br>"
                    "・Confirm family history for RCND.<br>"
                    "・As a large breed, keeping COI low is particularly important."
                ),
            },
        ],
    },

    "mini-schnauzer-genetic-health-guide": {
        "title": "Miniature Schnauzer Genetic Testing & Health Guide",
        "summary": "PMDS, hyperlipidemia, and juvenile cataracts are particularly important in this breed.",
        "category": "🐕 Breed-specific",
        "reading_time": "5 min",
        "sections": [
            {
                "heading": "🐕 Key genetic diseases in Miniature Schnauzers",
                "body": (
                    "・<strong>PMDS (Persistent Müllerian Duct Syndrome / AMHR2)</strong> — male dogs retain uterus / oviducts. Reported in Miniature Schnauzers.<br>"
                    "・<strong>Hyperlipidemia / Pancreatitis</strong> — genetic predisposition. Diet management is critical.<br>"
                    "・<strong>Juvenile cataract (HSF4)</strong> — reported in some lines.<br>"
                    "・<strong>Diabetes mellitus</strong> — risk rises in middle to senior age.<br>"
                    "・<strong>Urolithiasis</strong> (calcium oxalate stones)<br>"
                    "・<strong>Progressive Retinal Atrophy (PRA)</strong>"
                ),
            },
            {
                "heading": "🎨 Miniature Schnauzer colors",
                "body": (
                    "<strong>FCI-accepted colors</strong>: salt-and-pepper (G-locus fading), black-and-silver (at/at + G), solid black, white (e/e).<br>"
                    "<strong>Non-standard colors</strong>: chocolate (bb), parti-color (sp/sp)."
                ),
            },
            {
                "heading": "💡 Miniature Schnauzer breeding recommendations",
                "body": (
                    "・Feed a <strong>low-fat diet</strong> (pancreatitis prevention).<br>"
                    "・Run <strong>HSF4 / PRA testing</strong>.<br>"
                    "・Confirm family history of juvenile cataract.<br>"
                    "・Reconsider breeding male dogs affected by PMDS."
                ),
            },
        ],
    },
}
