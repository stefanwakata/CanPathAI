"""Golden testset for RAGAS evaluation — bilingual FR/EN."""

TESTSET = [
    {
        "question": "Am I eligible for a PGWP after completing a 2-year college program in Canada?",
        "ground_truth": (
            "Graduates of eligible programs of at least 8 months at a designated learning "
            "institution can apply for a PGWP; a program of 2 years or more can qualify for "
            "a 3-year permit, subject to IRCC's current eligibility rules and field-of-study "
            "requirements."
        ),
        "lang": "en",
    },
    {
        "question": "Quel est le salaire médian d'un développeur de logiciels en Ontario ?",
        "ground_truth": (
            "Selon les données de Statistique Canada et du Guichet-Emplois sur les salaires par "
            "profession (CNP 21232/21231), le salaire d'un développeur de logiciels en Ontario "
            "se situe autour de 45 à 55 $ de l'heure en valeur médiane, selon l'année de référence."
        ),
        "lang": "fr",
    },
    {
        "question": "Which provinces admitted the most economic-class permanent residents recently?",
        "ground_truth": (
            "Ontario admits the largest number of economic-class permanent residents, followed "
            "by British Columbia, Alberta and Quebec, according to IRCC monthly admissions data."
        ),
        "lang": "en",
    },
    {
        "question": "Le taux de chômage des immigrants récents est-il plus élevé que celui des personnes nées au Canada ?",
        "ground_truth": (
            "Oui. Les données de l'Enquête sur la population active montrent que le taux de "
            "chômage des immigrants très récents (5 ans ou moins) est nettement supérieur à "
            "celui des personnes nées au Canada, l'écart se réduisant avec le temps passé au pays."
        ),
        "lang": "fr",
    },
    {
        "question": "What are the job prospects for registered nurses in Alberta?",
        "ground_truth": (
            "Job Bank rates the employment outlook for registered nurses (NOC 31301) in Alberta "
            "as good to very good, driven by high demand in the health sector."
        ),
        "lang": "en",
    },
    {
        "question": "Combien de temps faut-il pour traiter une demande de résidence permanente via Entrée express ?",
        "ground_truth": (
            "IRCC vise un délai de traitement d'environ 6 mois pour la plupart des demandes "
            "complètes soumises via Entrée express, selon les délais publiés."
        ),
        "lang": "fr",
    },
]
