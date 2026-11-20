<script lang="ts">
	let { attrape, nom, onclick }: { attrape: boolean; nom: string; onclick: () => void } = $props();
</script>

<button
	type="button"
	class="ball"
	class:attrape
	aria-pressed={attrape}
	aria-label={attrape ? `${nom} : attrapé (cliquer pour annuler)` : `Marquer ${nom} comme attrapé`}
	title={attrape ? 'Attrapé' : 'Pas encore attrapé'}
	{onclick}
>
	<svg viewBox="0 0 32 32" aria-hidden="true">
		<circle class="bas" cx="16" cy="16" r="13" />
		<path class="haut" d="M3 16a13 13 0 0 1 26 0z" />
		<path class="trait" d="M3 16h26" />
		<circle class="centre" cx="16" cy="16" r="4.2" />
	</svg>
</button>

<style>
	.ball {
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
		width: 32px;
		height: 32px;
		transition: transform 0.15s ease;
	}
	.ball:hover svg {
		transform: rotate(-12deg);
	}
	.ball:active svg {
		transform: scale(0.9);
	}
	circle,
	path {
		stroke: var(--ecran-texte-doux);
		stroke-width: 2;
	}
	.bas,
	.haut {
		fill: transparent;
	}
	.centre {
		fill: var(--ecran);
	}
	.ball:not(.attrape) {
		opacity: 0.55;
	}
	.attrape circle,
	.attrape path {
		stroke: #1d1d1d;
	}
	.attrape .haut {
		fill: var(--attrape);
	}
	.attrape .bas,
	.attrape .centre {
		fill: #fff;
	}
</style>
