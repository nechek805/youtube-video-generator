class YouTubeAccountNotFound(Exception):
    """User has no connected YouTube account."""


class YouTubeOAuthError(Exception):
    """Error during Google OAuth flow."""


class YouTubeUploadError(Exception):
    """Error while uploading video to YouTube."""
