exp_langs = ["spa_Latn", "fra_Latn", "hin_Deva", "ces_Latn", "pol_Latn", "tel_Telu", "mar_Deva", "deu_Latn", "vie_Latn", "tur_Latn"]
LANGS = {
    "eng_Latn": {
        "name": "English",
        "stanza_code": "en",
        "nllb_code": "eng_Latn",
        "iso3_code": "eng",
        "gtrans_code": "en",
        "ciphered_name": "Eldian",
        "ciphered_lang_info": "Eldian is a newly discovered Germanic language."
    },
    "spa_Latn": {
        "name": "Spanish",
        "stanza_code": "es",
        "nllb_code": "spa_Latn",
        "wmtpp_code": "es_MX",
        "iso3_code": "spa",
        "gtrans_code": "es",
        "ciphered_name": "Serra",
        "ciphered_lang_info": "Serra is a newly discovered Romance language.",
        "related_language_code": "fra_Latn",
    },
    "fra_Latn": {
        "name": "French",
        "stanza_code": "fr",
        "nllb_code": "fra_Latn",
        "iso3_code": "fra",
        "wmtpp_code": "fr_FR",
        "gtrans_code": "fr",
        "ciphered_name": "Gerestal",
        "ciphered_lang_info": "Gerestal is a newly discovered Romance language.",
        "related_language_code": "spa_Latn",
    },
    "deu_Latn": {
        "name": "German",
        "stanza_code": "de",
        "nllb_code": "deu_Latn",
        "wmtpp_code": "de_DE",
        "iso3_code": "deu",
        "gtrans_code": "de",
        "ciphered_name": "Markin",
        "ciphered_lang_info": "Markin is a newly discovered Germanic language."
    },
    "hin_Deva": {
        "name": "Hindi",
        "stanza_code": "hi",
        "nllb_code": "hin_Deva",
        "wmtpp_code": "hi_IN",
        "iso3_code": "hin",
        "gtrans_code": "hi",
        "ciphered_name": "Manthi",
        "ciphered_lang_info": "Manthi is a newly discovered Indic language.",
        "related_language_code": "mar_Deva",
    },
    "mar_Deva": {
        "name": "Marathi",
        "stanza_code": "mr",
        "nllb_code": "mar_Deva",
        "wmtpp_code": "mr_IN",
        "iso3_code": "mar",
        "gtrans_code": "mr",
        "ciphered_name": "Sakpuri",
        "ciphered_lang_info": "Sakpuri is a newly discovered Indic language.",
        "related_language_code": "hin_Deva",
    },
    # "arb_Arab": {
    #     "name": "Arabic",
    #     "stanza_code": "ar",
    #     "nllb_code": "arb_Arab",
    #     "wmtpp_code": "ar_SA",
    #     "iso3_code": "arb",
    #     "gtrans_code": "ar",
    #     "ciphered_name": "Qaramal",
    #     "ciphered_lang_info": "Qaramal is a newly discovered Semitic language."
    # },
    # "ind_Latn": {
    #     "name": "Indonesian",
    #     "stanza_code": "id",
    #     "nllb_code": "ind_Latn",
    #     "wmtpp_code": "id_ID",
    #     "iso3_code": "ind",
    #     "gtrans_code": "id",
    #     "ciphered_name": "Saurendi",
    #     "ciphered_lang_info": "Saurendi is a newly discovered Austronesian language."
    # }, # not supported by stanza ner
    # "zsm_Latn": {
    #     "name": "Malay",
    #     "stanza_code": "ms",
    #     "nllb_code": "zsm_Latn",
    #     "wmtpp_code": "ms_MY",
    #     "iso3_code": "msa",
    #     "gtrans_code": "ms",
    #     "ciphered_name": "Sulamal",
    #     "ciphered_lang_info": "Sulamal is a newly discovered Austronesian language."
    # },
    # "swa_Latn": {
    #     "name": "Swahili",
    #     "stanza_code": "sw",
    #     "nllb_code": "swa_Latn",
    #     "wmtpp_code": "sw_KE",
    #     "iso3_code": "swh",
    #     "gtrans_code": "sw",
    #     "ciphered_name": "Makaleni",
    #     "ciphered_lang_info": "Makaleni is a newly discovered Afro-Asiatic language."
    # },  # not supported by stanza
    "tur_Latn": {
        "name": "Turkish",
        "stanza_code": "tr",
        "nllb_code": "tur_Latn",
        "wmtpp_code": "tr_TR",
        "iso3_code": "tur",
        "gtrans_code": "tr",
        "ciphered_name": "Sekman",
        "ciphered_lang_info": "Sekman is a newly discovered Turkic language."
    },
    # "cmn_Hans": {
    #     "name": "Chinese",
    #     "stanza_code": "zh",
    #     "nllb_code": "cmn_Hans",
    #     "wmtpp_code": "zh_CN",
    #     "iso3_code": "cmn",
    #     "gtrans_code": "zh",
    #     "ciphered_name": "Yinshu",
    #     "ciphered_lang_info": "Yinshu is a newly discovered Sino-Tibetan language."
    # },
    "vie_Latn": {
        "name": "Vietnamese",
        "stanza_code": "vi",
        "nllb_code": "vie_Latn",
        "wmtpp_code": "vi_VN",
        "iso3_code": "vie",
        "gtrans_code": "vi",
        "ciphered_name": "Nolưa",
        "ciphered_lang_info": "Nolưa is a newly discovered Austroasiatic language."
    },
    "ces_Latn": {
        "name": "Czech",
        "stanza_code": "cs",
        "nllb_code": "ces_Latn",
        "wmtpp_code": "cs_CZ",
        "iso3_code": "ces",
        "gtrans_code": "cs",
        "ciphered_name": "Krajčar",
        "ciphered_lang_info": "Krajčar is a newly discovered Slavic language.",
        "related_language_code": "pol_Latn",
    },

    "pol_Latn": {
        "name": "Polish",
        "stanza_code": "pl",
        "nllb_code": "pol_Latn",
        "wmtpp_code": "pl_PL",
        "iso3_code": "pol",
        "gtrans_code": "pl",
        "ciphered_name": "Lukonik",
        "ciphered_lang_info": "Lukonik is a newly discovered Slavic language.",
        "related_language_code": "ces_Latn",
    },

    # "tam_Taml": {
    #     "name": "Tamil",
    #     "stanza_code": "ta",
    #     "nllb_code": "tam_Taml",
    #     "wmtpp_code": "ta_IN",
    #     "iso3_code": "tam",
    #     "gtrans_code": "ta",
    #     "ciphered_name": "Kushama",
    #     "ciphered_lang_info": "Kushama is a newly discovered Dravidian language."
    # },
    "tel_Telu": {
        "name": "Telugu",
        "stanza_code": "te",
        "nllb_code": "tel_Telu",
        "wmtpp_code": "te_IN",
        "iso3_code": "tel",
        "gtrans_code": "te",
        "ciphered_name": "Nalaprika",
        "ciphered_lang_info": "Nalaprika is a newly discovered Dravidian language."
    },
    # "kor_Hang": {
    #     "name": "Korean",
    #     "stanza_code": "ko",
    #     "nllb_code": "kor_Hang",
    #     "wmtpp_code": "ko_KR",
    #     "iso3_code": "kor",
    #     "gtrans_code": "ko",
    #     "ciphered_name": "Seongnim",
    #     "ciphered_lang_info": "Seongnim is a newly discovered Korean language."
    # },  # not supported by stanza ner
}

