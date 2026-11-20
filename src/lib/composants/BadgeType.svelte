<script lang="ts">
	import { cleType } from '$lib/donnees';

	let { type }: { type: string } = $props();
</script>

<span class="type" style:--couleur-type="var(--type-{cleType(type)})">{type}</span>

<style>
	.type {
		display: inline-block;
		padding: 1px 8px;
		border-radius: 4px;
		background: var(--couleur-type, var(--type-normal));
		color: #fff;
		font-size: 0.7rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		text-shadow: 0 1px 1px rgb(0 0 0 / 0.45);
	}
</style>
