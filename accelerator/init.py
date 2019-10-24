############################################################################
#                                                                          #
# Copyright (c) 2019 Carl Drougge                                          #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License");          #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#  http://www.apache.org/licenses/LICENSE-2.0                              #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
#                                                                          #
############################################################################


a_example = r"""description = r'''
This is just an example. It doesn't even try to do anything useful.

You can run it to see that your installation works.
'''

def analysis(sliceno):
	return sliceno

def synthesis(analysis_res):
	print("Sum of all sliceno:", sum(analysis_res))
"""


config_template = r"""# The configuration is a collection of key value pairs.
#
# Values are specified as
# key: value
# or for several values
# key:
# 	value 1
# 	value 2
# 	...
# (any leading whitespace is ok)
#
# Use ${{VAR}} or ${{VAR=DEFAULT}} to use environment variables.

slices: {slices}
workdirs:
	{name} {workdir}

# Target workdir defaults to the first workdir, but you can override it.
# target workdir: {name}
# (this is where jobs without a workdir override are built)

method packages:
	{name}
	accelerator.standard_methods
#	accelerator.test_methods

urd: # URL/socket to your urd.

result directory: {prefix}/results
source directory: {source}
logfile: {prefix}/daemon.log

# If you want to run methods on different python interpreters you can
# specify names for other interpreters here, and put that name after
# the method in methods.conf.
# You automatically get four names for the interpreter that started
# the daemon: DEFAULT, {major}, {major}.{minor} and {major}.{minor}.{micro} (adjusted to the actual
# version used). You can override these here, except DEFAULT.
# interpreters:
# 	2.7 /path/to/python2.7
# 	test /path/to/beta/python
"""


def main(argv):
	from os import makedirs, listdir
	from os.path import exists, join, realpath
	from sys import version_info
	from argparse import ArgumentParser
	from accelerator.shell import UserError
	from accelerator.configfile import interpolate

	parser = ArgumentParser(
		prog='init',
		description=r'''
			Creates an accelerator project directory.
			Defaults to the current directory.
			Creates accelerator.conf and a method directory.
			Also creates workdirs and result dir (in ~/accelerator by default).
			Both the method directory and workdir will be named <NAME>,
			"dev" by default.
		''',
	)
	parser.add_argument('--slices', default=None, type=int, help='Override slice count detection')
	parser.add_argument('--name', default='dev', help='Name of method dir and workdir, default "dev"')
	parser.add_argument('--directory', default='.', help='project directory to create. default "."', metavar='DIR')
	parser.add_argument('--prefix', default='${HOME}/accelerator', help='Put workdirs and daemon.log here, default "${HOME}/accelerator"')
	parser.add_argument('--source', default='# /some/path where you want import methods to look.', help='source directory')
	parser.add_argument('--force', action='store_true', help='Go ahead even though directory is not empty, or workdir exists with incompatible slice count')
	options = parser.parse_args(argv)

	assert options.name
	if not options.prefix.startswith('${'):
		options.prefix = realpath(options.prefix)
	if not options.source.startswith('#'):
		options.source = realpath(options.source)
	cfg_workdir = join(options.prefix, 'workdirs', options.name)
	workdir = interpolate(cfg_workdir)
	if not exists(workdir):
		makedirs(workdir)
	slices_conf = join(workdir, options.name + '-slices.conf')
	try:
		with open(slices_conf, 'r') as fh:
			workdir_slices = int(fh.read())
	except OSError:
		workdir_slices = None
	if workdir_slices and options.slices is None:
		options.slices = workdir_slices
	if options.slices is None:
		from multiprocessing import cpu_count
		options.slices = cpu_count()
	if workdir_slices and workdir_slices != options.slices and not options.force:
		raise UserError('Workdir %r has %d slices, refusing to continue with %d slices' % (workdir, workdir_slices, options.slices,))

	if not exists(options.directory):
		makedirs(options.directory)
	if not options.force and listdir(options.directory):
		raise UserError('Directory %r is not empty.' % (options.directory,))
	with open(slices_conf, 'w') as fh:
		fh.write('%d\n' % (options.slices,))
	method_dir = join(options.directory, options.name)
	if not exists(method_dir):
		makedirs(method_dir)
	with open(join(method_dir, 'methods.conf'), 'w') as fh:
		fh.write('example\n')
	with open(join(method_dir, 'a_example.py'), 'w') as fh:
		fh.write(a_example)
	with open(join(options.directory, 'accelerator.conf'), 'w') as fh:
		fh.write(config_template.format(
			name=options.name,
			prefix=options.prefix,
			workdir=cfg_workdir,
			slices=options.slices,
			source=options.source,
			major=version_info.major,
			minor=version_info.minor,
			micro=version_info.micro,
		))