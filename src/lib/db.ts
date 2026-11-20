/**
 * Stockage local (IndexedDB) : copie de travail de la progression.
 * La synchronisation Dropbox (lot L4) s'appuiera sur cette copie.
 */
import type { Partie } from './types';

const NOM_BASE = 'pokedex-tracker';
const VERSION_BASE = 1;
const PARTIES = 'parties';
const REGLAGES = 'reglages';

let ouverture: Promise<IDBDatabase> | null = null;

function ouvrir(): Promise<IDBDatabase> {
	ouverture ??= new Promise((resolve, reject) => {
		const req = indexedDB.open(NOM_BASE, VERSION_BASE);
		req.onupgradeneeded = () => {
			const db = req.result;
			if (!db.objectStoreNames.contains(PARTIES)) db.createObjectStore(PARTIES, { keyPath: 'id' });
			if (!db.objectStoreNames.contains(REGLAGES)) db.createObjectStore(REGLAGES);
		};
		req.onsuccess = () => resolve(req.result);
		req.onerror = () => reject(req.error);
	});
	return ouverture;
}

async function transaction<T>(
	magasin: string,
	mode: IDBTransactionMode,
	action: (store: IDBObjectStore) => IDBRequest<T>
): Promise<T> {
	const db = await ouvrir();
	return new Promise((resolve, reject) => {
		const tx = db.transaction(magasin, mode);
		const req = action(tx.objectStore(magasin));
		tx.oncomplete = () => resolve(req.result);
		tx.onerror = () => reject(tx.error);
		tx.onabort = () => reject(tx.error);
	});
}

export const db = {
	toutesLesParties: () => transaction<Partie[]>(PARTIES, 'readonly', (s) => s.getAll()),
	enregistrerPartie: (p: Partie) => transaction(PARTIES, 'readwrite', (s) => s.put(p)),
	supprimerPartie: (id: string) => transaction(PARTIES, 'readwrite', (s) => s.delete(id)),
	lireReglage: <T>(cle: string) => transaction<T | undefined>(REGLAGES, 'readonly', (s) => s.get(cle)),
	ecrireReglage: (cle: string, valeur: unknown) => transaction(REGLAGES, 'readwrite', (s) => s.put(valeur, cle))
};
