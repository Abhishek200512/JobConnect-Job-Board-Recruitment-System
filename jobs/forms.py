"""Job posting form."""
from django import forms
from .models import Job, Category


class JobForm(forms.ModelForm):
    skills = forms.CharField(
        required=False,
        help_text="Comma separated, e.g. Python, Django, SQL",
        widget=forms.TextInput(attrs={"placeholder": "Python, Django, SQL"}),
    )

    class Meta:
        model = Job
        fields = [
            "title", "category", "location", "job_type", "work_mode", "experience",
            "salary_min", "salary_max", "openings", "description",
            "responsibilities", "qualifications", "benefits", "skills",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "responsibilities": forms.Textarea(attrs={"rows": 4, "placeholder": "One responsibility per line"}),
            "qualifications": forms.Textarea(attrs={"rows": 4, "placeholder": "One qualification per line"}),
            "benefits": forms.Textarea(attrs={"rows": 3, "placeholder": "One benefit per line"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ["title", "location", "description"]:
            self.fields[name].widget.attrs.setdefault("class", "form-control")
        self.fields["category"].queryset = Category.objects.all()

    def clean_skills(self):
        raw = self.cleaned_data.get("skills", "")
        return [s.strip() for s in raw.split(",") if s.strip()][:20]

    def clean(self):
        cleaned = super().clean()
        smin = cleaned.get("salary_min")
        smax = cleaned.get("salary_max")
        if smin and smax and smin > smax:
            raise forms.ValidationError("Minimum salary cannot exceed maximum salary.")
        return cleaned
