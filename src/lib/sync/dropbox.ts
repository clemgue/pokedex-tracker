/**
 * Accès minimal à l'API Dropbox (sans SDK) : OAuth 2 PKCE + lecture/écriture d'un fichier
 * dans le dossier de l'application (« Applications/<nom de l'app> »).
 *
 * Aucun secret n'est stocké : PKCE est prévu pour les applications publiques (navigateur).
 * Le jeton de rafraîchissement (offline) permet de rester connecté sans redemander l'accord.
 */

export const CHEMIN_FICHIER = '/progression.json';
const AUTORISATION = 'https://www.dropbox.com/oauth2/authorize';
const JETON = 'https://api.dropboxapi.com/oauth2/token';
const CONTENU = 'https://content.dropboxapi.com/2/files';
const REVOCATION = 'https://api.dropboxapi.com/2/auth/token/revoke';

export interface JetonsDropbox {
	cleApp: string;
	refresh: string;
	acces: string;
	expire: number;
}

export class ErreurConflit extends Error {}

function base64Url(octets: Uint8Array): string {
	return btoa(String.fromCharCode(...octets))
		.replace(/\+/g, '-')
		.replace(/\//g, '_')
		.replace(/=+$/, '');
}

function aleatoire(n = 48): string {
	return base64Url(crypto.getRandomValues(new Uint8Array(n)));
}

/** Adresse de retour : la page de l'application, sans ancre ni paramètres. */
export function adresseRetour(): string {
	return location.origin + location.pathname;
}

/** Démarre la connexion : redirige vers Dropbox. */
export async function demarrerConnexion(cleApp: string): Promise<void> {
	const verificateur = aleatoire();
	const etat = aleatoire(16);
	const empreinte = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verificateur)));
	sessionStorage.setItem('dropbox-pkce', JSON.stringify({ verificateur, etat, cleApp }));
	const params = new URLSearchParams({
		client_id: cleApp,
		response_type: 'code',
		code_challenge: base64Url(empreinte),
		code_challenge_method: 'S256',
		token_access_type: 'offline',
		redirect_uri: adresseRetour(),
		state: etat
	});
	location.assign(`${AUTORISATION}?${params}`);
}

/**
 * Au retour de Dropbox (?code=…&state=…) : échange le code contre des jetons.
 * Renvoie null si l'adresse ne contient pas de retour Dropbox.
 */
export async function terminerConnexion(): Promise<JetonsDropbox | null> {
	const url = new URL(location.href);
	const code = url.searchParams.get('code');
	const etatRecu = url.searchParams.get('state');
	const erreur = url.searchParams.get('error');
	if (!code && !erreur) return null;

	// Nettoie l'adresse (on garde l'ancre éventuelle)
	history.replaceState(null, '', adresseRetour() + location.hash);
	const attendu = JSON.parse(sessionStorage.getItem('dropbox-pkce') ?? 'null');
	sessionStorage.removeItem('dropbox-pkce');
	if (erreur) throw new Error(`Connexion Dropbox refusée (${erreur}).`);
	if (!attendu || attendu.etat !== etatRecu) throw new Error('Retour Dropbox inattendu : recommence la connexion.');

	const rep = await fetch(JETON, {
		method: 'POST',
		body: new URLSearchParams({
			code: code!,
			grant_type: 'authorization_code',
			client_id: attendu.cleApp,
			redirect_uri: adresseRetour(),
			code_verifier: attendu.verificateur
		})
	});
	if (!rep.ok) throw new Error(`Échec de la connexion Dropbox (${rep.status}).`);
	const j = await rep.json();
	return {
		cleApp: attendu.cleApp,
		refresh: j.refresh_token,
		acces: j.access_token,
		expire: Date.now() + (j.expires_in - 60) * 1000
	};
}

async function jetonValide(jetons: JetonsDropbox): Promise<JetonsDropbox> {
	if (Date.now() < jetons.expire) return jetons;
	const rep = await fetch(JETON, {
		method: 'POST',
		body: new URLSearchParams({ grant_type: 'refresh_token', refresh_token: jetons.refresh, client_id: jetons.cleApp })
	});
	if (!rep.ok) throw new Error('Session Dropbox expirée : reconnecte-toi.');
	const j = await rep.json();
	return { ...jetons, acces: j.access_token, expire: Date.now() + (j.expires_in - 60) * 1000 };
}

/** En-tête Dropbox-API-Arg : JSON en ASCII (les caractères non ASCII doivent être échappés). */
function argument(obj: unknown): string {
	return JSON.stringify(obj).replace(/[\u007f-￿]/g, (c) => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
}

export interface Telechargement {
	contenu: unknown | null;
	revision: string | null;
	jetons: JetonsDropbox;
}

export async function telecharger(jetons: JetonsDropbox): Promise<Telechargement> {
	jetons = await jetonValide(jetons);
	const rep = await fetch(`${CONTENU}/download`, {
		method: 'POST',
		headers: { Authorization: `Bearer ${jetons.acces}`, 'Dropbox-API-Arg': argument({ path: CHEMIN_FICHIER }) }
	});
	if (rep.status === 409) return { contenu: null, revision: null, jetons }; // fichier absent
	if (!rep.ok) throw new Error(`Lecture Dropbox impossible (${rep.status}).`);
	const meta = JSON.parse(rep.headers.get('Dropbox-API-Result') ?? '{}');
	return { contenu: await rep.json(), revision: meta.rev ?? null, jetons };
}

/** Écrit le fichier. Avec `revision`, échoue (ErreurConflit) si le fichier a changé entre-temps. */
export async function envoyer(
	jetons: JetonsDropbox,
	contenu: unknown,
	revision: string | null
): Promise<{ revision: string; jetons: JetonsDropbox }> {
	jetons = await jetonValide(jetons);
	const mode = revision ? { '.tag': 'update', update: revision } : { '.tag': 'add' };
	const rep = await fetch(`${CONTENU}/upload`, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${jetons.acces}`,
			'Content-Type': 'application/octet-stream',
			'Dropbox-API-Arg': argument({ path: CHEMIN_FICHIER, mode, mute: true, autorename: false })
		},
		body: JSON.stringify(contenu)
	});
	if (rep.status === 409) throw new ErreurConflit('Le fichier Dropbox a changé pendant la synchronisation.');
	if (!rep.ok) throw new Error(`Écriture Dropbox impossible (${rep.status}).`);
	const meta = await rep.json();
	return { revision: meta.rev, jetons };
}

export async function revoquer(jetons: JetonsDropbox): Promise<void> {
	try {
		const j = await jetonValide(jetons);
		await fetch(REVOCATION, { method: 'POST', headers: { Authorization: `Bearer ${j.acces}` } });
	} catch {
		// Déconnexion locale quoi qu'il arrive
	}
}
