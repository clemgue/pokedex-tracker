<script lang="ts">
	import { sprite } from '$lib/donnees';
	import { analyserVersion, INFOS_METHODES, type FichePokedex } from '$lib/analyse';
	import PuceMethode from '$lib/composants/PuceMethode.svelte';
	import StatutPartie from '$lib/composants/StatutPartie.svelte';
	import { avancement } from '$lib/aventure';
	import { etat } from '$lib/etat.svelte';
	import type { Methode } from '$lib/types';

	let partie = $derived(etat.partieActive);
	let donnees = $derived(etat.donnees && partie && etat.donnees.jeu.id === partie.jeu ? etat.donnees : null);
	let version = $derived(donnees?.jeu.versions.find((v) => v.id === partie?.version));

	let parPokedex = $derived(
		donnees && partie
			? donnees.pokedex.map((p) => {
					const fiches = analyserVersion(donnees, partie.version, p.id);
					const attrapes = fiches.filter((f) => etat.estAttrape(f.pokemon.id)).length;
					return { pokedex: p, fiches, attrapes };
				})
			: []
	);
	let fiches = $derived(parPokedex[0]?.fiches ?? []);
	let manquants = $derived(fiches.filter((f) => !etat.estAttrape(f.pokemon.id)));

	/** Meilleure méthode pour chaque manquant (la plus « directe ») */
	const ordre = Object.keys(INFOS_METHODES) as Methode[];
	function methodePrincipale(f: FichePokedex): Methode | null {
		return ordre.find((m) => f.methodes.has(m)) ?? null;
	}
	let repartition = $derived.by(() => {
		const r = new Map<Methode | null, FichePokedex[]>();
		for (const f of manquants) {
			const m = methodePrincipale(f);
			r.set(m, [...(r.get(m) ?? []), f]);
		}
		return [...r].sort((a, b) => b[1].length - a[1].length);
	});
	let aEchanger = $derived(manquants.filter((f) => f.parEchange));
	let introuvables = $derived(fiches.filter((f) => !f.obtentions.length));

	let av = $derived(
		partie ? avancement(partie, etat.jeux.find((j) => j.id === partie.jeu), etat.progression) : null
	);

	let nbShiny =$derived(partie ? Object.values(partie.captures).filter((c) => c.shiny).length : 0);

	/** Formes et Méga-évolutions : obtenues / total, par type */
	function compterVariantes(type: 'forme' | 'mega') {
		let total = 0;
		let obtenues = 0;
		for (const f of fiches) {
			for (const x of f.pokemon.formes ?? []) {
				if (x.type !== type) continue;
				total++;
				if (partie?.captures[f.pokemon.id]?.formes?.[x.id]) obtenues++;
			}
		}
		return { total, obtenues };
	}
	let formes = $derived(compterVariantes('forme'));
	let megasCompte = $derived(compterVariantes('mega'));

	function pourcent(n: number, total: number) {
		return total ? Math.round((n / total) * 100) : 0;
	}
</script>

