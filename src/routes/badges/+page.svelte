<script lang="ts">
	import { avancement, cleEtape, etapesVersion, LIBELLES_STATUT } from '$lib/aventure';
	import BadgeType from '$lib/composants/BadgeType.svelte';
	import { cleType } from '$lib/donnees';
	import { etat } from '$lib/etat.svelte';

	let partie = $derived(etat.partieActive);
	let jeu = $derived(etat.jeux.find((j) => j.id === partie?.jeu));
	let version = $derived(jeu?.versions.find((v) => v.id === partie?.version));
	let groupes = $derived(partie ? etapesVersion(etat.progression, partie.jeu, partie.version) : []);
	let av = $derived(partie ? avancement(partie, jeu, etat.progression) : null);
	let final = $derived(partie ? etat.progression?.jeux[partie.jeu]?.final : undefined);
</script>

{#if !partie}
	<p class="vide"><a href="#/">Choisis d'abord une partie.</a></p>
{:else if !etat.progression}
	<p class="vide">Chargement…</p>
{:else if !groupes.length}
	<p class="vide">Aucune étape n'est encore répertoriée pour ce jeu.</p>
{:else}
	<h1>Badges et Ligue</h1>
	<p class="intro" style:--couleur-version={version?.couleur}>
		{jeu?.nom} — {version?.nom} ·
		<strong>{av?.etapesFaites} / {av?.etapesTotal}</strong> étapes ·
		<span class="statut">{av ? LIBELLES_STATUT[av.statut] : ''}</span>
	</p>

	{#each groupes as g (g.id)}
		{@const faits = g.etapes.filter((e) => etat.estFaite(cleEtape(g.id, e.id))).length}
		<section class="groupe">
			<h2>
				{g.titre}
				<span class="compte" class:complet={faits === g.etapes.length}>{faits} / {g.etapes.length}</span>
			</h2>
			<ol class="etapes">
				{#each g.etapes as e, i (e.id + i)}
					{@const cle = cleEtape(g.id, e.id)}
					{@const fait = etat.estFaite(cle)}
					<li class:fait class:final={cle === final}>
						<button
							type="button"
							class="medaille"
							style:--couleur-type={e.type ? `var(--type-${cleType(e.type)})` : undefined}
							aria-pressed={fait}
							aria-label="{e.nom}{e.personne ? ` — ${e.personne}` : ''} : {fait ? 'obtenu (cliquer pour annuler)' : 'pas encore obtenu'}"
							title={fait ? 'Obtenu' : 'Pas encore obtenu'}
							onclick={() => etat.basculerEtape(cle)}
						>
							{#if fait}
								<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12.5 4.5 4.5L19 7.5" /></svg>
							{:else}
								<span aria-hidden="true">{i + 1}</span>
							{/if}
						</button>
						<div class="texte">
							<div class="ligne1">
								{#if e.personne}
									{#if e.url_personne}
										<a href={e.url_personne} target="_blank" rel="noopener" class="personne">{e.personne}</a>
									{:else}
										<span class="personne">{e.personne}</span>
									{/if}
								{:else if e.url_personne}
									<a href={e.url_personne} target="_blank" rel="noopener" class="personne">{e.nom}</a>
								{:else}
									<span class="personne">{e.nom}</span>
								{/if}
								{#if e.type}<BadgeType type={e.type} />{/if}
							</div>
							<div class="ligne2">
								{#if e.personne}<span>{e.nom}</span>{/if}
								{#if e.lieu}
									<span
										>{#if e.url_lieu}<a href={e.url_lieu} target="_blank" rel="noopener">{e.lieu}</a>{:else}{e.lieu}{/if}</span
									>
								{/if}
								{#if e.note}<span class="note">{e.note}</span>{/if}
							</div>
						</div>
					</li>
				{/each}
			</ol>
		</section>
	{/each}
{/if}

<style>
	h1 {
		margin: 0 0 4px;
	}
	.intro {
		margin: 0 0 16px;
		font-size: 0.9rem;
		color: var(--ecran-texte-doux);
	}
	.intro strong {
		color: var(--ecran-texte);
	}
	.groupe + .groupe {
		margin-top: 22px;
	}
	h2 {
		display: flex;
		align-items: baseline;
		gap: 10px;
		margin: 0 0 8px;
		font-size: 1.05rem;
	}
	.compte {
		font-family: var(--police-ecran);
		font-size: 0.85rem;
		font-weight: 400;
		color: var(--ecran-texte-doux);
	}
	.compte.complet {
		color: var(--progression);
		font-weight: 700;
	}
	.etapes {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
		gap: 8px;
		margin: 0;
		padding: 0;
		list-style: none;
	}
	li {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 8px 10px;
		border-radius: 10px;
		background: var(--ecran-alt);
		box-shadow: inset 0 0 0 1px var(--ecran-ligne);
	}
	li.final {
		box-shadow: inset 0 0 0 2px var(--voyant-jaune);
	}
	.medaille {
		display: grid;
		place-items: center;
		flex: none;
		width: 44px;
		height: 44px;
		padding: 0;
		border: 3px solid var(--couleur-type, var(--ecran-texte-doux));
		border-radius: 50%;
		background: transparent;
		color: var(--ecran-texte-doux);
		font-family: var(--police-ecran);
		font-weight: 700;
		cursor: pointer;
		transition: transform 0.15s ease;
	}
	.medaille:hover {
		transform: scale(1.08);
	}
	.medaille:active {
		transform: scale(0.92);
	}
	.fait .medaille {
		background: radial-gradient(circle at 35% 30%, #fff8, transparent 45%),
			var(--couleur-type, var(--progression));
		color: #fff;
		box-shadow: 0 0 0 2px rgb(0 0 0 / 0.15);
	}
	.medaille svg {
		width: 24px;
		height: 24px;
		fill: none;
		stroke: currentColor;
		stroke-width: 3;
		stroke-linecap: round;
		stroke-linejoin: round;
		filter: drop-shadow(0 1px 1px rgb(0 0 0 / 0.5));
	}
	.texte {
		min-width: 0;
	}
	.ligne1 {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 4px 8px;
	}
	.personne {
		font-weight: 700;
		text-decoration: none;
	}
	a.personne:hover {
		text-decoration: underline;
	}
	.ligne2 {
		display: flex;
		flex-wrap: wrap;
		gap: 0 6px;
		font-size: 0.8rem;
		color: var(--ecran-texte-doux);
	}
	.ligne2 > span + span::before {
		content: '·';
		margin-right: 6px;
	}
	.ligne2 a {
		color: inherit;
	}
	.note {
		font-style: italic;
	}
	.fait .personne {
		color: var(--attrape);
	}
	.vide {
		padding: 32px 0;
		text-align: center;
		color: var(--ecran-texte-doux);
	}
</style>
