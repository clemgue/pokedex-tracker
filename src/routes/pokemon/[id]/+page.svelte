<script lang="ts">
	import { page } from '$app/state';
	import { analyserVersion, chaineEvolution } from '$lib/analyse';
	import BadgeType from '$lib/composants/BadgeType.svelte';
	import BoutonCapture from '$lib/composants/BoutonCapture.svelte';
	import Evolutions from '$lib/composants/Evolutions.svelte';
	import ListeObtentions from '$lib/composants/ListeObtentions.svelte';
	import PuceMethode from '$lib/composants/PuceMethode.svelte';
	import Variantes from '$lib/composants/Variantes.svelte';
	import { numero, sprite } from '$lib/donnees';
	import { etat } from '$lib/etat.svelte';

	let id = $derived(Number(page.params.id));
	let partie = $derived(etat.partieActive);
	let donnees = $derived(etat.donnees && partie && etat.donnees.jeu.id === partie.jeu ? etat.donnees : null);

	let fiches = $derived(donnees && partie ? analyserVersion(donnees, partie.version) : []);
	let index = $derived(fiches.findIndex((f) => f.pokemon.id === id));
	let fiche = $derived(index >= 0 ? fiches[index] : null);
	let precedente = $derived(index > 0 ? fiches[index - 1] : null);
	let suivante = $derived(index >= 0 && index < fiches.length - 1 ? fiches[index + 1] : null);

	let autresVersions = $derived(
		donnees && partie
			? donnees.jeu.versions
					.filter((v) => v.id !== partie.version)
					.map((v) => ({ version: v, fiche: analyserVersion(donnees, v.id).find((f) => f.pokemon.id === id) }))
			: []
	);
	let evolution = $derived(donnees ? chaineEvolution(donnees, id) : null);
	let capture = $derived(etat.capture(id));
	let gen = $derived(donnees?.jeu.generation ?? 1);

	let note = $state('');
	$effect(() => {
		note = etat.capture(id)?.note ?? '';
	});
	function enregistrerNote() {
		if ((capture?.note ?? '') !== note) etat.modifierCapture(id, { note });
	}
</script>

