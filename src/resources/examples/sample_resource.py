from fastmcp.resources import resource


@resource("resource://readme-snippet", name="readme_snippet")
def readme_snippet() -> str:
    """A small static resource example."""
    return "This is a sample resource string."
