<script lang="ts">
	import '$lib/theme.css';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import BasculeTheme from '$lib/composants/BasculeTheme.svelte';
	import RetourHaut from '$lib/composants/RetourHaut.svelte';
	import { etat } from '$lib/etat.svelte';
	import { synchro } from '$lib/sync/sync.svelte';

	let { children } = $props();

	onMount(async () => {
		await etat.init();
		await synchro.init();
	});

	const titresSynchro = {
		deconnecte: 'Réglages — synchronisation Dropbox non configurée',
		pret: 'Réglages — synchronisé avec Dropbox',
		en_cours: 'Réglages — synchronisation en cours…',
		erreur: 'Réglages — erreur de synchronisation',
		hors_ligne: 'Réglages — hors ligne'
	};

	const liens = [
		{ href: '#/', libelle: 'Pokédex', route: '/', aussi: ['/pokemon/[id]'] },
		{ href: '#/lieux', libelle: 'Lieux', route: '/lieux', aussi: ['/lieux/[id]'] },
		{ href: '#/badges', libelle: 'Badges', route: '/badges', aussi: [] },
		{ href: '#/stats', libelle: 'Bilan', route: '/stats', aussi: [] },
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
		<a
			class="reglages statut-{synchro.statut}"
			href="#/reglages"
			title={titresSynchro[synchro.statut]}
			aria-label={titresSynchro[synchro.statut]}
		>
			<svg viewBox="0 0 24 24" aria-hidden="true"
				><path d="M7 18h10a4 4 0 0 0 .6-7.95A6 6 0 0 0 6.1 9.1 4.5 4.5 0 0 0 7 18z" /></svg
			>
			<span class="voyant-synchro"></span>
		</a>
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

	<RetourHaut />

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

	.reglages {
		position: relative;
		display: grid;
		place-items: center;
		width: 40px;
		height: 40px;
		border: 2px solid rgb(0 0 0 / 0.25);
		border-radius: 50%;
		background: var(--coque-fonce);
		color: var(--coque-texte);
		box-shadow: inset 0 2px 0 rgb(255 255 255 / 0.15);
	}
	.reglages:hover {
		background: var(--coque-clair);
	}
	.reglages svg {
		width: 22px;
		height: 22px;
		fill: none;
		stroke: currentColor;
		stroke-width: 2;
		stroke-linejoin: round;
	}
	.voyant-synchro {
		position: absolute;
		right: 1px;
		bottom: 1px;
		width: 11px;
		height: 11px;
		border: 2px solid var(--coque-fonce);
		border-radius: 50%;
		background: #9a9a9a;
	}
	.statut-pret .voyant-synchro {
		background: var(--voyant-vert);
	}
	.statut-en_cours .voyant-synchro {
		background: var(--voyant-jaune);
	}
	.statut-erreur .voyant-synchro {
		background: var(--voyant-rouge);
	}

	.onglets {
		display: flex;
		gap: 4px;
		padding: 10px 16px 0;
		background: var(--coque-fonce);
		overflow-x: auto;
		scrollbar-width: none;
	}
	.onglets a {
		flex: none;
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
