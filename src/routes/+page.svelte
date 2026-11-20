<script lang="ts">
	import { analyserVersion, methodesPresentes, type FichePokedex } from '$lib/analyse';
	import BadgeType from '$lib/composants/BadgeType.svelte';
	import ListeObtentions from '$lib/composants/ListeObtentions.svelte';
	import PuceMethode from '$lib/composants/PuceMethode.svelte';
	import BoutonCapture from '$lib/composants/BoutonCapture.svelte';
	import NouvellePartie from '$lib/composants/NouvellePartie.svelte';
	import { normaliser, numero , sprite } from '$lib/donnees';
	import { etat } from '$lib/etat.svelte';
	import { filtres as F, reinitialiserFiltres, type Statut } from '$lib/filtres.svelte';

	let partie = $derived(etat.partieActive);

	$effect.pre(() => {
		// Nouvelle partie active : filtres remis à zéro
		if (partie && F.partie !== partie.id) reinitialiserFiltres(partie.id);
	});
	let donnees = $derived(etat.donnees);
	let version = $derived(donnees?.jeu.versions.find((v) => v.id === partie?.version));

	let fiches = $derived(
		donnees && partie && donnees.jeu.id === partie.jeu
			? analyserVersion(donnees, partie.version, F.pokedexId || undefined)
			: []
	);

	let lieuxVersion = $derived(
		donnees && partie ? donnees.lieux.filter((l) => l.versions.includes(partie.version)) : []
	);
	let methodes = $derived(donnees ? methodesPresentes(fiches, donnees) : []);
	let types = $derived([...new Set(fiches.flatMap((f) => f.pokemon.types))].sort((a, b) => a.localeCompare(b, 'fr')));

	let nbAttrapes = $derived(fiches.filter((f) => etat.estAttrape(f.pokemon.id)).length);
	let pourcentage = $derived(fiches.length ? Math.round((nbAttrapes / fiches.length) * 100) : 0);

	function correspond(f: FichePokedex): boolean {
		const attrape = etat.estAttrape(f.pokemon.id);
		if (F.statut === 'attrapes' && !attrape) return false;
		if (F.statut === 'manquants' && attrape) return false;
		if (F.methode && !f.methodes.has(F.methode)) return false;
		if (F.lieu && !f.lieux.has(F.lieu)) return false;
		if (F.type && !f.pokemon.types.includes(F.type)) return false;
		if (F.special === 'exclusifs' && !f.exclusif) return false;
		if (F.special === 'echange' && !f.parEchange) return false;
		const q = normaliser(F.recherche);
		if (q) {
			const n = String(f.numero);
			const textes = [normaliser(f.pokemon.nom), normaliser(f.pokemon.nom_en)];
			if (!(/^\d+$/.test(q) ? n === String(Number(q)) || n.startsWith(q) : textes.some((t) => t.includes(q))))
				return false;
		}
		return true;
	}

	let visibles = $derived.by(() => {
		const liste = fiches.filter(correspond);
		if (F.tri === 'nom') liste.sort((a, b) => a.pokemon.nom.localeCompare(b.pokemon.nom, 'fr'));
		return liste;
	});

	let nbFiltres = $derived([F.statut !== 'tous', F.methode, F.lieu, F.type, F.special].filter(Boolean).length);

	function reinitialiser() {
		const { tri, pokedexId } = F;
		reinitialiserFiltres();
		Object.assign(F, { tri, pokedexId });
	}

	const statuts: { id: Statut; libelle: string }[] = [
		{ id: 'tous', libelle: 'Tous' },
		{ id: 'manquants', libelle: 'Manquants' },
		{ id: 'attrapes', libelle: 'Attrapés' }
	];
</script>

