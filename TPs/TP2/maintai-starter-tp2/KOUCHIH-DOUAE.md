# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** G7 · **Membre :** Kouchih Douae · **Date :** 04/11/2026

> Compte rendu évolutif : les éléments marqués **À compléter après test** doivent être remplacés par les observations réelles avant le rendu. Les sorties de terminal sont conservées entre trois accents graves.

---

## 1. Activité 1 : casser son API (dans `TPs/TP1`)

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| 1 | Champ manquant : `load_pct` absent | 422 | 422 |
| 2 | Valeur absurde : `temperature_c = 500` | 422 | 422 |
| 3 | Texte au lieu d'un nombre : `load_pct = "bonjour"` | 422 | 422 |
| 4 | Champ en trop : `couleur = "rouge"` | 422 | 422 |
| 5 | Mauvaise route : `/v1/predicte` au lieu de `/v1/predict` | 404 | 404 |

### Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

Non, les cinq prévisions étaient correctes. Les quatre requêtes contenant des données invalides ont retourné **422 (Unprocessable Entity)**, car elles ne respectaient pas le schéma Pydantic `SensorReading`. La mauvaise route `/v1/predicte` a retourné **404 (Not Found)**, car cet endpoint n'existe pas.

### Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TPs/TP1`)

```text
5 passed, 1 warning in 1.61s
```

Lors de l'exécution de l'ensemble des tests du TP1, le résultat était :

```text
19 passed, 1 warning in 1.70s
```

Ce total comprend un test supplémentaire conservé dans `tests/test_.py`.

### À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

`@pytest.mark.parametrize` permet de tester une même fonction avec plusieurs jeux de données, sans dupliquer le code. Les cinq scénarios de `CAS_REFUSES` correspondent à **cinq exécutions distinctes**, donc pytest compte cinq tests pour `test_requete_refusee`.

---

## 2. Ruff

### Sortie de `ruff check .` dans `TPs/TP1`

```text
UP017 [*] Use `datetime.UTC` alias
  --> maintai\train.py:58:36
   |
58 |         "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
   |                                    ^^^^^^^^^^^^
   |
help: Convert to `datetime.UTC` alias

Found 1 error.
[*] 1 fixable with `--fix`.
```

### Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

`ruff check .` réalise une **analyse statique** du code Python : il signale des problèmes de style, des imports inutilisés et certaines pratiques à améliorer, sans exécuter les tests. `python -m pytest` **exécute les tests automatisés** pour vérifier le comportement de l'application. Ici, pytest a validé 19 tests sur l'ensemble du TP1, tandis que Ruff a signalé la règle **UP017** dans `maintai/train.py`, recommandant `datetime.UTC` à la place de `timezone.utc`.

---

## 3. Mise en place du TP2 (dans `TPs/TP2`)

### Dernière ligne de `python -m pytest` juste après la mise en place

```text
2 failed, 16 passed, 1 warning in 5.26s
```

### Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

- `tests/test_security.py::test_missing_key_is_rejected`
- `tests/test_security.py::test_wrong_key_is_rejected`

Ces tests recevaient **200 (OK)** au lieu de **401 (Unauthorized)**. À ce stade, la protection par clé API n'était pas encore activée sur le router `/v1`, donc les requêtes sans clé ou avec une fausse clé étaient acceptées.

---

## 4. La clé API (sprint 1)

### Fonction `require_api_key()` dans `maintai/api/security.py`

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    expected_key = get_settings().api_key

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clé API non configurée sur le serveur"
        )

    if not x_api_key or not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide"
        )
