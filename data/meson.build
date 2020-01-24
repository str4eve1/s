gnome = import('gnome')

desktopdir = join_paths(datadir, 'applications')
icondir = join_paths(datadir, 'icons', 'hicolor', 'scalable', 'apps')
metainfodir = join_paths(datadir, 'metainfo')

conf = configuration_data()
conf.set('version', meson.project_version())
conf.set('version_date', version_date)

about_dialog = configure_file(input: 'ui/AboutDialog.ui.in',
			      output: 'AboutDialog.ui',
			      configuration: conf)

install_data('org.freedesktop.Piper.svg', install_dir: icondir)

i18n.merge_file(input: 'org.freedesktop.Piper.desktop.in',
                output: 'org.freedesktop.Piper.desktop',
                type: 'desktop',
                po_dir: podir,
                install: true,
                install_dir: desktopdir)

appdata = configure_file(input: 'org.freedesktop.Piper.appdata.xml.in.in',
                         output: 'org.freedesktop.Piper.appdata.xml.in',
                         configuration: conf)

i18n.merge_file(input: appdata,
                output: 'org.freedesktop.Piper.appdata.xml',
                type: 'xml',
                po_dir: podir,
                install: true,
                install_dir: metainfodir)


# SVG files

svgs = [
	'svgs/fallback.svg',
	'svgs/logitech-g9.svg',
	'svgs/logitech-g102-g203.svg',
	'svgs/logitech-g300.svg',
	'svgs/logitech-g303.svg',
	'svgs/logitech-g402.svg',
	'svgs/logitech-g403.svg',
	'svgs/logitech-g500.svg',
	'svgs/logitech-g500s.svg',
	'svgs/logitech-g502.svg',
	'svgs/logitech-g600.svg',
	'svgs/logitech-g602.svg',
	'svgs/logitech-g603.svg',
	'svgs/logitech-g604.svg',
	'svgs/logitech-g700.svg',
	'svgs/logitech-g703.svg',
	'svgs/logitech-g900.svg',
	'svgs/logitech-g-pro.svg',
	'svgs/logitech-g-pro-wireless.svg',
	'svgs/logitech-mx-anywhere2.svg',
	'svgs/logitech-mx-anywhere2s.svg',
	'svgs/logitech-mx-ergo.svg',
	'svgs/logitech-mx-master.svg',
	'svgs/logitech-mx-master-2s.svg',
	'svgs/logitech-mx-master-3.svg',
	'svgs/roccat-kone-pure.svg',
	'svgs/roccat-kone-xtd.svg',
	'svgs/steelseries-kinzu-v2.svg',
	'svgs/steelseries-kinzu-v3.svg',
	'svgs/steelseries-rival.svg',
	'svgs/steelseries-rival310.svg',
	'svgs/steelseries-rival600.svg',
	'svgs/steelseries-sensei310.svg',
	'svgs/steelseries-senseiraw.svg',
]

svg_mapping = files('svgs/svg-lookup.ini')

test_svg_files = find_program('svgs/check-svg.py')
test('check-svg', test_svg_files,
     args: svgs,
     env: ['BASEDIR=@0@'.format(meson.current_source_dir())])

test('svg-lookup-check',
     find_program('svg-lookup-ini-test.py'),
     args: [
         svg_mapping,
         join_paths(meson.source_root(), 'data/svgs/')
     ],

)
# meson requires that we specify all files one-by-one, so let's add a test
# that we can't forget about that.
test('svg-files-in-meson.build',
     find_program('check-svg-in-meson.build.sh'),
     args: [meson.source_root()],
     suite: ['all'])
test('files-in-git',
     find_program('check-files-in-git.sh'),
     args: [meson.source_root()],
     suite: ['all'])

gresource = configure_file(input: 'piper.gresource.xml.in',
                           output: 'piper.gresource.xml',
                           command: ['generate-piper-gresource.xml.py',
                                     join_paths(meson.current_source_dir(), 'piper.gresource.xml.in'),
                                     join_paths(meson.current_build_dir(), 'piper.gresource.xml'),
                                     svgs
                                     ]
                           )

gnome.compile_resources('piper', gresource,
			source_dir: '.',
			dependencies: [about_dialog],
			gresource_bundle: true,
			install: true,
			install_dir: pkgdatadir)
