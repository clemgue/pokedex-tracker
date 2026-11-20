<script lang="ts">
	import { etat } from '$lib/etat.svelte';
	import { adresseRetour } from '$lib/sync/dropbox';
	import { exporter, importer, lireFichier } from '$lib/sync/fichier';
	import type { FichierProgression } from '$lib/sync/fusion';
	import { synchro } from '$lib/sync/sync.svelte';

	let cle = $state(synchro.cleApp);
	let message = $state<{ texte: string; erreur?: boolean } | null>(null);
	let fichierImporte = $state<FichierProgression | null>(null);

	const libelles = {
		deconnecte: 'Non connecté',
		pret: 'Synchronisé',
		en_cours: 'Synchronisation…',
		erreur: 'Erreur',
		hors_ligne: 'Hors ligne (synchronisation au retour du réseau)'
	};

	function date(t: number | null) {
		return t ? new Date(t).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }) : 'jamais';
	}

	async function connecter() {
		try {
			await synchro.enregistrerCleApp(cle);
			await synchro.connecter();
		} catch (e) {
			message = { texte: e instanceof Error ? e.message : String(e), erreur: true };
		}
	}

	async function choisirFichier(e: Event) {
		const input = e.currentTarget as HTMLInputElement;
		const f = input.files?.[0];
		input.value = '';
		if (!f) return;
		try {
			fichierImporte = await lireFichier(f);
			message = null;
		} catch (err) {
			message = { texte: err instanceof Error ? err.message : String(err), erreur: true };
		}
	}

	async function confirmerImport(mode: 'fusionner' | 'remplacer') {
		if (!fichierImporte) return;
		await importer(fichierImporte, mode);
		message = {
			texte: `Sauvegarde importée (${fichierImporte.parties.length} partie(s), ${mode === 'fusionner' ? 'fusionnée' : 'remplacement'}).`
		};
		fichierImporte = null;
	}
</script>

<h1>Réglages</h1>

{#if message}
	<p class="message" class:erreur={message.erreur} role="status">{message.texte}</p>
{/if}

<section>
	<h2>Synchronisation Dropbox</h2>
	<p class="aide">
		Ta progression est enregistrée dans un fichier <code>progression.json</code> de ton Dropbox (dossier
		<em>Applications</em>), partagé entre tous tes appareils. Sans connexion, elle reste sur cet appareil.
	</p>

	<p class="statut statut-{synchro.statut}">
		<span class="pastille" aria-hidden="true"></span>
		<strong>{libelles[synchro.statut]}</strong>
		{#if synchro.connecte}· dernière synchronisation : {date(synchro.derniere)}{/if}
	</p>
	{#if synchro.erreur}<p class="message erreur">{synchro.erreur}</p>{/if}

	{#if synchro.connecte}
		<div class="actions">
			<button class="bouton" type="button" onclick={() => synchro.synchroniser()} disabled={synchro.statut === 'en_cours'}
				>Synchroniser maintenant</button
			>
			<button class="bouton secondaire" type="button" onclick={() => synchro.deconnecter()}>Se déconnecter</button>
		</div>
	{:else}
		<div class="cle">
			<label class="etiquette" for="cle">Clé d'application Dropbox (App key)</label>
			<input id="cle" class="champ" bind:value={cle} autocomplete="off" spellcheck="false" placeholder="ex. a1b2c3d4e5f6g7h" />
		</div>
		<div class="actions">
			<button class="bouton" type="button" onclick={connecter} disabled={!cle.trim()}>Se connecter à Dropbox</button>
		</div>
		<details class="guide">
			<summary>Comment obtenir la clé (une seule fois)</summary>
			<ol>
				<li>
					Ouvre la <a href="https://www.dropbox.com/developers/apps" target="_blank" rel="noopener">console des
						applications Dropbox</a
					> et clique sur <em>Create app</em>.
				</li>
				<li>Choisis <em>Scoped access</em> puis <em>App folder</em>, et donne un nom (ex. « Pokedex Tracker »).</li>
				<li>
					Onglet <em>Permissions</em> : coche <code>files.content.read</code> et <code>files.content.write</code>, puis
					<em>Submit</em>.
				</li>
				<li>
					Onglet <em>Settings</em> : dans <em>OAuth 2 → Redirect URIs</em>, ajoute exactement
					<code>{adresseRetour()}</code> (et l'adresse de chaque autre site où tu utilises l'application).
				</li>
				<li>Copie la valeur <em>App key</em> dans le champ ci-dessus. (Le <em>App secret</em> n'est pas nécessaire.)</li>
			</ol>
		</details>
	{/if}
</section>

<section>
	<h2>Sauvegarde manuelle</h2>
	<p class="aide">Fichier JSON contenant toutes tes parties : pour archiver ou transférer sans Dropbox.</p>
	<div class="actions">
		<button class="bouton" type="button" onclick={exporter} disabled={!etat.parties.length}>Exporter</button>
		<label class="bouton secondaire">
			Importer…
			<input class="sr-only" type="file" accept="application/json,.json" onchange={choisirFichier} />
		</label>
	</div>
	{#if fichierImporte}
		<div class="confirmation" role="alert">
			<p>
				Fichier lu : {fichierImporte.parties.length} partie(s). <strong>Fusionner</strong> garde tes parties actuelles et
				ajoute/actualise celles du fichier. <strong>Remplacer</strong> supprime les parties absentes du fichier.
			</p>
			<div class="actions">
				<button class="bouton" type="button" onclick={() => confirmerImport('fusionner')}>Fusionner</button>
				<button class="bouton danger" type="button" onclick={() => confirmerImport('remplacer')}>Remplacer</button>
				<button class="bouton secondaire" type="button" onclick={() => (fichierImporte = null)}>Annuler</button>
			</div>
		</div>
	{/if}
</section>

<style>
	h1 {
		margin: 0 0 12px;
	}
	section {
		margin-bottom: 28px;
	}
	h2 {
		margin: 0 0 6px;
		font-size: 1.1rem;
	}
	.aide {
		margin: 0 0 10px;
		color: var(--ecran-texte-doux);
		font-size: 0.9rem;
	}
	.statut {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 6px;
		margin: 0 0 10px;
	}
	.pastille {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		background: var(--ecran-texte-doux);
	}
	.statut-pret .pastille {
		background: var(--progression);
	}
	.statut-en_cours .pastille {
		background: var(--voyant-jaune);
	}
	.statut-erreur .pastille {
		background: var(--alerte);
	}
	.cle {
		max-width: 420px;
		margin-bottom: 10px;
	}
	.actions {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}
	.guide {
		margin-top: 12px;
		font-size: 0.9rem;
	}
	.guide summary {
		cursor: pointer;
		font-weight: 600;
	}
	.guide li {
		margin: 4px 0;
	}
	code {
		padding: 1px 5px;
		border-radius: 4px;
		background: var(--ecran-alt);
		font-family: var(--police-ecran);
		font-size: 0.85em;
		word-break: break-all;
	}
	.message {
		padding: 8px 12px;
		border-radius: 8px;
		background: var(--ecran-alt);
	}
	.message.erreur {
		color: var(--alerte);
	}
	.confirmation {
		margin-top: 12px;
		padding: 10px 12px;
		border-radius: 8px;
		background: var(--ecran-alt);
	}
	.confirmation p {
		margin: 0 0 8px;
	}
	label.bouton {
		position: relative;
	}
</style>
