"""data_quality_indexing_audit_trail

Revision ID: a1b2c3d4e5f6
Revises: be68d3d26ac1
Create Date: 2026-03-29 01:31:25.000000

Implements issues #50, #51, #52:
  #50 – Validation rules and integrity constraints
       (slug unique lookup, is_archived soft-delete, review_status curation field)
  #51 – Indexing strategy for search and API queries
       (composite facet indexes, slug index, review_status index, ApiKey owner index)
  #52 – Audit trail for curation and restoration changes
       (curation_audit_log table)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'be68d3d26ac1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply data quality, indexing, and audit trail changes."""

    # -----------------------------------------------------------------------
    # Issue #50 – Validation rules and integrity constraints
    # -----------------------------------------------------------------------

    # Add slug for stable, URL-safe external references (also satisfies #51
    # slug-lookup index requirement).
    op.add_column(
        'font_samples',
        sa.Column('slug', sa.String(length=255), nullable=True),
    )
    op.create_index(
        'ix_font_samples_slug', 'font_samples', ['slug'], unique=True
    )

    # Soft-delete / archive support: mark a sample as archived rather than
    # hard-deleting it so that audit logs and referential integrity survive.
    op.add_column(
        'font_samples',
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='0'),
    )
    op.add_column(
        'font_samples',
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        'ix_font_samples_is_archived', 'font_samples', ['is_archived'], unique=False
    )

    # Curation review state (pending | approved | rejected | needs_review).
    op.add_column(
        'font_samples',
        sa.Column('review_status', sa.String(length=50), nullable=True,
                  server_default='pending'),
    )
    op.create_index(
        'ix_font_samples_review_status', 'font_samples', ['review_status'], unique=False
    )

    # -----------------------------------------------------------------------
    # Issue #51 – Indexing strategy
    # -----------------------------------------------------------------------

    # Index ApiKey.owner for integration-facing lookup patterns.
    op.create_index(
        'ix_api_keys_owner', 'api_keys', ['owner'], unique=False
    )

    # Denormalized review_status in the search projection for fast status
    # filtering without joining back to font_samples.
    op.add_column(
        'font_search_index',
        sa.Column('review_status', sa.String(length=50), nullable=True),
    )
    op.create_index(
        'ix_font_search_index_review_status',
        'font_search_index', ['review_status'], unique=False
    )

    # Composite facet indexes for common combined-filter query patterns.
    op.create_index(
        'ix_search_category_style',
        'font_search_index', ['font_category', 'style'], unique=False
    )
    op.create_index(
        'ix_search_restoration_rights',
        'font_search_index', ['restoration_status', 'rights_status'], unique=False
    )
    op.create_index(
        'ix_search_confidence_completeness',
        'font_search_index', ['confidence', 'completeness'], unique=False
    )
    op.create_index(
        'ix_search_review_status_glyph_count',
        'font_search_index', ['review_status', 'glyph_count'], unique=False
    )

    # -----------------------------------------------------------------------
    # Issue #52 – Audit trail for curation and restoration changes
    # -----------------------------------------------------------------------

    op.create_table(
        'curation_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        # Nullable FK so audit rows outlive hard-deleted font_samples.
        sa.Column('sample_id', sa.Integer(), nullable=True),
        sa.Column('actor', sa.String(length=255), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('field_name', sa.String(length=255), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['sample_id'], ['font_samples.id'], ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_curation_audit_log_id'),
        'curation_audit_log', ['id'], unique=False
    )
    op.create_index(
        op.f('ix_curation_audit_log_sample_id'),
        'curation_audit_log', ['sample_id'], unique=False
    )
    op.create_index(
        'ix_audit_sample_action',
        'curation_audit_log', ['sample_id', 'action'], unique=False
    )
    op.create_index(
        'ix_audit_created_at',
        'curation_audit_log', ['created_at'], unique=False
    )


def downgrade() -> None:
    """Revert data quality, indexing, and audit trail changes."""

    # Issue #52
    op.drop_index('ix_audit_created_at', table_name='curation_audit_log')
    op.drop_index('ix_audit_sample_action', table_name='curation_audit_log')
    op.drop_index(
        op.f('ix_curation_audit_log_sample_id'), table_name='curation_audit_log'
    )
    op.drop_index(
        op.f('ix_curation_audit_log_id'), table_name='curation_audit_log'
    )
    op.drop_table('curation_audit_log')

    # Issue #51 – composite indexes
    op.drop_index(
        'ix_search_review_status_glyph_count', table_name='font_search_index'
    )
    op.drop_index(
        'ix_search_confidence_completeness', table_name='font_search_index'
    )
    op.drop_index(
        'ix_search_restoration_rights', table_name='font_search_index'
    )
    op.drop_index('ix_search_category_style', table_name='font_search_index')
    op.drop_index(
        'ix_font_search_index_review_status', table_name='font_search_index'
    )
    op.drop_column('font_search_index', 'review_status')
    op.drop_index('ix_api_keys_owner', table_name='api_keys')

    # Issue #50
    op.drop_index('ix_font_samples_review_status', table_name='font_samples')
    op.drop_column('font_samples', 'review_status')
    op.drop_index('ix_font_samples_is_archived', table_name='font_samples')
    op.drop_column('font_samples', 'archived_at')
    op.drop_column('font_samples', 'is_archived')
    op.drop_index('ix_font_samples_slug', table_name='font_samples')
    op.drop_column('font_samples', 'slug')
