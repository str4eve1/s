project('piper',
    version: '0.5.1',
    license: 'GPL-2.0-or-later',
    meson_version: '>= 0.42.0')
# The tag date of the project_version(), update when the version bumps.
version_date='2020-06-22'

# The DBus API version of ratbagd that we are compatible with. Anything
# higher or lower will not be compatible so make sure you bumpt that to the
# latest released ratbagd version whenever a piper release is made.
ratbagd_api_version = 1


# Options
enable_runtime_dependency_checks = get_option('runtime-dependency-checks')
enable_tests = get_option('tests')

# Dependencies
if enable_runtime_dependency_checks
    ratbagd = find_program('ratbagd', required: true)
    ratbagd_required_version='0.14'

    if not ratbagd.found()
        message('''
        ************************ ERROR ***********************
        * _???_     Dependency libratbag not found in $PATH! *
        *(_)_(_)    ratbagd must be installed and running    *
        * (o o)     for Piper to work.                       *
        *==\o/==                                             *
        ******************************************************
        ''')
    else
        r = run_command(ratbagd, '--version')
        if r.returncode() != 0 or r.stdout().version_compare('<' + ratbagd_required_version)
        error('''
        ************************ ERROR *****************************
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

    # external python modules that are required for running piper
    python_modules = [
        'lxml',
        'evdev',
        'cairo',
        'gi',
    ]

    dependency('pygobject-3.0', required: true)
else
    # external python modules that are required for building piper
    python_modules = ['lxml']
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
mandir = join_paths(prefix, get_option('mandir'))

i18n = import('i18n')

subdir('data')
subdir('po')

# Find the directory to install our Python code
if meson.version().version_compare('<0.48.0')
    python = import('python3')
    py3 = python.find_python()
    python_dir = python.sysconfig_path('purelib')
    message('Getting Python3 install dir')
    if not python_dir.endswith('site-packages')
        error('Python3 purelib path seems invalid')
    endif
else
    pymod = import('python')
    if meson.version().version_compare('>=0.51')
        py3 = pymod.find_installation(modules: python_modules)
    else
        py3 = pymod.find_installation()

        foreach module: python_modules
            if run_command(py3, '-c', 'import @0@'.format(module)).returncode() != 0
                error('Failed to find required python module \'@0@\'.'.format(module))
            endif
        endforeach
    endif
    python_dir = py3.get_install_dir()
endif
install_subdir('piper',
               install_dir: python_dir,
               exclude_directories: '__pycache__')

config_piper = configuration_data()
config_piper.set('pkgdatadir', pkgdatadir)
config_piper.set('localedir', localedir)
config_piper.set('gtk_major_version', gtk_major_version)
config_piper.set('gtk_minor_version', gtk_minor_version)
config_piper.set('RATBAGD_API_VERSION', ratbagd_api_version)
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

if enable_tests
    flake8 = find_program('flake8')
    if flake8.found()
        test('flake8', flake8,
             args: ['--ignore=E501,W504',
                    join_paths(meson.source_root(), 'piper'),
                    join_paths(meson.source_root(), 'piper.in')])
    endif
endif
