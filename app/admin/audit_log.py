from datetime import datetime
from typing import Any, Optional

from fastapi import Request
from sqladmin import ModelView
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload, joinedload

from app.models import AuditLog, AuditAction, User


class AuditLogAdmin(ModelView, model=AuditLog):
    """Admin interface for viewing audit logs."""
    
    # Display columns
    column_list = [
        AuditLog.id,
        AuditLog.action,
        AuditLog.user,
        AuditLog.target_type,
        AuditLog.target_id,
        AuditLog.status_code,
        AuditLog.ip_address,
        AuditLog.created_at,
    ]
    
    # Columns to include in the detail view
    column_details_list = [
        'id',
        'action',
        'user',
        'target_type',
        'target_id',
        'status_code',
        'ip_address',
        'user_agent',
        'error_message',
        'metadata_',
        'created_at',
    ]
    
    # Columns that can be used for searching
    column_searchable_list = [
        'action',
        'target_type',
        'ip_address',
        'user_agent',
        'error_message',
    ]
    
    # Columns that can be used for filtering
    column_filters = [
        'action',
        'target_type',
        'status_code',
        'created_at',
        'user.username',
    ]
    
    # Default sort order (newest first)
    column_default_sort = [(AuditLog.created_at, True)]
    
    # Form options (read-only)
    can_create = False
    can_edit = False
    can_delete = False
    
    # Page size for list view
    page_size = 50
    
    # Enable export
    can_export = True
    export_types = ['csv', 'xlsx']
    
    # Enable view details
    can_view_details = True
    
    # Customize the list view
    column_formatters = {
        'created_at': lambda m, a: m.created_at.strftime('%Y-%m-%d %H:%M:%S') if m.created_at else None,
        'action': lambda m, a: m.action.value.upper() if m.action else '',
        'status_code': lambda m, a: f"<span class='badge bg-{'success' if 200 <= m.status_code < 300 else 'warning' if 300 <= m.status_code < 400 else 'danger' if m.status_code >= 400 else 'secondary'}'>{m.status_code}</span>" if m.status_code else '',
    }
    
    # Custom labels
    column_labels = {
        'id': 'ID',
        'action': 'Action',
        'user': 'User',
        'target_type': 'Target Type',
        'target_id': 'Target ID',
        'status_code': 'Status',
        'ip_address': 'IP Address',
        'user_agent': 'User Agent',
        'error_message': 'Error Message',
        'metadata_': 'Metadata',
        'created_at': 'Timestamp',
    }
    
    # Custom sort for enum fields
    column_sortable_list = [
        'action',
        'target_type',
        'status_code',
        'created_at',
    ]
    
    # Custom query to include related data
    async def get_list_query(self, *args, **kwargs):
        stmt = select(self.model).options(
            selectinload(AuditLog.user),
        ).order_by(desc(AuditLog.created_at))
        return stmt
    
    # Custom query for detail view
    async def get_detail_query(self, *args, **kwargs):
        stmt = select(self.model).options(
            joinedload(AuditLog.user),
        )
        return stmt
    
    # Format the metadata for display
    def on_model_change(self, data, model, is_created, **kwargs):
        # This is a read-only view, but we'll keep this for consistency
        pass
    
    # Add custom CSS for status badges
    def get_css_extra(self) -> str:
        return """
        <style>
            .badge {
                padding: 0.35em 0.65em;
                font-size: 0.75em;
                font-weight: 700;
                line-height: 1;
                color: #fff;
                text-align: center;
                white-space: nowrap;
                vertical-align: baseline;
                border-radius: 0.25rem;
            }
            .badge.bg-success { background-color: #198754; }
            .badge.bg-warning { background-color: #ffc107; color: #000; }
            .badge.bg-danger { background-color: #dc3545; }
            .badge.bg-secondary { background-color: #6c757d; }
            
            /* Make metadata more readable */
            .json-viewer {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 0.25rem;
                padding: 1rem;
                max-height: 400px;
                overflow-y: auto;
                font-family: monospace;
                white-space: pre;
            }
        </style>
        """
    
    # Add custom JavaScript for JSON pretty-printing
    def get_js_extra(self) -> str:
        return """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Format JSON in the metadata column
            document.querySelectorAll('.json-viewer').forEach(el => {
                try {
                    const json = JSON.parse(el.textContent);
                    el.textContent = JSON.stringify(json, null, 2);
                } catch (e) {
                    console.error('Failed to parse JSON:', e);
                }
            });
            
            // Add click handler for viewing full details
            document.querySelectorAll('.view-details-btn').forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    const logId = this.dataset.logId;
                    // Show a modal with the full log details
                    alert('Viewing details for log #' + logId);
                });
            });
        });
        </script>
        """