```

### Déclaration du router dans `maintai/api/main.py`

```python
router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_api_key)],
)
```

### Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

**Deux tests échouaient encore** :

```text
2 failed, 16 passed, 1 warning in 2.22s
```

Même si la fonction de vérification était implémentée, FastAPI ne l'appelait pas automatiquement. Il fallait la déclarer dans les dépendances du router avec `Depends(require_api_key)`.

### Dernière ligne de `python -m pytest` à la fin du sprint 1

```text
18 passed, 1 warning in 2.46s
```

### Vérifications HTTP après `uvicorn maintai.api.main:app --reload --env-file .env`

| Requête | Code obtenu | Réponse (corps JSON) |
|---|---|---|
| `GET /health`, sans clé | **À compléter après test** | **À compléter après test** |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | **À compléter après test** | **À compléter après test** |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | Prédiction réussie ; un essai Swagger a retourné `failure_probability: 0.9553`, `alert: true`, `threshold: 0.3`, `model_version: "2026-11-04T17:45:52Z"` (recopier le JSON exact si exigé) |
| `POST /v1/predict`, 500 °C, sans clé | **À compléter après test** | **À compléter après test** |
| `POST /v1/predict`, 500 °C, bonne clé | **À compléter après test** | **À compléter après test** |

### 500 °C sans clé et avec la bonne clé : pourquoi des codes différents ?

**Explication théorique à confirmer par les essais :** la dépendance `require_api_key` peut refuser une requête non authentifiée avec **401** avant que le corps soit validé par le modèle Pydantic. Avec la bonne clé, la validation des données peut alors produire **422**, car `temperature_c = 500` dépasse la plage autorisée.

### Relancer Uvicorn sans `--env-file .env` : quel code et pourquoi pas 401 ?

**À compléter après test.** Le comportement attendu dépend de la configuration réellement disponible dans l'environnement du processus. Si aucune clé serveur n'est configurée, `require_api_key` déclenche **500 (erreur de configuration du serveur)** avant de comparer les clés. Ne pas présenter ce résultat comme observé avant le test.

---

## 5. La page web (sprint 2)

### Code `fetch` (contenu du `addEventListener` dans `web/index.html`)

```javascript
document.getElementById("go").addEventListener("click", async () => {
  const reading = Object.fromEntries(
    FEATURES.map(f => [f, Number(document.getElementById(f).value)])
  );

  const url = document.getElementById("url")
    .value.trim().replace(/\/$/, "");
  const cle = document.getElementById("key").value;

  try {
    const resp = await fetch(`${url}/v1/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": cle
      },
      body: JSON.stringify(reading)
    });

    const data = await resp.json();

    if (!resp.ok) {
      show("err", `Erreur HTTP ${resp.status} : ${JSON.stringify(data)}`);
      return;
    }

    const probabilite = (data.failure_probability * 100).toFixed(2);

    if (data.alert) {
      show("alert", `ALERTE : risque de panne de ${probabilite} %`);
    } else {
      show("ok", `Pas d'alerte : risque de panne de ${probabilite} %`);
    }

  } catch (e) {
    show("err", `API injoignable ou requête bloquée : ${e.message}`);
  }
});
```

### Ce qu'affiche la page (servie sur le port 5500)

| Essai | Ce qu'affiche la page |
|---|---|
| Relevé normal, bonne clé | `ALERTE : risque de panne de 94.75 %` |
| 500 °C, bonne clé | **À compléter après test** |
| Relevé normal, fausse clé | **À compléter après test** |

### Expérience CORS : page servie sur le port 5501

**Message de la page :** À compléter après test.

**Message de la console (F12) :** À compléter après test, en recopiant l'erreur réelle.

### Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

La politique **CORS est appliquée par les navigateurs** aux requêtes JavaScript entre origines différentes. L'origine `http://localhost:5501` n'est pas dans la liste autorisée (`http://localhost:5500` et `http://127.0.0.1:5500`). Le navigateur bloque donc l'accès à la réponse lorsque le serveur n'autorise pas cette origine. `curl.exe` n'applique pas les restrictions CORS du navigateur : il peut afficher la réponse HTTP. **Explication à illustrer avec les observations réelles.**

---

## 6. Les tests de l'activité 1 dans le TP2

### Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

**À compléter après test.** Hypothèse à vérifier : les quatre requêtes adressées à `/v1/predict` sont refusées avec **401**, car elles ne fournissent pas de clé API. La requête vers `/v1/predicte` peut toujours obtenir **404**, car aucune route ne correspond à ce chemin.

### Dernière ligne de `python -m pytest` avec `headers=HEADERS`

sans headers=HEADERS, combien de tests échouent, et avec quel code ?

Le résultat de cette expérience n'a pas été confirmé. Les tests ont été exécutés avec headers=HEADERS, ce qui permet de transmettre la clé API de test.

Dernière ligne de python -m pytest avec headers=HEADERS

5 passed, 1 warning in 2.63s

Les cinq tests de l'activité 1 réussissent dans le TP2 avec la clé API de test.

## 7. Questions de compréhension

### 1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?

- **401 Unauthorized** : la requête ne présente pas des informations d'authentification valides (clé absente ou incorrecte).
- **422 Unprocessable Entity** : le corps de la requête ne respecte pas les règles de validation des données.
- **403 Forbidden** : le serveur comprend la requête, mais refuse l'accès à la ressource, par exemple parce que l'utilisateur authentifié n'a pas les droits nécessaires.

### 2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?

La clé est une information sensible. L'inscrire directement dans le code ou la publier sur GitHub exposerait l'accès à l'API. Le fichier **`.env`** contient la vraie valeur locale de `MAINTAI_API_KEY` et la configuration CORS ; il est ignoré par Git. Le fichier **`.env.example`** fournit un exemple de configuration avec une valeur fictive, sans secret, et peut être commité. La commande `git check-ignore .env` a confirmé que `.env` était ignoré.

### 3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?

L'en-tête `X-API-Key` sépare les informations d'authentification des paramètres de la ressource. Une clé placée dans l'URL risque davantage d'être enregistrée dans l'historique du navigateur, les journaux des serveurs ou des systèmes intermédiaires. L'en-tête n'est pas une protection suffisante à lui seul : en production, il faut aussi utiliser **HTTPS** et éviter de journaliser les secrets.

### 4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?

`secrets.compare_digest` compare les secrets d'une manière conçue pour limiter les fuites d'information liées au temps de comparaison. Cela réduit certains risques d'attaques temporelles par rapport à une comparaison ordinaire avec `==`.

### 5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?