SYNTAX_DESCRIPTIONS = {
    "spa_Latn": """
Serra is a Romance language.
Sentence-level word order (SVO): Serra is typically SVO.
Object-verb order: (VO) The verb precedes the object.
Order of Adposition and Noun Phrase (Preposition–Noun): This language uses prepositions placed before noun phrases.
Order of Noun and Genitive (Noun–Genitive): The noun typically precedes the genitive/possessor.
Order of Adjective and Noun (Noun–Adjective): Adjectives typically follow the noun.
Order of Relative Clause and Noun (Noun–Relative clause): Relative clauses typically follow the noun.
Interrogatives: Polar questions are typically marked by an initial question particle; content questions use clause-initial interrogative phrases, and subject–verb inversion may also occur.
Order of negation and verb (NegV): Negation typically precedes the verb.
Morphosyntactic profile: Serra has richer verbal inflection than nominal inflection, with little or no productive case marking.
Verbal inflection profile: Verbs inflect for person/number and tense/aspect/mood; periphrastic auxiliaries are common.
Other characteristics: Null subjects are possible; clitic pronouns cluster near the verb; agreement is expressed for gender/number within the noun phrase.
""",

    "fra_Latn": """
Gerestal is a Romance language.
Sentence-level word order (SVO): Gerestal is typically SVO.
Object-verb order: (VO) The verb precedes the object.
Order of Adposition and Noun Phrase (Preposition–Noun): This language uses prepositions placed before noun phrases.
Order of Noun and Genitive (Noun–Genitive): The noun typically precedes the genitive, often realized via a prepositional construction.
Order of Adjective and Noun (Noun–Adjective): Adjectives typically follow the noun; a limited subclass may precede it.
Order of Relative Clause and Noun (Noun–Relative clause): Relative clauses typically follow the noun.
Interrogatives: Interrogatives may involve subject–verb inversion or intonation alone; polar questions have an initial question particle.
Order of negation and verb (Discontinuous negation): Negation is commonly expressed with a discontinuous marker bracketing the finite verb.
Morphosyntactic profile: Gerestal has rich verbal morphology and limited nominal morphology, with no productive case marking.
Verbal inflection profile: Verbs agree with person/number and inflect for tense/aspect/mood; auxiliaries are frequent.
Other characteristics: Subject omission is limited; preverbal clitic pronouns are prominent; noun–adjective agreement in gender/number is present.
""",

    "deu_Latn": """
Markin is a Germanic language.
Sentence-level word order (No dominant order): Markin lacks a single dominant clause-level order due to systematic verb-placement alternations (e.g., main vs. embedded clauses).
Object-verb order (No dominant order): Both VO and OV occur in different clause types, with neither fully dominant.
Order of Adposition and Noun Phrase (Preposition–Noun): This language primarily uses prepositions placed before noun phrases.
Order of Noun and Genitive (Noun–Genitive): The noun typically precedes the genitive/possessor.
Order of Adjective and Noun (Adjective–Noun): Adjectives typically precede the noun.
Order of Relative Clause and Noun (Noun–Relative clause): Relative clauses typically follow the noun.
Interrogatives: Polar and content questions commonly involve verb-initial/verb-second patterns rather than question particles.
Order of negation and verb (Two patterns): Negation shows two common placements relative to the verb/verb phrase, varying by construction.
Morphosyntactic profile: Markin has comparatively rich nominal morphology (including case) and moderate-to-rich verbal morphology.
Verbal inflection profile: Verbs inflect for person/number and tense/aspect/mood, with distinct finite vs. non-finite forms.
Other characteristics: Word order is used for information structure; case marking supports constituent reordering; agreement is expressed within the noun phrase and on the verb.
""",

    "hin_Deva": """
Manthi is an Indic language.
Sentence-level word order (SOV): Manthi is typically SOV.
Object-verb order: (OV) The object precedes the verb.
Order of Adposition and Noun Phrase (Noun–Postposition): This language uses postpositions placed after noun phrases.
Order of Genitive and Noun (Genitive–Noun): The genitive typically precedes the noun.
Order of Adjective and Noun (Adjective–Noun): Adjectives typically precede the noun.
Order of Relative Clause and Noun (Correlative): Relative-clause constructions are typically correlative rather than simple prenominal/postnominal relatives.
Interrogatives: Interrogatives generally do not require subject–verb inversion; interrogative phrases occur in characteristic positions and intonation may mark polar questions.
Order of negation and verb (NegV): Negation typically precedes the verb.
Morphosyntactic profile: Manthi shows productive case marking and substantial agreement morphology; word order is discourse-flexible.
Verbal inflection profile: Verbs inflect for tense/aspect/mood and agree with subject features; auxiliary-based complexes are common.
Other characteristics: Differential argument marking and compound verbal constructions are common; case marking supports scrambling for focus/topic.
""",

    "mar_Deva": """
Sakpuri is an Indic language.
Sentence-level word order (SOV): Sakpuri is typically SOV.
Object-verb order: (OV) The object precedes the verb.
Order of Adposition and Noun Phrase (Noun–Postposition): This language uses postpositions placed after noun phrases.
Order of Genitive and Noun (Genitive–Noun): The genitive typically precedes the noun.
Order of Adjective and Noun (Adjective–Noun): Adjectives typically precede the noun.
Order of Relative Clause and Noun (Relative Clause-Noun): Relative clauses typically precede the noun.
Interrogatives: Interrogatives generally do not require subject–verb inversion; polar questions use a clause-final question particle.
Order of negation and verb (VNeg): Negation commonly follows the verb (or is realized in the verbal complex after the verb stem).
Morphosyntactic profile: Sakpuri is strongly suffixing, with productive nominal case marking (5-case system) and rich verbal morphology.
Verbal inflection profile: Verbs inflect for tense/aspect/mood and show agreement; auxiliary-like constructions are frequent.
Other characteristics: Case marking enables flexible constituent order for information structure; complex predicate constructions are common.
""",

    "ind_Latn": """
Saurendi is an Austronesian language.
Sentence-level word order (SVO): Saurendi is typically SVO.
Object-verb order: (VO) The verb precedes the object.
Order of Adposition and Noun Phrase (Preposition–Noun): This language uses prepositions placed before noun phrases.
Order of Noun and Genitive (Noun–Genitive): The noun typically precedes the genitive/possessor.
Order of Adjective and Noun (Noun–Adjective): Adjectives typically follow the noun.
Order of Relative Clause and Noun (Noun–Relative clause): Relative clauses typically follow the noun.
Interrogatives: Polar questions often use a question particle and/or intonation; content questions use interrogative phrases without obligatory inversion.
Order of negation and verb (NegV): Negation typically precedes the verb.
Morphosyntactic profile: Saurendi is strongly suffixing overall but has no morphological case marking; verbal voice/valency morphology is prominent.
Verbal inflection profile: Verbal morphology is moderate and often involves derivational/voice marking; tense is largely analytic.
Other characteristics: Word order is relatively flexible for topicalization; pronominal clitics are limited compared to many Romance languages.
""",

    "swa_Latn": """
Makaleni is a Niger-Congo language.
Sentence-level word order (SVO): Makaleni is typically SVO.
Object-verb order: (VO) The verb precedes the object.
Order of Adposition and Noun Phrase (Preposition–Noun): This language uses prepositions placed before noun phrases.
Order of Noun and Genitive (Noun–Genitive): The noun typically precedes the genitive/possessor.
Order of Adjective and Noun (Noun–Adjective): Adjectives typically follow the noun.
Order of Relative Clause and Noun (Noun–Relative clause): Relative clauses typically follow the noun.
Interrogatives: Polar questions may be marked by an initial question particle and/or intonation; content questions use interrogative phrases.
Order of negation and verb (Neg–V): Negation typically precedes the verb complex.
Morphosyntactic profile: Makaleni is weakly prefixing in inflectional morphology; nominal noun-class agreement is extensive; there is no morphological case marking.
Verbal inflection profile: Verbs show rich agreement and tense/aspect/mood marking, much of it expressed in the verbal complex.
Other characteristics: Agreement morphology is pervasive across the clause; object marking in the verbal complex is common; constituent order can vary with information structure.
""",

    "tur_Latn": """
Sekman is a Turkic language.
Sentence-level word order (SOV): Sekman is typically SOV.
Object-verb order: (OV) The object precedes the verb.
Order of Adposition and Noun Phrase (Postposition–Noun): This language uses postpositions placed after the noun phrase.
Order of Noun and Genitive (Genitive–Noun): The genitive precedes the noun, typically marked by genitive case on the possessor and possessive agreement on the noun.
Order of Adjective and Noun (Adjective–Noun): Adjectives typically precede the noun; relative clauses also precede the noun.
Order of Relative Clause and Noun (Relative clause–Noun): Relative clauses typically precede the noun.
Interrogatives: Interrogatives generally do not involve subject–verb inversion; yes–no questions are marked by a clause-final question particle, and wh-phrases are typically in situ.
Order of negation and verb (V-Neg): Negation is expressed morphologically as a suffix after the verb.
Morphosyntactic profile: Sekman is strongly agglutinative and strongly suffixing, with rich verbal morphology and productive nominal case marking, but no grammatical gender.
Verbal inflection profile: Verbs inflect for tense/aspect/mood/negation and subject agreement through ordered suffixes.
Other characteristics: Subject omission is common; case marking supports flexible constituent order; there are no preverbal clitic pronoun clusters analogous to Romance clitics.
""",

    "vie_Latn": """
Nolưa is an Austroasiatic language.
Sentence-level word order (SVO): Nolưa is typically SVO.
Object-verb order: (VO) The verb precedes the object.
Order of Adposition and Noun Phrase (Preposition–Noun): This language uses prepositions placed before noun phrases.
Order of Noun and Genitive (Noun–Genitive): The noun typically precedes the genitive/possessor.
Order of Adjective and Noun (Noun–Adjective): Adjectives typically follow the noun.
Order of Relative Clause and Noun (Noun–Relative clause): Relative clauses typically follow the noun.
Interrogatives: Polar questions often use a clause-final question particle; content questions use interrogative phrases without obligatory inversion.
Order of negation and verb (NegV): Negation typically precedes the verb.
Morphosyntactic profile: Nolưa has little inflectional affixation and no morphological case marking; grammatical relations are primarily expressed analytically.
Verbal inflection profile: Verbal categories (e.g., tense/aspect/modality) are largely expressed with separate particles/auxiliaries rather than inflection.
Other characteristics: Constituent order and function words play a central role; agreement morphology is minimal.
""",

    "ces_Latn": """
Krajčar is a Slavic language.
Sentence-level word order (SVO): Krajčar is typically SVO, with substantial discourse-driven flexibility.
Object-verb order: (VO) The verb precedes the object in neutral clauses.
Order of Adposition and Noun Phrase (Preposition–Noun): This language uses prepositions placed before noun phrases.
Order of Noun and Genitive (No dominant order): Both Genitive–Noun and Noun–Genitive occur with neither fully dominant.
Order of Adjective and Noun (Adjective–Noun): Adjectives typically precede the noun.
Order of Relative Clause and Noun (Noun–Relative clause): Relative clauses typically follow the noun.
Interrogatives: Interrogatives do not require question particles; content questions front interrogative phrases and polar questions rely on intonation.
Order of negation and verb (Neg–V): Negation typically precedes the verb.
Morphosyntactic profile: Krajčar is weakly suffixing in inflectional morphology, with productive nominal case marking and rich agreement within the noun phrase.
Verbal inflection profile: Verbs inflect for person/number and tense/aspect/mood; aspectual distinctions are prominent.
Other characteristics: Flexible word order is enabled by case marking; agreement is expressed across modifiers and targets.
""",

    "pol_Latn": """
Lukonik is a Slavic language.
Sentence-level word order (SVO): Lukonik is typically SVO, with discourse-driven flexibility.
Object-verb order: (VO) The verb precedes the object in neutral clauses.
Order of Adposition and Noun Phrase (Preposition–Noun): This language uses prepositions placed before noun phrases.
Order of Noun and Genitive (Noun–Genitive): The noun typically precedes the genitive/possessor.
Order of Adjective and Noun (Adjective–Noun): Adjectives typically precede the noun.
Order of Relative Clause and Noun (Noun–Relative clause): Relative clauses typically follow the noun.
Interrogatives: Polar questions may use an initial question particle and/or intonation; content questions typically front interrogative phrases.
Order of negation and verb (NegV): Negation typically precedes the verb.
Morphosyntactic profile: Lukonik is strongly suffixing, with a robust nominal case system (6–7 cases) and rich agreement in the noun phrase.
Verbal inflection profile: Verbs inflect for person/number and tense/aspect/mood; aspectual distinctions are prominent.
Other characteristics: Case marking supports flexible constituent order; agreement and inflectional paradigms are comparatively rich.
""",

    "tel_Telu": """
Nalaprika is a Dravidian language.
Sentence-level word order (SOV): Nalaprika is typically SOV.
Object-verb order: (OV) The object precedes the verb.
Order of Adposition and Noun Phrase (Noun–Postposition): This language uses postpositions placed after noun phrases.
Order of Genitive and Noun (Genitive–Noun): The genitive typically precedes the noun.
Order of Adjective and Noun (Adjective–Noun): Adjectives typically precede the noun.
Order of Relative Clause and Noun (Relative clause–Noun): Relative clauses typically precede the noun.
Interrogatives: Polar questions do not use a dedicated question particle in the typology coding; content questions use interrogative phrases without obligatory inversion.
Order of negation and verb (V–Neg): Negation typically follows the verb stem (i.e., is expressed after V).
Morphosyntactic profile: Nalaprika is strongly suffixing and agglutinative, with productive nominal case marking and rich verbal morphology.
Verbal inflection profile: Verbs inflect for tense/aspect/mood and agreement; complex predicate structures are common.
Other characteristics: Case marking supports constituent reordering for information structure; agreement is primarily expressed in the verbal domain rather than via gendered noun–adjective agreement.
""",
}


