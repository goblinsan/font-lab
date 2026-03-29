use font_lab_db::run_migrations;
use sqlx::sqlite::SqlitePoolOptions;
use tracing_subscriber::EnvFilter;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::try_from_default_env().unwrap_or_else(|_| "info".into()))
        .init();

    let args: Vec<String> = std::env::args().collect();
    let command = args.get(1).map(|s| s.as_str()).unwrap_or("help");

    match command {
        "migrate" => {
            let database_url = std::env::var("DATABASE_URL")
                .unwrap_or_else(|_| "sqlite:./font_lab.db?mode=rwc".into());
            let pool = SqlitePoolOptions::new()
                .max_connections(1)
                .connect(&database_url)
                .await?;
            run_migrations(&pool).await?;
            println!("Migrations complete.");
        }
        "seed-taxonomy" => {
            let database_url = std::env::var("DATABASE_URL")
                .unwrap_or_else(|_| "sqlite:./font_lab.db?mode=rwc".into());
            let pool = SqlitePoolOptions::new()
                .max_connections(1)
                .connect(&database_url)
                .await?;
            run_migrations(&pool).await?;
            seed_taxonomy(&pool).await?;
            println!("Taxonomy seeded.");
        }
        "help" | _ => {
            println!("font-lab CLI");
            println!();
            println!("Commands:");
            println!("  migrate         Run database migrations");
            println!("  seed-taxonomy   Seed taxonomy dimensions and terms");
            println!("  help            Show this help");
        }
    }

    Ok(())
}

async fn seed_taxonomy(pool: &sqlx::SqlitePool) -> anyhow::Result<()> {
    use font_lab_db::repo::taxonomy;

    let dimensions = vec![
        ("styles", "Style", "single", true, false, false),
        ("genres", "Genre", "single", true, false, false),
        ("themes", "Theme", "multi", true, false, false),
        ("moods", "Mood", "multi", true, false, false),
        ("categories", "Category", "single", true, false, false),
        ("use_cases", "Use Case", "multi", true, false, false),
        ("eras", "Era", "single", true, true, false),
        ("origin_contexts", "Origin", "single", true, false, false),
        ("construction_traits", "Construction Trait", "multi", true, false, false),
        ("visual_traits", "Visual Trait", "multi", true, false, false),
        ("restoration_statuses", "Restoration Status", "single", true, false, false),
        ("source_types", "Source Type", "single", true, false, false),
        ("rights_statuses", "Rights Status", "single", true, false, false),
    ];

    for (name, label, cardinality, filterable, sortable, required) in &dimensions {
        taxonomy::upsert_dimension(pool, name, label, cardinality, *filterable, *sortable, *required)
            .await?;
    }

    // Seed style terms
    let styles = ["Serif", "Sans-Serif", "Monospace", "Display", "Script", "Decorative", "Blackletter", "Slab Serif"];
    if let Some(dim) = taxonomy::get_dimension_by_name(pool, "styles").await? {
        for (i, style) in styles.iter().enumerate() {
            taxonomy::upsert_term(pool, dim.id, style, i as i32, &[], None).await?;
        }
    }

    // Seed categories
    let categories = ["Body Text", "Headline", "Logo", "UI", "Poster", "Signage", "Editorial"];
    if let Some(dim) = taxonomy::get_dimension_by_name(pool, "categories").await? {
        for (i, cat) in categories.iter().enumerate() {
            taxonomy::upsert_term(pool, dim.id, cat, i as i32, &[], None).await?;
        }
    }

    // Seed restoration statuses
    let statuses = ["Raw Scan", "Cleaned", "Segmented", "Outlined", "Kerned", "Hinted", "Complete", "Published", "Archived"];
    if let Some(dim) = taxonomy::get_dimension_by_name(pool, "restoration_statuses").await? {
        for (i, s) in statuses.iter().enumerate() {
            taxonomy::upsert_term(pool, dim.id, s, i as i32, &[], None).await?;
        }
    }

    // Seed rights statuses
    let rights = ["Public Domain", "Open Font License", "Commercial License", "Custom License", "Rights Unclear", "All Rights Reserved", "Orphan Work"];
    if let Some(dim) = taxonomy::get_dimension_by_name(pool, "rights_statuses").await? {
        for (i, r) in rights.iter().enumerate() {
            taxonomy::upsert_term(pool, dim.id, r, i as i32, &[], None).await?;
        }
    }

    Ok(())
}
