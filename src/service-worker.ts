/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />
/**
 * Service worker : fonctionnement hors ligne.
 * - Application (code, données de jeu, icônes) : mise en cache à l'installation, cache d'abord.
 * - Sprites et illustrations (GitHub/PokéAPI) : mis en cache au premier affichage.
 * - Tout le reste (Dropbox, Poképédia) : réseau uniquement.
 */
import { base, build, files, version } from '$service-worker';

const sw = self as unknown as ServiceWorkerGlobalScope;

const CACHE_APP = `app-${version}`;
const CACHE_IMAGES = 'images-v1';
const CACHE_DONNEES = 'donnees-v1';
const RACINE = `${base}/`;
const DONNEES_JEU = /\/data\/jeux\/(?!index\.json)[^/]+\.json$/;
// Les fichiers de jeu (~300 Ko chacun) ne sont pas préchargés : mis en cache à l'ouverture
const RESSOURCES = [RACINE, ...build, ...files.filter((f) => !DONNEES_JEU.test(f))];
const HOTES_IMAGES = ['raw.githubusercontent.com'];

sw.addEventListener('install', (event) => {
	event.waitUntil(
		caches
			.open(CACHE_APP)
			.then((cache) => cache.addAll(RESSOURCES))
			.then(() => sw.skipWaiting())
	);
});

sw.addEventListener('activate', (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((cles) =>
				Promise.all(
					cles.filter((c) => ![CACHE_APP, CACHE_IMAGES, CACHE_DONNEES].includes(c)).map((c) => caches.delete(c))
				)
			)
			.then(() => sw.clients.claim())
	);
});

sw.addEventListener('fetch', (event) => {
	const req = event.request;
	if (req.method !== 'GET') return;
	const url = new URL(req.url);

	// Navigation : la page unique de l'application (routage par ancre)
	if (req.mode === 'navigate' && url.origin === location.origin) {
		event.respondWith(fetch(req).catch(async () => (await caches.match(RACINE)) ?? Response.error()));
		return;
	}

	// Ressources de l'application
	if (url.origin === location.origin && RESSOURCES.includes(url.pathname)) {
		event.respondWith(caches.match(url.pathname).then((r) => r ?? fetch(req)));
		return;
	}

	// Données d'un jeu : cache immédiat + mise à jour en arrière-plan (stale-while-revalidate)
	if (url.origin === location.origin && DONNEES_JEU.test(url.pathname)) {
		event.respondWith(
			caches.open(CACHE_DONNEES).then(async (cache) => {
				const enCache = await cache.match(req);
				const reseau = fetch(req)
					.then((rep) => {
						if (rep.ok) cache.put(req, rep.clone());
						return rep;
					})
					.catch(() => enCache ?? Response.error());
				if (enCache) {
					event.waitUntil(reseau.then(() => undefined));
					return enCache;
				}
				return reseau;
			})
		);
		return;
	}

	// Images externes : cache d'abord, enregistrées au premier affichage
	if (HOTES_IMAGES.includes(url.hostname)) {
		event.respondWith(
			caches.open(CACHE_IMAGES).then(async (cache) => {
				const enCache = await cache.match(req);
				if (enCache) return enCache;
				const rep = await fetch(req);
				if (rep.ok || rep.type === 'opaque') cache.put(req, rep.clone());
				return rep;
			})
		);
	}
});
