<script lang="ts">
	import { etat } from '$lib/etat.svelte';

	let { apresCreation }: { apresCreation?: () => void } = $props();

	let jeuId = $state(etat.jeux[0]?.id ?? '');
	let jeu = $derived(etat.jeux.find((j) => j.id === jeuId));
	let versionId = $state(etat.jeux[0]?.versions[0]?.id ?? '');
	let nom = $state('');
	let enCours = $state(false);

	$effect(() => {
		// Version par défaut quand on change de jeu
		if (jeu && !jeu.versions.some((v) => v.id === versionId)) versionId = jeu.versions[0].id;
	});

	let nomParDefaut = $derived(
		`Ma partie ${jeu?.versions.find((v) => v.id === versionId)?.nom ?? ''}`.trim()
	);

	async function creer(e: SubmitEvent) {
		e.preventDefault();
		if (!jeu || enCours) return;
		enCours = true;
		await etat.creerPartie(nom || nomParDefaut, jeu.id, versionId);
		nom = '';
		enCours = false;
		apresCreation?.();
	}
</script>

<form class="nouvelle" onsubmit={creer}>
	<div>
		<label class="etiquette" for="np-jeu">Jeu</label>
		<select id="np-jeu" class="champ" bind:value={jeuId}>
			{#each etat.jeux as j (j.id)}
				<option value={j.id}>{j.nom}</option>
			{/each}
		</select>
	</div>

	{#if jeu}
		<fieldset>
			<legend class="etiquette">Version</legend>
			<div class="versions">
				{#each jeu.versions as v (v.id)}
					<label class="version" style:--couleur={v.couleur}>
						<input type="radio" name="np-version" value={v.id} bind:group={versionId} />
						<span>{v.nom}</span>
					</label>
				{/each}
			</div>
		</fieldset>
	{/if}

	<div>
		<label class="etiquette" for="np-nom">Nom de la partie</label>
		<input id="np-nom" class="champ" bind:value={nom} placeholder={nomParDefaut} maxlength="60" />
	</div>

	<button class="bouton" type="submit" disabled={enCours}>Créer la partie</button>
</form>

<style>
	.nouvelle {
		display: grid;
		gap: 14px;
		max-width: 460px;
	}
	fieldset {
		margin: 0;
		padding: 0;
		border: 0;
	}
	.versions {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}
	.version {
		position: relative;
		cursor: pointer;
	}
	.version input {
		position: absolute;
		opacity: 0;
	}
	.version span {
		display: inline-block;
		padding: 8px 16px;
		border-radius: 999px;
		border: 2px solid var(--couleur);
		font-weight: 700;
	}
	.version input:checked + span {
		background: var(--couleur);
		color: #fff;
		text-shadow: 0 1px 2px rgb(0 0 0 / 0.5);
	}
	.version input:focus-visible + span {
		outline: 3px solid var(--lentille);
		outline-offset: 2px;
	}
	button {
		justify-self: start;
	}
</style>
