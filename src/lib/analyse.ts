/**
 * Calculs sur les données d'un jeu pour une version donnée.
 */
import type { DonneesJeu, Lieu, Methode, Obtention, Pokemon } from './types';

/** Familles de méthodes (couleur des pastilles) */
export type Famille = 'sauvage' | 'cadeau' | 'evolution' | 'echange';

/** Libellé court, famille et priorité d'affichage de chaque méthode */
export const INFOS_METHODES: Record<Methode, { court: string; famille: Famille }> = {
	hautes_herbes: { court: 'Herbes', famille: 'sauvage' },
	marche: { court: 'À pied', famille: 'sauvage' },
	surf: { court: 'Surf', famille: 'sauvage' },
	peche: { court: 'Pêche', famille: 'sauvage' },
	fixe: { court: 'Fixe', famille: 'cadeau' },
	don: { court: 'Don', famille: 'cadeau' },
	echange_pnj: { court: 'Échange PNJ', famille: 'cadeau' },
	achat: { court: 'Achat', famille: 'cadeau' },
	fossile: { court: 'Fossile', famille: 'cadeau' },
	autre: { court: 'Autre', famille: 'sauvage' },
	evolution: { court: 'Évolution', famille: 'evolution' },
	evenement: { court: 'Événement', famille: 'echange' },
	echange_version: { court: 'Autre version', famille: 'echange' },
	bug: { court: 'Bug', famille: 'echange' }
};
const ORDRE_METHODES = Object.keys(INFOS_METHODES) as Methode[];

export interface GroupeLieu {
	lieu: Lieu;
	obtentions: Obtention[];
}

export interface FichePokedex {
	pokemon: Pokemon;
	numero: number;
	obtentions: Obtention[];
	methodes: Set<Methode>;
	/** Méthodes distinctes, dans l'ordre d'affichage */
	puces: Methode[];
	lieux: Set<string>;
	/** Obtentions regroupées par lieu, dans l'ordre de progression */
	parLieu: GroupeLieu[];
	/** Obtentions sans lieu (évolution, échange entre versions, événement) */
	sansLieu: Obtention[];
	/** « Route 1, Route 22 +3 » ou texte de repli quand il n'y a aucun lieu */
	resume: string;
	/** S'obtient uniquement par échange depuis une autre version */
	parEchange: boolean;
	/** Obtenable dans cette version mais pas dans au moins une autre */
	exclusif: boolean;
}

export function analyserVersion(donnees: DonneesJeu, version: string, pokedexId?: string): FichePokedex[] {
	const pokedex = donnees.pokedex.find((p) => p.id === pokedexId) ?? donnees.pokedex[0];
	const pokemons = new Map(donnees.pokemon.map((p) => [p.id, p]));
	const lieux = new Map(donnees.lieux.map((l) => [l.id, l]));

	const parPokemon = new Map<number, Obtention[]>();
	const echangeAilleurs = new Set<number>();
	for (const o of donnees.obtentions) {
		if (o.glitch) continue;
		if (o.versions.includes(version)) {
			const liste = parPokemon.get(o.pokemon) ?? [];
			liste.push(o);
			parPokemon.set(o.pokemon, liste);
		} else if (o.methode === 'echange_version') {
			echangeAilleurs.add(o.pokemon);
		}
	}

	return pokedex.entrees.map(({ numero, pokemon: id }) => {
		const obtentions = parPokemon.get(id) ?? [];
		const methodes = new Set(obtentions.map((o) => o.methode));
		const parEchange = methodes.has('echange_version');

		const groupes = new Map<string, GroupeLieu>();
		const sansLieu: Obtention[] = [];
		for (const o of obtentions) {
			if (!o.lieu) {
				sansLieu.push(o);
				continue;
			}
			const g = groupes.get(o.lieu) ?? { lieu: lieux.get(o.lieu)!, obtentions: [] };
			g.obtentions.push(o);
			groupes.set(o.lieu, g);
		}
		const parLieu = [...groupes.values()].sort((a, b) => (a.lieu.ordre ?? 999) - (b.lieu.ordre ?? 999));

		return {
			pokemon: pokemons.get(id)!,
			numero,
			obtentions,
			methodes,
			puces: ORDRE_METHODES.filter((m) => methodes.has(m)),
			lieux: new Set(groupes.keys()),
			parLieu,
			sansLieu,
			resume: resumer(parLieu, sansLieu, donnees),
			parEchange,
			exclusif: !parEchange && echangeAilleurs.has(id)
		};
	});
}

function resumer(parLieu: GroupeLieu[], sansLieu: Obtention[], donnees: DonneesJeu): string {
	if (parLieu.length) {
		const noms = parLieu.map((g) => g.lieu.nom);
		return noms.length > 2 ? `${noms.slice(0, 2).join(', ')} +${noms.length - 2}` : noms.join(', ');
	}
	const o = sansLieu.find((x) => x.methode === 'evolution') ?? sansLieu[0];
	if (o) return o.detail ?? donnees.methodes[o.methode];
	return 'Introuvable dans cette version';
}

