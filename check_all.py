import ast, os

files = [
    'app.py','auth.py','database.py',
    'modules/dashboard.py','modules/santri.py','modules/hafalan.py',
    'modules/monitoring.py','modules/prediksi.py','modules/laporan.py',
    'modules/users.py','modules/notifikasi.py'
]

print('=== SYNTAX CHECK ===')
all_ok = True
for f in files:
    try:
        src = open(f, encoding='utf-8').read()
        ast.parse(src)
        print('  OK  ' + f)
    except SyntaxError as e:
        print('  ERR ' + f + ': ' + str(e))
        all_ok = False

print('')
print('=== CEK KATA SKRIPSI DI UI ===')
found_any = False
for f in files:
    src = open(f, encoding='utf-8').read()
    for i, line in enumerate(src.splitlines(), 1):
        stripped = line.strip()
        is_comment = stripped.startswith('#')
        if 'Skripsi' in line and not is_comment:
            print('  ' + f + ':' + str(i) + '  ' + stripped)
            found_any = True
if not found_any:
    print('  BERSIH - tidak ada kata Skripsi di UI strings')

if all_ok:
    print('')
    print('Semua file LOLOS syntax check.')
