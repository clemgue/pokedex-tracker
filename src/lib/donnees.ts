import { base } from '$app/paths';
import type { DonneesJeu, InfoJeu } from './types';

const cache = new Map<string, Promise<DonneesJeu>>();

async function lireJson<T>(chemin: string): Promise<T> {
	const rep = await fetch(`${base}/data/jeux/${chemin}`);
	if (!rep.ok) throw new Error(`Impossible de charger ${chemin} (${rep.status})`);
	return rep.json();
}

export function chargerIndex(): Promise<InfoJeu[]> {
	return lireJson<{ jeux: InfoJeu[] }>('index.json').then((i) => i.jeux);
}

export function chargerJeu(id: string): Promise<DonneesJeu> {
	let p = cache.get(id);
	if (!p) {
		p = lireJson<DonneesJeu>(`${id}.json`);
		p.catch(() => cache.delete(id));
		cache.set(id, p);
	}
	return p;
}

/** Nom d'un type → suffixe de variable CSS (« Électrik » → « electrik »). */
export function cleType(type: string): string {
	return type
		.normalize('NFD')
		.replace(/[̀-ͯ]/g, '')
		.toLowerCase();
}

/** Comparaison insensible à la casse et aux accents. */
export function normaliser(texte: string): string {
	return cleType(texte).replace(/[^a-z0-9♀♂]+/g, ' ').trim();
}

export function numero(n: number, chiffres = 3): string {
	return '#' + String(n).padStart(chiffres, '0');
}
