<?php
declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

add_action('after_setup_theme', static function (): void {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('responsive-embeds');
    add_theme_support('wp-block-styles');
    add_theme_support('editor-styles');
    add_editor_style('style.css');
});

add_action('wp_enqueue_scripts', static function (): void {
    wp_enqueue_style('audo-starter-style', get_stylesheet_uri(), [], wp_get_theme()->get('Version'));
});
