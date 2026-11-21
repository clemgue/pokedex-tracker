import { describe, expect, it } from 'vitest';
import { avancement, vignettes } from './aventure';
import type { DonneesProgression, InfoJeu, Partie } from './types';

const jeu = { id: 'j', versions: [], pokedex_principal: { id: 'r', pokemon: [1, 2] } } as unknown as InfoJeu;
const prog: DonneesProgression = {
	format: 1,
	jeux: {
		j: {
			final: 'ligue/maitre',
			groupes: [
				{ id: 'arenes', titre: 'Arènes', etapes: [{ id: 'roche', nom: 'Badge Roche' }] },
				{ id: 'ligue', titre: 'Ligue', etapes: [{ id: 'maitre', nom: 'Maître' }] }
			]
		}
	}
};

function partie(attrapes: number[], etapes: string[]): Partie {
	return {
		id: 'p', nom: 'p', jeu: 'j', version: 'v', creee: 0, modifiee: 0,
		captures: Object.fromEntries(attrapes.map((id) => [id, { attrape: true, maj: 1 }])),
		etapes: Object.fromEntries(etapes.map((c) => [c, { fait: true, maj: 1 }]))
	};
}
const libelles = (p: Partie) => vignettes(avancement(p, jeu, prog)).map((v) => v.libelle);

describe('statut d’une partie', () => {
	it('pas commencée', () => expect(libelles(partie([], []))).toEqual(['Pas commencée']));
	it('en cours des deux côtés : une seule vignette', () =>
		expect(libelles(partie([1], ['arenes/roche']))).toEqual(['En cours']));
	it('histoire finie, Pokédex en cours', () =>
		expect(libelles(partie([1], ['ligue/maitre']))).toEqual(['Histoire terminée', 'Pokédex en cours']));
	it('Pokédex complet, histoire en cours', () =>
		expect(libelles(partie([1, 2], []))).toEqual(['Pokédex complété', 'Histoire en cours']));
	it('tout fini : jeu terminé', () => expect(libelles(partie([1, 2], ['ligue/maitre']))).toEqual(['Jeu terminé']));
	it('prochaine étape de chaque groupe', () =>
		expect(avancement(partie([], ['arenes/roche']), jeu, prog).groupes.map((g) => g.prochaine?.id ?? null)).toEqual([
			null,
			'maitre'
		]));
});
