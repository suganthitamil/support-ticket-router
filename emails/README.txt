Support Ticket Router — Sample Email Dataset
================================================

These are synthetic .eml email files created for development and testing.
They are not real customer emails.

Files:
- ticket_001_password_reset.eml
- ticket_002_service_outage.eml
- ticket_003_billing_dispute.eml
- ticket_004_feature_request.eml
- ticket_005_slow_application.eml
- ticket_006_account_access.eml

Suggested fields for your classifier:
- category: account_access, incident, billing, feature_request, performance
- urgency: low, medium, high, critical
- summary: short description of the issue
- route_to: support, engineering, billing, product

Treat urgency as a model prediction, not a ground-truth label. Review and adjust
the model's output before allowing any real ticket creation.
