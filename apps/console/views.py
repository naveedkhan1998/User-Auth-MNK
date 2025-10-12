from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from urllib.parse import urlencode

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import SuspiciousFileOperation
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils._os import safe_join
from django.views.generic import TemplateView, View

from apps.open_messages.models import Message
from apps.portfolio.models import Image, Project

from .forms import (
    CreateDirectoryForm,
    DeleteEntryForm,
    MessageFilterForm,
    ProjectDeleteForm,
    ProjectForm,
    ProjectImageUploadForm,
    UploadFileForm,
)
from .storage_backends import get_storage_backend

DEFAULT_STORAGE_ROOT = "static"
STORAGE_ROOTS = {
    "static": {
        "key": "static",
        "label": "Static files",
        "root_label": "Static",
        "description": "Manage build-time assets such as CSS, JavaScript, and images stored in STATIC_ROOT.",
    },
    "media": {
        "key": "media",
        "label": "Media files",
        "root_label": "Media",
        "description": "Manage uploaded media content stored in MEDIA_ROOT (user uploads, images, documents).",
    },
}


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
    template_name = "console/file_manager/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_path = (self.request.GET.get("path") or "").strip()
        storage_root = _normalize_storage_root(self.request.GET.get("storage"))
        storage = get_storage_backend(storage_root)

        # Get entries from storage backend (works for both local and GCS)
        try:
            entries = storage.list_entries(current_path)
        except Exception as e:
            messages.error(self.request, f"Error listing files: {str(e)}")
            entries = []
            current_path = ""

        # Build breadcrumbs
        breadcrumbs = _build_breadcrumbs(storage_root, current_path)
        parent_path = storage.get_parent_path(current_path)

        # Determine storage type for UI
        storage_type = "GCS" if "GCS" in type(storage).__name__ else "Local"
        storage_meta = STORAGE_ROOTS[storage_root]
        storage_options = list(STORAGE_ROOTS.values())
        entries_data = []
        for entry in entries:
            entries_data.append(
                {
                    "name": entry.name,
                    "rel_path": entry.rel_path,
                    "is_dir": entry.is_dir,
                    "size": entry.size,
                    "modified": entry.modified,
                    "url": _build_entry_url(self.request, storage, entry),
                }
            )

        context.update(
            {
                "storage_root": storage_root,
                "storage_meta": storage_meta,
                "storage_options": storage_options,
                "current_path": current_path,
                "entries": entries_data,
                "breadcrumbs": breadcrumbs,
                "parent_path": parent_path,
                "storage_type": storage_type,
                "upload_form": UploadFileForm(
                    initial={
                        "current_path": current_path,
                        "storage_root": storage_root,
                    }
                ),
                "mkdir_form": CreateDirectoryForm(
                    initial={
                        "current_path": current_path,
                        "storage_root": storage_root,
                    }
                ),
            }
        )
        return context


class FileUploadView(StaffOnlyMixin, View):
    def post(self, request):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            current_path = form.cleaned_data["current_path"] or ""
            storage_root = _normalize_storage_root(
                 form.cleaned_data.get("storage_root")
             )
            uploaded_file = form.cleaned_data["file"]
            storage = get_storage_backend(storage_root)

            file_name = Path(uploaded_file.name).name
            if not file_name:
                messages.error(request, "Could not determine a valid file name.")
                return _redirect_to_manager(current_path, storage_root)

            # Build the target path
            target_path = (
                f"{current_path}/{file_name}".strip("/") if current_path else file_name
            )

            # Read file content
            file_content = uploaded_file.read()
            content_type = uploaded_file.content_type or "application/octet-stream"

            try:
                storage.upload_file(target_path, file_content, content_type)
                messages.success(request, f"Uploaded {file_name}.")
            except Exception as e:
                messages.error(request, f"Error uploading file: {str(e)}")

            return _redirect_to_manager(current_path, storage_root)

        _add_form_errors(request, form)
        return _redirect_to_manager(
            request.POST.get("current_path", ""),
            _normalize_storage_root(request.POST.get("storage_root")),
        )


