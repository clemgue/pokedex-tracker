<script lang="ts">
	import '$lib/theme.css';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import BasculeTheme from '$lib/composants/BasculeTheme.svelte';
	import { etat } from '$lib/etat.svelte';

	let { children } = $props();

	onMount(() => {
		etat.init();
	});

	const liens = [
		{ href: '#/', libelle: 'Pokédex', route: '/', aussi: ['/pokemon/[id]'] },
		{ href: '#/lieux', libelle: 'Lieux', route: '/lieux', aussi: ['/lieux/[id]'] },
		{ href: '#/parties', libelle: 'Parties', route: '/parties', aussi: [] }
	];
</script>

<div class="appareil">
	<header class="coque">
		<div class="voyants" aria-hidden="true">
			<span class="lentille"></span>
			<span class="voyant rouge"></span>
			<span class="voyant jaune"></span>
			<span class="voyant vert"></span>
		</div>
		<div class="titre">
			<span class="marque">Pokédex</span>
			{#if etat.partieActive}
				<span class="partie">{etat.partieActive.nom}</span>
			{/if}
		</div>
		<BasculeTheme />
	</header>

	<nav class="onglets" aria-label="Navigation principale">
		{#each liens as lien (lien.route)}
			<a
				href={lien.href}
				aria-current={page.route.id === lien.route || lien.aussi.includes(page.route.id ?? '') ? 'page' : undefined}
				>{lien.libelle}</a
			>
		{/each}
	</nav>

	<main class="cadre">
		<div class="ecran">
			{#if !etat.pret}
				<p class="message">Chargement…</p>
			{:else if etat.erreur}
				<p class="message erreur">Erreur : {etat.erreur}</p>
			{:else}
				{@render children()}
			{/if}
		</div>
	</main>

	<footer class="pied">
		Données : <a href="https://www.pokepedia.fr/" target="_blank" rel="noopener">Poképédia</a> (CC BY-NC-SA)
		et <a href="https://pokeapi.co/" target="_blank" rel="noopener">PokéAPI</a>. Projet personnel non
		commercial ; Pokémon est une marque de Nintendo, Creatures et Game Freak.
	</footer>
</div>

<style>
	.appareil {
		max-width: 980px;
		margin: 0 auto;
		padding: 0 0 24px;
	}

	.coque {
		position: sticky;
		top: 0;
		z-index: 10;
		display: flex;
		align-items: center;
		gap: 14px;
		padding: 12px 16px;
		background: linear-gradient(180deg, var(--coque-clair), var(--coque) 40%, var(--coque-fonce));
		color: var(--coque-texte);
		border-bottom: 4px solid var(--coque-fonce);
		box-shadow: 0 4px 12px rgb(0 0 0 / 0.35);
	}

	.voyants {
		display: flex;
		align-items: flex-start;
		gap: 6px;
	}
	.lentille {
		width: 44px;
		height: 44px;
		border-radius: 50%;
		border: 4px solid #fff;
		background: radial-gradient(circle at 35% 35%, var(--lentille-clair), var(--lentille) 55%, #0b4f8a);
		box-shadow: 0 0 0 2px rgb(0 0 0 / 0.35);
	}
	.voyant {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		border: 2px solid rgb(0 0 0 / 0.35);
	}
	.rouge {
		background: var(--voyant-rouge);
	}
	.jaune {
		background: var(--voyant-jaune);
	}
	.vert {
		background: var(--voyant-vert);
	}

	.titre {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		line-height: 1.15;
	}
	.marque {
		font-size: 1.35rem;
		font-weight: 800;
		letter-spacing: 0.02em;
		text-shadow: 0 2px 0 rgb(0 0 0 / 0.3);
	}
	.partie {
		font-size: 0.85rem;
		opacity: 0.9;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.onglets {
		display: flex;
		gap: 4px;
		padding: 10px 16px 0;
		background: var(--coque-fonce);
	}
	.onglets a {
		padding: 8px 16px;
		border-radius: 10px 10px 0 0;
		color: var(--coque-texte);
		text-decoration: none;
		font-weight: 600;
		opacity: 0.8;
	}
	.onglets a[aria-current='page'] {
		background: var(--cadre);
		color: var(--ecran-texte);
		opacity: 1;
	}

	.cadre {
		padding: 12px;
		background: var(--cadre);
		border-bottom: 6px solid var(--cadre-ombre);
		border-radius: 0 0 var(--rayon) var(--rayon);
	}
	.ecran {
		min-height: 60vh;
		padding: 16px;
		background: var(--ecran);
		color: var(--ecran-texte);
		border-radius: 6px;
		box-shadow: inset 0 0 0 2px var(--ecran-ligne), inset 0 3px 10px rgb(0 0 0 / 0.15);
	}

	.message {
		padding: 32px 0;
		text-align: center;
		color: var(--ecran-texte-doux);
	}
	.erreur {
		color: var(--alerte);
	}

	.pied {
		padding: 16px;
		font-size: 0.75rem;
		color: #d8c4c7;
		text-align: center;
	}

	@media (max-width: 600px) {
		.coque {
			padding: 10px 12px;
			gap: 10px;
		}
		.lentille {
			width: 36px;
			height: 36px;
		}
		.onglets {
			padding: 8px 12px 0;
		}
		.cadre {
			padding: 6px;
			border-radius: 0;
		}
		.ecran {
			padding: 12px;
		}
	}
</style>