{#if !partie || !donnees}
	<p class="vide"><a href="#/">Choisis d'abord une partie.</a></p>
{:else if !fiche}
	<p class="vide">Ce Pokémon n'existe pas dans {donnees.jeu.nom}. <a href="#/">Retour au Pokédex</a></p>
{:else}
	<nav class="navigation" aria-label="Pokémon voisins">
		<a href="#/">← Pokédex</a>
		<span class="voisins">
			{#if precedente}<a href="#/pokemon/{precedente.pokemon.id}">‹ {precedente.pokemon.nom}</a>{/if}
			{#if suivante}<a href="#/pokemon/{suivante.pokemon.id}">{suivante.pokemon.nom} ›</a>{/if}
		</span>
	</nav>

	<header class="entete">
		<div class="visuel">
			<img class="artwork" src={fiche.pokemon.artwork} alt="Illustration de {fiche.pokemon.nom}" width="160" height="160" />
			<img
				class="sprite"
				src={sprite(fiche.pokemon, partie.version, capture?.shiny ?? false)}
				alt="Sprite de {fiche.pokemon.nom}"
				width="64"
				height="64"
			/>
		</div>
		<div class="identite">
			<span class="numero">{numero(fiche.numero)}</span>
			<h1>{fiche.pokemon.nom}</h1>
			<p class="en">{fiche.pokemon.nom_en}</p>
			<div class="types">
				{#each fiche.pokemon.types as t (t)}<BadgeType type={t} />{/each}
			</div>
			<div class="actions">
				<BoutonCapture
					attrape={capture?.attrape ?? false}
					nom={fiche.pokemon.nom}
					onclick={() => etat.basculerCapture(id)}
				/>
				<span>{capture?.attrape ? 'Attrapé' : 'Pas encore attrapé'}</span>
				{#if gen >= 2}
					<label class="shiny">
						<input
							type="checkbox"
							checked={capture?.shiny ?? false}
							onchange={(e) => etat.modifierCapture(id, { shiny: e.currentTarget.checked })}
						/>
						Chromatique obtenu
					</label>
				{/if}
			</div>
			{#if fiche.pokemon.url_pokepedia}
				<a class="pokepedia" href={fiche.pokemon.url_pokepedia} target="_blank" rel="noopener">Fiche Poképédia ↗</a>
			{/if}
		</div>
	</header>

	<section>
		<h2>
			Où le trouver
			<small>— {donnees.jeu.versions.find((v) => v.id === partie.version)?.nom}</small>
		</h2>
		<div class="puces">
			{#each fiche.puces as m (m)}<PuceMethode methode={m} titre={donnees.methodes[m]} />{/each}
		</div>
		<ListeObtentions parLieu={fiche.parLieu} sansLieu={fiche.sansLieu} {donnees} lienInterne />
	</section>

	{#if fiche.pokemon.formes?.length}
		<section>
			<h2>Formes et Méga-évolutions</h2>
			<Variantes pokemon={fiche.pokemon} />
		</section>
	{/if}

	{#if evolution}
		<section>
			<h2>Évolutions</h2>
			<div class="evolutions">
				<Evolutions noeud={evolution} version={partie.version} actuel={id} attrape={(p) => etat.estAttrape(p)} />
			</div>
		</section>
	{/if}

	{#if autresVersions.length}
		<section>
			<h2>Dans les autres versions</h2>
			<ul class="versions">
				{#each autresVersions as { version: v, fiche: f } (v.id)}
					<li style:--couleur={v.couleur}>
						<strong>{v.nom}</strong>
						{#if f}
							<span class="puces">
								{#each f.puces as m (m)}<PuceMethode methode={m} />{/each}
							</span>
							<span>{f.resume}</span>
						{/if}
					</li>
				{/each}
			</ul>
		</section>
	{/if}

	<section>
		<h2><label for="note">Note personnelle</label></h2>
		<textarea
			id="note"
			class="champ note"
			rows="3"
			maxlength="500"
			placeholder="Ex. : à échanger avec Léo, niveau 30 dans la boîte 2…"
			bind:value={note}
			onblur={enregistrerNote}
		></textarea>
	</section>
{/if}

<style>
	.vide {
		padding: 32px 0;
		text-align: center;
	}
	.navigation {
		display: flex;
		flex-wrap: wrap;
		justify-content: space-between;
		gap: 8px;
		margin-bottom: 12px;
		font-size: 0.9rem;
	}
	.navigation a {
		text-decoration: none;
		font-weight: 600;
	}
	.navigation a:hover {
		text-decoration: underline;
	}
	.voisins {
		display: flex;
		gap: 16px;
	}

	.entete {
		display: flex;
		flex-wrap: wrap;
		gap: 16px 24px;
		align-items: center;
		margin-bottom: 20px;
	}
	.visuel {
		position: relative;
		width: 160px;
		height: 160px;
		border-radius: 50%;
		background: radial-gradient(circle, var(--ecran-alt), var(--ecran-ligne));
	}
	.artwork {
		width: 160px;
		height: 160px;
		object-fit: contain;
	}
	.sprite {
		position: absolute;
		right: -10px;
		bottom: -6px;
		padding: 2px;
		border-radius: 8px;
		background: var(--ecran);
		box-shadow: 0 0 0 2px var(--ecran-ligne);
		image-rendering: pixelated;
	}
	.identite {
		display: grid;
		gap: 6px;
		min-width: 0;
	}
	.numero {
		font-family: var(--police-ecran);
		color: var(--ecran-texte-doux);
	}
	h1 {
		margin: 0;
		font-size: 2rem;
		line-height: 1.1;
	}
	.en {
		margin: 0;
		color: var(--ecran-texte-doux);
		font-style: italic;
	}
	.types {
		display: flex;
		gap: 6px;
	}
	.actions {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 4px 12px;
		font-weight: 600;
	}
	.shiny {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-weight: 500;
	}
	.pokepedia {
		font-size: 0.9rem;
	}

	section {
		margin-bottom: 20px;
	}
	h2 {
		margin: 0 0 8px;
		font-size: 1.1rem;
	}
	h2 small {
		font-weight: 500;
		color: var(--ecran-texte-doux);
	}
	.puces {
		display: inline-flex;
		flex-wrap: wrap;
		gap: 4px;
	}
	.evolutions {
		overflow-x: auto;
		padding-bottom: 4px;
	}
	.versions {
		display: grid;
		gap: 6px;
		margin: 0;
		padding: 0;
		list-style: none;
		font-size: 0.9rem;
	}
	.versions li {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 6px 10px;
		padding: 6px 10px;
		border-left: 5px solid var(--couleur);
		border-radius: 6px;
		background: var(--ecran-alt);
	}
	.note {
		min-height: 80px;
		padding: 8px 12px;
		resize: vertical;
	}
</style>