{#if !partie || !donnees}
	<p class="vide"><a href="#/">Choisis d'abord une partie.</a></p>
{:else}
	<h1>Bilan</h1>
	<p class="intro">
		{partie.nom} — {donnees.jeu.nom} ({version?.nom})
		{#if av}<StatutPartie {av} />{/if}
	</p>

	<section class="tuiles">
		{#each parPokedex as p (p.pokedex.id)}
			{@const pc = pourcent(p.attrapes, p.fiches.length)}
			<div class="tuile">
				<span class="titre">Pokédex {p.pokedex.nom}</span>
				<span class="valeur">{p.attrapes}<small> / {p.fiches.length}</small></span>
				<div class="barre"><span style:width="{pc}%"></span></div>
				<span class="pc">{pc} %</span>
			</div>
		{/each}
		<div class="tuile">
			<span class="titre">Encore à attraper</span>
			<span class="valeur">{manquants.length}</span>
			<span class="pc">dont {aEchanger.length} par échange</span>
		</div>
		{#if donnees.jeu.generation >= 2}
			<div class="tuile">
				<span class="titre">Chromatiques</span>
				<span class="valeur">{nbShiny}</span>
			</div>
		{/if}
		{#if formes.total}
			<div class="tuile">
				<span class="titre">Formes</span>
				<span class="valeur">{formes.obtenues}<small> / {formes.total}</small></span>
			</div>
		{/if}
		{#if megasCompte.total}
			<div class="tuile">
				<span class="titre">Méga-Gemmes</span>
				<span class="valeur">{megasCompte.obtenues}<small> / {megasCompte.total}</small></span>
			</div>
		{/if}
	</section>

	{#if av?.groupes.length}
		<section>
			<h2 class="avec-lien">Badges et Ligue <a href="#/badges">Tout voir →</a></h2>
			<div class="tuiles">
				{#each av.groupes as g (g.id)}
					{@const pc = pourcent(g.faits, g.total)}
					<a class="tuile lien-tuile" href="#/badges">
						<span class="titre">{g.titre}</span>
						<span class="valeur">{g.faits}<small> / {g.total}</small></span>
						<div class="barre"><span style:width="{pc}%"></span></div>
						<span class="pc">
							{#if g.prochaine}
								Prochaine : {g.prochaine.personne ?? g.prochaine.nom}{g.prochaine.lieu ? ` (${g.prochaine.lieu})` : ''}
							{:else}
								✓ Terminé
							{/if}
						</span>
					</a>
				{/each}
			</div>
		</section>
	{/if}

	{#if manquants.length}
		<section>
			<h2>Comment obtenir les manquants</h2>
			<ul class="repartition">
				{#each repartition as [m, liste] (m)}
					<li>
						<span class="methode">
							{#if m}<PuceMethode methode={m} titre={donnees.methodes[m]} />{:else}Introuvable{/if}
						</span>
						<span class="nombre">{liste.length}</span>
						<span class="noms">
							{#each liste.slice(0, 12) as f, i (f.pokemon.id)}{i ? ', ' : ''}<a href="#/pokemon/{f.pokemon.id}"
									>{f.pokemon.nom}</a
								>{/each}{liste.length > 12 ? '…' : ''}
						</span>
					</li>
				{/each}
			</ul>
		</section>
	{/if}

	{#if aEchanger.length}
		<section>
			<h2>À obtenir par échange</h2>
			<p class="aide">Absents de {version?.nom} : à faire venir d'une autre version.</p>
			<ul class="echanges">
				{#each aEchanger as f (f.pokemon.id)}
					<li>
						<a href="#/pokemon/{f.pokemon.id}">
							<img src={sprite(f.pokemon, partie.version)} alt="" width="40" height="40" />
							<span>{f.pokemon.nom}</span>
						</a>
						<small>{f.obtentions.find((o) => o.methode === 'echange_version')?.detail}</small>
					</li>
				{/each}
			</ul>
		</section>
	{/if}

	{#if introuvables.length}
		<section>
			<h2>Introuvables dans ce jeu</h2>
			<p class="aide">
				{introuvables.map((f) => f.pokemon.nom).join(', ')} — uniquement par événement, transfert ou bug selon les cas.
			</p>
		</section>
	{/if}

	{#if etat.parties.length > 1}
		<section>
			<h2>Toutes les parties</h2>
			<ul class="parties">
				{#each etat.parties as p (p.id)}
					{@const jeu = etat.jeux.find((j) => j.id === p.jeu)}
					{@const a = avancement(p, jeu, etat.progression)}
					<li>
						<strong>{p.nom}</strong>
						<span>{jeu?.versions.find((v) => v.id === p.version)?.nom ?? p.version}</span>
						<span>{a.total ? `${a.pourcentage} % du Pokédex` : `${a.attrapes} attrapés`}</span>
						{#if a.premierGroupe}<span>{a.premierGroupe.titre} : {a.premierGroupe.faits} / {a.premierGroupe.total}</span>{/if}
						<StatutPartie av={a} />
					</li>
				{/each}
			</ul>
		</section>
	{/if}
{/if}

<style>
	h1 {
		margin: 0;
	}
	.intro {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 4px 10px;
		margin: 0 0 14px;
		color: var(--ecran-texte-doux);
	}
	.avec-lien {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 10px;
	}
	.avec-lien a {
		font-size: 0.85rem;
		font-weight: 600;
		text-decoration: none;
	}
	.lien-tuile {
		color: inherit;
		text-decoration: none;
	}
	.lien-tuile:hover {
		background: var(--ecran-survol);
	}
	section {
		margin-bottom: 22px;
	}
	h2 {
		margin: 0 0 8px;
		font-size: 1.1rem;
	}
	.aide {
		margin: 0 0 8px;
		font-size: 0.9rem;
		color: var(--ecran-texte-doux);
	}
	.tuiles {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
		gap: 10px;
	}
	.tuile {
		display: grid;
		gap: 4px;
		padding: 12px;
		border-radius: 10px;
		background: var(--ecran-alt);
		box-shadow: inset 0 0 0 1px var(--ecran-ligne);
	}
	.titre {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--ecran-texte-doux);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.valeur {
		font-family: var(--police-ecran);
		font-size: 1.8rem;
		font-weight: 700;
	}
	.valeur small {
		font-size: 1rem;
		color: var(--ecran-texte-doux);
	}
	.pc {
		font-size: 0.85rem;
		color: var(--ecran-texte-doux);
	}
	.barre {
		height: 8px;
		border-radius: 999px;
		background: var(--ecran-ligne);
		overflow: hidden;
	}
	.barre span {
		display: block;
		height: 100%;
		background: var(--progression);
	}
	.repartition,
	.parties {
		display: grid;
		gap: 6px;
		margin: 0;
		padding: 0;
		list-style: none;
	}
	.repartition li {
		display: grid;
		grid-template-columns: 110px 36px 1fr;
		align-items: baseline;
		gap: 8px;
		padding: 6px 0;
		border-bottom: 1px solid var(--ecran-ligne);
		font-size: 0.9rem;
	}
	.nombre {
		font-family: var(--police-ecran);
		font-weight: 700;
	}
	.noms a {
		text-decoration: none;
	}
	.noms a:hover {
		text-decoration: underline;
	}
	.echanges {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
		gap: 8px;
		margin: 0;
		padding: 0;
		list-style: none;
	}
	.echanges li {
		display: grid;
		padding: 6px 8px;
		border-radius: 8px;
		background: var(--ecran-alt);
	}
	.echanges a {
		display: flex;
		align-items: center;
		gap: 6px;
		font-weight: 700;
		text-decoration: none;
	}
	.echanges img {
		image-rendering: pixelated;
	}
	.echanges small {
		color: var(--ecran-texte-doux);
	}
	.parties li {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 4px 12px;
		padding: 6px 10px;
		border-radius: 6px;
		background: var(--ecran-alt);
	}
	.vide {
		padding: 32px 0;
		text-align: center;
	}
	@media (max-width: 600px) {
		.repartition li {
			grid-template-columns: 90px 30px 1fr;
		}
	}
</style>
