from django import forms


class PathAwareForm(forms.Form):
    """Shared hidden field for tracking the current relative path."""

    current_path = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_tailwind_attrs()

    def _apply_tailwind_attrs(self):
        base_classes = (
            "w-full rounded-2xl border border-slate-300/70 bg-white/80 px-4 py-2.5 "
            "text-sm text-slate-800 transition focus:outline-none focus:ring-2 "
            "focus:ring-brand-500 dark:border-slate-700 dark:bg-slate-900/80 "
            "dark:text-slate-100"
        )
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.HiddenInput):
                continue
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {base_classes}".strip()
            widget.attrs.setdefault("placeholder", field.label)


class UploadFileForm(PathAwareForm):
    file = forms.FileField(label="Select file")


class CreateDirectoryForm(PathAwareForm):
    directory_name = forms.CharField(label="Folder name", max_length=255)


class DeleteEntryForm(PathAwareForm):
    target = forms.CharField(widget=forms.HiddenInput)
