import markdown
import os

# Define file paths
md_file_path = "C:\\Python\\12.InfoMensajes-Power\\help_manual.md"
html_file_path = "C:\\Python\\12.InfoMensajes-Power\\assets\\help_manual.html"

# Read Markdown content from file
with open(md_file_path, "r", encoding="utf-8") as f:
    markdown_content = f.read()

# Convert Markdown to HTML
html_content = markdown.markdown(markdown_content)

# Add some basic HTML structure and styling for better readability
final_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Manual de Usuario - InfoMensajes-Power</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; background-color: #f4f4f4; color: #333; }}
        h1, h2, h3, h4, h5, h6 {{ color: #0056b3; }}
        a {{ color: #007bff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        ul {{ list-style-type: disc; margin-left: 20px; }}
        ol {{ list-style-type: decimal; margin-left: 20px; }}
        strong {{ font-weight: bold; }}
        em {{ font-style: italic; }}
        code {{ font-family: 'Courier New', Courier, monospace; background-color: #e9e9e9; padding: 2px 4px; border-radius: 4px; }}
        pre {{ background-color: #e9e9e9; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

# Write HTML content to file
with open(html_file_path, "w", encoding="utf-8") as f:
    f.write(final_html)

print(f"Manual de ayuda convertido a HTML y guardado en {html_file_path}")