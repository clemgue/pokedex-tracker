/**
 * État global de l'application : parties, partie active, données du jeu actif.
 * Chaque modification est écrite immédiatement dans IndexedDB.
 */
import { db } from './db';
import { chargerIndex, chargerJeu } from './donnees';
import type { Capture, DonneesJeu, InfoJeu, Partie } from './types';

class Etat {
	pret = $state(false);
	erreur = $state<string | null>(null);
	jeux = $state<InfoJeu[]>([]);
	parties = $state<Partie[]>([]);
	partieActiveId = $state<string | null>(null);
	donnees = $state.raw<DonneesJeu | null>(null);
	chargementJeu = $state(false);

	partieActive = $derived(this.parties.find((p) => p.id === this.partieActiveId) ?? null);

	async init() {
		if (this.pret) return;
		try {
			const [jeux, parties, active] = await Promise.all([
				chargerIndex(),
				db.toutesLesParties(),
				db.lireReglage<string>('partieActive')
			]);
			this.jeux = jeux;
			this.parties = parties.sort((a, b) => a.creee - b.creee);
			this.partieActiveId = parties.some((p) => p.id === active) ? active! : (parties[0]?.id ?? null);
			await this.chargerDonneesActives();
		} catch (e) {
			this.erreur = e instanceof Error ? e.message : String(e);
		} finally {
			this.pret = true;
		}
	}

	private async chargerDonneesActives() {
		const partie = this.partieActive;
		if (!partie) {
			this.donnees = null;
			return;
		}
		if (this.donnees?.jeu.id === partie.jeu) return;
		this.chargementJeu = true;
		try {
			this.donnees = await chargerJeu(partie.jeu);
		} finally {
			this.chargementJeu = false;
		}
	}

	private async sauver(partie: Partie) {
		partie.modifiee = Date.now();
		await db.enregistrerPartie($state.snapshot(partie) as Partie);
	}

	async activer(id: string) {
		this.partieActiveId = id;
		await db.ecrireReglage('partieActive', id);
		await this.chargerDonneesActives();
	}

	async creerPartie(nom: string, jeu: string, version: string) {
		const maintenant = Date.now();
		const partie: Partie = {
			id: crypto.randomUUID(),
			nom: nom.trim() || 'Ma partie',
			jeu,
			version,
			creee: maintenant,
			modifiee: maintenant,
			captures: {}
		};
		this.parties.push(partie);
		await db.enregistrerPartie(partie);
		await this.activer(partie.id);
	}

	async renommer(id: string, nom: string) {
		const partie = this.parties.find((p) => p.id === id);
		if (!partie || !nom.trim()) return;
		partie.nom = nom.trim();
		await this.sauver(partie);
	}

	async supprimer(id: string) {
		this.parties = this.parties.filter((p) => p.id !== id);
		await db.supprimerPartie(id);
		if (this.partieActiveId === id) {
			const suivante = this.parties[0]?.id ?? null;
			this.partieActiveId = suivante;
			await db.ecrireReglage('partieActive', suivante);
			await this.chargerDonneesActives();
		}
	}

	estAttrape(pokemon: number): boolean {
		return this.partieActive?.captures[pokemon]?.attrape ?? false;
	}

	capture(pokemon: number): Capture | undefined {
		return this.partieActive?.captures[pokemon];
	}

	/** Modifie la capture d'un Pokémon (attrapé, chromatique, note…) et l'enregistre. */
	async modifierCapture(pokemon: number, modif: Partial<Omit<Capture, 'maj'>>) {
		const partie = this.partieActive;
		if (!partie) return;
		const actuelle = partie.captures[pokemon] ?? { attrape: false, maj: 0 };
		const suivante: Capture = { ...actuelle, ...modif, maj: Date.now() };
		// Un chromatique ou une forme obtenue implique que le Pokémon est attrapé
		if (modif.shiny || (modif.formes && Object.values(modif.formes).some(Boolean))) suivante.attrape = true;
		partie.captures[pokemon] = suivante;
		await this.sauver(partie);
	}

	async basculerCapture(pokemon: number) {
		await this.modifierCapture(pokemon, { attrape: !this.estAttrape(pokemon) });
	}
}

export const etat = new Etat();
