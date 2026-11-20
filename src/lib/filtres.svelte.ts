/**
 * Filtres de la vue Pokédex, conservés pendant la navigation (fiche, lieux…).
 * Remis à zéro quand on change de partie (les lieux et méthodes dépendent du jeu).
 */
import type { Methode } from './types';

export type Statut = 'tous' | 'manquants' | 'attrapes';
export type Special = '' | 'exclusifs' | 'echange';

function initial() {
	return {
		recherche: '',
		statut: 'tous' as Statut,
		methode: '' as '' | Methode,
		lieu: '',
		type: '',
		special: '' as Special,
		tri: 'numero' as 'numero' | 'nom',
		pokedexId: '',
		/** Partie pour laquelle ces filtres valent */
		partie: null as string | null
	};
}

export const filtres = $state(initial());

export function reinitialiserFiltres(partie: string | null = filtres.partie) {
	Object.assign(filtres, initial(), { partie });
}
