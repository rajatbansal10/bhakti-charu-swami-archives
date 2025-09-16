from datetime import datetime
from typing import Optional, Any

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from sqladmin import ModelView
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload

from app.models import Asset, AssetType, AssetStatus, User
from app.utils.storage import get_presigned_url


class AssetAdmin(ModelView, model=Asset):
    """Admin interface for managing assets."""
    
    # Display columns
    column_list = [
        Asset.id,
        Asset.filename,
        Asset.type,
        Asset.category,
        Asset.content_type,
        Asset.size_bytes,
        Asset.status,
        Asset.is_public,
        Asset.uploader,
        Asset.created_at,
    ]
    
    # Columns to include in the edit form
    form_columns = [
        'filename',
        'title',
        'description',
        'type',
        'category',
        'tags',
        'status',
        'is_public',
        'metadata_',
        'uploader',
    ]
    
    # Columns that can be used for searching
    column_searchable_list = [
        Asset.filename,
        Asset.title,
        Asset.description,
        Asset.category,
    ]
    
    # Columns that can be used for filtering
    column_filters = [
        Asset.type,
        Asset.status,
        Asset.is_public,
        Asset.created_at,
        'uploader.username',
    ]
    
    # Default sort order
    column_default_sort = [(Asset.created_at, True)]
    
    # Form options
    form_excluded_columns = [
        'key',
        'checksum_sha256',
    ]
    
    # Field options
    form_args = {
        'type': {
            'choices': [(t.value, t.name.lower().capitalize()) for t in AssetType],
        },
        'status': {
            'choices': [(s.value, s.name.lower().capitalize()) for s in AssetStatus],
        },
        'metadata_': {
            'render_kw': {
                'rows': 10,
                'class': 'json-editor',
            }
        },
    }
    
    # Customize the form
    form_widget_args = {
        'created_at': {
            'readonly': True,
        },
        'updated_at': {
            'readonly': True,
        },
        'content_type': {
            'readonly': True,
        },
        'size_bytes': {
            'readonly': True,
        },
    }
    
    # Page size for list view
    page_size = 25
    
    # Enable export
    can_export = True
    export_types = ['csv', 'xlsx']
    
    # Enable view details
    can_view_details = True
    
    # Customize the detail view
    column_details_list = [
        'id',
        'key',
        'filename',
        'title',
        'description',
        'type',
        'content_type',
        'size_bytes',
        'category',
        'tags',
        'status',
        'is_public',
        'checksum_sha256',
        'metadata_',
        'uploader',
        'created_at',
        'updated_at',
    ]
    
    # Customize the list view
    column_formatters = {
        'created_at': lambda m, a: m.created_at.strftime('%Y-%m-%d %H:%M:%S') if m.created_at else None,
        'updated_at': lambda m, a: m.updated_at.strftime('%Y-%m-%d %H:%M:%S') if m.updated_at else None,
        'size_bytes': lambda m, a: f"{m.size_bytes / (1024 * 1024):.2f} MB" if m.size_bytes else '0 B',
        'type': lambda m, a: m.type.value.upper() if m.type else '',
        'status': lambda m, a: m.status.value.upper() if m.status else '',
    }
    
    # Custom labels
    column_labels = {
        'id': 'ID',
        'key': 'Storage Key',
        'filename': 'Filename',
        'title': 'Title',
        'description': 'Description',
        'type': 'Type',
        'content_type': 'Content Type',
        'size_bytes': 'Size',
        'category': 'Category',
        'tags': 'Tags',
        'status': 'Status',
        'is_public': 'Is Public',
        'checksum_sha256': 'SHA-256 Checksum',
        'metadata_': 'Metadata',
        'uploader': 'Uploaded By',
        'created_at': 'Created At',
        'updated_at': 'Updated At',
    }
    
    # Custom sort for enum fields
    column_sortable_list = [
        'filename',
        'type',
        'status',
        'is_public',
        'created_at',
        'updated_at',
    ]
    
    # Custom query to include related data
    async def get_list_query(self, *args, **kwargs):
        stmt = select(self.model).options(
            selectinload(Asset.uploader),
        )
        return stmt
    
    # Custom query for detail view
    async def get_detail_query(self, *args, **kwargs):
        stmt = select(self.model).options(
            joinedload(Asset.uploader),
        )
        return stmt
    
    # Handle model changes
    async def on_model_change(self, data, model, is_created, **kwargs):
        # Update timestamps
        if is_created:
            model.created_at = datetime.utcnow()
        model.updated_at = datetime.utcnow()
    
    # Add custom actions to the list view
    column_extra_row_actions = [
        {
            'name': 'download',
            'label': 'Download',
            'icon': 'fa fa-download',
            'class': 'btn btn-sm btn-outline-primary',
            'onclick': 'window.open(`/api/v1/assets/${row.id}/download`, `_blank`)',
        },
        {
            'name': 'preview',
            'label': 'Preview',
            'icon': 'fa fa-eye',
            'class': 'btn btn-sm btn-outline-info',
            'onclick': 'window.open(`/assets/${row.id}/preview`, `_blank`)',
            'condition': lambda m: m.type in [AssetType.IMAGE, AssetType.PDF, AssetType.VIDEO],
        },
    ]
    
    # Add custom JavaScript for the form
    def get_js_extra(self) -> str:
        return """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize JSON editor for metadata
            const metadataEditor = document.querySelector('textarea[name="metadata_"]');
            if (metadataEditor) {
                const editor = new JSONEditor(
                    metadataEditor.closest('.form-group'),
                    { mode: 'code' },
                    JSON.parse(metadataEditor.value || '{}')
                );
                
                // Update the textarea when the form is submitted
                const form = metadataEditor.closest('form');
                if (form) {
                    form.addEventListener('submit', function() {
                        try {
                            metadataEditor.value = JSON.stringify(editor.get());
                        } catch (e) {
                            console.error('Invalid JSON in metadata editor:', e);
                        }
                    });
                }
            }
        });
        </script>
        """
    
    # Add custom CSS for the form
    def get_css_extra(self) -> str:
        return """
        <style>
            .json-editor {
                font-family: monospace;
                min-height: 200px;
            }
            .jsoneditor {
                border: 1px solid #ced4da;
                border-radius: 0.25rem;
            }
        </style>
        """
