<script lang="ts">
	import { sprite } from '$lib/donnees';
	import { page } from '$app/state';
	import { analyserLieux, decrire } from '$lib/analyse';
	import BadgeType from '$lib/composants/BadgeType.svelte';
	import BoutonCapture from '$lib/composants/BoutonCapture.svelte';
	import PuceMethode from '$lib/composants/PuceMethode.svelte';
	import { etat } from '$lib/etat.svelte';

	let partie = $derived(etat.partieActive);
	let donnees = $derived(etat.donnees && partie && etat.donnees.jeu.id === partie.jeu ? etat.donnees : null);
	let lieux = $derived(donnees && partie ? analyserLieux(donnees, partie.version) : []);
	let index = $derived(lieux.findIndex((l) => l.lieu.id === page.params.id));
	let fiche = $derived(index >= 0 ? lieux[index] : null);

	let manquantsSeulement = $state(false);
	let pokemons = $derived(
		fiche
			? [...fiche.pokemons]
					.sort((a, b) => Number(etat.estAttrape(a.pokemon.id)) - Number(etat.estAttrape(b.pokemon.id)))
					.filter((p) => !manquantsSeulement || !etat.estAttrape(p.pokemon.id))
			: []
	);
	let reste = $derived(fiche ? fiche.pokemons.filter((p) => !etat.estAttrape(p.pokemon.id)).length : 0);
</script>

{#if !partie || !donnees}
	<p class="vide"><a href="#/">Choisis d'abord une partie.</a></p>
{:else if !fiche}
	<p class="vide">Ce lieu n'existe pas dans cette version. <a href="#/lieux">Retour aux lieux</a></p>
{:else}
	<nav class="navigation" aria-label="Lieux voisins">
		<a href="#/lieux">← Lieux</a>
		<span class="voisins">
			{#if index > 0}<a href="#/lieux/{lieux[index - 1].lieu.id}">‹ {lieux[index - 1].lieu.nom}</a>{/if}
			{#if index < lieux.length - 1}<a href="#/lieux/{lieux[index + 1].lieu.id}">{lieux[index + 1].lieu.nom} ›</a>{/if}
		</span>
	</nav>

	<h1>{fiche.lieu.nom}</h1>
	<p class="resume">
		{#if reste === 0}
			<strong class="termine">✓ Tous les Pokémon de ce lieu sont attrapés.</strong>
		{:else}
			Reste <strong>{reste}</strong> Pokémon à attraper sur {fiche.pokemons.length}.
		{/if}
		{#if fiche.lieu.url_pokepedia}
			<a href={fiche.lieu.url_pokepedia} target="_blank" rel="noopener">Page Poképédia ↗</a>
		{/if}
	</p>
	<label class="case"><input type="checkbox" bind:checked={manquantsSeulement} /> Manquants seulement</label>

	<ul class="liste">
		{#each pokemons as p (p.pokemon.id)}
			{@const attrape = etat.estAttrape(p.pokemon.id)}
			<li class:attrape>
				<img src={sprite(p.pokemon, partie.version)} alt="" width="56" height="56" loading="lazy" />
				<div class="infos">
					<div class="nom">
						<a href="#/pokemon/{p.pokemon.id}">{p.pokemon.nom}</a>
						{#each p.pokemon.types as t (t)}<BadgeType type={t} />{/each}
					</div>
					<ul class="obtentions">
						{#each p.obtentions as o (o.id)}
							<li><PuceMethode methode={o.methode} /> {decrire(o, donnees, false)}</li>
						{/each}
					</ul>
				</div>
				<BoutonCapture {attrape} nom={p.pokemon.nom} onclick={() => etat.basculerCapture(p.pokemon.id)} />
			</li>
		{/each}
	</ul>
{/if}

<style>
	.vide {
		padding: 32px 0;
		text-align: center;
	}
	.navigation {
		display: flex;
		flex-wrap: wrap;
		justify-content: space-between;
		gap: 8px;
		margin-bottom: 12px;
		font-size: 0.9rem;
	}
	.navigation a {
		text-decoration: none;
		font-weight: 600;
	}
	.voisins {
		display: flex;
		gap: 16px;
	}
	h1 {
		margin: 0 0 4px;
	}
	.resume {
		display: flex;
		flex-wrap: wrap;
		gap: 4px 14px;
		margin: 0 0 8px;
	}
	.termine {
		color: var(--progression);
	}
	.case {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 8px;
		font-size: 0.9rem;
	}
	.liste {
		margin: 0;
		padding: 0;
		list-style: none;
	}
	.liste > li {
		display: grid;
		grid-template-columns: 56px 1fr auto;
		align-items: center;
		gap: 10px;
		padding: 6px;
		border-bottom: 1px solid var(--ecran-ligne);
	}
	.liste > li.attrape {
		opacity: 0.6;
	}
	img {
		image-rendering: pixelated;
	}
	.nom {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 4px 6px;
		font-weight: 700;
	}
	.nom a {
		text-decoration: none;
	}
	.attrape .nom a {
		color: var(--attrape);
	}
	.obtentions {
		display: grid;
		gap: 2px;
		margin: 4px 0 0;
		padding: 0;
		list-style: none;
		font-size: 0.8rem;
		color: var(--ecran-texte-doux);
	}
</style>
