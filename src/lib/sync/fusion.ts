/**
 * Fusion de deux copies de la progression (locale et Dropbox).
 *
 * Règles :
 * - parties : union par identifiant ;
 * - métadonnées d'une partie (nom…) : la copie modifiée le plus récemment l'emporte ;
 * - captures : Pokémon par Pokémon, la capture la plus récente (`maj`) l'emporte ;
 * - étapes de l'aventure (badges…) : même règle, étape par étape ;
 * - suppressions : une partie supprimée (marqueur horodaté) disparaît si elle n'a pas été
 *   modifiée après sa suppression.
 */
import type { Capture, EtapeFaite, Partie } from '$lib/types';

export const FORMAT_FICHIER = 1;

export interface FichierProgression {
	format: number;
	application: 'pokedex-tracker';
	modifie: number;
	parties: Partie[];
	/** Parties supprimées : identifiant → date de suppression */
	supprimees: Record<string, number>;
}

export function fichierVide(): FichierProgression {
	return { format: FORMAT_FICHIER, application: 'pokedex-tracker', modifie: 0, parties: [], supprimees: {} };
}

export function valider(donnees: unknown): FichierProgression {
	const f = donnees as Partial<FichierProgression>;
	if (!f || typeof f !== 'object' || !Array.isArray(f.parties)) {
		throw new Error("Ce fichier n'est pas une sauvegarde Pokédex Tracker.");
	}
	if ((f.format ?? 1) > FORMAT_FICHIER) {
		throw new Error('Sauvegarde créée par une version plus récente de l’application : mets-la à jour.');
	}
	return { ...fichierVide(), ...f, supprimees: f.supprimees ?? {} } as FichierProgression;
}

/** Fusion élément par élément : l'entrée la plus récente (`maj`) l'emporte. */
function fusionnerParMaj<T extends { maj: number }>(a: Record<string, T>, b: Record<string, T>): Record<string, T> {
	const resultat: Record<string, T> = { ...a };
	for (const [cle, cb] of Object.entries(b)) {
		const ca = resultat[cle];
		if (!ca || (cb.maj ?? 0) > (ca.maj ?? 0)) resultat[cle] = cb;
	}
	return resultat;
}

function fusionnerPartie(a: Partie, b: Partie): Partie {
	const recente = b.modifiee > a.modifiee ? b : a;
	const fusion: Partie = {
		...recente,
		creee: Math.min(a.creee, b.creee),
		modifiee: Math.max(a.modifiee, b.modifiee),
		captures: fusionnerParMaj<Capture>(a.captures, b.captures)
	};
	if (a.etapes || b.etapes) fusion.etapes = fusionnerParMaj<EtapeFaite>(a.etapes ?? {}, b.etapes ?? {});
	return fusion;
}

export function fusionner(a: FichierProgression, b: FichierProgression): FichierProgression {
	const supprimees: Record<string, number> = { ...a.supprimees };
	for (const [id, t] of Object.entries(b.supprimees)) supprimees[id] = Math.max(t, supprimees[id] ?? 0);

	const parties = new Map<string, Partie>();
	for (const p of [...a.parties, ...b.parties]) {
		const existante = parties.get(p.id);
		parties.set(p.id, existante ? fusionnerPartie(existante, p) : p);
	}
	for (const [id, t] of Object.entries(supprimees)) {
		const p = parties.get(id);
		if (p && p.modifiee <= t) parties.delete(id);
	}

	return {
		format: FORMAT_FICHIER,
		application: 'pokedex-tracker',
		modifie: Math.max(a.modifie, b.modifie),
		parties: [...parties.values()].sort((x, y) => x.creee - y.creee),
		supprimees
	};
}

/** Égalité de contenu (hors horodatage global), pour éviter des envois inutiles. */
export function memeContenu(a: FichierProgression, b: FichierProgression): boolean {
	const cle = (f: FichierProgression) => JSON.stringify({ p: f.parties, s: f.supprimees });
	return cle(a) === cle(b);
}
