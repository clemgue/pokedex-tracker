<script lang="ts">
	import { goto } from '$app/navigation';
	import { avancement, LIBELLES_STATUT } from '$lib/aventure';
	import NouvellePartie from '$lib/composants/NouvellePartie.svelte';
	import { etat } from '$lib/etat.svelte';
	import type { Partie } from '$lib/types';

	let renommage = $state<{ id: string; nom: string } | null>(null);
	/** Partie en attente de confirmation de suppression (pas de confirm() : bloqué dans certains navigateurs) */
	let aSupprimer = $state<string | null>(null);

	function infos(p: Partie) {
		const jeu = etat.jeux.find((j) => j.id === p.jeu);
		const version = jeu?.versions.find((v) => v.id === p.version);
		return { jeu, version, av: avancement(p, jeu, etat.progression) };
	}

	async function choisir(id: string) {
		await etat.activer(id);
		goto('#/');
	}

	async function valider(e: SubmitEvent) {
		e.preventDefault();
		if (renommage) await etat.renommer(renommage.id, renommage.nom);
		renommage = null;
	}

	async function supprimer(id: string) {
		aSupprimer = null;
		await etat.supprimer(id);
	}
</script>

<h1>Parties</h1>

{#if etat.parties.length}
	<ul class="liste">
		{#each etat.parties as p (p.id)}
			{@const i = infos(p)}
			<li class:active={p.id === etat.partieActiveId} style:--couleur={i.version?.couleur}>
				{#if renommage?.id === p.id}
					<form class="renommer" onsubmit={valider}>
						<label class="sr-only" for="ren-{p.id}">Nouveau nom</label>
						<!-- svelte-ignore a11y_autofocus -->
						<input id="ren-{p.id}" class="champ" bind:value={renommage.nom} maxlength="60" autofocus />
						<button class="bouton" type="submit">OK</button>
						<button class="bouton secondaire" type="button" onclick={() => (renommage = null)}>Annuler</button>
					</form>
				{:else if aSupprimer === p.id}
					<div class="confirmation" role="alert">
						<p>Supprimer « {p.nom} » et toute sa progression ? Cette action est définitive.</p>
						<div class="actions">
							<button class="bouton danger" type="button" onclick={() => supprimer(p.id)}>Supprimer définitivement</button>
							<button class="bouton secondaire" type="button" onclick={() => (aSupprimer = null)}>Annuler</button>
						</div>
					</div>
				{:else}
					<div class="infos">
						<div class="entete">
							<strong>{p.nom}</strong>
							<span class="statut statut-{i.av.statut}">{LIBELLES_STATUT[i.av.statut]}</span>
						</div>
						<span>{i.jeu?.nom ?? p.jeu} — {i.version?.nom ?? p.version}</span>
						{#if i.av.total}
							<div class="avancement">
								<div
									class="barre"
									role="progressbar"
									aria-label="Pokédex"
									aria-valuemin="0"
									aria-valuemax={i.av.total}
									aria-valuenow={i.av.attrapes}
								>
									<span style:width="{i.av.pourcentage}%"></span>
								</div>
								<span class="chiffres"><strong>{i.av.pourcentage} %</strong> · {i.av.attrapes} / {i.av.total}</span>
							</div>
						{/if}
						{#if i.av.premierGroupe}
							<span>
								{i.av.premierGroupe.titre} : {i.av.premierGroupe.faits} / {i.av.premierGroupe.total}
								{#if i.av.histoireFinie}· histoire terminée{/if}
							</span>
						{/if}
					</div>
					<div class="actions">
						{#if p.id === etat.partieActiveId}
							<span class="badge">Active</span>
						{:else}
							<button class="bouton" type="button" onclick={() => choisir(p.id)}>Jouer</button>
						{/if}
						<button class="bouton secondaire" type="button" onclick={() => (renommage = { id: p.id, nom: p.nom })}
							>Renommer</button
						>
						<button class="bouton secondaire" type="button" onclick={() => (aSupprimer = p.id)}>Supprimer</button>
					</div>
				{/if}
			</li>
		{/each}
	</ul>
{/if}

<h2>Nouvelle partie</h2>
<NouvellePartie apresCreation={() => goto('#/')} />

<style>
	h1,
	h2 {
		margin: 0 0 12px;
	}
	h2 {
		margin-top: 28px;
		font-size: 1.1rem;
	}
	.liste {
		display: grid;
		gap: 10px;
		margin: 0;
		padding: 0;
		list-style: none;
	}
	li {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 12px 14px;
		border-radius: 8px;
		background: var(--ecran-alt);
		border-left: 6px solid var(--couleur, var(--champ-bord));
	}
	li.active {
		box-shadow: inset 0 0 0 2px var(--couleur, var(--champ-bord));
	}
	.infos {
		display: grid;
		gap: 4px;
		flex: 1;
		min-width: 220px;
	}
	.infos > span {
		font-size: 0.85rem;
		color: var(--ecran-texte-doux);
	}
	.entete {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 4px 10px;
	}
	.statut {
		padding: 1px 10px;
		border-radius: 999px;
		font-size: 0.75rem;
		font-weight: 700;
		border: 1px solid currentColor;
		color: var(--ecran-texte-doux);
	}
	.statut-en_cours {
		color: var(--lentille);
	}
	.statut-terminee {
		color: var(--progression);
	}
	.statut-complete {
		background: var(--progression);
		border-color: var(--progression);
		color: #fff;
	}
	.avancement {
		display: flex;
		align-items: center;
		gap: 10px;
		max-width: 420px;
	}
	.barre {
		flex: 1;
		height: 10px;
		border-radius: 999px;
		background: var(--ecran-ligne);
		overflow: hidden;
	}
	.barre span {
		display: block;
		height: 100%;
		background: var(--couleur, var(--progression));
	}
	.chiffres {
		font-family: var(--police-ecran);
		font-size: 0.8rem;
		white-space: nowrap;
	}
	.actions,
	.renommer {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		align-items: center;
	}
	.renommer {
		flex: 1;
	}
	.renommer .champ {
		flex: 1;
		min-width: 160px;
	}
	.confirmation {
		display: grid;
		gap: 10px;
		width: 100%;
	}
	.confirmation p {
		margin: 0;
		font-weight: 600;
		color: var(--alerte);
	}
	.badge {
		padding: 4px 12px;
		border-radius: 999px;
		background: var(--couleur, var(--bouton));
		color: #fff;
		font-weight: 700;
		font-size: 0.85rem;
	}
</style>
