<script lang="ts">
	import { decrire, type GroupeLieu } from '$lib/analyse';
	import type { DonneesJeu, Obtention } from '$lib/types';
	import PuceMethode from './PuceMethode.svelte';

	let {
		parLieu,
		sansLieu,
		donnees,
		lienInterne = false
	}: {
		parLieu: GroupeLieu[];
		sansLieu: Obtention[];
		donnees: DonneesJeu;
		/** Lier le nom du lieu à la vue interne du lieu (sinon à Poképédia) */
		lienInterne?: boolean;
	} = $props();
</script>

<ul class="detail">
	{#each parLieu as g (g.lieu.id)}
		<li>
			{#if lienInterne}
				<a class="lieu" href="#/lieux/{g.lieu.id}">{g.lieu.nom}</a>
			{:else if g.lieu.url_pokepedia}
				<a class="lieu" href={g.lieu.url_pokepedia} target="_blank" rel="noopener">{g.lieu.nom}</a>
			{:else}
				<span class="lieu">{g.lieu.nom}</span>
			{/if}
			<ul>
				{#each g.obtentions as o (o.id)}
					<li><PuceMethode methode={o.methode} /> {decrire(o, donnees, false)}</li>
				{/each}
			</ul>
		</li>
	{/each}
	{#each sansLieu as o (o.id)}
		<li>
			<PuceMethode methode={o.methode} />
			{#if o.depuis}
				<a href="#/pokemon/{o.depuis}">{decrire(o, donnees, false)}</a>
			{:else}
				{decrire(o, donnees, false)}
			{/if}
		</li>
	{/each}
	{#if !parLieu.length && !sansLieu.length}
		<li class="vide">Introuvable dans cette version.</li>
	{/if}
</ul>

<style>
	.detail {
		display: grid;
		gap: 6px;
		margin: 6px 0 4px;
		padding: 8px 10px;
		border-radius: 8px;
		background: var(--ecran-alt);
		box-shadow: inset 0 0 0 1px var(--ecran-ligne);
		list-style: none;
		color: var(--ecran-texte);
		font-size: 0.85rem;
	}
	.detail ul {
		display: grid;
		gap: 3px;
		margin: 2px 0 0;
		padding: 0 0 0 10px;
		list-style: none;
		color: var(--ecran-texte-doux);
	}
	.lieu {
		font-weight: 700;
	}
	.vide {
		color: var(--ecran-texte-doux);
	}
</style>
