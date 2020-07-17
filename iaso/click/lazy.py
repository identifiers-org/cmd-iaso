import importlib
import re

import click

IMPORT_PATTERN = re.compile(
    r"from\s+(\.*(?:[a-zA-Z_][a-zA-Z0-9_]*)?(?:\.(?:[a-zA-Z_][a-zA-Z0-9_]*))*)\s+import\s+(?:\(\s*)?((?:(?:[a-zA-Z_][a-zA-Z0-9_]*)(?:\s+as\s+[a-zA-Z_][a-zA-Z0-9_]*)?(?:,\s*)?)+)\s*\)?"
)


def LazyCommandGroup(package, subcommands):
    class LazyCommandGroup(click.MultiCommand):
        def list_commands(self, ctx):
            return subcommands

        def get_command(self, ctx, name):
            return getattr(importlib.import_module(f".{name}", package=package), name)

    return LazyCommandGroup


def lazy_import(locals, imports):
    package = ".".join(locals["__name__"].split(".")[:-1])

    def LazyImportWrapper(path, name, glob):
        class LazyImport:
            def __getattribute__(self, attr):
                module = importlib.import_module(path, package=package)
                helper = getattr(module, name)

                locals[glob] = globals()[glob] = helper

                return getattr(helper, attr)

            def __call__(self, *args, **kwargs):
                module = importlib.import_module(path, package=package)
                helper = getattr(module, name)

                locals[glob] = globals()[glob] = helper

                return helper(*args, **kwargs)

        return LazyImport()

    globs = globals()

    for match in IMPORT_PATTERN.finditer(imports):
        import_path = match.group(1)

        imports = match.group(2).split(",")

        for r_import in imports:
            r_import = r_import.strip()

            if len(r_import) == 0:
                continue

            import_split = re.split(r"\sas\s", r_import)

            import_name = import_split[0].strip()
            import_as = import_split[len(import_split) - 1].strip()

            if globs.get(import_as) is None:
                globs[import_as] = LazyImportWrapper(
                    import_path, import_name, import_as
                )

            locals[import_as] = globs[import_as]
