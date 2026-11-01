#!/bin/sh
# Assemble the single-file dashboard from src/.
cd "$(dirname "$0")"
{ cat src/1_head.html; printf '<script>\n'; cat src/2_data.js src/3_app.js; printf '</script>\n</body>\n</html>\n'; } > index.html