class CreateDirectoryView(StaffOnlyMixin, View):
    def post(self, request):
        form = CreateDirectoryForm(request.POST)
        if form.is_valid():
            current_path = form.cleaned_data["current_path"] or ""
            storage_root = _normalize_storage_root(
                form.cleaned_data.get("storage_root")
            )
            folder_name = form.cleaned_data["directory_name"].strip()

            if not folder_name:
                messages.error(request, "Folder name cannot be empty.")
                return _redirect_to_manager(current_path, storage_root)
            if any(sep in folder_name for sep in ("/", "\\")):
                messages.error(request, "Folder name cannot contain path separators.")
                return _redirect_to_manager(current_path, storage_root)
            if Path(folder_name).name != folder_name:
                messages.error(request, "Folder name is invalid.")
                return _redirect_to_manager(current_path, storage_root)

            storage = get_storage_backend(storage_root)
            target_path = (
                f"{current_path}/{folder_name}".strip("/")
                if current_path
                else folder_name
            )

            try:
                storage.create_directory(target_path)
                messages.success(request, f"Created folder {folder_name}.")
            except FileExistsError:
                messages.warning(request, f"{folder_name} already exists.")
            except Exception as e:
                messages.error(request, f"Error creating folder: {str(e)}")

            return _redirect_to_manager(current_path, storage_root)

        _add_form_errors(request, form)
        return _redirect_to_manager(
            request.POST.get("current_path", ""),
            _normalize_storage_root(request.POST.get("storage_root")),
        )


class DeleteEntryView(StaffOnlyMixin, View):
    def post(self, request):
        form = DeleteEntryForm(request.POST)
        if form.is_valid():
            current_path = form.cleaned_data["current_path"] or ""
            storage_root = _normalize_storage_root(
                form.cleaned_data.get("storage_root")
            )
            target_relative = form.cleaned_data["target"]

            if not target_relative:
                messages.error(request, "Cannot delete the root folder.")
                return _redirect_to_manager(current_path, storage_root)

            storage = get_storage_backend(storage_root)

            try:
                storage.delete(target_relative)
                messages.success(request, f"Deleted {Path(target_relative).name}.")
            except Exception as exc:
                messages.error(request, f"Unable to delete: {exc}")

            return _redirect_to_manager(current_path, storage_root)

        _add_form_errors(request, form)
        return _redirect_to_manager(
            request.POST.get("current_path", ""),
            _normalize_storage_root(request.POST.get("storage_root")),
        )


class DownloadFileView(StaffOnlyMixin, View):
    def get(self, request):
        relative_path = (request.GET.get("path") or "").strip()
        if not relative_path:
            raise Http404
        storage_root = _normalize_storage_root(request.GET.get("storage"))

        storage = get_storage_backend(storage_root)

        try:
            content, content_type = storage.download_file(relative_path)
            from django.http import HttpResponse

            response = HttpResponse(content, content_type=content_type)
            response["Content-Disposition"] = (
                f'attachment; filename="{Path(relative_path).name}"'
            )
            return response
        except Exception as e:
            raise Http404(f"File not found: {e}")

    def post(self, request):
        # Support POST method with 'target' parameter from forms
        relative_path = (request.POST.get("target") or "").strip()
        storage_root = _normalize_storage_root(request.POST.get("storage_root"))
        if not relative_path:
            raise Http404

        storage = get_storage_backend(storage_root)

        try:
            content, content_type = storage.download_file(relative_path)
            from django.http import HttpResponse

            response = HttpResponse(content, content_type=content_type)
            response["Content-Disposition"] = (
                f'attachment; filename="{Path(relative_path).name}"'
            )
            return response
        except Exception as e:
            raise Http404(f"File not found: {e}")


class ProjectListView(StaffOnlyMixin, TemplateView):
    template_name = "console/projects/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        projects = list(
            Project.objects.prefetch_related("images").order_by("-created_at")
        )
        context.update({"projects": projects, "project_count": len(projects)})
        return context


