import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		// Site 100 % statique (GitHub Pages) : une seule page, navigation par ancre (#/…)
		adapter: adapter({ fallback: 'index.html' }),
		router: { type: 'hash' },
		paths: {
			// Sous-dossier GitHub Pages (ex. /pokedex-tracker) fourni au moment du build
			base: process.env.BASE_PATH ?? '',
			relative: true
		}
	}
};

export default config;
