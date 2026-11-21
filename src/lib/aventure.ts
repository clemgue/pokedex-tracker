/**
 * Avancement d'une partie : Pokédex principal, étapes de l'aventure (badges…) et statut.
 */
import type { DonneesProgression, GroupeEtapes, InfoJeu, Partie } from './types';

/** Clé d'une étape dans Partie.etapes */
export const cleEtape = (groupe: string, etape: string) => `${groupe}/${etape}`;

/** Groupes d'étapes du jeu, limités aux entrées de la version jouée. */
export function etapesVersion(prog: DonneesProgression | null, jeu: string, version: string): GroupeEtapes[] {
	const groupes = prog?.jeux[jeu]?.groupes ?? [];
	return groupes
		.map((g) => ({ ...g, etapes: g.etapes.filter((e) => !e.versions || e.versions.includes(version)) }))
		.filter((g) => g.etapes.length);
}

export type Statut = 'pas_commencee' | 'en_cours' | 'terminee' | 'complete';

export const LIBELLES_STATUT: Record<Statut, string> = {
	pas_commencee: 'Pas commencée',
	en_cours: 'En cours',
	terminee: 'Aventure terminée',
	complete: 'Pokédex complété'
};

export interface Avancement {
	attrapes: number;
	total: number;
	pourcentage: number;
	etapesFaites: number;
	etapesTotal: number;
	/** Badges d'Arène (ou équivalent) : premier groupe du jeu */
	premierGroupe: { titre: string; faits: number; total: number } | null;
	histoireFinie: boolean;
	statut: Statut;
}

export function avancement(partie: Partie, jeu: InfoJeu | undefined, prog: DonneesProgression | null): Avancement {
	const dex = jeu?.pokedex_principal?.pokemon ?? [];
	const attrapes = dex.length
		? dex.filter((id) => partie.captures[id]?.attrape).length
		: Object.values(partie.captures).filter((c) => c.attrape).length;
	const total = dex.length;
	const pourcentage = total ? Math.floor((attrapes / total) * 100) : 0;

	const fait = (cle: string) => !!partie.etapes?.[cle]?.fait;
	const groupes = etapesVersion(prog, partie.jeu, partie.version);
	let etapesFaites = 0;
	let etapesTotal = 0;
	for (const g of groupes) {
		for (const e of g.etapes) {
			etapesTotal++;
			if (fait(cleEtape(g.id, e.id))) etapesFaites++;
		}
	}
	const g0 = groupes[0];
	const premierGroupe = g0
		? { titre: g0.titre, faits: g0.etapes.filter((e) => fait(cleEtape(g0.id, e.id))).length, total: g0.etapes.length }
		: null;
	const final = prog?.jeux[partie.jeu]?.final;
	const histoireFinie = !!final && fait(final);

	const commencee = Object.values(partie.captures).some((c) => c.attrape) || etapesFaites > 0;
	const statut: Statut =
		total > 0 && attrapes === total
			? 'complete'
			: histoireFinie
				? 'terminee'
				: commencee
					? 'en_cours'
					: 'pas_commencee';

	return { attrapes, total, pourcentage, etapesFaites, etapesTotal, premierGroupe, histoireFinie, statut };
}
