{ pkgs ? import <nixpkgs> { } }:

pkgs.mkShell {
  name = "ics-proxy-env";

  buildInputs = [
    pkgs.python312
    pkgs.python312Packages.fastapi
    pkgs.python312Packages.uvicorn
    pkgs.python312Packages.httpx
  ];

  # Optionale Umgebungsvariablen
  shellHook = ''
    echo "⚙️  Starte ICS Proxy Entwicklungsumgebung"
    echo "Tipp: uvicorn app:app --reload --host 0.0.0.0 --port 8000"

    # Beispiel: Hochschul-Kalender setzen (Token geheim halten!)
    export UPSTREAM_ICS_URL="https://meincampus.hs-kempten.de:443/qisserver/pages/cm/exa/timetable/individualTimetableCalendarExport.faces?user=..."
    export CACHE_TTL_SECONDS=300
  '';
}
