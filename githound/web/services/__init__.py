"""External services and integrations for GitHound web interface.

This module provides service layer components for external integrations and
third-party service interactions used by the GitHound web interface.

Key Services:
    - AuthService: Authentication and authorization service integration
    - WebhookService: Webhook management and delivery
    - NotificationService: Real-time notifications and alerts
    - ExportService: Data export and format conversion
    - CacheService: Distributed caching and session management

These services abstract external dependencies and provide clean interfaces
for the web application to interact with external systems while maintaining
loose coupling and testability.
"""