Une **origine** est définie par le protocole, le nom d'hôte et le port. Les adresses `http://localhost:5500` et `http://localhost:8000` sont **deux origines différentes**, car leurs ports diffèrent. Le navigateur applique donc les règles CORS lorsque le JavaScript de la page sur le port 5500 appelle l'API sur le port 8000.

---

## 8. Le rendu Git

- **Lien de la pull request :** À compléter après création.
- **Le tag `tp2` existe sur GitHub :** À vérifier après publication.
- **`git status` avant le commit : le fichier `.env` apparaissait-il ?** Non, il était ignoré (vérifié avec `git check-ignore .env`).
- **Qui a relu la pull request, et quel commentaire a-t-il laissé ?** À compléter après relecture.

---

## 9. Ce qui reste flou

**À personnaliser avant le rendu.** Exemple de formulation, à conserver uniquement si elle correspond aux difficultés réellement rencontrées :

> J'ai mieux compris la différence entre la validation Pydantic, l'authentification par clé API et les restrictions CORS du navigateur. Je souhaite encore approfondir l'ordre d'exécution entre les dépendances FastAPI et la validation du corps de requête, ainsi que la distinction entre une erreur HTTP du serveur et un blocage CORS dans le navigateur.

---

## 10. Problèmes rencontrés et solutions apportées

### 10.1. Impossible de démarrer le serveur web sur le port 5500

**Commande exécutée :**

```powershell
python -m http.server 5500 -d web
```

**Erreur observée :**

```text
PermissionError: [WinError 10013] Une tentative d’accès à un socket de manière interdite par ses autorisations d’accès a été tentée
```

**Diagnostic :** nous avons recherché le processus associé au port 5500 :

```powershell
Get-NetTCPConnection -LocalPort 5500 -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, State, OwningProcess
Get-Process -Id 5724 | Select-Object Id, ProcessName, Path
Get-CimInstance Win32_Service | Where-Object { $_.ProcessId -eq 5724 } | Select-Object Name, DisplayName, State
```

Le PID **5724** correspondait au processus **`tnslsnr`**, associé au service Oracle **`OracleOraDB19Home1TNSListener`**. Ce service utilisait le port 5500.

**Solution :** le port a été libéré après intervention sur le service Oracle. La vérification suivante n'a plus retourné de listener :

```powershell
Get-NetTCPConnection -LocalPort 5500 -State Listen -ErrorAction SilentlyContinue
```

Le serveur HTTP a ensuite pu servir la page sur `http://localhost:5500`.

**Précaution :** arrêter Oracle TNS Listener peut interrompre les connexions à Oracle. Le service doit être redémarré après le TP si nécessaire, avec les autorisations appropriées :

```powershell
Start-Service -Name "OracleOraDB19Home1TNSListener"
```

### 10.2. API accessible, mais modèle de Machine Learning non chargé

**Erreur observée après authentification :**

```json
{"detail":"Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API"}
```

**Code HTTP :** `503 Service Unavailable`.

**Cause :** la requête franchissait la vérification de clé API, mais le modèle entraîné n'était pas disponible pour la prédiction.

**Solution :** préparer les données si nécessaire, entraîner le modèle et redémarrer l'API :

```powershell
python -m maintai.dataset
python -m maintai.train
uvicorn maintai.api.main:app --reload --env-file .env
```

**Résultat :** une prédiction a ensuite réussi avec **200 OK** dans Swagger ; le client web a également affiché une alerte à **94,75 %** pour les valeurs saisies.

### 10.3. Le navigateur affichait encore « À compléter »

**Symptôme :** cliquer sur **Prédire** affichait le texte `À compléter` au lieu d'appeler l'API.

**Cause constatée :** le fichier `web/index.html` contenait toujours le code initial :

```javascript
// TODO (TP2) : Envoyez reading en POST JSON...
show("err", "À compléter");
```

**Solution :** remplacer le code provisoire par l'appel `fetch()` avec `POST`, `Content-Type: application/json`, `X-API-Key` et `JSON.stringify(reading)`, puis enregistrer le fichier et actualiser le navigateur.

**Résultat :** le formulaire a finalement affiché :

```text
ALERTE : risque de panne de 94.75 %
```

### 10.4. Vérification du bon serveur API sur le port 8000

Lors des essais Swagger, des réponses inattendues ont été observées avant de confirmer que la sécurité du TP2 fonctionnait : une requête sans clé a ensuite bien retourné **401**. Une instance précédente de l'API ou un serveur non redémarré était une **hypothèse**, mais la cause précise n'a pas été formellement confirmée.

**Bonne pratique retenue :** vérifier quel processus écoute sur le port 8000, arrêter les anciennes instances si nécessaire et relancer l'API du bon dossier avec son fichier `.env`, sans arrêter le serveur web du port 5500.

---

## 11. Bilan provisoire

La sécurisation de l'API par `X-API-Key` est opérationnelle : **18 tests passent** à la fin du sprint 1. Le client web servi sur le port **5500** appelle FastAPI sur le port **8000** et affiche une prédiction de panne. Il reste à compléter les essais HTTP du tableau, les tests web négatifs, l'expérience CORS sur **5501**, la reprise des tests de l'activité 1 dans le TP2 et le rendu Git.
