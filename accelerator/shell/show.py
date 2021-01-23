############################################################################
#                                                                          #
# Copyright (c) 2020 Carl Drougge                                          #
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

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from glob import glob
from os.path import join, dirname
import importlib

from accelerator.compat import terminal_size
from accelerator.unixhttp import call
from collections import defaultdict

def main(argv, cfg):
	prog = argv.pop(0)
	if '--help' in argv or '-h' in argv:
		print('usage: %s [method]' % (prog,))
		print('gives description and options for method,')
		print('or lists methods with no method specified.')
		return

	default = False
	for package in cfg.method_directories:
		if '.' in package:
			data = importlib.import_module(package)
			path = dirname(data.__file__)
		else:
			path = join(cfg.project_directory, package)
		v = []
		for item in sorted(glob(join(path + '/build*.py'))):
			name = item[:-3].rsplit('/', 1)[1]
			data = importlib.import_module(package + '.' + name)
			description = getattr(data, 'description', '').strip('\n').rstrip('\n')
			description = '\n# '.join(description.split('\n'))
			v.append((name, description))
		if v:
			print(package + ':')
			maxlen = max(len(x[0]) for x in v)
			for key, val in v:
				if key == 'build' and not default:
					default = True
					dot = '\x1b[1m*\x1b[m'
				else:
					dot = ' '
				if val:
					fmt = "  %%s %%-%ds  : %%s" % (maxlen,)
					print(fmt % (dot, key, val))
				else:
					fmt = "  %%s %%-%ds" % (maxlen,)
					print(fmt % (dot, key,))
