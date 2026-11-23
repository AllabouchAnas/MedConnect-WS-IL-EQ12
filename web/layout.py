"""Shared HTML layout helpers."""

import html


def esc(value):
    if value is None:
        return ""
    return html.escape(str(value))


def page(title, body, notice=""):
    alert = f'<p class="notice" role="alert">{esc(notice)}</p>' if notice else ""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} — MedConnect</title>
  <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
  <header class="site-header">
    <div>
      <a class="brand" href="/"><strong>MedConnect</strong></a>
      <p>Dossier médical informatisé</p>
    </div>
    <a class="button" href="/consultations/nouvelle">Nouvelle consultation</a>
  </header>
  <main>
    {alert}
    {body}
  </main>
</body>
</html>"""
