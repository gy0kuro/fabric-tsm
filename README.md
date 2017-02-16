## Scripts d'installation automatisée du client TSM
### Prerequis

- fabric
- ssh
- clefs déployées sur les clients

### Fonctionnement

Appeler le script après avoir renseigné la listes des hôtes cibles (env.roledef) via :

> fab tsm_client_install -f <script>.py
