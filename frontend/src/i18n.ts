import type { Lang } from "./types";

export interface Strings {
  title: string; tagline: string; placeholder: string; send: string;
  occupationHint: string;
  help: string; backToChat: string;
  profile: string; occupation: string; nocCode: string; province: string;
  country: string; status: string; experience: string; saveProfile: string;
  profileSaved: string; sources: string; thinking: string; errorGeneric: string;
  stats: string; chat: string; newChat: string; evaluatedAt: string;
  noEval: string; ingestionTitle: string; disclaimer: string; suggestions: string[];
}

const STRINGS: Record<Lang, Strings> = {
  fr: {
    title: "CanPath AI",
    tagline: "Vos perspectives d'emploi au Canada, appuyées par les données IRCC et StatCan",
    placeholder: "Posez votre question… ex. « Quel est le salaire d'une infirmière en Alberta ? »",
    send: "Envoyer",
    help: "Aide",
    backToChat: "Retour à la conversation",
    profile: "Mon profil",
    occupation: "Profession",
    occupationHint: "Tapez 2 lettres et choisissez dans la liste : le code CNP se remplit tout seul.",
    nocCode: "Code CNP",
    province: "Province visée",
    country: "Pays de citoyenneté",
    status: "Statut",
    experience: "Années d'expérience",
    saveProfile: "Enregistrer le profil",
    profileSaved: "Profil enregistré — l'agent en tiendra compte.",
    sources: "Sources",
    thinking: "CanPath réfléchit…",
    errorGeneric: "Une erreur est survenue. Réessayez.",
    stats: "Qualité (RAGAS)",
    chat: "Conversation",
    newChat: "Nouvelle conversation",
    evaluatedAt: "Dernière évaluation",
    noEval: "Aucune évaluation RAGAS disponible. Lancez `python -m app.eval.ragas_eval`.",
    ingestionTitle: "Dernières ingestions de données",
    disclaimer: "CanPath AI fournit un contexte statistique, pas des conseils juridiques.",
    suggestions: [
      "Quel est le salaire médian d'un développeur logiciel en Ontario ?",
      "Quelles provinces admettent le plus de résidents permanents économiques ?",
      "Suis-je admissible au PTPD après un programme collégial de 2 ans ?",
      "Compare le taux de chômage des immigrants récents et des natifs.",
    ],
  },
  en: {
    title: "CanPath AI",
    tagline: "Your Canadian job prospects, grounded in IRCC and StatCan data",
    placeholder: "Ask a question… e.g. “What do registered nurses earn in Alberta?”",
    send: "Send",
    help: "Help",
    backToChat: "Back to chat",
    profile: "My profile",
    occupation: "Occupation",
    occupationHint: "Type 2 letters and pick from the list: the NOC code fills in automatically.",
    nocCode: "NOC code",
    province: "Target province",
    country: "Country of citizenship",
    status: "Status",
    experience: "Years of experience",
    saveProfile: "Save profile",
    profileSaved: "Profile saved — the agent will use it.",
    sources: "Sources",
    thinking: "CanPath is thinking…",
    errorGeneric: "Something went wrong. Please retry.",
    stats: "Quality (RAGAS)",
    chat: "Chat",
    newChat: "New conversation",
    evaluatedAt: "Last evaluated",
    noEval: "No RAGAS evaluation yet. Run `python -m app.eval.ragas_eval`.",
    ingestionTitle: "Latest data ingestion runs",
    disclaimer: "CanPath AI provides statistical context, not legal advice.",
    suggestions: [
      "What is the median wage for software developers in Ontario?",
      "Which provinces admit the most economic permanent residents?",
      "Am I eligible for a PGWP after a 2-year college program?",
      "Compare unemployment for recent immigrants vs Canadian-born.",
    ],
  },
};

export function t(lang: Lang): Strings {
  return STRINGS[lang];
}

export const PROVINCES = [
  "Ontario", "Quebec", "British Columbia", "Alberta", "Manitoba",
  "Saskatchewan", "Nova Scotia", "New Brunswick",
  "Newfoundland and Labrador", "Prince Edward Island",
];

export const STATUSES = ["PGWP", "Study permit", "Work permit", "PR applicant", "Permanent resident"];
