<script lang="ts">
	import type { NoeudEvolution } from '$lib/analyse';
	import Evolutions from './Evolutions.svelte';

	let {
		noeud,
		version,
		actuel,
		attrape
	}: { noeud: NoeudEvolution; version: string; actuel: number; attrape: (id: number) => boolean } = $props();
</script>

<div class="stade">
	<a
		class="pokemon"
		class:actuel={noeud.pokemon.id === actuel}
		class:attrape={attrape(noeud.pokemon.id)}
		href="#/pokemon/{noeud.pokemon.id}"
	>
		<img src={noeud.pokemon.sprites[version] ?? noeud.pokemon.artwork} alt="" width="56" height="56" />
		<span>{noeud.pokemon.nom}</span>
	</a>
	{#if noeud.suivants.length}
		<div class="branches">
			{#each noeud.suivants as s (s.pokemon.id)}
				<div class="branche">
					<div class="fleche">
						<span aria-hidden="true">→</span>
						<small>{s.condition ?? ''}</small>
					</div>
					<Evolutions noeud={s} {version} {actuel} {attrape} />
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.stade {
		display: flex;
		align-items: center;
		gap: 4px;
	}
	.branches {
		display: grid;
		gap: 6px;
	}
	.branche {
		display: flex;
		align-items: center;
		gap: 4px;
	}
	.pokemon {
		display: grid;
		justify-items: center;
		width: 84px;
		padding: 4px;
		border-radius: 8px;
		text-decoration: none;
		font-size: 0.75rem;
		font-weight: 600;
		text-align: center;
	}
	.pokemon:hover {
		background: var(--ecran-survol);
	}
	.pokemon.actuel {
		box-shadow: inset 0 0 0 2px var(--ecran-texte-doux);
	}
	.pokemon.attrape span {
		color: var(--attrape);
	}
	img {
		image-rendering: pixelated;
	}
	.fleche {
		display: grid;
		justify-items: center;
		width: 84px;
		color: var(--ecran-texte-doux);
		text-align: center;
		line-height: 1.2;
	}
	.fleche span {
		font-size: 1.2rem;
	}
	.fleche small {
		font-size: 0.68rem;
	}
	@media (max-width: 600px) {
		.pokemon,
		.fleche {
			width: 64px;
		}
		img {
			width: 44px;
			height: 44px;
		}
	}
</style>
