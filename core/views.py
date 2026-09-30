from django.views.generic import TemplateView

class LandingPageView(TemplateView):
    """Public landing page. Template: public/landing.html. Context: none."""
    template_name = 'public/landing.html'

class PrivacyPolicyView(TemplateView):
    """Data privacy notice page (RA 10173)."""
    template_name = 'public/privacy_policy.html'
