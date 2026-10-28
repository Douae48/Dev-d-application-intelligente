# Compte rendu du TP1 — Développement d’une API de prédiction pour MaintAI

**Groupe :** 7  
**Membre :** HAZIME SOFIA  
**Date :** 28/10/2026

## 1. Mise en place

**Dernière ligne affichée lors du premier lancement de `python -m pytest` :**

La sortie exacte de cette première exécution n’a pas été conservée.

**Les quatre tests réussis au départ :**
- `test_health`
- `test_out_of_range_value_is_rejected`
- `test_missing_field_is_rejected`
- `test_openapi_documents_predict`

**Pourquoi les deux tests censés retourner une erreur 422 réussissaient-ils pour une mauvaise raison ?**

Au début, la classe `SensorReading` ne définissait aucun champ. Avec l’option `extra="forbid"`, Pydantic refusait toutes les données supplémentaires envoyées dans les requêtes.

Les deux tests recevaient donc bien une réponse HTTP 422, mais celle-ci ne résultait pas de la vérification des limites des valeurs ou de l’absence de champs obligatoires. Le rejet était simplement dû à la configuration initiale du schéma.

## 2. Définition du schéma d’entrée (`maintai/api/schemas.py`)

Les champs ont été définis avec les types et les limites suivants :

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification |
|---|---|---:|---:|---|
| `temperature_c` | float | -40 | 150 | Valeurs compatibles avec une plage plausible de température industrielle. |
| `vibration_mm_s` | float | 0 | 100 | Une vibration ne peut pas être négative et 100 mm/s constitue une limite supérieure de validation. |
| `load_pct` | float | 0 | 100 | La charge correspond à un pourcentage de la capacité nominale. |
| `runtime_hours` | float | 0 | 1000000 | Le temps de fonctionnement ne peut pas être négatif ; la limite supérieure permet d'écarter les valeurs excessives. |

**Que se passe-t-il après la création de `schemas.py`, avant l’implémentation de `predict()` ? Pourquoi est-ce encourageant ?**

L’exécution de `python -m pytest` donne le résultat suivant :

```text
3 failed, 10 passed, 1 warning in 3.23s
```

Les trois tests en échec sont :
- `test_predict_returns_probability`
- `test_high_risk_reading_raises_alert`
- `test_503_when_model_missing`

L’erreur rencontrée est :

```text
NotImplementedError
```

Ce résultat montre que le schéma de validation fonctionne désormais : les tests liés aux données sont réussis. Les requêtes valides atteignent maintenant la fonction `predict()`, mais celle-ci n’a pas encore été développée. La prochaine étape consiste donc à implémenter cette fonction dans `main.py`.

## 3. Implémentation de `predict()` (`maintai/api/main.py`)

**Code utilisé :**

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

**Pourquoi utiliser le code HTTP 503 plutôt que 500 lorsque le modèle est absent ?**

Le code 503 indique que le service ne peut momentanément pas répondre à la demande. Ici, l’API peut fonctionner correctement sans que le modèle de prédiction soit disponible.

À l’inverse, le code 500 correspond à une erreur interne inattendue du serveur. Le code 503 est donc plus approprié pour signaler l’indisponibilité du modèle.

**Pourquoi charger le modèle au démarrage plutôt qu’à chaque requête ?**

Le chargement d’un modèle peut nécessiter du temps et des ressources mémoire. Grâce au mécanisme `lifespan`, le modèle est initialisé au démarrage de l’application, puis réutilisé pour les requêtes suivantes.

Cette approche évite de répéter inutilement le chargement, améliore les performances et contribue à réduire le temps de réponse de l’API.

## 4. Résultat final des tests

Après les modifications, l’exécution de `python -m pytest` affiche :

```text
13 passed, 1 warning in 1.71s
```

Les 13 tests passent, ce qui confirme que les fonctionnalités vérifiées par la suite de tests sont opérationnelles.

## 5. Vérification de l’API

Après avoir exécuté les commandes suivantes :

```bash
python -m maintai.dataset
python -m maintai.train
uvicorn maintai.api.main:app --reload
```

Les requêtes peuvent être testées depuis `/docs` ou avec `curl.exe`.

| Requête | Code HTTP | Résultat |
|---|---:|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec les valeurs demandées | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-28T17:35:44Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | Erreur de validation indiquant que la température dépasse la limite autorisée de 150. |
| `POST /v1/predicte` | 404 | `{"detail":"Not Found"}` |

**Où peut-on consulter les limites définies dans Swagger (`/docs`) ?**

Les contraintes sont visibles dans la documentation Swagger, dans la partie **Schemas → SensorReading**. On y retrouve les valeurs minimales et maximales de chaque variable.

Elles sont définies dans `schemas.py` avec `Field(ge=..., le=...)`. FastAPI s’appuie sur Pydantic pour vérifier les données reçues et renvoyer une réponse 422 lorsqu’une valeur ne respecte pas les contraintes.

## 6. Questions de compréhension

**1. Quelle différence existe-t-il entre REST et FastAPI ?**

REST correspond à un style d’architecture utilisé pour organiser les échanges entre applications via HTTP. FastAPI est un framework Python qui facilite la création d’API, notamment grâce à la validation des données et à la génération automatique de la documentation.

**2. Quels sont les trois rôles du schéma Pydantic ?**

- Décrire les champs attendus ainsi que leurs types.
- Contrôler les données reçues, notamment les champs obligatoires et les limites autorisées.
- Fournir les informations nécessaires à la génération de la documentation OpenAPI et Swagger.

**3. Que représentent `localhost`, `8000` et `/v1/predict` dans l’adresse `http://localhost:8000/v1/predict` ?**

- `localhost` désigne la machine sur laquelle le serveur est exécuté.
- `8000` correspond au port utilisé par le serveur pour recevoir les requêtes.
- `/v1/predict` est le chemin de l’endpoint qui permet de demander une prédiction.

**4. À quoi sert la partie `/v1` dans l’URL ?**

Elle identifie la première version de l’API. Le versionnement permet de faire évoluer l’interface au fil du temps tout en conservant la compatibilité avec les clients utilisant les versions précédentes.

**5. Que signifient `maintai.api.main` et `app` dans `uvicorn maintai.api.main:app` ?**

- `maintai.api.main` désigne le module Python correspondant au fichier `main.py`, situé dans le répertoire `maintai/api`.
- `app` correspond à l’objet FastAPI déclaré dans ce fichier, généralement avec `app = FastAPI(...)`.

Uvicorn utilise cet objet pour lancer le serveur et traiter les requêtes HTTP.

## 7. Rendu Git

- **Lien de la pull request :** à compléter.
- **Le tag `tp1` existe sur GitHub :** oui / non, à vérifier.
- **Personne ayant relu la pull request et commentaire laissé :** à compléter.

## 8. Points restant à clarifier

À compléter avec les questions ou les notions qui restent difficiles à comprendre après la réalisation du TP.