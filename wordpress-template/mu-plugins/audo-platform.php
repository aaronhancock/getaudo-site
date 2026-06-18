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

function audo_free_page_limit(): int
{
    return max(1, (int) audo_env('AUDO_FREE_PAGE_LIMIT', '5'));
}

function audo_free_upload_limit_bytes(): int
{
    return max(10, (int) audo_env('AUDO_FREE_UPLOAD_LIMIT_MB', '250')) * 1024 * 1024;
}

function audo_free_page_count(): int
{
    $counts = wp_count_posts('page');
    $count = 0;

    foreach (['publish', 'future', 'draft', 'pending', 'private'] as $status) {
        $count += isset($counts->{$status}) ? (int) $counts->{$status} : 0;
    }

    return $count;
}

function audo_upload_usage_bytes(): int
{
    $upload = wp_get_upload_dir();
    $base = $upload['basedir'] ?? '';

    if (!$base || !is_dir($base)) {
        return 0;
    }

    $bytes = 0;
    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($base, FilesystemIterator::SKIP_DOTS)
    );

    foreach ($iterator as $file) {
        if ($file->isFile()) {
            $bytes += $file->getSize();
        }
    }

    return $bytes;
}

function audo_is_paid(): bool
{
    return audo_site_plan() === 'paid';
}

add_action('after_setup_theme', static function (): void {
    if (!defined('DISALLOW_FILE_EDIT')) {
        define('DISALLOW_FILE_EDIT', true);
    }
});

add_filter('xmlrpc_enabled', '__return_false');

add_action('init', static function (): void {
    if (!get_option('audo_initial_settings_applied')) {
        $title = audo_env('AUDO_SITE_TITLE');
        $adminEmail = audo_env('AUDO_ADMIN_EMAIL');

        if ($title !== '') {
            update_option('blogname', $title);
        }
        if (is_email($adminEmail)) {
            update_option('admin_email', $adminEmail);
            delete_option('new_admin_email');
        }
        update_option('audo_initial_settings_applied', '1', false);
    }

});

add_filter('wp_insert_post_data', static function (array $data, array $postarr): array {
    if (audo_is_paid() || ($data['post_type'] ?? '') !== 'page') {
        return $data;
    }

    if (in_array($data['post_status'] ?? '', ['auto-draft', 'trash'], true)) {
        return $data;
    }

    if (!empty($postarr['ID'])) {
        return $data;
    }

    if (audo_free_page_count() >= audo_free_page_limit()) {
        wp_die(
            esc_html(sprintf('The free Audo plan allows %d pages. Upgrade in Audo to add more pages.', audo_free_page_limit())),
            'Audo page limit',
            ['response' => 403]
        );
    }

    return $data;
}, 10, 2);

add_filter('wp_handle_upload_prefilter', static function (array $file): array {
    if (audo_is_paid()) {
        return $file;
    }

    $nextSize = audo_upload_usage_bytes() + (int) ($file['size'] ?? 0);
    if ($nextSize > audo_free_upload_limit_bytes()) {
        $file['error'] = sprintf(
            'The free Audo plan includes %d MB of media storage. Upgrade in Audo to upload more files.',
            (int) audo_env('AUDO_FREE_UPLOAD_LIMIT_MB', '250')
        );
    }

    return $file;
});

add_filter('user_has_cap', static function (array $allcaps): array {
    $alwaysBlocked = [
        'edit_plugins',
        'edit_themes',
        'unfiltered_html',
        'update_core',
    ];

    $freeBlocked = [
        'activate_plugins',
        'delete_plugins',
        'install_plugins',
        'update_plugins',
        'upload_plugins',
        'delete_themes',
        'install_themes',
        'update_themes',
        'upload_themes',
    ];

    foreach ($alwaysBlocked as $cap) {
        $allcaps[$cap] = false;
    }

    if (!audo_is_paid()) {
        foreach ($freeBlocked as $cap) {
            $allcaps[$cap] = false;
        }
    }

    return $allcaps;
});

add_action('admin_menu', static function (): void {
    if (audo_is_paid()) {
        return;
    }

    remove_menu_page('plugins.php');
    remove_submenu_page('themes.php', 'themes.php');
    remove_submenu_page('themes.php', 'theme-install.php');
}, 99);

add_action('admin_notices', static function (): void {
    if (!current_user_can('manage_options')) {
        return;
    }

    $domain = audo_env('AUDO_SITE_DOMAIN', wp_parse_url(home_url(), PHP_URL_HOST) ?: '');
    $plan = audo_site_plan() === 'paid' ? 'Paid hosting' : 'Free DIY hosting';
    $freeDetails = audo_is_paid()
        ? ''
        : sprintf(' Page limit: %d. Media limit: %d MB.', audo_free_page_limit(), (int) audo_env('AUDO_FREE_UPLOAD_LIMIT_MB', '250'));
    ?>
    <div class="notice notice-info">
        <p><strong>Audo:</strong> <?php echo esc_html($plan); ?> is active<?php echo $domain ? ' for ' . esc_html($domain) : ''; ?>.<?php echo esc_html($freeDetails); ?></p>
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