INFLECTION_PARADIGMS_DESCRIPTIONS = {

    "spa_Latn": '''Infinitival suffix: "<ar>", "<er>", "<ir>",
    Running examples (regular): "<hablar>" (<ar>), "<comer>" (<er>/<ir>-type endings)

    Present:
    (<ar> endings)
    - "<o>" (1st person singular)     example: "<hablo>"
    - "<as>" (2nd person singular informal)   example: "<hablas>"
    - "<a>" (3rd person singular)    example: "<habla>"
    - "<amos>" (1st person plural)   example: "<hablamos>"
    - "<áis>" (2nd person plural informal, Spain) example: "<habláis>"
    - "<an>" (3rd person plural)     example: "<hablan>"

    (<er>/<ir> endings)
    - "<o>" (1st person singular)     example: "<como>"
    - "<es>" (2nd person singular informal)   example: "<comes>"
    - "<e>" (3rd person singular)    example: "<come>"
    - "<emos>" / "<imos>" (1st person plural) example: "<comemos>"
    - "<éis>" / "<ís>" (2nd person plural informal, Spain) example: "<coméis>"
    - "<en>" (3rd person plural)     example: "<comen>"

    Simple Past:
    (<ar> endings)
    - "<é>" (1st person singular)     example: "<hablé>"
    - "<aste>" (2nd person singular informal) example: "<hablaste>"
    - "<ó>" (3rd person singular)    example: "<habló>"
    - "<amos>" (1st person plural)   example: "<hablamos>"
    - "<asteis>" (2nd person plural informal, Spain) example: "<hablasteis>"
    - "<aron>" (3rd person plural)   example: "<hablaron>"

    (<er>/<ir> endings)
    - "<í>" (1st person singular)     example: "<comí>"
    - "<iste>" (2nd person singular informal) example: "<comiste>"
    - "<ió>" (3rd person singular)   example: "<comió>"
    - "<imos>" (1st person plural)   example: "<comimos>"
    - "<isteis>" (2nd person plural informal, Spain) example: "<comisteis>"
    - "<ieron>" (3rd person plural)  example: "<comieron>"

    Simple Future:
    (Formed by adding endings to the infinitive.)
    - "<é>" (1st person singular)     examples: "<hablaré>", "<comeré>"
    - "<ás>" (2nd person singular informal) examples: "<hablarás>", "<comerás>"
    - "<á>" (3rd person singular)     examples: "<hablará>", "<comerá>"
    - "<emos>" (1st person plural)    examples: "<hablaremos>", "<comeremos>"
    - "<éis>" (2nd person plural informal, Spain) examples: "<hablaréis>", "<comeréis>"
    - "<án>" (3rd person plural)      examples: "<hablarán>", "<comerán>"
    ''',

    "fra_Latn": '''Infinitival suffix: "<er>", "<ir>", "<re>",
    Running examples (regular): "<parler>" (<er>), "<finir>" (<ir>/<re>-type patterns)

    Present:
    (<er> verbs)
    - "<e>" (1st person singular)     example: "<parle>"
    - "<es>" (2nd person singular)    example: "<parles>"
    - "<e>" (3rd person singular)     example: "<parle>"
    - "<ons>" (1st person plural)     example: "<parlons>"
    - "<ez>" (2nd person plural)      example: "<parlez>"
    - "<ent>" (3rd person plural)     example: "<parlent>"

    (<ir>/<re> verbs; common regular pattern)
    - "<is>" (1st person singular)    example: "<finis>"
    - "<is>" (2nd person singular)    example: "<finis>"
    - "<it>" (3rd person singular)    example: "<finit>"
    - "<issons>" (1st person plural)  example: "<finissons>"
    - "<issez>" (2nd person plural)   example: "<finissez>"
    - "<issent>" (3rd person plural)  example: "<finissent>"

    Simple Past:
    (Formed with auxiliary "<avoir>" or "<être>" in the present + past participle.)
    You must conjugate the auxiliary according to the subject, then add the correct past participle form of the verb.

    Auxiliary "<avoir>" (present forms):
    - "<ai>" (1st person singular)
    - "<as>" (2nd person singular)
    - "<a>" (3rd person singular)
    - "<avons>" (1st person plural)
    - "<avez>" (2nd person plural)
    - "<ont>" (3rd person plural)

    Past participle endings:
    - "<é>" (<er> verbs)              example: "<parlé>"
    - "<i>" (<ir> verbs)              example: "<fini>"
    - "<u>" (<re> verbs)

    Full examples:
    - "<ai parlé>" (1st person singular)
    - "<as parlé>" (2nd person singular)
    - "<a parlé>" (3rd person singular)
    - "<ai fini>" (1st person singular)
    - "<avons fini>" (1st person plural)
    - "<ont fini>" (3rd person plural)

    Simple Future:
    (Formed by adding endings to the infinitive.)
    - "<ai>" (1st person singular)    examples: "<parlerai>", "<finirai>"
    - "<as>" (2nd person singular)    examples: "<parleras>", "<finiras>"
    - "<a>" (3rd person singular)     examples: "<parlera>", "<finira>"
    - "<ons>" (1st person plural)     examples: "<parlerons>", "<finirons>"
    - "<ez>" (2nd person plural)      examples: "<parlerez>", "<finirez>"
    - "<ont>" (3rd person plural)     examples: "<parleront>", "<finiront>"
    ''',

    "deu_Latn": '''Infinitival suffix: "<en>" or "<n>",
    Running examples (regular): "<machen>", "<handeln>"

    Present:
    - "<e>" (1st person singular)     examples: "<mache>", "<handle>"
    - "<st>" (2nd person singular informal) examples: "<machst>", "<handelst>"
    - "<t>" (3rd person singular)     examples: "<macht>", "<handelt>"
    - "<en>" (1st person plural)      examples: "<machen>", "<handeln>"
    - "<t>" (2nd person plural informal) examples: "<macht>", "<handelt>"
    - "<en>" (3rd person plural)      examples: "<machen>", "<handeln>"

    Simple Past:
    (Formed with auxiliary "<haben>" in the present + past participle.)
    You must conjugate "<haben>" according to the subject, then add the past participle of the verb at the end.

    Auxiliary "<haben>" (present forms):
    - "<habe>" (1st person singular)
    - "<hast>" (2nd person singular informal)
    - "<hat>" (3rd person singular)
    - "<haben>" (1st person plural)
    - "<habt>" (2nd person plural informal)
    - "<haben>" (3rd person plural)

    Past participle formation (regular verbs):
    - "<ge>" + verb stem + "<t>"      examples: "<gemacht>", "<gehandelt>"

    Full examples:
    - "<habe gemacht>" (1st person singular)
    - "<hast gemacht>" (2nd person singular)
    - "<hat gemacht>" (3rd person singular)
    - "<haben gemacht>" (1st person plural)
    - "<habt gemacht>" (2nd person plural)
    - "<haben gemacht>" (3rd person plural)
    - "<habe gehandelt>"
    - "<haben gehandelt>"

    Simple Future:
    (Formed with auxiliary "<werden>" + infinitive.)
    - "<werde>" (1st person singular)  examples: "<werde machen>", "<werde handeln>"
    - "<wirst>" (2nd person singular informal) examples: "<wirst machen>", "<wirst handeln>"
    - "<wird>" (3rd person singular)   examples: "<wird machen>", "<wird handeln>"
    - "<werden>" (1st/3rd person plural) examples: "<werden machen>", "<werden handeln>"
    - "<werdet>" (2nd person plural informal) examples: "<werdet machen>", "<werdet handeln>"
    ''',


    "tur_Latn": '''Infinitival suffix: "<mek>" or "<mak>",
    Running examples (regular): "<gelmek>", "<bakmak>"

    Present:
    - "<rım>" / "<arım>" (1st person singular) examples: "<gelirim>", "<bakarım>"
    - "<rsın>" / "<arsın>" (2nd person singular) examples: "<gelirsin>", "<bakarsın>"
    - "<r>" / "<ar>" (3rd person singular) examples: "<gelir>", "<bakar>"
    - "<rız>" / "<arız>" (1st person plural) examples: "<geliriz>", "<bakarız>"
    - "<rsınız>" / "<arsınız>" (2nd person plural) examples: "<gelirsiniz>", "<bakarsınız>"
    - "<rlar>" / "<arlar>" (3rd person plural) examples: "<gelirler>", "<bakarlar>"

    Simple Past:
    - "<dım>" / "<dim>" / "<dum>" / "<düm>" (1st person singular) examples: "<geldim>", "<baktım>"
    - "<dın>" / "<din>" / "<dun>" / "<dün>" (2nd person singular) examples: "<geldin>", "<baktın>"
    - "<dı>" / "<di>" / "<du>" / "<dü>" (3rd person singular) examples: "<geldi>", "<baktı>"
    - "<dık>" / "<dik>" / "<duk>" / "<dük>" (1st person plural) examples: "<geldik>", "<baktık>"
    - "<dınız>" / "<diniz>" / "<dunuz>" / "<dünüz>" (2nd person plural) examples: "<geldiniz>", "<baktınız>"
    - "<dılar>" / "<diler>" / "<dular>" / "<düler>" (3rd person plural) examples: "<geldiler>", "<baktılar>"

    Simple Future:
    - "<acağım>" / "<eceğim>" (1st person singular) examples: "<geleceğim>", "<bakacağım>"
    - "<acaksın>" / "<eceksin>" (2nd person singular) examples: "<geleceksin>", "<bakacaksın>"
    - "<acak>" / "<ecek>" (3rd person singular) examples: "<gelecek>", "<bakacak>"
    - "<acağız>" / "<eceğiz>" (1st person plural) examples: "<geleceğiz>", "<bakacağız>"
    - "<acaksınız>" / "<eceksiniz>" (2nd person plural) examples: "<geleceksiniz>", "<bakacaksınız>"
    - "<acaklar>" / "<ecekler>" (3rd person plural) examples: "<gelecekler>", "<bakacaklar>"
    ''',

    "hin_Deva": '''Infinitival suffix: "<ना>",
    Running examples (regular): "<खाना>", "<देखना>"
    
    Present:
    - "<ता हूँ>" (1st person masc. sing)        examples: "<खाता हूँ>", "<देखता हूँ>"
    - "<ती हूँ>" (1st person fem. sing)        examples: "<खाती हूँ>", "<देखती हूँ>"
    - "<ता है>" (3rd person masc. sing)        examples: "<खाता है>", "<देखता है>"
    - "<ती है>" (3rd person fem. sing)         examples: "<खाती है>", "<देखती है>"
    - "<ते हो>" (2nd person masc. sing, 2nd person plural) examples: "<खाते हो>", "<देखते हो>"
    - "<ती हो>" (2nd person fem. sing)         examples: "<खाती हो>", "<देखती हो>"
    - "<ते हैं>" (1st/3rd person masc plural ) examples: "<खाते हैं>", "<देखते हैं>"
    - "<ती हैं>" (1st/3rd person fem plural and 2nd person honorific fem.) examples: "<खाती हैं>", "<देखती हैं>"

    Simple Past:
    - "<आ>" or "<ा>" (masc. sing)              examples: "<खाया>", "<देखा>"
    - "<ई>" or "<ी>" (fem. sing)               examples: "<खाई>", "<देखी>"
    - "<ए>" or "<े>" (masc. plural / honorific) examples: "<खाए>", "<देखे>"
    - "<ईं>" or "<ीं>" (fem. plural)           examples: "<खाईं>", "<देखीं>"
    Note: For transitive verbs, the subject takes the particle "<ने>" and the verb agrees with the object in number and gender.

    Simple Future:
    - "<ऊँगा>" (1st person masc. sing)         examples: "<खाऊँगा>", "<देखूँगा>"
    - "<ऊँगी>" (1st person fem. sing)          examples: "<खाऊँगी>", "<देखूँगी>"
    - "<ओगे>" (2nd person masc. plural)        examples: "<खाओगे>", "<देखोगे>"
    - "<ओगी>" (2nd person fem. plural)         examples: "<खाओगी>", "<देखोगी>"
    - "<एगा>" (3rd person masc. sing)          examples: "<खाएगा>", "<देखेगा>"
    - "<एगी>" (3rd person fem. sing)           examples: "<खाएगी>", "<देखेगी>"
    - "<एंगे>" (1st/3rd person plural and 2nd person honorific masc.) examples: "<खाएँगे>", "<देखेंगे>"
    - "<एंगी>" (1st/3rd person plural and 2nd person honorific fem.) examples: "<खाएँगी>", "<देखेंगी>"
    ''',

}