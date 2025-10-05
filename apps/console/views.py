from __future__ import annotations

import mimetypes
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import SuspiciousFileOperation
from django.http import FileResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils._os import safe_join
from django.views.generic import TemplateView, View

from .forms import CreateDirectoryForm, DeleteEntryForm, UploadFileForm


class StaffAuthenticationForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        base_classes = (
            "w-full rounded-2xl border border-slate-300/70 bg-white/80 px-4 py-2.5 "
            "text-sm text-slate-800 transition focus:outline-none focus:ring-2 focus:ring-brand-500 "
            "dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-100"
        )
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{existing} {base_classes}".strip()
            field.widget.attrs.setdefault("placeholder", field.label)

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise forms.ValidationError(
                "Only staff users can sign in to the console.",
                code="not_staff",
            )


class StaffOnlyMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = reverse_lazy("console:login")

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(
                self.request, "You do not have permission to access the console."
            )
            return redirect("console:login")
        return super().handle_no_permission()


class ConsoleLoginView(LoginView):
    form_class = StaffAuthenticationForm
    template_name = "console/login.html"
    redirect_authenticated_user = True
    success_url = reverse_lazy("console:file-manager")


class ConsoleLogoutView(LogoutView):
    next_page = reverse_lazy("console:login")


class FileManagerView(StaffOnlyMixin, TemplateView):
    template_name = "console/file_manager.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_dir = _static_root()
        current_relative = (self.request.GET.get("path") or "").strip()
        current_dir = _resolve_path(base_dir, current_relative)

        if not current_dir.exists() or not current_dir.is_dir():
            messages.warning(
                self.request, "Folder not found. Showing the static root instead."
            )
            current_relative = ""
            current_dir = base_dir

        entries = []
        for entry in sorted(
            current_dir.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())
        ):
            stat = entry.stat()
            entries.append(
                {
                    "name": entry.name,
                    "path": "" if entry == base_dir else _to_relative(entry, base_dir),
                    "is_dir": entry.is_dir(),
                    "size": None if entry.is_dir() else stat.st_size,
                    "modified": timezone.localtime(
                        datetime.fromtimestamp(
                            stat.st_mtime, tz=timezone.get_current_timezone()
                        )
                    ),
                }
            )

        breadcrumbs = _build_breadcrumbs(current_relative)
        parent_path = _parent_path(current_relative)

        context.update(
            {
                "current_path": current_relative,
                "entries": entries,
                "breadcrumbs": breadcrumbs,
                "parent_path": parent_path,
                "upload_form": UploadFileForm(
                    initial={"current_path": current_relative}
                ),
                "mkdir_form": CreateDirectoryForm(
                    initial={"current_path": current_relative}
                ),
            }
        )
        return context


class FileUploadView(StaffOnlyMixin, View):
    def post(self, request):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            current_path = form.cleaned_data["current_path"] or ""
            uploaded_file = form.cleaned_data["file"]
            base_dir = _static_root()
            destination_dir = _resolve_path(base_dir, current_path)
            destination_dir.mkdir(parents=True, exist_ok=True)

            file_name = Path(uploaded_file.name).name
            if not file_name:
                messages.error(request, "Could not determine a valid file name.")
                return _redirect_to_manager(current_path)

            destination_path = destination_dir / file_name
            if destination_path.exists():
                messages.warning(request, f"Replacing existing file {file_name}.")

            with destination_path.open("wb+") as target:
                for chunk in uploaded_file.chunks():
                    target.write(chunk)

            messages.success(request, f"Uploaded {file_name}.")
            return _redirect_to_manager(current_path)

        _add_form_errors(request, form)
        return _redirect_to_manager(request.POST.get("current_path", ""))


