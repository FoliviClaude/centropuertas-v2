/*
 * static/sw.js
 * =============
 * Service Worker de CentroPuertas.
 *
 * LIMITE IMPORTANTE (a lire avant de modifier ce fichier) : Streamlit ne
 * sert les fichiers statiques que sous /app/static/, et n'envoie pas
 * l'entete HTTP "Service-Worker-Allowed". Un service worker enregistre
 * depuis /app/static/sw.js a donc, par les regles standard du navigateur,
 * une PORTEE (scope) limitee a /app/static/ -- il ne recoit JAMAIS les
 * requetes de navigation vers "/", ou vit reellement l'application
 * Streamlit. Impossible de l'elargir sans changer d'architecture cote
 * serveur (Streamlit ne l'expose pas).
 *
 * Consequence concrete : ce service worker peut mettre en cache et servir
 * hors-ligne les fichiers STATIQUES (manifest, icones, page de secours),
 * mais ne peut pas rendre l'application elle-meme (formulaires, tableau
 * de bord...) utilisable hors-ligne -- celle-ci a de toute facon besoin
 * d'une connexion WebSocket permanente au serveur Python pour fonctionner,
 * meme en theorie ca ne changerait rien.
 */

const VERSION = "v1";
const CACHE_NAME = `centropuertas-shell-${VERSION}`;

// Chemins relatifs au scope du service worker (/app/static/).
const APP_SHELL = [
    "./offline.html",
    "./manifest.json",
    "./icon-192.png",
    "./icon-512.png",
    "./icon-maskable-192.png",
    "./icon-maskable-512.png",
];

// --- install : pre-cache de l'App Shell -------------------------------
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches
            .open(CACHE_NAME)
            .then((cache) => cache.addAll(APP_SHELL))
            .then(() => self.skipWaiting())
    );
});

// --- activate : nettoyage des anciens caches ---------------------------
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches
            .keys()
            .then((noms) =>
                Promise.all(
                    noms
                        .filter((nom) => nom !== CACHE_NAME)
                        .map((nom) => caches.delete(nom))
                )
            )
            .then(() => self.clients.claim())
    );
});

// --- fetch : Cache First pour les assets, page de secours pour la nav --
self.addEventListener("fetch", (event) => {
    const { request } = event;

    // On ne traite que les requetes GET (POST/PUT ne se mettent pas en
    // cache correctement et n'ont pas de sens a re-servir hors-ligne).
    if (request.method !== "GET") return;

    // Requete de navigation (ex: on ouvre /app/static/offline.html a la
    // main, ou le navigateur revalide le SW) : reseau d'abord pour avoir
    // la version la plus fraiche, secours sur le cache/la page hors-ligne
    // si le reseau echoue.
    if (request.mode === "navigate") {
        event.respondWith(
            fetch(request).catch(async () => {
                const enCache = await caches.match(request);
                return enCache || caches.match("./offline.html");
            })
        );
        return;
    }

    // Assets statiques (icones, manifest...) : Cache First -- ils changent
    // rarement, donc autant repondre instantanement depuis le cache, tout
    // en rafraichissant silencieusement ce cache en arriere-plan pour la
    // prochaine visite.
    event.respondWith(
        caches.match(request).then((reponseCache) => {
            const miseAJourReseau = fetch(request)
                .then((reponseReseau) => {
                    if (reponseReseau && reponseReseau.ok) {
                        const copie = reponseReseau.clone();
                        caches.open(CACHE_NAME).then((cache) => cache.put(request, copie));
                    }
                    return reponseReseau;
                })
                .catch(() => reponseCache);

            return reponseCache || miseAJourReseau;
        })
    );
});