{#if !partie}
	<section class="accueil">
		<h1>Bienvenue !</h1>
		<p>Crée une partie pour commencer à suivre tes captures. Ta progression est enregistrée sur cet appareil.</p>
		<NouvellePartie />
	</section>
{:else if !donnees || etat.chargementJeu}
	<p class="vide">Chargement du jeu…</p>
{:else}
	<section class="progression" aria-label="Progression" style:--couleur-version={version?.couleur}>
		<div class="ligne">
			<span class="version">{donnees.jeu.nom} — {version?.nom}</span>
			<span class="compte"><strong>{nbAttrapes}</strong> / {fiches.length} · {pourcentage} %</span>
		</div>
		<div class="barre" role="progressbar" aria-valuemin="0" aria-valuemax={fiches.length} aria-valuenow={nbAttrapes}>
			<span style:width="{pourcentage}%"></span>
		</div>
	</section>

	<section class="outils" aria-label="Recherche et filtres">
		<div class="recherche">
			<label class="sr-only" for="recherche">Rechercher un Pokémon</label>
			<input
				id="recherche"
				class="champ"
				type="search"
				placeholder="Nom (FR ou EN) ou numéro…"
				bind:value={F.recherche}
				autocomplete="off"
			/>
		</div>

		<div class="statuts" role="radiogroup" aria-label="Statut">
			{#each statuts as s (s.id)}
				<button
					type="button"
					role="radio"
					aria-checked={F.statut === s.id}
					class:actif={F.statut === s.id}
					onclick={() => (F.statut = s.id)}>{s.libelle}</button
				>
			{/each}
		</div>

		<details class="filtres">
			<summary>Filtres{nbFiltres ? ` (${nbFiltres})` : ''}</summary>
			<div class="grille">
				{#if donnees.pokedex.length > 1}
					<div>
						<label class="etiquette" for="f-pokedex">Pokédex</label>
						<select id="f-pokedex" class="champ" bind:value={F.pokedexId}>
							{#each donnees.pokedex as p, i (p.id)}
								<option value={i === 0 ? '' : p.id}>{p.nom}</option>
							{/each}
						</select>
					</div>
				{/if}
				<div>
					<label class="etiquette" for="f-methode">Méthode</label>
					<select id="f-methode" class="champ" bind:value={F.methode}>
						<option value="">Toutes</option>
						{#each methodes as m (m.id)}
							<option value={m.id}>{m.nom}</option>
						{/each}
					</select>
				</div>
				<div>
					<label class="etiquette" for="f-lieu">Lieu</label>
					<select id="f-lieu" class="champ" bind:value={F.lieu}>
						<option value="">Tous</option>
						{#each lieuxVersion as l (l.id)}
							<option value={l.id}>{l.nom}</option>
						{/each}
					</select>
				</div>
				<div>
					<label class="etiquette" for="f-type">Type</label>
					<select id="f-type" class="champ" bind:value={F.type}>
						<option value="">Tous</option>
						{#each types as t (t)}
							<option value={t}>{t}</option>
						{/each}
					</select>
				</div>
				<div>
					<label class="etiquette" for="f-special">Exclusivités</label>
					<select id="f-special" class="champ" bind:value={F.special}>
						<option value="">Toutes</option>
						<option value="exclusifs">Exclusifs de ma version</option>
						<option value="echange">À obtenir par échange</option>
					</select>
				</div>
				<div>
					<label class="etiquette" for="f-tri">Tri</label>
					<select id="f-tri" class="champ" bind:value={F.tri}>
						<option value="numero">Numéro</option>
						<option value="nom">Nom</option>
					</select>
				</div>
			</div>
		</details>
	</section>

	<p class="resultats" aria-live="polite">
		{visibles.length} Pokémon
		{#if visibles.length !== fiches.length || F.recherche}
			<button type="button" class="lien" onclick={reinitialiser}>Réinitialiser</button>
		{/if}
	</p>

	{#if visibles.length}
		<ol class="liste">
			{#each visibles as f (f.pokemon.id)}
				{@const attrape = etat.estAttrape(f.pokemon.id)}
				<li class:attrape>
					<span class="numero">{numero(f.numero)}</span>
					<img
						class="sprite"
						src={sprite(f.pokemon, partie.version)}
						alt=""
						width="56"
						height="56"
						loading="lazy"
					/>
					<div class="infos">
						<div class="nom">
							<a class="lien-fiche" href="#/pokemon/{f.pokemon.id}">{f.pokemon.nom}</a>
							{#each f.pokemon.types as t (t)}
								<BadgeType type={t} />
							{/each}
							{#if f.exclusif}
								<span class="etiquette-ex" title="Absent d'au moins une autre version">Exclusif</span>
							{/if}
						</div>
						{#if f.parLieu.length}
							<details class="obtention">
								<summary>
									<span class="puces">
										{#each f.puces as m (m)}
											<PuceMethode methode={m} titre={donnees.methodes[m]} />
										{/each}
									</span>
									<span class="resume">{f.resume}</span>
									<svg class="chevron" viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6" /></svg>
								</summary>
								<ListeObtentions parLieu={f.parLieu} sansLieu={f.sansLieu} {donnees} />
							</details>
						{:else}
							<div class="obtention simple" class:echange={f.parEchange}>
								<span class="puces">
									{#each f.puces as m (m)}
										<PuceMethode methode={m} titre={donnees.methodes[m]} />
									{/each}
								</span>
								<span class="resume">{f.resume}</span>
							</div>
						{/if}
					</div>
					{#if f.pokemon.url_pokepedia}
						<a
							class="pokepedia"
							href={f.pokemon.url_pokepedia}
							target="_blank"
							rel="noopener"
							title="Fiche Poképédia"
							aria-label="Fiche Poképédia de {f.pokemon.nom}"
						>
							<svg viewBox="0 0 24 24" aria-hidden="true"
								><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" /></svg
							>
						</a>
					{/if}
					<BoutonCapture {attrape} nom={f.pokemon.nom} onclick={() => etat.basculerCapture(f.pokemon.id)} />
				</li>
			{/each}
		</ol>
	{:else}
		<p class="vide">Aucun Pokémon ne correspond à ces critères.</p>
	{/if}
{/if}

<style>
	h1 {
		margin: 0 0 8px;
	}
	.accueil p {
		margin: 0 0 20px;
		color: var(--ecran-texte-doux);
	}

	.progression {
		margin-bottom: 14px;
	}
	.ligne {
		display: flex;
		flex-wrap: wrap;
		justify-content: space-between;
		gap: 4px 12px;
		margin-bottom: 6px;
		font-size: 0.9rem;
	}
	.version {
		font-weight: 700;
	}
	.compte {
		font-family: var(--police-ecran);
	}
	.barre {
		height: 12px;
		border-radius: 999px;
		background: var(--ecran-ligne);
		overflow: hidden;
	}
	.barre span {
		display: block;
		height: 100%;
		background: var(--progression);
		transition: width 0.3s ease;
	}

	.outils {
		display: grid;
		gap: 10px;
		margin-bottom: 8px;
	}
	.statuts {
		display: inline-flex;
		justify-self: start;
		padding: 3px;
		border-radius: 999px;
		background: var(--ecran-alt);
		box-shadow: inset 0 0 0 2px var(--ecran-ligne);
	}
	.statuts button {
		min-height: 34px;
		padding: 0 14px;
		border: 0;
		border-radius: 999px;
		background: transparent;
		font-weight: 600;
		cursor: pointer;
	}
	.statuts button.actif {
		background: var(--bouton);
		color: var(--bouton-texte);
	}

	.filtres summary {
		cursor: pointer;
		font-weight: 600;
		padding: 4px 0;
	}
	.grille {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 10px;
		padding-top: 8px;
	}

	.resultats {
		margin: 8px 0;
		font-size: 0.85rem;
		color: var(--ecran-texte-doux);
	}
	.lien {
		margin-left: 8px;
		padding: 0;
		border: 0;
		background: none;
		text-decoration: underline;
		cursor: pointer;
	}

	.liste {
		margin: 0;
		padding: 0;
		list-style: none;
	}
	.liste > li {
		display: grid;
		grid-template-columns: 3.4rem 56px 1fr auto auto;
		align-items: start;
		gap: 10px;
		padding: 4px 6px;
		border-bottom: 1px solid var(--ecran-ligne);
	}
	.liste > li:hover {
		background: var(--ecran-survol);
	}
	.liste > li > :global(*) {
		align-self: start;
	}
	.liste > li > :global(button) {
		margin-top: 6px;
	}
	.infos {
		padding-top: 6px;
	}
	.numero {
		font-family: var(--police-ecran);
		font-size: 0.85rem;
		line-height: 56px;
		color: var(--ecran-texte-doux);
	}
	.sprite {
		width: 56px;
		height: 56px;
		image-rendering: pixelated;
	}
	.infos {
		min-width: 0;
	}
	.nom {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 4px 6px;
		font-weight: 700;
	}
	.obtention {
		margin-top: 3px;
		font-size: 0.8rem;
		color: var(--ecran-texte-doux);
	}
	.obtention summary,
	.obtention.simple {
		display: flex;
		align-items: center;
		gap: 6px;
		min-width: 0;
	}
	.obtention summary {
		width: fit-content;
		max-width: 100%;
		padding: 2px 6px 2px 0;
		border-radius: 6px;
		cursor: pointer;
		list-style: none;
	}
	.obtention summary::-webkit-details-marker {
		display: none;
	}
	.obtention summary:hover .resume {
		color: var(--ecran-texte);
		text-decoration: underline;
	}
	.puces {
		display: inline-flex;
		flex-wrap: wrap;
		gap: 3px;
		flex: none;
	}
	.resume {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.obtention.echange .resume {
		color: var(--alerte);
	}
	.chevron {
		width: 16px;
		height: 16px;
		flex: none;
		fill: none;
		stroke: currentColor;
		stroke-width: 2.5;
		transition: transform 0.15s ease;
	}
	.obtention[open] .chevron {
		transform: rotate(180deg);
	}
	.lien-fiche {
		text-decoration: none;
	}
	.lien-fiche:hover {
		text-decoration: underline;
	}
	.etiquette-ex {
		padding: 0 6px;
		border-radius: 4px;
		border: 1px solid var(--couleur-version, var(--ecran-texte-doux));
		font-size: 0.65rem;
		font-weight: 700;
		text-transform: uppercase;
	}
	.attrape .lien-fiche {
		color: var(--attrape);
	}
	.pokepedia {
		margin-top: 10px;
		display: grid;
		place-items: center;
		width: 36px;
		height: 36px;
		border-radius: 50%;
		color: var(--ecran-texte-doux);
	}
	.pokepedia:hover {
		background: var(--ecran-alt);
		color: var(--ecran-texte);
	}
	.pokepedia svg {
		width: 18px;
		height: 18px;
		fill: none;
		stroke: currentColor;
		stroke-width: 2;
		stroke-linecap: round;
		stroke-linejoin: round;
	}

	.vide {
		padding: 32px 0;
		text-align: center;
		color: var(--ecran-texte-doux);
	}

	@media (max-width: 600px) {
		.liste > li {
			grid-template-columns: 2.6rem 44px 1fr auto;
			gap: 6px;
			padding: 4px 0;
		}
		.liste > li > :global(button) {
			margin-top: 0;
		}
		.infos {
			padding-top: 2px;
		}
		.numero {
			font-size: 0.75rem;
			line-height: 44px;
		}
		.sprite {
			width: 44px;
			height: 44px;
		}
		.pokepedia {
			display: none;
		}
	}
</style>
