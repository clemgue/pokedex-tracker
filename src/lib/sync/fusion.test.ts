import { describe, expect, it } from 'vitest';
import type { Partie } from '$lib/types';
import { fichierVide, fusionner, memeContenu, valider, type FichierProgression } from './fusion';

function partie(id: string, modifiee: number, captures: Partie['captures'] = {}, nom = id): Partie {
	return { id, nom, jeu: 'rouge-bleu-jaune', version: 'rouge', creee: 1, modifiee, captures };
}

function fichier(parties: Partie[], supprimees: Record<string, number> = {}): FichierProgression {
	return { ...fichierVide(), parties, supprimees };
}

describe('fusionner', () => {
	it('réunit les parties des deux copies', () => {
		const r = fusionner(fichier([partie('a', 10)]), fichier([partie('b', 20)]));
		expect(r.parties.map((p) => p.id).sort()).toEqual(['a', 'b']);
	});

	it('garde la capture la plus récente, Pokémon par Pokémon', () => {
		const pc = partie('a', 10, { 1: { attrape: true, maj: 5 }, 4: { attrape: false, maj: 9 } });
		const tel = partie('a', 12, { 1: { attrape: false, maj: 7 }, 4: { attrape: true, maj: 8 }, 7: { attrape: true, maj: 3 } });
		const r = fusionner(fichier([pc]), fichier([tel]));
		const c = r.parties[0].captures;
		expect(c[1].attrape).toBe(false); // téléphone plus récent
		expect(c[4].attrape).toBe(false); // PC plus récent
		expect(c[7].attrape).toBe(true); // seulement sur le téléphone
	});

	it('fusionne les étapes (badges) une à une, même absentes d’une copie', () => {
		const pc = { ...partie('a', 10), etapes: { 'arenes/roche': { fait: true, maj: 5 } } };
		const tel = { ...partie('a', 20), etapes: { 'arenes/roche': { fait: false, maj: 3 }, 'arenes/cascade': { fait: true, maj: 4 } } };
		const ancienne = partie('a', 30); // copie d'une version de l'appli sans étapes
		const r = fusionner(fusionner(fichier([pc]), fichier([tel])), fichier([ancienne]));
		expect(r.parties[0].etapes).toEqual({
			'arenes/roche': { fait: true, maj: 5 },
			'arenes/cascade': { fait: true, maj: 4 }
		});
	});

	it('prend le nom de la copie la plus récemment modifiée', () => {
		const r = fusionner(fichier([partie('a', 10, {}, 'Ancien')]), fichier([partie('a', 20, {}, 'Nouveau')]));
		expect(r.parties[0].nom).toBe('Nouveau');
		expect(r.parties[0].modifiee).toBe(20);
	});

	it('propage une suppression', () => {
		const r = fusionner(fichier([partie('a', 10)]), fichier([], { a: 15 }));
		expect(r.parties).toHaveLength(0);
		expect(r.supprimees.a).toBe(15);
	});

	it("ne supprime pas une partie modifiée après sa suppression ailleurs", () => {
		const r = fusionner(fichier([partie('a', 30)]), fichier([], { a: 15 }));
		expect(r.parties.map((p) => p.id)).toEqual(['a']);
	});

	it('est symétrique', () => {
		const a = fichier([partie('a', 10, { 1: { attrape: true, maj: 5 } })], { z: 3 });
		const b = fichier([partie('a', 12, { 2: { attrape: true, maj: 6 } }), partie('b', 4)]);
		expect(memeContenu(fusionner(a, b), fusionner(b, a))).toBe(true);
	});

	it('est idempotente', () => {
		const a = fichier([partie('a', 10, { 1: { attrape: true, maj: 5 } })]);
		expect(memeContenu(fusionner(a, a), a)).toBe(true);
	});
});

describe('valider', () => {
	it('refuse un fichier étranger', () => {
		expect(() => valider({ bonjour: 1 })).toThrow();
	});
	it('refuse un format plus récent', () => {
		expect(() => valider({ format: 99, parties: [] })).toThrow();
	});
	it('complète les champs manquants', () => {
		expect(valider({ parties: [] }).supprimees).toEqual({});
	});
});