class ProjectCreateView(StaffOnlyMixin, TemplateView):
    template_name = "console/projects/create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("form", ProjectForm())
        context.setdefault("image_form", ProjectImageUploadForm())
        return context

    def post(self, request, *args, **kwargs):
        form = ProjectForm(request.POST)
        image_form = ProjectImageUploadForm(request.POST, request.FILES)

        if form.is_valid():
            project = form.save()

            # Handle multiple file uploads
            uploaded_files = request.FILES.getlist("images")
            added = 0

            for uploaded_file in uploaded_files:
                try:
                    # Create Image instance and save
                    image = Image(file=uploaded_file)
                    image.save()  # This triggers compression in the model's save method
                    project.images.add(image)
                    added += 1
                except Exception as e:
                    messages.warning(
                        request, f"Could not upload {uploaded_file.name}: {str(e)}"
                    )

            if added:
                messages.success(
                    request,
                    f"Project created with {added} image{'s' if added != 1 else ''}.",
                )
            else:
                messages.success(request, "Project created successfully.")

            return redirect("console:project-detail", pk=project.pk)

        # If form is invalid
        messages.error(request, "Please correct the errors below.")
        context = self.get_context_data(form=form, image_form=image_form)
        return render(request, self.template_name, context, status=400)


class ProjectDetailView(StaffOnlyMixin, TemplateView):
    template_name = "console/projects/detail.html"

    def get_project(self):
        return get_object_or_404(
            Project.objects.prefetch_related("images"), pk=self.kwargs["pk"]
        )

    def get_context_data(self, **kwargs):
        project = self.get_project()
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "project": project,
                "form": kwargs.get("form", ProjectForm(instance=project)),
                "image_form": kwargs.get("image_form", ProjectImageUploadForm()),
                "delete_form": kwargs.get("delete_form", ProjectDeleteForm()),
            }
        )
        return context


class ProjectUpdateView(StaffOnlyMixin, View):
    template_name = "console/projects/detail.html"

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project updated.")
            return redirect("console:project-detail", pk=project.pk)

        messages.error(request, "Please correct the errors below.")
        context = {
            "project": project,
            "form": form,
            "image_form": ProjectImageUploadForm(),
            "delete_form": ProjectDeleteForm(),
        }
        return render(request, self.template_name, context, status=400)


class ProjectImageUploadView(StaffOnlyMixin, View):
    template_name = "console/projects/detail.html"

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        image_form = ProjectImageUploadForm(request.POST, request.FILES)

        # Get all uploaded files
        uploaded_files = request.FILES.getlist("images")

        if not uploaded_files:
            messages.warning(request, "No images were selected.")
            return redirect("console:project-detail", pk=project.pk)

        added = 0
        errors = []

        for uploaded_file in uploaded_files:
            try:
                # Validate file type
                if not uploaded_file.content_type.startswith("image/"):
                    errors.append(f"{uploaded_file.name} is not a valid image file")
                    continue

                # Create and save image
                image = Image(file=uploaded_file)
                image.save()  # This triggers compression
                project.images.add(image)
                added += 1
            except Exception as e:
                errors.append(f"Could not upload {uploaded_file.name}: {str(e)}")

        # Provide feedback
        if added:
            messages.success(
                request, f"Successfully added {added} image{'s' if added != 1 else ''}."
            )

        for error in errors:
            messages.warning(request, error)

        if not added and not errors:
            messages.info(request, "No images were uploaded.")

        return redirect("console:project-detail", pk=project.pk)


class ProjectImageDeleteView(StaffOnlyMixin, View):
    def post(self, request, pk, image_pk):
        project = get_object_or_404(Project, pk=pk)
        image = get_object_or_404(Image, pk=image_pk)
        project.images.remove(image)

        if not image.project_set.exists():
            image.file.delete(save=False)
            image.delete()
        messages.success(request, "Image removed.")
        return redirect("console:project-detail", pk=project.pk)


class ProjectDeleteView(StaffOnlyMixin, View):
    template_name = "console/projects/detail.html"

    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        form = ProjectDeleteForm(request.POST)
        if form.is_valid():
            images = list(project.images.all())
            project.delete()
            for image in images:
                if not image.project_set.exists():
                    image.file.delete(save=False)
                    image.delete()
            messages.success(request, "Project deleted.")
            return redirect("console:project-list")

        messages.error(request, "Please confirm deletion before proceeding.")
        context = {
            "project": project,
            "form": ProjectForm(instance=project),
            "image_form": ProjectImageUploadForm(),
            "delete_form": form,
        }
        return render(request, self.template_name, context, status=400)


