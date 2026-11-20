<script lang="ts">
	import { onMount } from 'svelte';

	type Theme = 'clair' | 'sombre';
	let theme = $state<Theme>('clair');

	function themeSysteme(): Theme {
		return matchMedia('(prefers-color-scheme: dark)').matches ? 'sombre' : 'clair';
	}

	onMount(() => {
		const choisi = document.documentElement.dataset.theme;
		theme = choisi === 'clair' || choisi === 'sombre' ? choisi : themeSysteme();
	});

	function basculer() {
		theme = theme === 'sombre' ? 'clair' : 'sombre';
		document.documentElement.dataset.theme = theme;
		try {
			localStorage.setItem('theme', theme);
		} catch {
			// Stockage indisponible (navigation privée) : le choix vaut pour la session
		}
	}
</script>

<button
	class="bascule"
	type="button"
	onclick={basculer}
	aria-label={theme === 'sombre' ? 'Passer au thème clair' : 'Passer au thème sombre'}
	title={theme === 'sombre' ? 'Thème clair' : 'Thème sombre'}
>
	{#if theme === 'sombre'}
		<svg viewBox="0 0 24 24" aria-hidden="true"
			><circle cx="12" cy="12" r="4.5" /><path
				d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"
			/></svg
		>
	{:else}
		<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" /></svg>
	{/if}
</button>

<style>
	.bascule {
		display: grid;
		place-items: center;
		width: 40px;
		height: 40px;
		padding: 0;
		border: 2px solid rgb(0 0 0 / 0.25);
		border-radius: 50%;
		background: var(--coque-fonce);
		color: var(--coque-texte);
		cursor: pointer;
		box-shadow: inset 0 2px 0 rgb(255 255 255 / 0.15);
	}
	.bascule:hover {
		background: var(--coque-clair);
	}
	svg {
		width: 20px;
		height: 20px;
		fill: none;
		stroke: currentColor;
		stroke-width: 2;
		stroke-linecap: round;
		stroke-linejoin: round;
	}
	path:only-child {
		fill: currentColor;
		stroke: none;
	}
</style>
