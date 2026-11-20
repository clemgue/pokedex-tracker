/**
 * Synchronisation de la progression avec Dropbox.
 *
 * Cycle : télécharger le fichier Dropbox → fusionner avec la copie locale → appliquer
 * localement → renvoyer si le résultat diffère (écriture conditionnelle à la révision lue ;
 * en cas de conflit, on recommence).
 *
 * Déclencheurs : démarrage, retour de l'application au premier plan, retour du réseau,
 * et quelques secondes après chaque modification locale.
 */
import { db } from '$lib/db';
import { etat } from '$lib/etat.svelte';
import * as dropbox from './dropbox';
import { fichierVide, fusionner, memeContenu, valider } from './fusion';

const DELAI_ENVOI = 3000;

type Statut = 'deconnecte' | 'pret' | 'en_cours' | 'erreur' | 'hors_ligne';

class Synchronisation {
	statut = $state<Statut>('deconnecte');
	erreur = $state<string | null>(null);
	derniere = $state<number | null>(null);
	/** Clé d'application Dropbox : réglage local, sinon valeur fournie au build */
	cleApp = $state('');

	private jetons: dropbox.JetonsDropbox | null = null;
	private minuterie: ReturnType<typeof setTimeout> | null = null;
	private enCours: Promise<void> | null = null;
	private aRefaire = false;

	connecte = $derived(this.statut !== 'deconnecte');

	async init() {
		// Clé saisie dans les réglages, sinon fournie au build (VITE_DROPBOX_APP_KEY, voir README)
		this.cleApp = (await db.lireReglage<string>('dropboxCleApp')) || (import.meta.env.VITE_DROPBOX_APP_KEY ?? '');
		this.derniere = (await db.lireReglage<number>('dropboxDerniere')) ?? null;
		try {
			const retour = await dropbox.terminerConnexion();
			if (retour) await db.ecrireReglage('dropbox', retour);
		} catch (e) {
			this.erreur = e instanceof Error ? e.message : String(e);
		}
		this.jetons = (await db.lireReglage<dropbox.JetonsDropbox>('dropbox')) ?? null;
		if (!this.jetons) return;
		this.statut = 'pret';
		etat.surModification = () => this.planifier();
		addEventListener('online', () => this.synchroniser());
		addEventListener('offline', () => (this.statut = 'hors_ligne'));
		document.addEventListener('visibilitychange', () => {
			if (document.visibilityState === 'visible') this.synchroniser();
			else if (this.minuterie) this.synchroniser(); // envoi immédiat avant mise en arrière-plan
		});
		await this.synchroniser();
	}

	async enregistrerCleApp(cle: string) {
		this.cleApp = cle.trim();
		await db.ecrireReglage('dropboxCleApp', this.cleApp);
	}

	async connecter() {
		if (!this.cleApp) throw new Error("Renseigne d'abord la clé d'application Dropbox.");
		await dropbox.demarrerConnexion(this.cleApp);
	}

	async deconnecter() {
		if (this.jetons) await dropbox.revoquer(this.jetons);
		this.jetons = null;
		await db.ecrireReglage('dropbox', null);
		etat.surModification = null;
		this.statut = 'deconnecte';
	}

	planifier() {
		if (!this.jetons) return;
		if (this.minuterie) clearTimeout(this.minuterie);
		this.minuterie = setTimeout(() => this.synchroniser(), DELAI_ENVOI);
	}

	/** Lance une synchronisation (regroupe les demandes simultanées). */
	synchroniser(): Promise<void> {
		if (this.minuterie) clearTimeout(this.minuterie);
		this.minuterie = null;
		if (!this.jetons) return Promise.resolve();
		if (this.enCours) {
			this.aRefaire = true;
			return this.enCours;
		}
		this.enCours = this.cycle().finally(() => {
			this.enCours = null;
			if (this.aRefaire) {
				this.aRefaire = false;
				this.synchroniser();
			}
		});
		return this.enCours;
	}

	private async cycle() {
		if (!navigator.onLine) {
			this.statut = 'hors_ligne';
			return;
		}
		this.statut = 'en_cours';
		try {
			for (let essai = 0; essai < 3; essai++) {
				const lu = await dropbox.telecharger(this.jetons!);
				this.jetons = lu.jetons;
				const distant = lu.contenu ? valider(lu.contenu) : fichierVide();
				const fusion = fusionner(etat.fichierLocal(), distant);
				if (!memeContenu(fusion, etat.fichierLocal())) await etat.appliquerFichier(fusion);
				if (lu.contenu && memeContenu(fusion, distant)) break; // rien à envoyer
				try {
					const ecrit = await dropbox.envoyer(this.jetons, { ...fusion, modifie: Date.now() }, lu.revision);
					this.jetons = ecrit.jetons;
					break;
				} catch (e) {
					if (!(e instanceof dropbox.ErreurConflit) || essai === 2) throw e;
				}
			}
			await db.ecrireReglage('dropbox', this.jetons);
			this.derniere = Date.now();
			await db.ecrireReglage('dropboxDerniere', this.derniere);
			this.erreur = null;
			this.statut = 'pret';
		} catch (e) {
			this.erreur = e instanceof Error ? e.message : String(e);
			this.statut = navigator.onLine ? 'erreur' : 'hors_ligne';
		}
	}
}

export const synchro = new Synchronisation();
