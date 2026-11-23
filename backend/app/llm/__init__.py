"""Model configuration and provider adapters.

Progressive Model Configuration with Hierarchical Overrides: a required
primary model, optional per-capability overrides, optional per-task
overrides, and a separately configured embedding model. Resolution never
falls back silently; see ``resolver.py``.
"""
