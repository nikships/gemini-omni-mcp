"""Legacy image app-icon tests intentionally replaced by Gemini Omni video tests."""


def test_legacy_app_icon_tool_removed() -> None:
    import gemini_omni_mcp.tools

    assert not hasattr(gemini_omni_mcp.tools, "register_generate_app_icon_tool")
