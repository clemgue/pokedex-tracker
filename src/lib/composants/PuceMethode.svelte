<script lang="ts">
	import { INFOS_METHODES } from '$lib/analyse';
	import type { Methode } from '$lib/types';

	let { methode, titre }: { methode: Methode; titre?: string } = $props();
	let infos = $derived(INFOS_METHODES[methode]);
</script>

<span class="puce {infos.famille}" title={titre}>{infos.court}</span>

<style>
	.puce {
		display: inline-block;
		padding: 0 7px;
		border-radius: 999px;
		border: 1.5px solid var(--c);
		background: color-mix(in srgb, var(--c) 14%, transparent);
		color: var(--ecran-texte);
		font-size: 0.7rem;
		font-weight: 700;
		line-height: 1.5;
		white-space: nowrap;
	}
	.sauvage {
		--c: var(--famille-sauvage);
	}
	.cadeau {
		--c: var(--famille-cadeau);
	}
	.evolution {
		--c: var(--famille-evolution);
	}
	.echange {
		--c: var(--famille-echange);
	}
</style>
