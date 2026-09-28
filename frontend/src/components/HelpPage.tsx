import type { Lang } from "../types";

interface Section {
  title: string;
  body: string[];
  list?: string[];
}

const CONTENT: Record<Lang, { heading: string; sections: Section[] }> = {
  fr: {
    heading: "À propos de CanPath AI",
    sections: [
      {
        title: "Notre mission",
        body: [
          "Les nouveaux arrivants prennent des décisions majeures choix de province, de formation, de carrière souvent sans accès simple aux données qui existent pourtant. CanPath AI croise les données ouvertes d'Immigration, Réfugiés et Citoyenneté Canada (IRCC) avec les statistiques du marché du travail de Statistique Canada et du Guichet-Emplois, et vous permet de les interroger en langage courant, en français ou en anglais.",
          "Chaque réponse s'appuie sur des chiffres réels et cite ses sources. Si une donnée n'existe pas, l'agent vous le dit plutôt que d'inventer.",
        ],
      },
      {
        title: "Bien utiliser l'agent",
        body: [
          "Remplissez d'abord votre profil dans le panneau de gauche. Tapez deux lettres dans « Profession » et choisissez dans la liste : le code CNP (Classification nationale des professions) se remplit automatiquement, ce qui rend les recherches de salaires et de perspectives beaucoup plus précises. L'agent tiendra compte de votre profil dans toutes ses réponses.",
          "Posez ensuite des questions précises. Quelques exemples de ce qui fonctionne bien :",
        ],
        list: [
          "« Quel est le salaire médian de ma profession en Alberta ? »",
          "« Compare les admissions de résidents permanents entre l'Ontario et le Québec depuis 2023 »",
          "« Suis-je admissible au permis de travail post-diplôme après un programme de 2 ans ? »",
          "« Le taux de chômage des immigrants récents est-il plus élevé que la moyenne ? »",
          "Demandez « montre-moi un graphique » pour visualiser une comparaison ou une tendance.",
        ],
      },
      {
        title: "D'où viennent les données",
        body: [
          "Admissions de résidents permanents par province, pays et profession : données ouvertes IRCC, mises à jour mensuellement. Salaires par profession et taux d'emploi : Enquête sur la population active et tableaux de Statistique Canada. Perspectives d'emploi : Guichet-Emplois Canada. Règles d'immigration (PTPD, Entrée express) : pages officielles de Canada.ca. Nos données sont rafraîchies chaque semaine.",
        ],
      },
      {
        title: "Nos limites",
        body: [
          "CanPath AI fournit un contexte statistique pour éclairer vos décisions ; ce n'est pas un avis juridique et les réponses peuvent contenir des erreurs. Pour une décision d'immigration qui engage votre dossier, consultez un consultant réglementé en immigration canadienne (CRIC) ou un avocat, et vérifiez toujours les règles à jour sur Canada.ca.",
          "Votre profil n'est associé qu'à votre session de conversation. Ne partagez pas de renseignements sensibles (numéros de dossier, passeport) dans le chat : l'agent n'en a pas besoin.",
        ],
      },
    ],
  },
  en: {
    heading: "About CanPath AI",
    sections: [
      {
        title: "Our mission",
        body: [
          "Newcomers make major decisions which province, which training, which career often without easy access to data that already exists. CanPath AI crosses Immigration, Refugees and Citizenship Canada (IRCC) open data with labour-market statistics from Statistics Canada and Job Bank, and lets you query them in plain language, in English or French.",
          "Every answer is grounded in real figures and cites its sources. When the data doesn't exist, the agent says so instead of guessing.",
        ],
      },
      {
        title: "Getting good answers",
        body: [
          "Start by filling in your profile in the left panel. Type two letters in \"Occupation\" and pick from the list: the NOC code (National Occupational Classification) fills in automatically, which makes wage and outlook lookups far more precise. The agent uses your profile in every answer.",
          "Then ask specific questions. Examples of what works well:",
        ],
        list: [
          "\"What is the median wage for my occupation in Alberta?\"",
          "\"Compare permanent resident admissions between Ontario and Quebec since 2023\"",
          "\"Am I eligible for a post-graduation work permit after a 2-year program?\"",
          "\"Is unemployment higher for recent immigrants than average?\"",
          "Ask for \"a chart\" to visualize a comparison or a trend.",
        ],
      },
      {
        title: "Where the data comes from",
        body: [
          "Permanent resident admissions by province, country and occupation: IRCC open data, updated monthly. Wages by occupation and employment rates: Labour Force Survey and Statistics Canada tables. Job outlooks: Job Bank Canada. Immigration rules (PGWP, Express Entry): official Canada.ca pages. Our data refreshes weekly.",
        ],
      },
      {
        title: "Our limits",
        body: [
          "CanPath AI provides statistical context to inform your decisions; it is not legal advice and answers may contain errors. For an immigration decision that affects your file, consult a Regulated Canadian Immigration Consultant (RCIC) or a lawyer, and always verify current rules on Canada.ca.",
          "Your profile is tied only to your chat session. Don't share sensitive information (file numbers, passport) in the chat: the agent doesn't need it.",
        ],
      },
    ],
  },
};

function Sec({ sec }: { sec: Section }) {
  return (
    <section>
      <h3>{sec.title}</h3>
      {sec.body.map((p, i) => (
        <p key={i}>{p}</p>
      ))}
      {sec.list && (
        <ul>
          {sec.list.map((item, i) => (
            <li key={i}>{item}</li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function HelpPage({ lang }: { lang: Lang }) {
  const c = CONTENT[lang];
  const [mission, ...rest] = c.sections;
  return (
    <div className="help">
      <h2>{c.heading}</h2>
      <div className="help-mission">
        <Sec sec={mission} />
      </div>
      <div className="help-sections">
        {rest.map((sec) => (
          <Sec key={sec.title} sec={sec} />
        ))}
      </div>
    </div>
  );
}
