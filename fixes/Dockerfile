# Patched release plus least-privilege configuration. No host files are mounted.
FROM httpd:2.4.69

# Official httpd defaults deny /, allow only htdocs, and leave CGI disabled.
# Keep these defaults instead of the deliberately weakened Vulhub settings.
RUN httpd -t
