# Audo WordPress Template

This folder is the Audo-managed WordPress stack that should back the Coolify `wordpress-with-mariadb` service template.

It includes:

- `docker-compose.yml`: WordPress plus MariaDB with persistent volumes.
- `mu-plugins/audo-platform.php`: always-on Audo platform controls.
- `themes/audo-starter`: a small starter theme for clean first launches.

## Plan Environment

Set these on each generated service:

```bash
AUDO_SITE_ID=<site-record-id>
AUDO_SITE_DOMAIN=<slug>.getaudo.com
AUDO_SITE_PLAN=free
AUDO_ADS_ENABLED=true
```

For paid sites:

```bash
AUDO_SITE_PLAN=paid
AUDO_ADS_ENABLED=false
```

## Coolify Template Notes

The WordPress service must mount or copy:

- `/audo/mu-plugins/audo-platform.php` into `/var/www/html/wp-content/mu-plugins/audo-platform.php`
- `/audo/themes/audo-starter` into `/var/www/html/wp-content/themes/audo-starter`

The included compose file does that at container start and then hands off to the official WordPress entrypoint.
