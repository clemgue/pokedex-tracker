// --- Données de jeu (générées par tools/data/build.py) -------------------------

export interface VersionJeu {
	id: string;
	nom: string;
	couleur: string;
}

export interface InfoJeu {
	id: string;
	nom: string;
	generation: number;
	region: string;
	annee_sortie: number;
	annee_sortie_fr: number;
	ordre: number;
	versions: VersionJeu[];
	fichier?: string;
}

export interface Pokedex {
	id: string;
	nom: string;
	entrees: { numero: number; pokemon: number }[];
}

export interface Pokemon {
	id: number;
	nom: string;
	nom_en: string;
	types: string[];
	sprites: Record<string, string>;
	artwork: string | null;
	url_pokepedia: string | null;
}

export interface Lieu {
	id: string;
	nom: string;
	url_pokepedia: string | null;
	versions: string[];
	ordre: number | null;
}

export type Methode =
	| 'hautes_herbes'
	| 'marche'
	| 'surf'
	| 'peche'
	| 'don'
	| 'echange_pnj'
	| 'achat'
	| 'fossile'
	| 'fixe'
	| 'evolution'
	| 'echange_version'
	| 'evenement'
	| 'bug';

export interface Obtention {
	id: number;
	pokemon: number;
	lieu: string | null;
	methode: Methode;
	detail: string | null;
	zone: string | null;
	versions: string[];
	niveaux: string | null;
	taux: number | null;
	taux_texte: string | null;
	depuis?: number;
	glitch: boolean;
}

export interface DonneesJeu {
	format: number;
	jeu: InfoJeu;
	methodes: Record<Methode, string>;
	pokedex: Pokedex[];
	pokemon: Pokemon[];
	lieux: Lieu[];
	obtentions: Obtention[];
	sources: { nom: string; url: string; licence?: string }[];
}

// --- Progression de l'utilisateur ------------------------------------------------

export interface Capture {
	attrape: boolean;
	shiny?: boolean;
	/** Formes obtenues (clé : identifiant de forme) */
	formes?: Record<string, boolean>;
	/** Méga-Gemme obtenue */
	mega?: boolean;
	note?: string;
	/** Horodatage de la dernière modification (fusion lors de la synchronisation) */
	maj: number;
}

export interface Partie {
	id: string;
	nom: string;
	jeu: string;
	version: string;
	creee: number;
	modifiee: number;
	/** Clé : numéro national du Pokémon */
	captures: Record<string, Capture>;
}
