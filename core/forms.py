from django import forms

class CandidateForm(forms.Form):
    full_name = forms.CharField(max_length=100, required=False, widget=forms.HiddenInput())
    first_name = forms.CharField(max_length=50, required=False)
    last_name = forms.CharField(max_length=50, required=False)
    email = forms.EmailField(required=True)  # Now required
    phone = forms.CharField(max_length=20, required=True)  # Now required
    linkedin = forms.URLField(required=False)
    github = forms.URLField(required=True)
    image = forms.ImageField(required=True)
    resume = forms.FileField(required=True)  # Now required
    user_email = forms.EmailField(required=True, label="Your Email")

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get("first_name", "")
        last_name = cleaned_data.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip()
        cleaned_data["full_name"] = full_name
        return cleaned_data

