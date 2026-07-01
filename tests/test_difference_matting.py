"""Legacy transparent-image matte tests intentionally replaced by video tests."""


def test_difference_matting_not_exported() -> None:
    import gemini_omni_mcp.services

    assert not hasattr(gemini_omni_mcp.services, "ImageService")
