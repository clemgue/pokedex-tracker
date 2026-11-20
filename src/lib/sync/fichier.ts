/** Export / import manuel de la progression (fichier JSON). */
import { etat } from '$lib/etat.svelte';
import { fusionner, valider, type FichierProgression } from './fusion';

export function exporter() {
	const contenu = JSON.stringify({ ...etat.fichierLocal(), modifie: Date.now() }, null, 1);
	const url = URL.createObjectURL(new Blob([contenu], { type: 'application/json' }));
	const lien = document.createElement('a');
	lien.href = url;
	lien.download = `pokedex-tracker-${new Date().toISOString().slice(0, 10)}.json`;
	lien.click();
	setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export async function lireFichier(fichier: File): Promise<FichierProgression> {
	let json: unknown;
	try {
		json = JSON.parse(await fichier.text());
	} catch {
		throw new Error("Ce fichier n'est pas un JSON valide.");
	}
	return valider(json);
}

/** Importe une sauvegarde : fusion (par défaut) ou remplacement complet. */
export async function importer(f: FichierProgression, mode: 'fusionner' | 'remplacer') {
	const local = etat.fichierLocal();
	let resultat: FichierProgression;
	if (mode === 'fusionner') {
		resultat = fusionner(local, f);
	} else {
		// Remplacement : les parties locales absentes du fichier sont marquées supprimées
		const maintenant = Date.now();
		const supprimees = { ...f.supprimees };
		const gardees = new Set(f.parties.map((p) => p.id));
		for (const p of local.parties) if (!gardees.has(p.id)) supprimees[p.id] = maintenant;
		resultat = { ...f, parties: f.parties.map((p) => ({ ...p, modifiee: maintenant })), supprimees };
	}
	await etat.appliquerFichier(resultat);
	etat.surModification?.();
}
