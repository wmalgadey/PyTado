import importlib
import inspect
import os

OUTPUT_FILE = "docs/content/api.md"
MODULES_TO_SCAN = [
    "PyTado.interface.api",  # Main API classes
    "PyTado.interface",      # Central interface
    "PyTado.zone",           # Zone management
]


def format_signature(method):
    """Returns the method signature as a readable string."""
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
    """Generates formatted Markdown documentation for a method with parameter details."""
    doc = f"### {method.__name__}{format_signature(method)}\n\n"
    docstring = inspect.getdoc(method) or "No description available."
    doc += f"{docstring}\n\n"

    try:
        signature = inspect.signature(method)
        params = signature.parameters
        if params:
            doc += "**Parameters:**\n\n"
            for name, param in params.items():
                param_type = f"`{param.annotation}`" if param.annotation != inspect.Parameter.empty else "Unknown"  # noqa: E501
                default_value = param.default if param.default != inspect.Parameter.empty else "Required"  # noqa: E501
                doc += f"- **{name}** ({param_type}): {default_value}\n"
            doc += "\n"
    except ValueError:
        pass  # If no signature can be extracted

    return doc


def get_class_doc(cls):
    """
        Generates formatted Markdown documentation for a class
        with methods and attributes.
    """
    doc = f"## {cls.__name__}\n\n"
    doc += f"{inspect.getdoc(cls) or 'No documentation available.'}\n\n"

    # Collect attributes (no methods or private elements)
    attributes = {name: value for name, value in vars(
        cls).items() if not callable(value) and not name.startswith("_")}

    if attributes:
        doc += "**Attributes:**\n\n"
        for attr_name, attr_value in attributes.items():
            attr_type = type(attr_value).__name__
            doc += f"- **{attr_name}** (`{attr_type}`): `{attr_value}`\n"
        doc += "\n"

    # Document public methods
    methods = inspect.getmembers(cls, predicate=inspect.isfunction)
    for _, method in methods:
        if method.__name__.startswith("_"):  # Skip private methods
            continue
        doc += get_method_doc(method)

    return doc


def add_frontmatter(content, key="API", order=3):
    """Adds frontmatter for 11ty navigation."""
    frontmatter = f"""---
eleventyNavigation:
  key: "{key}"
  order: {order}
---

"""
    return frontmatter + content


def generate_markdown():
    """Generates a Markdown file with all relevant classes."""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    doc = "# API Documentation for `PyTado`\n\n"

    for module_name in MODULES_TO_SCAN:
        try:
            module = importlib.import_module(module_name)
            classes = [
                cls for _,
                cls in inspect.getmembers(
                    module,
                    predicate=inspect.isclass) if cls.__module__.startswith(module_name)]

            if classes:
                doc += f"## Module `{module_name}`\n\n"
                for cls in classes:
                    doc += get_class_doc(cls)
        except Exception as e:
            print(f"Error loading {module_name}: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(add_frontmatter(doc))

    print(f"API documentation generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_markdown()