class MessageListView(StaffOnlyMixin, TemplateView):
    template_name = "console/messages/list.html"

    def get_queryset(self, form: MessageFilterForm):
        queryset = Message.objects.all().order_by("-created_at")
        if not form.is_valid():
            return queryset

        query = form.cleaned_data.get("query")
        timeframe = form.cleaned_data.get("timeframe")

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(email__icontains=query)
                | Q(message__icontains=query)
            )

        if timeframe:
            try:
                days = int(timeframe)
            except (TypeError, ValueError):
                days = None
            if days:
                since = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(created_at__gte=since)
        return queryset

    def get_context_data(self, **kwargs):
        form = MessageFilterForm(self.request.GET or None)
        queryset = self.get_queryset(form)
        if not form.is_valid():
            form = MessageFilterForm()

        messages_list = list(queryset)
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "messages_list": messages_list,
                "filter_form": form,
                "message_count": len(messages_list),
            }
        )
        return context


class MessageDetailView(StaffOnlyMixin, TemplateView):
    template_name = "console/messages/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        message_obj = get_object_or_404(Message, pk=self.kwargs["pk"])
        context.update({"message_obj": message_obj})
        return context


def _static_root() -> Path:
    """Get the static root directory without trying to create it."""
    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root:
        base_dir = Path(static_root)
    else:
        static_dirs = getattr(settings, "STATICFILES_DIRS", [])
        base_dir = (
            Path(static_dirs[0]) if static_dirs else Path(settings.BASE_DIR) / "static"
        )
    # Don't try to create the directory - it may not exist in production with cloud storage
    # Just return the path and let the view handle if it doesn't exist
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


def _normalize_storage_root(value) -> str:
    value = (value or DEFAULT_STORAGE_ROOT).strip().lower()
    if value not in STORAGE_ROOTS:
        return DEFAULT_STORAGE_ROOT
    return value


def _build_entry_url(request, storage, entry) -> str | None:
    if getattr(entry, "is_dir", False):
        return None
    if entry.url:
        return entry.url

    base_url = getattr(storage, "base_url", None)
    if not base_url:
        return None

    rel_path = getattr(entry, "rel_path", "") or ""
    rel_path = rel_path.replace("\\", "/").lstrip("/")

    base = base_url.rstrip("/") if base_url else ""
    if rel_path:
        url = f"{base}/{rel_path}" if base else rel_path
    else:
        url = base

    if url.startswith(("http://", "https://")):
        return url

    absolute_path = "/" + url.lstrip("/")
    return request.build_absolute_uri(absolute_path)


def _build_breadcrumbs(storage_root: str, relative: str):
    storage_root = _normalize_storage_root(storage_root)
    meta = STORAGE_ROOTS[storage_root]
    base_url = reverse("console:file-manager")
    params = {"storage": storage_root}
    crumbs = []

    root_url = f"{base_url}?{urlencode(params)}"
    crumbs.append(
        {
            "label": meta["root_label"],
            "url": None if not relative else root_url,
        }
    )

    if not relative:
        return crumbs

    parts = [part for part in relative.split("/") if part]
    for index, part in enumerate(parts):
        path = "/".join(parts[: index + 1])
        crumb_params = {"storage": storage_root, "path": path}
        crumb_url = (
            f"{base_url}?{urlencode(crumb_params)}"
            if index < len(parts) - 1
            else None
        )
        crumbs.append({"label": part, "url": crumb_url})
    return crumbs


def _redirect_to_manager(relative: str, storage_root: str = DEFAULT_STORAGE_ROOT):
    url = reverse("console:file-manager")
    params = {}
    storage_root = _normalize_storage_root(storage_root)

    if storage_root:
        params["storage"] = storage_root

    relative = (relative or "").strip()
    if relative:
        params["path"] = relative

    if params:
        url = f"{url}?{urlencode(params)}"
    return redirect(url)


def _add_form_errors(request, form):
    if form.errors:
        for _, errors in form.errors.items():
            for error in errors:
                messages.error(request, error)
