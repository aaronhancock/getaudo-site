<?php
/**
 * Plugin Name: Audo Platform
 * Description: Always-on platform controls for Audo-managed WordPress sites.
 * Version: 0.1.0
 * Author: Audo
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

function audo_env(string $key, string $fallback = ''): string
{
    $value = getenv($key);
    if ($value === false || $value === '') {
        return $fallback;
    }

    return (string) $value;
}

function audo_bool_env(string $key, bool $fallback = false): bool
{
    $value = strtolower(audo_env($key, $fallback ? 'true' : 'false'));

    return in_array($value, ['1', 'true', 'yes', 'on'], true);
}

function audo_site_plan(): string
{
    return strtolower(audo_env('AUDO_SITE_PLAN', 'free')) === 'paid' ? 'paid' : 'free';
}

function audo_ads_enabled(): bool
{
    return audo_bool_env('AUDO_ADS_ENABLED', audo_site_plan() !== 'paid');
}

add_action('after_setup_theme', static function (): void {
    if (!defined('DISALLOW_FILE_EDIT')) {
        define('DISALLOW_FILE_EDIT', true);
    }
});

add_filter('xmlrpc_enabled', '__return_false');

add_action('admin_notices', static function (): void {
    if (!current_user_can('manage_options')) {
        return;
    }

    $domain = audo_env('AUDO_SITE_DOMAIN', wp_parse_url(home_url(), PHP_URL_HOST) ?: '');
    $plan = audo_site_plan() === 'paid' ? 'Paid hosting' : 'Free DIY hosting';
    ?>
    <div class="notice notice-info">
        <p><strong>Audo:</strong> <?php echo esc_html($plan); ?> is active<?php echo $domain ? ' for ' . esc_html($domain) : ''; ?>.</p>
    </div>
    <?php
});

add_action('wp_footer', static function (): void {
    if (!audo_ads_enabled() || is_admin()) {
        return;
    }
    ?>
    <aside class="audo-free-site-badge" aria-label="Audo free hosting">
        <span>Hosted on Audo free DIY WordPress</span>
        <a href="https://getaudo.com" rel="noopener">Create your site</a>
    </aside>
    <style>
        .audo-free-site-badge {
            position: fixed;
            right: 16px;
            bottom: 16px;
            z-index: 99999;
            display: flex;
            gap: 10px;
            align-items: center;
            max-width: min(420px, calc(100vw - 32px));
            padding: 10px 12px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 8px;
            background: #101815;
            color: #eff8f2;
            box-shadow: 0 12px 30px rgba(16, 24, 21, 0.2);
            font: 700 13px/1.3 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .audo-free-site-badge a {
            color: #8be0ba;
            text-decoration: none;
        }
        @media (max-width: 560px) {
            .audo-free-site-badge {
                left: 12px;
                right: 12px;
                bottom: 12px;
                justify-content: space-between;
            }
        }
    </style>
    <?php
});

add_action('wp_dashboard_setup', static function (): void {
    wp_add_dashboard_widget('audo_dashboard_widget', 'Audo hosting', static function (): void {
        $domain = audo_env('AUDO_SITE_DOMAIN', wp_parse_url(home_url(), PHP_URL_HOST) ?: '');
        $plan = audo_site_plan() === 'paid' ? 'Paid' : 'Free';
        ?>
        <p><strong>Plan:</strong> <?php echo esc_html($plan); ?></p>
        <?php if ($domain) : ?>
            <p><strong>Primary URL:</strong> <?php echo esc_html($domain); ?></p>
        <?php endif; ?>
        <p>Manage domains, backups, and hosting from your Audo console.</p>
        <?php
    });
});
