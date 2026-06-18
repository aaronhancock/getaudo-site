<?php
declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}
?><!doctype html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<div class="site-shell">
    <header class="site-header">
        <a href="<?php echo esc_url(home_url('/')); ?>"><?php bloginfo('name'); ?></a>
        <span><?php bloginfo('description'); ?></span>
    </header>
    <main class="site-main">
        <?php if (have_posts()) : ?>
            <?php while (have_posts()) : the_post(); ?>
                <article <?php post_class('site-card'); ?>>
                    <h1><?php the_title(); ?></h1>
                    <?php the_content(); ?>
                </article>
            <?php endwhile; ?>
        <?php else : ?>
            <article class="site-card">
                <h1><?php bloginfo('name'); ?></h1>
                <p>Your Audo-managed WordPress site is ready. Start editing pages, themes, and content in WordPress admin.</p>
            </article>
        <?php endif; ?>
    </main>
    <footer class="site-footer">
        <span>&copy; <?php echo esc_html(gmdate('Y')); ?> <?php bloginfo('name'); ?></span>
    </footer>
</div>
<?php wp_footer(); ?>
</body>
</html>
