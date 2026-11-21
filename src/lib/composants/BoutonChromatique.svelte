<script lang="ts">
	let { actif, nom, onclick }: { actif: boolean; nom: string; onclick: () => void } = $props();
</script>

<button
	type="button"
	class="chroma"
	class:actif
	aria-pressed={actif}
	aria-label={actif ? `${nom} : chromatique obtenu (cliquer pour annuler)` : `Marquer ${nom} chromatique comme obtenu`}
	title={actif ? 'Chromatique obtenu' : 'Chromatique pas encore obtenu'}
	{onclick}
>
	<!-- Étincelles à quatre branches, comme l'icône des chromatiques dans les jeux -->
	<svg viewBox="0 0 32 32" aria-hidden="true">
		<path d="M12 4 14.2 11.8 22 14 14.2 16.2 12 24 9.8 16.2 2 14 9.8 11.8Z" />
		<path d="M24 3 25.1 6.9 29 8 25.1 9.1 24 13 22.9 9.1 19 8 22.9 6.9Z" />
		<path d="M23 19 24.3 22.7 28 24 24.3 25.3 23 29 21.7 25.3 18 24 21.7 22.7Z" />
	</svg>
</button>

<style>
	.chroma {
		display: grid;
		place-items: center;
		width: 44px;
		height: 44px;
		flex: none;
		padding: 0;
		border: 0;
		border-radius: 50%;
		background: transparent;
		cursor: pointer;
	}
	svg {
		width: 28px;
		height: 28px;
		transition: transform 0.15s ease;
	}
	.chroma:hover svg {
		transform: scale(1.12);
	}
	.chroma:active svg {
		transform: scale(0.9);
	}
	path {
		fill: transparent;
		stroke: var(--ecran-texte-doux);
		stroke-width: 1.6;
		stroke-linejoin: round;
	}
	.chroma:not(.actif) {
		opacity: 0.55;
	}
	.actif path {
		fill: var(--voyant-jaune);
		stroke: #6b5300;
	}
</style>
