<script lang="ts">
	import { analyserLieux } from '$lib/analyse';
	import { normaliser } from '$lib/donnees';
	import { etat } from '$lib/etat.svelte';

	let partie = $derived(etat.partieActive);
	let donnees = $derived(etat.donnees && partie && etat.donnees.jeu.id === partie.jeu ? etat.donnees : null);
	let lieux = $derived(donnees && partie ? analyserLieux(donnees, partie.version) : []);

	let recherche = $state('');
	let masquerTermines = $state(false);

	let lignes = $derived(
		lieux
			.map((f) => {
				const reste = f.pokemons.filter((p) => !etat.estAttrape(p.pokemon.id)).length;
				return { ...f, reste, total: f.pokemons.length };
			})
			.filter((f) => !masquerTermines || f.reste > 0)
			.filter((f) => !recherche || normaliser(f.lieu.nom).includes(normaliser(recherche)))
	);
</script>

{#if !partie || !donnees}
	<p class="vide"><a href="#/">Choisis d'abord une partie.</a></p>
{:else}
	<h1>Lieux</h1>
	<p class="intro">
		Dans l'ordre de progression de {donnees.jeu.nom} ({donnees.jeu.versions.find((v) => v.id === partie.version)?.nom}).
		Le compteur indique les Pokémon encore à attraper sur place.
	</p>

	<div class="outils">
		<label class="sr-only" for="r-lieu">Rechercher un lieu</label>
		<input id="r-lieu" class="champ" type="search" placeholder="Rechercher un lieu…" bind:value={recherche} />
		<label class="case"><input type="checkbox" bind:checked={masquerTermines} /> Masquer les lieux terminés</label>
	</div>

	<ol class="liste">
		{#each lignes as l (l.lieu.id)}
			<li class:termine={l.reste === 0}>
				<a href="#/lieux/{l.lieu.id}">
					<span class="nom">{l.lieu.nom}</span>
					<span class="sprites" aria-hidden="true">
						{#each l.pokemons.filter((p) => !etat.estAttrape(p.pokemon.id)).slice(0, 6) as p (p.pokemon.id)}
							<img src={p.pokemon.sprites[partie.version] ?? p.pokemon.artwork} alt="" width="32" height="32" loading="lazy" />
						{/each}
					</span>
					<span class="compteur">
						{#if l.reste === 0}✓ Terminé{:else}reste <strong>{l.reste}</strong> / {l.total}{/if}
					</span>
				</a>
			</li>
		{:else}
			<li class="vide">Aucun lieu ne correspond.</li>
		{/each}
	</ol>
{/if}

<style>
	h1 {
		margin: 0 0 4px;
	}
	.intro {
		margin: 0 0 12px;
		color: var(--ecran-texte-doux);
		font-size: 0.9rem;
	}
	.outils {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 8px 16px;
		margin-bottom: 10px;
	}
	.outils .champ {
		flex: 1;
		min-width: 200px;
	}
	.case {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 0.9rem;
	}
	.liste {
		margin: 0;
		padding: 0;
		list-style: none;
	}
	.liste a {
		display: grid;
		grid-template-columns: 1fr auto auto;
		align-items: center;
		gap: 12px;
		padding: 8px 6px;
		border-bottom: 1px solid var(--ecran-ligne);
		text-decoration: none;
	}
	.liste a:hover {
		background: var(--ecran-survol);
	}
	.nom {
		font-weight: 700;
	}
	.sprites {
		display: flex;
	}
	.sprites img {
		image-rendering: pixelated;
	}
	.compteur {
		min-width: 90px;
		text-align: right;
		font-family: var(--police-ecran);
		font-size: 0.85rem;
	}
	.termine .nom,
	.termine .compteur {
		color: var(--progression);
	}
	.vide {
		padding: 24px 0;
		text-align: center;
		color: var(--ecran-texte-doux);
	}
	@media (max-width: 600px) {
		.sprites {
			display: none;
		}
	}
</style>
