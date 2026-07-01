"""Legacy background removal tests intentionally replaced by video tests."""


def test_background_removal_not_exported() -> None:
    import gemini_omni_mcp.tools

    assert hasattr(gemini_omni_mcp.tools, "generate_video_tool")
