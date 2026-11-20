<script lang="ts">
	import { etat } from '$lib/etat.svelte';
	import type { Pokemon } from '$lib/types';

	let { pokemon }: { pokemon: Pokemon } = $props();

	let capture = $derived(etat.capture(pokemon.id));
	let formes = $derived(pokemon.formes?.filter((f) => f.type === 'forme') ?? []);
	let megas = $derived(pokemon.formes?.filter((f) => f.type === 'mega') ?? []);

	function basculer(id: string, valeur: boolean) {
		etat.modifierCapture(pokemon.id, { formes: { ...(capture?.formes ?? {}), [id]: valeur } });
	}
</script>

{#if formes.length}
	<h3>Formes</h3>
	<ul class="cases">
		{#each formes as f (f.id)}
			<li>
				<label>
					<input
						type="checkbox"
						checked={capture?.formes?.[f.id] ?? false}
						onchange={(e) => basculer(f.id, e.currentTarget.checked)}
					/>
					{f.nom}
				</label>
			</li>
		{/each}
	</ul>
{/if}

{#if megas.length}
	<h3>Méga-évolutions</h3>
	<p class="aide">À cocher quand tu as la Méga-Gemme correspondante.</p>
	<ul class="cases">
		{#each megas as f (f.id)}
			<li>
				<label>
					<input
						type="checkbox"
						checked={capture?.formes?.[f.id] ?? false}
						onchange={(e) => basculer(f.id, e.currentTarget.checked)}
					/>
					{f.nom}
				</label>
			</li>
		{/each}
	</ul>
{/if}

<style>
	h3 {
		margin: 8px 0 6px;
		font-size: 0.95rem;
	}
	.aide {
		margin: 0 0 6px;
		font-size: 0.85rem;
		color: var(--ecran-texte-doux);
	}
	.cases {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin: 0;
		padding: 0;
		list-style: none;
	}
	.cases label {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 4px 10px;
		border-radius: 999px;
		background: var(--ecran-alt);
		box-shadow: inset 0 0 0 1px var(--ecran-ligne);
		font-size: 0.9rem;
		cursor: pointer;
	}
</style>
