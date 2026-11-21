<script lang="ts">
	import { vignettes, type Avancement } from '$lib/aventure';

	let { av }: { av: Avancement } = $props();
</script>

<span class="statuts">
	{#each vignettes(av) as v (v.libelle)}
		<span class="statut {v.classe}">{v.libelle}</span>
	{/each}
</span>

<style>
	.statuts {
		display: inline-flex;
		flex-wrap: wrap;
		gap: 4px;
	}
	.statut {
		padding: 1px 10px;
		border-radius: 999px;
		border: 1px solid currentColor;
		font-size: 0.75rem;
		font-weight: 700;
		white-space: nowrap;
		color: var(--ecran-texte-doux);
	}
	.en-cours {
		color: var(--lentille);
	}
	.termine {
		background: var(--progression);
		border-color: var(--progression);
		color: #fff;
	}
</style>
