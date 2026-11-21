/**
 * Avancement d'une partie : Pokédex principal, étapes de l'aventure (badges…) et statut.
 */
import type { DonneesProgression, Etape, GroupeEtapes, InfoJeu, Partie } from './types';

/** Clé d'une étape dans Partie.etapes */
export const cleEtape = (groupe: string, etape: string) => `${groupe}/${etape}`;

/** Groupes d'étapes du jeu, limités aux entrées de la version jouée. */
export function etapesVersion(prog: DonneesProgression | null, jeu: string, version: string): GroupeEtapes[] {
	const groupes = prog?.jeux[jeu]?.groupes ?? [];
	return groupes
		.map((g) => ({ ...g, etapes: g.etapes.filter((e) => !e.versions || e.versions.includes(version)) }))
		.filter((g) => g.etapes.length);
}

/** Vignette de statut : `classe` sert au style (pas-commencee, en-cours, termine). */
export interface Vignette {
	libelle: string;
	classe: 'pas-commencee' | 'en-cours' | 'termine';
}

/**
 * Statut d'une partie, histoire et Pokédex dissociés :
 * - rien de fait → « Pas commencée » ; tout fini → « Jeu terminé » ;
 * - un seul des deux fini → deux vignettes (ex. « Histoire terminée » + « Pokédex en cours ») ;
 * - sinon → « En cours ».
 */
export function vignettes(av: Avancement): Vignette[] {
	const { histoireFinie, pokedexComplet, commencee } = av;
	if (histoireFinie && pokedexComplet) return [{ libelle: 'Jeu terminé', classe: 'termine' }];
	if (histoireFinie) return [
		{ libelle: 'Histoire terminée', classe: 'termine' },
		{ libelle: 'Pokédex en cours', classe: 'en-cours' }
	];
	if (pokedexComplet) return [
		{ libelle: 'Pokédex complété', classe: 'termine' },
		{ libelle: 'Histoire en cours', classe: 'en-cours' }
	];
	if (commencee) return [{ libelle: 'En cours', classe: 'en-cours' }];
	return [{ libelle: 'Pas commencée', classe: 'pas-commencee' }];
}

export interface Avancement {
	attrapes: number;
	total: number;
	pourcentage: number;
	etapesFaites: number;
	etapesTotal: number;
	/** Avancement de chaque groupe d'étapes (le premier : badges d'Arène ou équivalent) */
	groupes: { id: string; titre: string; faits: number; total: number; prochaine: Etape | null }[];
	premierGroupe: { titre: string; faits: number; total: number } | null;
	histoireFinie: boolean;
	pokedexComplet: boolean;
	commencee: boolean;
}

export function avancement(partie: Partie, jeu: InfoJeu | undefined, prog: DonneesProgression | null): Avancement {
	const dex = jeu?.pokedex_principal?.pokemon ?? [];
	const attrapes = dex.length
		? dex.filter((id) => partie.captures[id]?.attrape).length
		: Object.values(partie.captures).filter((c) => c.attrape).length;
	const total = dex.length;
	const pourcentage = total ? Math.floor((attrapes / total) * 100) : 0;

	const fait = (cle: string) => !!partie.etapes?.[cle]?.fait;
	const groupes = etapesVersion(prog, partie.jeu, partie.version).map((g) => {
		const faites = g.etapes.filter((e) => fait(cleEtape(g.id, e.id)));
		return {
			id: g.id,
			titre: g.titre,
			faits: faites.length,
			total: g.etapes.length,
			prochaine: g.etapes.find((e) => !fait(cleEtape(g.id, e.id))) ?? null
		};
	});
	const etapesFaites = groupes.reduce((n, g) => n + g.faits, 0);
	const etapesTotal = groupes.reduce((n, g) => n + g.total, 0);
	const premierGroupe = groupes[0] ?? null;
	const final = prog?.jeux[partie.jeu]?.final;
	const histoireFinie = !!final && fait(final);
	const pokedexComplet = total > 0 && attrapes === total;
	const commencee = Object.values(partie.captures).some((c) => c.attrape) || etapesFaites > 0;

	return {
		attrapes,
		total,
		pourcentage,
		etapesFaites,
		etapesTotal,
		groupes,
		premierGroupe,
		histoireFinie,
		pokedexComplet,
		commencee
	};
}
