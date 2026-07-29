"""Translation catalogues, keyed by the English source string.

English is the source language and has no catalogue: any string missing from a
catalogue falls back to English automatically, so a partial translation is
always safe to ship.

Keep the placeholders ({n}, {version}, …) intact when translating; the code
formats these after lookup.
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# Swedish
# --------------------------------------------------------------------------
SV: dict[str, str] = {
    # Menu
    "Counting…": "Räknar…",
    "No browsers running": "Inga webbläsare igång",
    "{n} tab total": "{n} flik totalt",
    "{n} tabs total": "{n} flikar totalt",
    "— (permission?)": "— (behörighet?)",
    "Refresh now": "Uppdatera nu",
    "Export open tabs…": "Exportera öppna flikar…",
    "Alert threshold: off": "Varningsgräns: av",
    "Alert threshold: {n}": "Varningsgräns: {n}",
    "Permissions": "Behörigheter",
    "Re-request browser permissions": "Begär webbläsarbehörigheter igen",
    "Open Automation settings…": "Öppna Automation-inställningar…",
    "Launch at Login": "Starta vid inloggning",
    "About {app}": "Om {app}",
    "Quit": "Avsluta",

    # History line
    "Tab history: collecting…": "Flikhistorik: samlar in…",
    "Today": "Idag",
    "avg": "snitt",

    # Common buttons
    "OK": "OK",
    "Cancel": "Avbryt",
    "Save": "Spara",
    "Close": "Stäng",
    "Later": "Senare",

    # About panel
    "Version {version}": "Version {version}",
    "Installed: {date}": "Installerad: {date}",
    "Polls every {n}s": "Kollar var {n}:e sekund",
    "Browser permissions (Automation):": "Webbläsarbehörigheter (Automation):",
    "session file (no prompt)": "sessionsfil (ingen fråga)",
    "granted ✓": "beviljad ✓",
    "needs permission ✗": "behörighet krävs ✗",
    "(no supported browsers running)": "(inga webbläsare som stöds är igång)",
    "Developer: Mario Longhi — mariolonghi.com":
        "Utvecklare: Mario Longhi — mariolonghi.com",

    # Updates
    "Update check unavailable (offline?)":
        "Kunde inte söka efter uppdateringar (offline?)",
    "⬆ Update available: v{latest} (you have v{current})":
        "⬆ Uppdatering tillgänglig: v{latest} (du har v{current})",
    "✓ You're on the latest version (v{current})":
        "✓ Du har den senaste versionen (v{current})",
    "Update now to v{latest}": "Uppdatera nu till v{latest}",
    "Release notes": "Versionsinformation",
    "Download update": "Hämta uppdatering",
    "Visit mariolonghi.com": "Besök mariolonghi.com",
    "Update": "Uppdatering",
    "Updating to v{latest}…": "Uppdaterar till v{latest}…",
    "Downloading and verifying — the app will relaunch itself.":
        "Hämtar och verifierar — appen startar om sig själv.",
    "Couldn't update automatically:\n{error}":
        "Kunde inte uppdatera automatiskt:\n{error}",
    "Update failed:\n{error}": "Uppdateringen misslyckades:\n{error}",
    "Open download page": "Öppna nedladdningssidan",

    # Launch at login
    "Couldn't update setting:\n{error}":
        "Kunde inte ändra inställningen:\n{error}",

    # Permissions dialog
    "Re-request Browser Permissions": "Begär webbläsarbehörigheter igen",
    "Cleared the previous Automation choices.\n\nmacOS will now ask again the "
    "next time each browser is checked — click Allow on those prompts.\n\nIf "
    "nothing appears, use “Open Automation settings…” and enable each browser "
    "under “{app}”.":
        "Tidigare Automation-val har rensats.\n\nmacOS frågar nu igen nästa "
        "gång varje webbläsare kontrolleras — klicka på Tillåt i de dialogerna."
        "\n\nOm inget visas, använd “Öppna Automation-inställningar…” och "
        "aktivera varje webbläsare under “{app}”.",
    "Couldn't reset the permissions automatically":
        "Kunde inte återställa behörigheterna automatiskt",
    "Open Automation settings and enable each browser under “{app}”.":
        "Öppna Automation-inställningarna och aktivera varje webbläsare under "
        "“{app}”.",

    # Threshold
    "Alert Threshold": "Varningsgräns",
    "Show ⚠️ and notify once when the total goes above this many tabs.\n"
    "Enter 0 to turn the alert off.":
        "Visa ⚠️ och meddela en gång när antalet överstiger så här många "
        "flikar.\nAnge 0 för att stänga av varningen.",
    "Please enter a whole number (0 turns the alert off).":
        "Ange ett heltal (0 stänger av varningen).",
    "Over your {n}-tab limit": "Över din gräns på {n} flikar",
    "You have {n} tabs open.": "Du har {n} flikar öppna.",

    # Tab history
    "Tab History": "Flikhistorik",
    "Save Tab History": "Spara flikhistorik",
    "No history recorded yet — it starts filling in within a few minutes of "
    "running.":
        "Ingen historik ännu — den börjar fyllas i inom några minuter.",
    "Couldn't save the file:\n{error}": "Kunde inte spara filen:\n{error}",

    # Export
    "Export Open Tabs": "Exportera öppna flikar",
    "Couldn't read the open tabs:\n{error}":
        "Kunde inte läsa de öppna flikarna:\n{error}",
    "No open tabs found in the running browsers.":
        "Inga öppna flikar hittades i webbläsarna som är igång.",
    "Couldn't write the file:\n{error}": "Kunde inte skriva filen:\n{error}",
    "{n} open tab found.\n\nChoose a format:\n\n"
    "• Spreadsheet (CSV) — open in Numbers, Excel, anything.\n"
    "• Web page (HTML) — a sortable table with clickable links, viewable in "
    "any browser.":
        "{n} öppen flik hittades.\n\nVälj format:\n\n"
        "• Kalkylblad (CSV) — öppnas i Numbers, Excel eller liknande.\n"
        "• Webbsida (HTML) — en sorterbar tabell med klickbara länkar som kan "
        "visas i vilken webbläsare som helst.",
    "{n} open tabs found.\n\nChoose a format:\n\n"
    "• Spreadsheet (CSV) — open in Numbers, Excel, anything.\n"
    "• Web page (HTML) — a sortable table with clickable links, viewable in "
    "any browser.":
        "{n} öppna flikar hittades.\n\nVälj format:\n\n"
        "• Kalkylblad (CSV) — öppnas i Numbers, Excel eller liknande.\n"
        "• Webbsida (HTML) — en sorterbar tabell med klickbara länkar som kan "
        "visas i vilken webbläsare som helst.",
    "Spreadsheet (CSV)": "Kalkylblad (CSV)",
    "Web page (HTML)": "Webbsida (HTML)",
    "open tabs": "öppna flikar",
    "tab history": "flikhistorik",

    # HTML report
    "Open browser tabs": "Öppna webbläsarflikar",
    "{n} tab across {browsers} · captured {when} · click a column heading "
    "to sort":
        "{n} flik i {browsers} · hämtat {when} · klicka på en kolumnrubrik "
        "för att sortera",
    "{n} tabs across {browsers} · captured {when} · click a column heading "
    "to sort":
        "{n} flikar i {browsers} · hämtat {when} · klicka på en kolumnrubrik "
        "för att sortera",
    "no browsers": "inga webbläsare",
    "browser": "webbläsare",
    "window": "fönster",
    "tab": "flik",
    "title": "titel",
    "url": "url",
    "active": "aktiv",
    "pinned": "fäst",
    "loading": "laddar",
    "window mode": "fönsterläge",
    "last accessed": "senast använd",

    # Self-update failures
    "running from source": "körs från källkod",
    "not an .app bundle": "inte ett .app-paket",
    "the install location isn't writable": "installationsplatsen är skrivskyddad",
    "unexpected update URL, refusing to download":
        "oväntad uppdaterings-URL, hämtar inte",
    "update download is unexpectedly large":
        "uppdateringen är oväntat stor",
    "couldn't find the mounted update volume":
        "kunde inte hitta den monterade uppdateringsvolymen",
    "no application found inside the update":
        "ingen app hittades i uppdateringen",
    "the download's code signature is invalid":
        "hämtningens kodsignatur är ogiltig",
    "the download isn't notarized / accepted by macOS":
        "hämtningen är inte notariserad / godkänd av macOS",
    "the download isn't signed by the expected developer":
        "hämtningen är inte signerad av rätt utvecklare",
}

# --------------------------------------------------------------------------
# Spanish
# --------------------------------------------------------------------------
ES: dict[str, str] = {
    "Counting…": "Contando…",
    "No browsers running": "No hay navegadores abiertos",
    "{n} tab total": "{n} pestaña en total",
    "{n} tabs total": "{n} pestañas en total",
    "— (permission?)": "— (¿permiso?)",
    "Refresh now": "Actualizar ahora",
    "Export open tabs…": "Exportar pestañas abiertas…",
    "Alert threshold: off": "Umbral de aviso: desactivado",
    "Alert threshold: {n}": "Umbral de aviso: {n}",
    "Permissions": "Permisos",
    "Re-request browser permissions": "Volver a solicitar permisos del navegador",
    "Open Automation settings…": "Abrir ajustes de Automatización…",
    "Launch at Login": "Abrir al iniciar sesión",
    "About {app}": "Acerca de {app}",
    "Quit": "Salir",

    "Tab history: collecting…": "Historial de pestañas: recopilando…",
    "Today": "Hoy",
    "avg": "prom.",

    "OK": "OK",
    "Cancel": "Cancelar",
    "Save": "Guardar",
    "Close": "Cerrar",
    "Later": "Más tarde",

    "Version {version}": "Versión {version}",
    "Installed: {date}": "Instalado: {date}",
    "Polls every {n}s": "Consulta cada {n} s",
    "Browser permissions (Automation):": "Permisos del navegador (Automatización):",
    "session file (no prompt)": "archivo de sesión (sin permiso)",
    "granted ✓": "concedido ✓",
    "needs permission ✗": "requiere permiso ✗",
    "(no supported browsers running)": "(no hay navegadores compatibles abiertos)",
    "Developer: Mario Longhi — mariolonghi.com":
        "Desarrollador: Mario Longhi — mariolonghi.com",

    "Update check unavailable (offline?)":
        "No se pudo comprobar si hay actualizaciones (¿sin conexión?)",
    "⬆ Update available: v{latest} (you have v{current})":
        "⬆ Actualización disponible: v{latest} (tienes la v{current})",
    "✓ You're on the latest version (v{current})":
        "✓ Tienes la última versión (v{current})",
    "Update now to v{latest}": "Actualizar ahora a la v{latest}",
    "Release notes": "Notas de la versión",
    "Download update": "Descargar actualización",
    "Visit mariolonghi.com": "Visitar mariolonghi.com",
    "Update": "Actualización",
    "Updating to v{latest}…": "Actualizando a la v{latest}…",
    "Downloading and verifying — the app will relaunch itself.":
        "Descargando y verificando — la app se reiniciará sola.",
    "Couldn't update automatically:\n{error}":
        "No se pudo actualizar automáticamente:\n{error}",
    "Update failed:\n{error}": "La actualización falló:\n{error}",
    "Open download page": "Abrir la página de descarga",

    "Couldn't update setting:\n{error}":
        "No se pudo cambiar el ajuste:\n{error}",

    "Re-request Browser Permissions": "Volver a solicitar permisos del navegador",
    "Cleared the previous Automation choices.\n\nmacOS will now ask again the "
    "next time each browser is checked — click Allow on those prompts.\n\nIf "
    "nothing appears, use “Open Automation settings…” and enable each browser "
    "under “{app}”.":
        "Se han borrado las decisiones anteriores de Automatización.\n\nmacOS "
        "volverá a preguntar la próxima vez que se consulte cada navegador — "
        "pulsa Permitir en esos avisos.\n\nSi no aparece nada, usa “Abrir "
        "ajustes de Automatización…” y activa cada navegador dentro de “{app}”.",
    "Couldn't reset the permissions automatically":
        "No se pudieron restablecer los permisos automáticamente",
    "Open Automation settings and enable each browser under “{app}”.":
        "Abre los ajustes de Automatización y activa cada navegador dentro de "
        "“{app}”.",

    "Alert Threshold": "Umbral de aviso",
    "Show ⚠️ and notify once when the total goes above this many tabs.\n"
    "Enter 0 to turn the alert off.":
        "Muestra ⚠️ y avisa una vez cuando el total supere este número de "
        "pestañas.\nIntroduce 0 para desactivar el aviso.",
    "Please enter a whole number (0 turns the alert off).":
        "Introduce un número entero (0 desactiva el aviso).",
    "Over your {n}-tab limit": "Has superado tu límite de {n} pestañas",
    "You have {n} tabs open.": "Tienes {n} pestañas abiertas.",

    "Tab History": "Historial de pestañas",
    "Save Tab History": "Guardar el historial de pestañas",
    "No history recorded yet — it starts filling in within a few minutes of "
    "running.":
        "Aún no hay historial — empieza a llenarse a los pocos minutos de uso.",
    "Couldn't save the file:\n{error}": "No se pudo guardar el archivo:\n{error}",

    "Export Open Tabs": "Exportar pestañas abiertas",
    "Couldn't read the open tabs:\n{error}":
        "No se pudieron leer las pestañas abiertas:\n{error}",
    "No open tabs found in the running browsers.":
        "No se encontraron pestañas abiertas en los navegadores en ejecución.",
    "Couldn't write the file:\n{error}": "No se pudo escribir el archivo:\n{error}",
    "{n} open tab found.\n\nChoose a format:\n\n"
    "• Spreadsheet (CSV) — open in Numbers, Excel, anything.\n"
    "• Web page (HTML) — a sortable table with clickable links, viewable in "
    "any browser.":
        "Se ha encontrado {n} pestaña abierta.\n\nElige un formato:\n\n"
        "• Hoja de cálculo (CSV) — se abre en Numbers, Excel o similares.\n"
        "• Página web (HTML) — una tabla ordenable con enlaces, que se puede "
        "ver en cualquier navegador.",
    "{n} open tabs found.\n\nChoose a format:\n\n"
    "• Spreadsheet (CSV) — open in Numbers, Excel, anything.\n"
    "• Web page (HTML) — a sortable table with clickable links, viewable in "
    "any browser.":
        "Se han encontrado {n} pestañas abiertas.\n\nElige un formato:\n\n"
        "• Hoja de cálculo (CSV) — se abre en Numbers, Excel o similares.\n"
        "• Página web (HTML) — una tabla ordenable con enlaces, que se puede "
        "ver en cualquier navegador.",
    "Spreadsheet (CSV)": "Hoja de cálculo (CSV)",
    "Web page (HTML)": "Página web (HTML)",
    "open tabs": "pestañas abiertas",
    "tab history": "historial de pestañas",

    "Open browser tabs": "Pestañas abiertas del navegador",
    "{n} tab across {browsers} · captured {when} · click a column heading "
    "to sort":
        "{n} pestaña en {browsers} · capturado el {when} · pulsa una cabecera "
        "de columna para ordenar",
    "{n} tabs across {browsers} · captured {when} · click a column heading "
    "to sort":
        "{n} pestañas en {browsers} · capturado el {when} · pulsa una cabecera "
        "de columna para ordenar",
    "no browsers": "ningún navegador",
    "browser": "navegador",
    "window": "ventana",
    "tab": "pestaña",
    "title": "título",
    "url": "url",
    "active": "activa",
    "pinned": "fijada",
    "loading": "cargando",
    "window mode": "modo de ventana",
    "last accessed": "último acceso",

    "running from source": "ejecutándose desde el código fuente",
    "not an .app bundle": "no es un paquete .app",
    "the install location isn't writable":
        "la ubicación de instalación no permite escritura",
    "unexpected update URL, refusing to download":
        "URL de actualización inesperada, no se descargará",
    "update download is unexpectedly large":
        "la descarga de la actualización es inesperadamente grande",
    "couldn't find the mounted update volume":
        "no se encontró el volumen de actualización montado",
    "no application found inside the update":
        "no se encontró ninguna app dentro de la actualización",
    "the download's code signature is invalid":
        "la firma de código de la descarga no es válida",
    "the download isn't notarized / accepted by macOS":
        "la descarga no está notarizada ni aceptada por macOS",
    "the download isn't signed by the expected developer":
        "la descarga no está firmada por el desarrollador esperado",
}

# --------------------------------------------------------------------------
# German
# --------------------------------------------------------------------------
DE: dict[str, str] = {
    "Counting…": "Zähle…",
    "No browsers running": "Keine Browser geöffnet",
    "{n} tab total": "{n} Tab insgesamt",
    "{n} tabs total": "{n} Tabs insgesamt",
    "— (permission?)": "— (Berechtigung?)",
    "Refresh now": "Jetzt aktualisieren",
    "Export open tabs…": "Offene Tabs exportieren…",
    "Alert threshold: off": "Warnschwelle: aus",
    "Alert threshold: {n}": "Warnschwelle: {n}",
    "Permissions": "Berechtigungen",
    "Re-request browser permissions": "Browser-Berechtigungen erneut anfordern",
    "Open Automation settings…": "Automatisierungs-Einstellungen öffnen…",
    "Launch at Login": "Beim Anmelden starten",
    "About {app}": "Über {app}",
    "Quit": "Beenden",

    "Tab history: collecting…": "Tab-Verlauf: wird erfasst…",
    "Today": "Heute",
    "avg": "Ø",

    "OK": "OK",
    "Cancel": "Abbrechen",
    "Save": "Sichern",
    "Close": "Schließen",
    "Later": "Später",

    "Version {version}": "Version {version}",
    "Installed: {date}": "Installiert: {date}",
    "Polls every {n}s": "Prüft alle {n} s",
    "Browser permissions (Automation):": "Browser-Berechtigungen (Automatisierung):",
    "session file (no prompt)": "Sitzungsdatei (keine Abfrage)",
    "granted ✓": "erteilt ✓",
    "needs permission ✗": "Berechtigung nötig ✗",
    "(no supported browsers running)": "(keine unterstützten Browser geöffnet)",
    "Developer: Mario Longhi — mariolonghi.com":
        "Entwickler: Mario Longhi — mariolonghi.com",

    "Update check unavailable (offline?)":
        "Update-Prüfung nicht möglich (offline?)",
    "⬆ Update available: v{latest} (you have v{current})":
        "⬆ Update verfügbar: v{latest} (installiert: v{current})",
    "✓ You're on the latest version (v{current})":
        "✓ Du hast die neueste Version (v{current})",
    "Update now to v{latest}": "Jetzt auf v{latest} aktualisieren",
    "Release notes": "Versionshinweise",
    "Download update": "Update laden",
    "Visit mariolonghi.com": "mariolonghi.com besuchen",
    "Update": "Update",
    "Updating to v{latest}…": "Aktualisiere auf v{latest}…",
    "Downloading and verifying — the app will relaunch itself.":
        "Wird geladen und geprüft — die App startet sich selbst neu.",
    "Couldn't update automatically:\n{error}":
        "Automatisches Update fehlgeschlagen:\n{error}",
    "Update failed:\n{error}": "Update fehlgeschlagen:\n{error}",
    "Open download page": "Download-Seite öffnen",

    "Couldn't update setting:\n{error}":
        "Einstellung konnte nicht geändert werden:\n{error}",

    "Re-request Browser Permissions": "Browser-Berechtigungen erneut anfordern",
    "Cleared the previous Automation choices.\n\nmacOS will now ask again the "
    "next time each browser is checked — click Allow on those prompts.\n\nIf "
    "nothing appears, use “Open Automation settings…” and enable each browser "
    "under “{app}”.":
        "Die bisherigen Automatisierungs-Entscheidungen wurden zurückgesetzt."
        "\n\nmacOS fragt beim nächsten Prüfen jedes Browsers erneut — klicke "
        "dort auf „Erlauben“.\n\nFalls nichts erscheint, nutze "
        "„Automatisierungs-Einstellungen öffnen…“ und aktiviere jeden Browser "
        "unter „{app}“.",
    "Couldn't reset the permissions automatically":
        "Die Berechtigungen konnten nicht automatisch zurückgesetzt werden",
    "Open Automation settings and enable each browser under “{app}”.":
        "Öffne die Automatisierungs-Einstellungen und aktiviere jeden Browser "
        "unter „{app}“.",

    "Alert Threshold": "Warnschwelle",
    "Show ⚠️ and notify once when the total goes above this many tabs.\n"
    "Enter 0 to turn the alert off.":
        "Zeigt ⚠️ und meldet sich einmal, sobald die Gesamtzahl diesen Wert "
        "überschreitet.\n0 schaltet die Warnung aus.",
    "Please enter a whole number (0 turns the alert off).":
        "Bitte eine ganze Zahl eingeben (0 schaltet die Warnung aus).",
    "Over your {n}-tab limit": "Über deinem Limit von {n} Tabs",
    "You have {n} tabs open.": "Du hast {n} Tabs geöffnet.",

    "Tab History": "Tab-Verlauf",
    "Save Tab History": "Tab-Verlauf sichern",
    "No history recorded yet — it starts filling in within a few minutes of "
    "running.":
        "Noch kein Verlauf — er füllt sich nach wenigen Minuten Laufzeit.",
    "Couldn't save the file:\n{error}":
        "Datei konnte nicht gesichert werden:\n{error}",

    "Export Open Tabs": "Offene Tabs exportieren",
    "Couldn't read the open tabs:\n{error}":
        "Die offenen Tabs konnten nicht gelesen werden:\n{error}",
    "No open tabs found in the running browsers.":
        "In den laufenden Browsern wurden keine offenen Tabs gefunden.",
    "Couldn't write the file:\n{error}":
        "Datei konnte nicht geschrieben werden:\n{error}",
    "{n} open tab found.\n\nChoose a format:\n\n"
    "• Spreadsheet (CSV) — open in Numbers, Excel, anything.\n"
    "• Web page (HTML) — a sortable table with clickable links, viewable in "
    "any browser.":
        "{n} offener Tab gefunden.\n\nFormat wählen:\n\n"
        "• Tabelle (CSV) — für Numbers, Excel und alles andere.\n"
        "• Webseite (HTML) — eine sortierbare Tabelle mit anklickbaren Links, "
        "in jedem Browser lesbar.",
    "{n} open tabs found.\n\nChoose a format:\n\n"
    "• Spreadsheet (CSV) — open in Numbers, Excel, anything.\n"
    "• Web page (HTML) — a sortable table with clickable links, viewable in "
    "any browser.":
        "{n} offene Tabs gefunden.\n\nFormat wählen:\n\n"
        "• Tabelle (CSV) — für Numbers, Excel und alles andere.\n"
        "• Webseite (HTML) — eine sortierbare Tabelle mit anklickbaren Links, "
        "in jedem Browser lesbar.",
    "Spreadsheet (CSV)": "Tabelle (CSV)",
    "Web page (HTML)": "Webseite (HTML)",
    "open tabs": "offene Tabs",
    "tab history": "Tab-Verlauf",

    "Open browser tabs": "Offene Browser-Tabs",
    "{n} tab across {browsers} · captured {when} · click a column heading "
    "to sort":
        "{n} Tab in {browsers} · erfasst am {when} · zum Sortieren auf eine "
        "Spaltenüberschrift klicken",
    "{n} tabs across {browsers} · captured {when} · click a column heading "
    "to sort":
        "{n} Tabs in {browsers} · erfasst am {when} · zum Sortieren auf eine "
        "Spaltenüberschrift klicken",
    "no browsers": "keine Browser",
    "browser": "Browser",
    "window": "Fenster",
    "tab": "Tab",
    "title": "Titel",
    "url": "URL",
    "active": "aktiv",
    "pinned": "angeheftet",
    "loading": "lädt",
    "window mode": "Fenstermodus",
    "last accessed": "zuletzt benutzt",

    "running from source": "läuft aus dem Quellcode",
    "not an .app bundle": "kein .app-Paket",
    "the install location isn't writable":
        "der Installationsort ist nicht beschreibbar",
    "unexpected update URL, refusing to download":
        "unerwartete Update-URL, Download abgelehnt",
    "update download is unexpectedly large":
        "der Update-Download ist unerwartet groß",
    "couldn't find the mounted update volume":
        "das eingebundene Update-Volume wurde nicht gefunden",
    "no application found inside the update":
        "im Update wurde keine App gefunden",
    "the download's code signature is invalid":
        "die Codesignatur des Downloads ist ungültig",
    "the download isn't notarized / accepted by macOS":
        "der Download ist nicht notarisiert / von macOS akzeptiert",
    "the download isn't signed by the expected developer":
        "der Download stammt nicht vom erwarteten Entwickler",
}

CATALOGUES: dict[str, dict[str, str]] = {"sv": SV, "es": ES, "de": DE}
