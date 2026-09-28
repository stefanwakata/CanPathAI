/** Sous-ensemble de la Classification nationale des professions (CNP/NOC 2021),
 *  codes à 5 chiffres — les métiers les plus fréquents chez les nouveaux
 *  arrivants. Extensible : ajouter une ligne suffit. */
export interface NocEntry {
  code: string;
  en: string;
  fr: string;
}

export const NOC_LIST: NocEntry[] = [
  { code: "21231", en: "Software engineers and designers", fr: "Ingénieurs et concepteurs en logiciel" },
  { code: "21232", en: "Software developers and programmers", fr: "Développeurs et programmeurs de logiciels" },
  { code: "21234", en: "Web developers and programmers", fr: "Développeurs et programmeurs web" },
  { code: "21211", en: "Data scientists", fr: "Scientifiques des données" },
  { code: "21223", en: "Database analysts and data administrators", fr: "Analystes et administrateurs de bases de données" },
  { code: "21220", en: "Cybersecurity specialists", fr: "Spécialistes en cybersécurité" },
  { code: "22220", en: "Computer network and web technicians", fr: "Techniciens de réseau informatique et web" },
  { code: "20012", en: "Computer and information systems managers", fr: "Gestionnaires des systèmes informatiques" },
  { code: "31301", en: "Registered nurses", fr: "Infirmiers autorisés" },
  { code: "32101", en: "Licensed practical nurses", fr: "Infirmiers auxiliaires autorisés" },
  { code: "33102", en: "Nurse aides and orderlies", fr: "Aides-infirmiers et préposés aux bénéficiaires" },
  { code: "31102", en: "General practitioners and family physicians", fr: "Omnipraticiens et médecins de famille" },
  { code: "31120", en: "Pharmacists", fr: "Pharmaciens" },
  { code: "31110", en: "Dentists", fr: "Dentistes" },
  { code: "31202", en: "Physiotherapists", fr: "Physiothérapeutes" },
  { code: "31203", en: "Occupational therapists", fr: "Ergothérapeutes" },
  { code: "32120", en: "Medical laboratory technologists", fr: "Technologues de laboratoire médical" },
  { code: "21301", en: "Mechanical engineers", fr: "Ingénieurs mécaniciens" },
  { code: "21300", en: "Civil engineers", fr: "Ingénieurs civils" },
  { code: "21310", en: "Electrical and electronics engineers", fr: "Ingénieurs électriciens et électroniciens" },
  { code: "21320", en: "Chemical engineers", fr: "Ingénieurs chimistes" },
  { code: "11100", en: "Financial auditors and accountants", fr: "Vérificateurs et comptables" },
  { code: "11101", en: "Financial and investment analysts", fr: "Analystes financiers et en placements" },
  { code: "10010", en: "Financial managers", fr: "Directeurs financiers" },
  { code: "12200", en: "Accounting technicians and bookkeepers", fr: "Techniciens en comptabilité et teneurs de livres" },
  { code: "11200", en: "Human resources professionals", fr: "Professionnels en ressources humaines" },
  { code: "11202", en: "Advertising, marketing and PR professionals", fr: "Professionnels en publicité, marketing et relations publiques" },
  { code: "41200", en: "University professors and lecturers", fr: "Professeurs et chargés de cours d'université" },
  { code: "41220", en: "Secondary school teachers", fr: "Enseignants au secondaire" },
  { code: "41221", en: "Elementary school teachers", fr: "Enseignants au primaire" },
  { code: "42202", en: "Early childhood educators", fr: "Éducateurs de la petite enfance" },
  { code: "41300", en: "Social workers", fr: "Travailleurs sociaux" },
  { code: "41101", en: "Lawyers and Quebec notaries", fr: "Avocats et notaires du Québec" },
  { code: "51114", en: "Translators and interpreters", fr: "Traducteurs et interprètes" },
  { code: "52120", en: "Graphic designers and illustrators", fr: "Designers graphiques et illustrateurs" },
  { code: "13110", en: "Administrative assistants", fr: "Adjoints administratifs" },
  { code: "13100", en: "Administrative officers", fr: "Agents d'administration" },
  { code: "14101", en: "Receptionists", fr: "Réceptionnistes" },
  { code: "62010", en: "Retail sales supervisors", fr: "Superviseurs des ventes au détail" },
  { code: "62020", en: "Food service supervisors", fr: "Superviseurs des services alimentaires" },
  { code: "60030", en: "Restaurant and food service managers", fr: "Directeurs de la restauration" },
  { code: "62200", en: "Chefs", fr: "Chefs cuisiniers" },
  { code: "63200", en: "Cooks", fr: "Cuisiniers" },
  { code: "73300", en: "Transport truck drivers", fr: "Conducteurs de camions de transport" },
  { code: "72410", en: "Automotive service technicians", fr: "Mécaniciens de véhicules automobiles" },
  { code: "72200", en: "Electricians", fr: "Électriciens" },
  { code: "72106", en: "Welders", fr: "Soudeurs" },
  { code: "72310", en: "Carpenters", fr: "Charpentiers-menuisiers" },
  { code: "72300", en: "Plumbers", fr: "Plombiers" },
];

const strip = (s: string) =>
  s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");

export function searchNoc(query: string, max = 8): NocEntry[] {
  const q = strip(query.trim());
  if (q.length < 2) return [];
  return NOC_LIST.filter(
    (n) => strip(n.en).includes(q) || strip(n.fr).includes(q) || n.code.startsWith(q),
  ).slice(0, max);
}
