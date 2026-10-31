import io, re
from pathlib import Path

p = Path("static/admin/css/ario-admin.css")
t = p.read_text(encoding="utf-8")

# 1) topbar must never stack vertically (django responsive.css flips it to column)
t = t.replace(
    "    display: flex;\n    align-items: center;\n    justify-content: flex-start;\n    gap: 12px;\n    width: auto;\n    height: auto;\n    min-height: 60px;",
    "    display: flex;\n    flex-direction: row !important;\n    flex-wrap: nowrap !important;\n    align-items: center;\n    justify-content: space-between !important;\n    gap: 12px;\n    width: auto;\n    height: auto;\n    min-height: 60px;"
)

# 2) login: hard-pin the card width and never show the rail
t = t.replace(
    "body.adm.login #content { width: 100%; max-width: 430px; }",
    "body.adm.login #content { width: 100% !important; max-width: 430px !important; margin-inline: auto !important; padding: 0 !important; }\n"
    "body.adm.login .adm-rail, body.adm.login .adm-scrim { display: none !important; }\n"
    "body.adm.login #user-tools { display: none !important; }"
)

# 3) mobile: filters go below the results and stay short
t = t.replace(
    "    #changelist-filter { position: static; width: 100% !important; order: -1; }\n"
    "    #changelist-filter ul { display: flex; flex-wrap: wrap; gap: 4px; }\n"
    "    #changelist-filter li a { padding: 6px 12px !important; }",
    "    #changelist-filter { position: static; width: 100% !important; order: 2; max-height: 62vh; overflow-y: auto; }\n"
    "    #changelist-filter ul { display: block; }\n"
    "    #changelist-filter li a { padding: 8px 12px !important; }\n"
    "    #changelist .changelist-form-container { order: 1; }"
)

p.write_text(t, encoding="utf-8")
print("topbar row:", "flex-direction: row !important" in t)
print("login pin:", "max-width: 430px !important" in t)
print("login rail hidden:", "body.adm.login .adm-rail" in t)
print("mobile filter order:", "order: 2;" in t)
print("braces:", t.count("{"), t.count("}"))
