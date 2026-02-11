# Chatbot Cortex pour Snowflake

Ce projet est une application Streamlit qui sert d'interface de chat avec le service Cortex de Snowflake. Il permet de converser avec différents modèles d'IA, tout en sauvegardant l'historique des conversations dans une table Snowflake.

## Fonctionnalités principales
- Interface utilisateur interactive avec Streamlit
- Sélection du modèle Cortex (Claude, OpenAI, etc.)
- Réglage de la température de génération
- Historique des conversations stocké dans une table Snowflake
- Gestion multi-utilisateur (identification automatique)
- Reprise de conversation et gestion de sessions

## Prérequis
- Accès à un compte Snowflake avec Cortex activé
- Table `CHATBOT` dans Snowflake (créée automatiquement au premier lancement)
- Python 3.8+
- Packages : `streamlit`, `snowflake-snowpark-python`

## Installation
1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/linhto217/Chatbot.git
   cd Chatbot
   ```
2. Installez les dépendances :
   ```bash
   pip install streamlit snowflake-snowpark-python
   ```
3. Configurez vos identifiants Snowflake (via variables d'environnement ou profile Snowflake).

## Utilisation
Lancez l'application Streamlit :
```bash
streamlit run App.py
```

## Paramètres
- **Modèle Cortex** : Choisissez le modèle d'IA à utiliser.
- **Température** : Ajustez la créativité des réponses.
- **Nouvelle conversation** : Réinitialise l'historique pour démarrer un nouveau chat.

## Structure de la table `CHATBOT`
| Colonne           | Type           | Description                  |
|-------------------|----------------|------------------------------|
| conversation_id   | STRING         | Identifiant de conversation  |
| user_name         | STRING         | Utilisateur                  |
| timestamp         | TIMESTAMP_NTZ  | Date/heure du message        |
| role              | STRING         | Rôle (user/assistant/system) |
| content           | STRING         | Contenu du message           |

## Personnalisation
- Modifiez le prompt système par défaut dans `DEFAULT_SYSTEM_PROMPT`.
- Ajoutez ou retirez des modèles dans la liste `FALLBACK_MODELS`.

## Auteurs
- linhto217

## Licence
Ce projet est sous licence MIT.
