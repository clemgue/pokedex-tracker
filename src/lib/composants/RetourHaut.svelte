<script lang="ts">
	/** Bouton flottant « retour en haut », visible après un défilement d'environ un écran. */
	let visible = $state(false);

	function surDefilement() {
		visible = window.scrollY > window.innerHeight * 0.8;
	}

	function remonter() {
		const reduit = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
		window.scrollTo({ top: 0, behavior: reduit ? 'auto' : 'smooth' });
	}
</script>

<svelte:window onscroll={surDefilement} />

<button type="button" class="haut" class:visible onclick={remonter} aria-label="Retour en haut de la page" title="Retour en haut">
	<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 15 6-6 6 6" /></svg>
</button>

<style>
	.haut {
		position: fixed;
		right: max(16px, env(safe-area-inset-right));
		bottom: max(20px, env(safe-area-inset-bottom));
		z-index: 20;
		display: grid;
		place-items: center;
		width: 52px;
		height: 52px;
		padding: 0;
		border: 3px solid var(--coque-fonce);
		border-radius: 50%;
		background: var(--coque);
		color: var(--coque-texte);
		box-shadow: 0 4px 12px rgb(0 0 0 / 0.35);
		cursor: pointer;
		opacity: 0;
		transform: translateY(16px);
		pointer-events: none;
		transition:
			opacity 0.2s ease,
			transform 0.2s ease;
	}
	.haut.visible {
		opacity: 1;
		transform: none;
		pointer-events: auto;
	}
	.haut:hover {
		background: var(--coque-clair);
	}
	svg {
		width: 28px;
		height: 28px;
		fill: none;
		stroke: currentColor;
		stroke-width: 3;
		stroke-linecap: round;
		stroke-linejoin: round;
	}
</style>
