from django import forms

from apps.portfolio.models import Project


_INPUT_CLASSES = (
    "w-full rounded-2xl border border-slate-300/70 bg-white/80 px-4 py-2.5 "
    "text-sm text-slate-800 transition focus:outline-none focus:ring-2 focus:ring-brand-500 "
    "dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-100"
)
_TEXTAREA_CLASSES = _INPUT_CLASSES + " min-h-[140px]"
_FILE_INPUT_CLASSES = (
    "block w-full cursor-pointer rounded-2xl border border-dashed border-slate-300/70 "
    "bg-white/80 px-4 py-6 text-center text-sm text-slate-500 transition hover:border-brand-500 "
    "hover:text-brand-600 dark:border-slate-700 dark:bg-slate-900/70 dark:text-slate-300"
)
_CHECKBOX_CLASSES = (
    "h-4 w-4 rounded border-slate-300 text-brand-500 focus:ring-brand-500 "
    "dark:border-slate-600 dark:bg-slate-900"
)


class MultipleFileInput(forms.ClearableFileInput):
    """Custom widget that allows multiple file selection."""

    allow_multiple_selected = True

    def __init__(self, attrs=None):
        default_attrs = {"multiple": True}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class MultipleFileField(forms.FileField):
    """Custom field that handles multiple file uploads."""

    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
            return result
        return [single_file_clean(data, initial)]


class TailwindFormMixin:
    def _apply_tailwind(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.HiddenInput):
                continue
            classes = _INPUT_CLASSES
            placeholder = field.label
            if isinstance(widget, forms.Textarea):
                classes = _TEXTAREA_CLASSES
            elif isinstance(widget, (forms.ClearableFileInput, forms.FileInput)):
                classes = _FILE_INPUT_CLASSES
                placeholder = None
            elif isinstance(widget, forms.CheckboxInput):
                classes = _CHECKBOX_CLASSES
                placeholder = None
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {classes}".strip()
            if isinstance(widget, forms.ClearableFileInput):
                widget.attrs.setdefault("multiple", False)
            if placeholder:
                widget.attrs.setdefault("placeholder", placeholder)
            else:
                widget.attrs.pop("placeholder", None)


class TailwindForm(TailwindFormMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_tailwind()


class TailwindModelForm(TailwindFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_tailwind()


class PathAwareForm(TailwindForm):
    """Shared hidden field for tracking the current relative path."""

    current_path = forms.CharField(required=False, widget=forms.HiddenInput)
    storage_root = forms.CharField(required=False, widget=forms.HiddenInput)


class UploadFileForm(PathAwareForm):
    file = forms.FileField(label="Select file")


class CreateDirectoryForm(PathAwareForm):
    directory_name = forms.CharField(label="Folder name", max_length=255)


class DeleteEntryForm(PathAwareForm):
    target = forms.CharField(widget=forms.HiddenInput)


class ProjectForm(TailwindModelForm):
    class Meta:
        model = Project
        fields = [
            "title",
            "description",
            "technology_used",
            "live_site_url",
            "github_url",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class ProjectImageUploadForm(TailwindForm):
    images = MultipleFileField(
        label="Upload images",
        required=False,
        help_text="Select one or more images to upload. Supported formats: JPEG, PNG, WebP",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the multiple attribute is set
        self.fields["images"].widget.attrs.update(
            {"accept": "image/jpeg,image/png,image/webp,image/jpg", "multiple": True}
        )


class ProjectDeleteForm(TailwindForm):
    confirm = forms.BooleanField(
        required=True,
        initial=False,
        label="I understand this project will be permanently deleted",
    )


class ProjectImageDeleteForm(TailwindForm):
    image_id = forms.IntegerField(widget=forms.HiddenInput)


class MessageFilterForm(TailwindForm):
    query = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={"placeholder": "Filter by name or email"}),
    )
    timeframe = forms.ChoiceField(
        required=False,
        choices=(
            ("", "Any time"),
            ("7", "Last 7 days"),
            ("30", "Last 30 days"),
            ("365", "Last year"),
        ),
        label="Time frame",
    )
