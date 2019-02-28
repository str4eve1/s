project('piper',
	version: '0.2.904',
	license: 'GPLv2',
	meson_version: '>= 0.48.0')
# The tag date of the project_version(), update when the version bumps.
version_date='2019-01-24'
# Note: Update the Contributor list in data/ui/AboutDialog.ui.in when the
# version bumps

# Dependencies
dependency('python3', required: true)
dependency('pygobject-3.0', required: true)
ratbagd = find_program('ratbagd', required: false)
ratbagd_required_version='0.9.905'

if not ratbagd.found()
	message('''
	*********************** WARNING **********************
	* _???_     Dependency libratbag not found in $PATH! *
	*(_)_(_)    ratbagd must be installed and running    *
	* (o o)     for Piper to work.                       *
	*==\o/==                                             *
	******************************************************
	''')
else
	r = run_command(ratbagd, '--version')
	if r.returncode() != 0 or r.stdout().version_compare('<' + ratbagd_required_version)
	message('''
	*********************** WARNING ****************************
	*                 (   )(                                   *
	*         (\-.     ) (  )    ratbagd found in $PATH is too *
	*         / _`> .---------.  old and  will  not  work with *
	* _)     / _)=  |'-------'|  this version of Piper. Please *
	*(      / _/    |O   O   o|  update libratbag/ratbagd.     *
	* `-.__(___)_   | o O . o |                                *
	************************************************************
	''')
	endif
endif

# Gtk version required
gtk_major_version = 3
gtk_minor_version = 22

prefix = get_option('prefix')
datadir = join_paths(prefix, get_option('datadir'))
localedir = join_paths(prefix, get_option('localedir'))
pkgdatadir = join_paths(datadir, meson.project_name())
bindir = join_paths(prefix, get_option('bindir'))
podir = join_paths(meson.source_root(), 'po')

i18n = import('i18n')

subdir('data')
subdir('po')

# Find the directory to install our Python code
python = import('python3')
py3 = python.find_python()
message('Getting Python3 install dir')
python_dir = python.sysconfig_path('purelib')
if not python_dir.endswith('site-packages')
	error('Python3 purelib path seems invalid')
endif
install_subdir('piper', install_dir: python_dir)

config_piper = configuration_data()
config_piper.set('pkgdatadir', pkgdatadir)
config_piper.set('localedir', localedir)
config_piper.set('gtk_major_version', gtk_major_version)
config_piper.set('gtk_minor_version', gtk_minor_version)
config_piper.set('devel', '')

config_piper_devel = config_piper
config_piper_devel.set('pkgdatadir', join_paths(meson.build_root(), 'data'))
config_piper_devel.set('localedir', join_paths(meson.build_root(), 'po'))
config_piper_devel.set('devel', '''
sys.path.insert(1, '@0@')
print('Running from source tree, using local files')
'''.format(meson.source_root()))

configure_file(input: 'piper.in',
	       output: 'piper',
	       configuration: config_piper,
	       install_dir: bindir)

configure_file(input: 'piper.in',
	       output: 'piper.devel',
	       configuration: config_piper_devel)

meson.add_install_script('meson_install.sh')
