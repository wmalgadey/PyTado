import importlib
import inspect
import os

OUTPUT_FILE = "docs/content/api.md"
MODULES_TO_SCAN = [
    "PyTado.interface.api",  # Haupt-API-Klassen
    "PyTado.interface",      # Zentrale Schnittstelle
    "PyTado.zone",           # Zonen-Verwaltung
]


def format_signature(method):
    """Gibt die Methodensignatur als lesbaren String zurück."""
    try:
        signature = inspect.signature(method)
    except ValueError:
        return "()"

    param_list = []
    for param_name, param in signature.parameters.items():
        param_type = f": {param.annotation}" if param.annotation != inspect.Parameter.empty else ""
        param_list.append(f"**{param_name}**{param_type}")

    return f"({', '.join(param_list)})"


def get_method_doc(method):
    """Erzeugt eine formatierte Markdown-Dokumentation für eine Methode mit Parameterdetails."""
    doc = f"### {method.__name__}{format_signature(method)}\n\n"
    docstring = inspect.getdoc(method) or "Keine Beschreibung verfügbar."
    doc += f"{docstring}\n\n"

    try:
        signature = inspect.signature(method)
        params = signature.parameters
        if params:
            doc += "**Parameter:**\n\n"
            for name, param in params.items():
                param_type = f"`{param.annotation}`" if param.annotation != inspect.Parameter.empty else "Unbekannt"  # noqa: E501
                default_value = param.default if param.default != inspect.Parameter.empty else "Erforderlich"  # noqa: E501
                doc += f"- **{name}** ({param_type}): {default_value}\n"
            doc += "\n"
    except ValueError:
        pass  # Falls keine Signatur extrahiert werden kann

    return doc


def get_class_doc(cls):
    """
        Erzeugt eine formatierte Markdown-Dokumentation für eine Klasse
        mit Methoden und Attributen.
    """
    doc = f"## {cls.__name__}\n\n"
    doc += f"{inspect.getdoc(cls) or 'Keine Dokumentation verfügbar.'}\n\n"

    # Attribute sammeln (keine Methoden oder private Elemente)
    attributes = {name: value for name, value in vars(
        cls).items() if not callable(value) and not name.startswith("_")}

    if attributes:
        doc += "**Attribute:**\n\n"
        for attr_name, attr_value in attributes.items():
            attr_type = type(attr_value).__name__
            doc += f"- **{attr_name}** (`{attr_type}`): `{attr_value}`\n"
        doc += "\n"

    # Öffentliche Methoden dokumentieren
    methods = inspect.getmembers(cls, predicate=inspect.isfunction)
    for _, method in methods:
        if method.__name__.startswith("_"):  # Private Methoden auslassen
            continue
        doc += get_method_doc(method)

    return doc


def generate_markdown():
    """Generiert eine Markdown-Datei mit allen relevanten Klassen."""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    doc = "# API-Dokumentation für `PyTado`\n\n"

    for module_name in MODULES_TO_SCAN:
        try:
            module = importlib.import_module(module_name)
            classes = [
                cls for _,
                cls in inspect.getmembers(
                    module,
                    predicate=inspect.isclass) if cls.__module__.startswith(module_name)]

            if classes:
                doc += f"## Modul `{module_name}`\n\n"
                for cls in classes:
                    doc += get_class_doc(cls)
        except Exception as e:
            print(f"Fehler beim Laden von {module_name}: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(doc)

    print(f"Dokumentation generiert: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_markdown()