class CreateDirectoryView(StaffOnlyMixin, View):
    def post(self, request):
        form = CreateDirectoryForm(request.POST)
        if form.is_valid():
            current_path = form.cleaned_data["current_path"] or ""
            folder_name = form.cleaned_data["directory_name"].strip()
            if not folder_name:
                messages.error(request, "Folder name cannot be empty.")
                return _redirect_to_manager(current_path)
            if any(sep in folder_name for sep in ("/", "\\")):
                messages.error(request, "Folder name cannot contain path separators.")
                return _redirect_to_manager(current_path)
            if Path(folder_name).name != folder_name:
                messages.error(request, "Folder name is invalid.")
                return _redirect_to_manager(current_path)

            base_dir = _static_root()
            destination_dir = _resolve_path(base_dir, current_path)
            new_folder = destination_dir / folder_name

            if new_folder.exists():
                messages.warning(request, f"{folder_name} already exists.")
            else:
                new_folder.mkdir(parents=True, exist_ok=False)
                messages.success(request, f"Created folder {folder_name}.")

            return _redirect_to_manager(current_path)

        _add_form_errors(request, form)
        return _redirect_to_manager(request.POST.get("current_path", ""))


class DeleteEntryView(StaffOnlyMixin, View):
    def post(self, request):
        form = DeleteEntryForm(request.POST)
        if form.is_valid():
            current_path = form.cleaned_data["current_path"] or ""
            target_relative = form.cleaned_data["target"]
            base_dir = _static_root()
            target_path = _resolve_path(base_dir, target_relative)

            if target_path == base_dir:
                messages.error(request, "Cannot delete the static root folder.")
                return _redirect_to_manager(current_path)

            try:
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                    messages.success(request, f"Deleted folder {target_path.name}.")
                elif target_path.exists():
                    target_path.unlink()
                    messages.success(request, f"Deleted file {target_path.name}.")
                else:
                    messages.warning(request, "The selected item no longer exists.")
            except OSError as exc:
                messages.error(request, f"Unable to delete {target_path.name}: {exc}")

            return _redirect_to_manager(current_path)

        _add_form_errors(request, form)
        return _redirect_to_manager(request.POST.get("current_path", ""))


class DownloadFileView(StaffOnlyMixin, View):
    def get(self, request):
        relative_path = (request.GET.get("path") or "").strip()
        if not relative_path:
            raise Http404

        base_dir = _static_root()
        file_path = _resolve_path(base_dir, relative_path)

        if not file_path.exists() or not file_path.is_file():
            raise Http404

        content_type, _ = mimetypes.guess_type(file_path.name)
        return FileResponse(
            file_path.open("rb"),
            as_attachment=True,
            filename=file_path.name,
            content_type=content_type or "application/octet-stream",
        )


def _static_root() -> Path:
    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root:
        base_dir = Path(static_root)
    else:
        static_dirs = getattr(settings, "STATICFILES_DIRS", [])
        base_dir = (
            Path(static_dirs[0]) if static_dirs else Path(settings.BASE_DIR) / "static"
        )
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir.resolve()


def _resolve_path(base_dir: Path, relative: str) -> Path:
    relative = (relative or "").strip().replace("\\", "/")
    if not relative:
        return base_dir
    try:
        resolved = Path(safe_join(str(base_dir), relative))
    except (SuspiciousFileOperation, ValueError):
        raise Http404("Invalid path")
    return resolved.resolve()


def _to_relative(path: Path, base_dir: Path) -> str:
    return path.relative_to(base_dir).as_posix()


def _parent_path(relative: str) -> str:
    relative = (relative or "").strip().strip("/")
    if not relative:
        return ""
    parts = [part for part in relative.split("/") if part]
    return "/".join(parts[:-1])


def _build_breadcrumbs(relative: str):
    crumbs = [{"label": "static", "path": ""}]
    if not relative:
        return crumbs
    parts = [part for part in relative.split("/") if part]
    path_so_far = []
    for part in parts:
        path_so_far.append(part)
        crumbs.append({"label": part, "path": "/".join(path_so_far)})
    return crumbs


def _redirect_to_manager(relative: str):
    url = reverse("console:file-manager")
    relative = (relative or "").strip()
    if relative:
        url = f"{url}?{urlencode({'path': relative})}"
    return redirect(url)


def _add_form_errors(request, form):
    if form.errors:
        for _, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)
