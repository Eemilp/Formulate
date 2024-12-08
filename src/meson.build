pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'formulate'
element_moduledir = moduledir / 'elements'
gnome = import('gnome')

blueprints = custom_target('blueprints',
  input: files(
    'gtk/help-overlay.blp',
    'window.blp',
    'formulabox.blp',
    'document.blp',
    'cell.blp',
    'textbox.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

gnome.compile_resources('formulate',
  'formulate.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'formulate.in',
  output: 'formulate',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

formulate_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'utils.py',
  'data.py',
  'cursor.py',
  'parser.py',
  'formula.py',
  'formulabox.py',
  'qalculator.py',
  'document.py',
  'cell.py',
  'textbox.py',
  'converter.py',
]

install_data(formulate_sources, install_dir: moduledir)

elements_sources = [
  'elements/__init__.py',
  'elements/elements.py',
  'elements/element.py',
  'elements/atom.py',
  'elements/abs.py',
  'elements/abstractwrapped.py',
  'elements/abstractelement.py',
  'elements/ceil.py',
  'elements/floor.py',
  'elements/frac.py',
  'elements/index.py',
  'elements/paren.py',
  'elements/radical.py',
  'elements/sum.py',
  'elements/supersubscript.py',
]

install_data(elements_sources, install_dir: element_moduledir)