/**
 * Description d'une obtention : « Pêche (Méga Canne) · Sur les quais · niv. 15 · 25 % ».
 * `avecMethode: false` omet le nom de la méthode (déjà affiché par une pastille).
 */
export function decrire(o: Obtention, donnees: DonneesJeu, avecMethode = true): string {
	const parties: string[] = [];
	const methode = donnees.methodes[o.methode];
	if (o.methode === 'evolution' || o.methode === 'echange_version' || o.methode === 'evenement') {
		parties.push(o.detail ?? methode);
	} else if (avecMethode) {
		parties.push(o.detail ? `${methode} (${o.detail})` : methode);
	} else if (o.detail) {
		parties.push(o.detail);
	}
	if (o.zone) parties.push(o.zone);
	if (o.niveaux) parties.push(`niv. ${o.niveaux}`);
	if (o.taux_texte?.includes(' · ')) parties.push(o.taux_texte); // taux selon le moment / la saison
	else if (o.taux != null) parties.push(`${String(o.taux).replace('.', ',')} %`);
	else if (o.taux_texte && o.taux_texte !== 'Unique') parties.push(o.taux_texte);
	if (o.taux_texte === 'Unique') parties.push('unique');
	if (o.notes) parties.push(o.notes);
	return parties.join(' · ');
}

export interface PokemonDuLieu {
	pokemon: Pokemon;
	obtentions: Obtention[];
}

export interface FicheLieu {
	lieu: Lieu;
	pokemons: PokemonDuLieu[];
}

/** Lieux de la version (ordre de progression) et Pokémon obtenables dans chacun. */
export function analyserLieux(donnees: DonneesJeu, version: string): FicheLieu[] {
	const pokemons = new Map(donnees.pokemon.map((p) => [p.id, p]));
	const parLieu = new Map<string, Map<number, Obtention[]>>();
	for (const o of donnees.obtentions) {
		if (!o.lieu || o.glitch || !o.versions.includes(version)) continue;
		const m = parLieu.get(o.lieu) ?? new Map<number, Obtention[]>();
		m.set(o.pokemon, [...(m.get(o.pokemon) ?? []), o]);
		parLieu.set(o.lieu, m);
	}
	return donnees.lieux
		.filter((l) => l.versions.includes(version) && parLieu.has(l.id))
		.map((lieu) => ({
			lieu,
			pokemons: [...parLieu.get(lieu.id)!]
				.sort(([a], [b]) => a - b)
				.map(([id, obtentions]) => ({ pokemon: pokemons.get(id)!, obtentions }))
		}));
}

export interface NoeudEvolution {
	pokemon: Pokemon;
	/** Condition pour atteindre ce stade depuis le précédent */
	condition: string | null;
	suivants: NoeudEvolution[];
}

/** Chaîne d'évolution complète contenant `id`, déduite des obtentions « évolution » du jeu. */
export function chaineEvolution(donnees: DonneesJeu, id: number): NoeudEvolution | null {
	const pokemons = new Map(donnees.pokemon.map((p) => [p.id, p]));
	const suivants = new Map<number, Map<number, string | null>>();
	const precedent = new Map<number, number>();
	for (const o of donnees.obtentions) {
		if (o.methode !== 'evolution' || !o.depuis) continue;
		const m = suivants.get(o.depuis) ?? new Map();
		if (!m.has(o.pokemon)) m.set(o.pokemon, o.detail);
		suivants.set(o.depuis, m);
		precedent.set(o.pokemon, o.depuis);
	}
	let racine = id;
	while (precedent.has(racine)) racine = precedent.get(racine)!;
	if (!suivants.has(racine)) return null; // pas d'évolution

	// « Faire évoluer Évoli avec une Pierre Eau » → « Pierre Eau » ; « … au niveau 16 » → « Niveau 16 »
	const raccourcir = (cond: string | null, pre: Pokemon): string | null => {
		if (!cond) return null;
		const court = cond
			.split(' ou ')
			.map((c) =>
				c
					.replace(`Faire évoluer ${pre.nom}`, '')
					.replace(/^\s*(avec une?|avec|au)\s+/, '')
					.replace(/^\s*par échange/, 'Échange')
					.trim()
			)
			.filter(Boolean)
			.join(' ou ');
		return court ? court[0].toUpperCase() + court.slice(1) : null;
	};
	const construire = (pid: number, condition: string | null): NoeudEvolution => ({
		pokemon: pokemons.get(pid)!,
		condition,
		suivants: [...(suivants.get(pid) ?? new Map())].map(([post, cond]) =>
			construire(post, raccourcir(cond, pokemons.get(pid)!))
		)
	});
	return construire(racine, null);
}

/** Méthodes présentes, pour le filtre */
export function methodesPresentes(fiches: FichePokedex[], donnees: DonneesJeu): { id: Methode; nom: string }[] {
	const presentes = new Set(fiches.flatMap((f) => [...f.methodes]));
	return (Object.keys(donnees.methodes) as Methode[])
		.filter((m) => presentes.has(m))
		.map((m) => ({ id: m, nom: donnees.methodes[m] }));
}
