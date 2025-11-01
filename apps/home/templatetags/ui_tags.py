"""
Custom template tags for UI components and utilities.

Professional Django template tag library following best practices.
"""

from django import template
from django.utils.safestring import mark_safe
from django.urls import reverse, NoReverseMatch
import json

register = template.Library()


@register.simple_tag(takes_context=True)
def active_link(context, url_name, css_class="active", **kwargs):
    """
    Returns the CSS class if the current URL matches the given URL name.

    Usage:
        <a class="nav-link {% active_link 'home' %}" href="{% url 'home' %}">Home</a>
    """
    try:
        url = reverse(url_name, kwargs=kwargs)
        request = context.get("request")
        if request and request.path == url:
            return css_class
    except NoReverseMatch:
        pass
    return ""


@register.simple_tag(takes_context=True)
def active_section(context, *url_names, css_class="active"):
    """
    Returns the CSS class if the current URL matches any of the given URL names.
    Useful for highlighting navigation sections.

    Usage:
        <li class="{% active_section 'console:project-list' 'console:project-create' %}">
    """
    request = context.get("request")
    if not request:
        return ""

    for url_name in url_names:
        try:
            url = reverse(url_name)
            if request.path.startswith(url):
                return css_class
        except NoReverseMatch:
            continue
    return ""


@register.inclusion_tag("components/breadcrumb_item.html")
def breadcrumb_item(label, url=None, active=False):
    """
    Renders a breadcrumb item component.

    Usage:
        {% breadcrumb_item "Home" url='landing' %}
        {% breadcrumb_item "Projects" active=True %}
    """
    return {
        "label": label,
        "url": url,
        "active": active,
    }


@register.inclusion_tag("components/alert.html")
def alert(message, type="info", dismissible=True):
    """
    Renders an alert component.

    Types: success, error, warning, info

    Usage:
        {% alert "Operation successful!" type="success" %}
    """
    return {
        "message": message,
        "type": type,
        "dismissible": dismissible,
    }


@register.inclusion_tag("components/badge.html")
def badge(text, variant="default", size="md"):
    """
    Renders a badge component.

    Variants: default, primary, success, warning, error
    Sizes: sm, md, lg

    Usage:
        {% badge "New" variant="primary" %}
    """
    return {
        "text": text,
        "variant": variant,
        "size": size,
    }


@register.inclusion_tag("components/button.html")
def button(text, url=None, variant="primary", size="md", icon=None):
    """
    Renders a button component.

    Usage:
        {% button "Save" variant="primary" icon="check" %}
    """
    return {
        "text": text,
        "url": url,
        "variant": variant,
        "size": size,
        "icon": icon,
    }


@register.filter
def add_class(field, css_class):
    """
    Adds CSS class to a form field.

    Usage:
        {{ form.username|add_class:"form-input w-full" }}
    """
    return field.as_widget(attrs={"class": css_class})


@register.filter
def add_attrs(field, attrs_string):
    """
    Adds multiple attributes to a form field.

    Usage:
        {{ form.email|add_attrs:"class:form-input,placeholder:Enter email" }}
    """
    attrs = {}
    for attr in attrs_string.split(","):
        key, value = attr.split(":")
        attrs[key.strip()] = value.strip()
    return field.as_widget(attrs=attrs)


@register.filter
def field_type(field):
    """
    Returns the widget type of a form field.

    Usage:
        {% if form.password|field_type == 'PasswordInput' %}
    """
    return field.field.widget.__class__.__name__


@register.filter
def has_error(form, field_name):
    """
    Checks if a form field has errors.

    Usage:
        {% if form|has_error:'email' %}
    """
    return field_name in form.errors


@register.filter
def json_encode(value):
    """
    Encodes a Python object as JSON for use in JavaScript.

    Usage:
        <script>
            const data = {{ my_data|json_encode }};
        </script>
    """
    return mark_safe(json.dumps(value))


@register.simple_tag
def icon(name, size="5", classes=""):
    """
    Renders an SVG icon from Heroicons.

    Usage:
        {% icon 'check' size='4' classes='text-green-500' %}
    """
    icons = {
        "check": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>',
        "x": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>',
        "arrow-right": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/>',
        "arrow-left": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>',
        "user": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>',
        "folder": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>',
        "file": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>',
        "search": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>',
        "plus": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>',
        "pencil": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"/>',
        "trash": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>',
        "eye": '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>',
    }

    path = icons.get(name, icons["check"])
    svg = f"""<svg class="h-{size} w-{size} {classes}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        {path}
    </svg>"""
    return mark_safe(svg)


@register.simple_tag
def query_string(request, **kwargs):
    """
    Updates the current query string with new parameters.

    Usage:
        <a href="?{% query_string request page=2 %}">Next</a>
    """
    query_dict = request.GET.copy()
    for key, value in kwargs.items():
        if value is None:
            query_dict.pop(key, None)
        else:
            query_dict[key] = value
    return query_dict.urlencode()


@register.simple_tag(takes_context=True)
def page_title(context, *parts):
    """
    Constructs a page title with site name.

    Usage:
        {% page_title "Projects" "Edit" %}  => "Projects - Edit - MNK Platform"
    """
    site_name = "MNK Platform"
    if parts:
        title = " - ".join(str(part) for part in parts if part)
        return f"{title} - {site_name}"
    return site_name


@register.filter
def truncate_path(path, max_length=50):
    """
    Truncates a file path to a maximum length, preserving the filename.

    Usage:
        {{ file.path|truncate_path:30 }}
    """
    if len(path) <= max_length:
        return path

    parts = path.split("/")
    filename = parts[-1]

    if len(filename) >= max_length - 3:
        return f"...{filename[-(max_length-3):]}"

    available = max_length - len(filename) - 4
    start = path[: available // 2]

    return f"{start}/.../{filename}"
