# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** 7  ·  **Membres :** kouchih  ·  **Date :** 28/10/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---


### 1. Mise en place

**Dernière ligne de `python -m pytest` avant modification :**

À récupérer depuis la première exécution du projet. La sortie initiale exacte n'a pas été conservée.

**Les 4 tests qui passent initialement :**

- `test_health`
- `test_out_of_range_value_is_rejected`
- `test_missing_field_is_rejected`
- `test_openapi_documents_predict`

**Pourquoi les deux tests qui attendent 422 passent-ils pour une mauvaise raison ?**

Initialement, la classe `SensorReading` ne contient aucun champ déclaré. Comme `extra="forbid"` interdit les champs inconnus, Pydantic rejette toutes les données envoyées dans les requêtes.

Les tests obtiennent donc le code HTTP 422, mais pour une mauvaise raison : ce n'est pas encore la validation des bornes de température ou la vérification des champs obligatoires qui provoque l'erreur.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

Variable	Type	Minimum (ge)	Maximum (le)	Justification physique
temperature_c	float	-40	150	Plage plausible pour un capteur de température industriel
vibration_mm_s	float	0	100	Une amplitude de vibration ne peut pas être négative ; 100 mm/s est une limite haute de validation
load_pct	float	0	100	La charge représente un pourcentage de la capacité nominale
runtime_hours	float	0	1000000	Le temps de fonctionnement ne peut pas être négatif ; la borne haute limite les valeurs aberrantes

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?
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

Les tests de validation des données passent correctement. Il reste donc à compléter la fonction `predict()` dans `main.py`.

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

Le code HTTP 503 signifie que le service est indisponible. Dans notre cas, l'API fonctionne, mais elle ne peut pas effectuer de prédiction lorsque le modèle n'est pas chargé.

Le code 500 indique une erreur interne inattendue du serveur. Le code 503 est donc plus adapté pour signaler que le service de prédiction n'est pas disponible.

**Pourquoi le modèle est-il chargé une seule fois, au démarrage, et pas à chaque requête ?**

Le chargement du modèle peut prendre du temps et consommer de la mémoire. En le chargeant une seule fois au démarrage avec `lifespan`, toutes les requêtes réutilisent le même modèle.

Cela améliore les performances, réduit le temps de réponse et évite les chargements répétés.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

13 passed, 1 warning in 1.71s

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

Requête	Code obtenu	Réponse JSON
GET /health	200	{"status":"ok","model_loaded":true}
POST /v1/predict avec les valeurs demandées	200	{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-28T17:35:44Z"}
POST /v1/predict avec température 500	422	{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "temperature_c"],
      "msg": "Input should be less than or equal to 150",
      "input": 500,
      "ctx": {
        "le": 150
      }
    }
  ]
}
POST /v1/predicte	404	{"detail":"Not Found"}

Dans `/docs`, où voit-on les bornes que vous avez choisies ?
Dans la documentation Swagger (`/docs`), les bornes de validation sont visibles dans la section **Schemas → SensorReading**.

Chaque variable possède des contraintes `minimum` et `maximum`, définies dans `schemas.py` à l'aide de `Field(ge=..., le=...)`.

Ces contraintes permettent à FastAPI et Pydantic de vérifier automatiquement les données envoyées à l'API et de retourner une erreur HTTP 422 lorsqu'une valeur ne respecte pas les limites autorisées.

## 6. Questions de compréhension

**1. REST et FastAPI : quelle est la différence ?**

REST est un style d'architecture permettant de concevoir des API web qui communiquent à travers HTTP.

FastAPI est un framework Python permettant de développer des API rapidement, avec validation des données et documentation automatique.

**2. Le schéma Pydantic sert à trois choses. Lesquelles ?**

- Définir la structure et les types des données attendues.
- Valider automatiquement les données reçues (champs obligatoires, bornes minimales et maximales).
- Générer automatiquement la documentation des schémas dans Swagger/OpenAPI.

**3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?**

- `localhost` : désigne l'ordinateur local sur lequel fonctionne l'API.
- `8000` : représente le port sur lequel le serveur écoute les requêtes.
- `/v1/predict` : représente l'endpoint permettant de demander une prédiction de panne.

**4. Pourquoi `/v1` dans l'adresse ?**

`/v1` signifie version 1 de l'API. Cela permet de gérer différentes versions et de faire évoluer l'API sans perturber les applications qui utilisent l'ancienne version.

**5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?**

- `maintai.api.main` : représente le module Python `main.py` situé dans le dossier `maintai/api`.
- `app` : représente l'instance FastAPI créée avec `app = FastAPI(...)`.

Uvicorn utilise cette instance pour démarrer le serveur web.

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp1` existe sur GitHub : oui / non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  …

## 8. Ce qui reste flou

…
