# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** 7 · **Membre :** Sara Hasnaoui · **Date :** 28/10/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.  
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

### 1. Mise en place

**Dernière ligne de `python -m pytest` avant modification :**

La sortie exacte de la première exécution n'a pas été conservée.

**Les 4 tests qui passent initialement :**

- `test_health`
- `test_out_of_range_value_is_rejected`
- `test_missing_field_is_rejected`
- `test_openapi_documents_predict`

**Pourquoi les deux tests qui attendent 422 passent-ils pour une mauvaise raison ?**

Au début, la classe `SensorReading` ne contient aucun champ déclaré. Comme `extra="forbid"` interdit les champs inconnus, Pydantic rejette toutes les données envoyées dans les requêtes.

Les tests obtiennent donc le code HTTP 422, mais pas pour la bonne raison : ce n'est pas encore la validation des limites de température ou la vérification des champs obligatoires qui provoque l'erreur.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

Variable  Type  Minimum (ge)  Maximum (le)  Justification physique

temperature_c float -40 150 Plage plausible pour un capteur de température industriel

vibration_mm_s float 0 100 Une vibration ne peut pas être négative ; 100 mm/s représente une limite haute de validation

load_pct float 0 100 La charge correspond à un pourcentage de la capacité nominale

runtime_hours float 0 1000000 Le temps de fonctionnement ne peut pas être négatif ; la limite haute permet d'éviter les valeurs aberrantes

**Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?**

```text
3 failed, 10 passed, 1 warning in 3.23s
```

Les trois tests qui échouent sont :

- `test_predict_returns_probability`
- `test_high_risk_reading_raises_alert`
- `test_503_when_model_missing`

Le message d'erreur est :

```text
NotImplementedError
```

C'est un bon signe, car les données sont maintenant correctement validées par le schéma Pydantic. Les requêtes valides arrivent jusqu'à la fonction `predict()`, mais celle-ci n'est pas encore implémentée.

Les tests de validation passent donc correctement. Il reste à compléter la fonction `predict()` dans `main.py`.

### 3. La fonction `predict()` (`maintai/api/main.py`)

**Votre code :**

```python
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")

    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non disponible"
        )

    return PredictionOut(
        **predictor.predict(reading.model_dump())
    )
```

**Pourquoi répondre 503 et pas 500 quand le modèle manque ?**

Le code HTTP 503 signifie que le service est indisponible. Ici, l'API fonctionne, mais elle ne peut pas effectuer de prédiction lorsque le modèle n'est pas chargé.

Le code 500 correspond plutôt à une erreur interne inattendue du serveur. Le code 503 est donc plus adapté à cette situation.

**Pourquoi le modèle est-il chargé une seule fois, au démarrage, et pas à chaque requête ?**

Le chargement du modèle peut prendre du temps et consommer de la mémoire. En le chargeant une seule fois au démarrage avec `lifespan`, toutes les requêtes peuvent réutiliser le même modèle.

Cela améliore les performances, réduit le temps de réponse et évite les chargements répétés.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```text
13 passed, 1 warning in 1.71s
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

Requête Code obtenu Réponse JSON

GET /health 200 {"status":"ok","model_loaded":true}

POST /v1/predict avec les valeurs demandées 200 {"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-28T17:35:44Z"}

POST /v1/predict avec température 500 422 Erreur de validation : la température doit être inférieure ou égale à 150.

POST /v1/predicte 404 {"detail":"Not Found"}

**Dans `/docs`, où voit-on les bornes que vous avez choisies ?**

Dans la documentation Swagger (`/docs`), les bornes sont affichées dans la section **Schemas → SensorReading**.

Chaque variable possède des contraintes `minimum` et `maximum`, définies dans `schemas.py` avec `Field(ge=..., le=...)`.

Ces contraintes permettent à FastAPI et Pydantic de vérifier automatiquement les données envoyées à l'API et de retourner une erreur HTTP 422 lorsqu'une valeur ne respecte pas les limites autorisées.

## 6. Questions de compréhension

**1. REST et FastAPI : quelle est la différence ?**

REST est un style d'architecture qui définit des principes pour concevoir des API web communiquant via HTTP.

FastAPI est un framework Python qui facilite la création d'API, la validation des données et la génération automatique de la documentation.

**2. Le schéma Pydantic sert à trois choses. Lesquelles ?**

- Définir la structure et les types des données attendues.
- Vérifier automatiquement les données reçues, notamment les champs obligatoires et les limites minimales et maximales.
- Générer automatiquement la documentation des schémas dans Swagger/OpenAPI.

**3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?**

- `localhost` : désigne l'ordinateur sur lequel l'API fonctionne.
- `8000` : correspond au port sur lequel le serveur écoute les requêtes.
- `/v1/predict` : représente l'endpoint utilisé pour demander une prédiction de panne.

**4. Pourquoi `/v1` dans l'adresse ?**

`/v1` indique la première version de l'API. Cela permet de faire évoluer l'API et d'ajouter de nouvelles versions sans perturber les applications qui utilisent encore l'ancienne version.

**5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?**

- `maintai.api.main` : désigne le module Python `main.py`, situé dans le dossier `maintai/api`.
- `app` : correspond à l'instance FastAPI créée avec `app = FastAPI(...)`.

Uvicorn utilise cette instance pour démarrer le serveur web.

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp1` existe sur GitHub : oui / non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?

  …

## 8. Ce qui reste flou

…