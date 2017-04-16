#!/usr/bin/env python
'''
Add centered guides,
extension by Samuel Dellicour,

This extension creates horizontal and vertical guides through
the center of the document or the selected object

# Licence
Licence GPL v2
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; version 2 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

# IMPORT

import csv
import inkex
import gettext
_ = gettext.gettext
import guidetools
import os
try:
	from subprocess import Popen, PIPE
except ImportError:
	inkex.errormsg(_(
		"Failed to import the subprocess module."
		))
	inkex.errormsg(
		"Python version is : " + str(inkex.sys.version_info)
		)
	exit(1)

# To show debugging output, error messages, use
#	inkex.debug( _(str(string)) )

class addCenteredGuides(inkex.Effect):

	def __init__(self):
		"""
		Constructor.
		Defines options of the script.
		"""
		# Call the base class constructor.
		inkex.Effect.__init__(self)

		# Define string option "--target"
		self.OptionParser.add_option('--target',
				action="store", type="string",
				dest="target", default="document",
				help="Target: document or selection")

	def find_minimums(self, minimums):
	    potential_mins = (value for value in minimums if value is not None)
	    if potential_mins:
	        return min(potential_mins)

	def find_maximums(self, minimums):
		potential_mins = (value for value in minimums if value is not None)
		if potential_mins:
			return max(potential_mins)

	def get_id_dim_size(self, ids):

		fieldnames = ['id', 'x', 'y', 'width', 'height']
		p = Popen(
			'inkscape --query-all "%s"' % (self.args[-1]),
			shell=True,
			stdout=PIPE,
			stderr=PIPE,
			)
		# we assume the output is not
		# so large that memory is an issue
		f = p.communicate()[0] # receive stdout

		reader = csv.DictReader(iter(f.split(os.linesep)),
								fieldnames=fieldnames)

		result = {}

		# get selected rows
		for row in reader:
			key = row.pop('id')
			if key in ids:
				result[key] = row

		# convert to float and convert units
		for key, value in result.iteritems():
			for k, v in value.iteritems():
				value[k] =  float(self.unittouu(v))

		return result

	def selection_bounding_box(self,ids):
		r = {}
		r['x_min'] = r['x_max'] = r['y_min'] = r['y_max'] = None

 		selected_wi = self.get_id_dim_size(ids)

		for i in selected_wi.keys():
			r['x_min'] = self.find_minimums([ selected_wi[i]['x'] , r['x_min'] ])
			r['x_max'] = self.find_maximums([ selected_wi[i]['x'] +
										selected_wi[i]['width'], r['x_max'] ])
			r['y_min'] = self.find_minimums([ selected_wi[i]['y'], r['y_min'] ])
			r['y_max'] = self.find_maximums([ selected_wi[i]['y'] +
										selected_wi[i]['height'], r['y_max'] ])

		d = {}
		d['x'] = r['x_min']
		d['y'] = r['y_min']
		d['width'] = r['x_max'] - r['x_min']
		d['height'] = r['y_max'] - r['y_min']
		return d

	def effect(self):

		# document or selection
		target = self.options.target

		# getting parent tag of the guides
		namedview = self.document.xpath('/svg:svg/sodipodi:namedview',namespaces=inkex.NSS)[0]

		# getting the main SVG document element (canvas)
		svg = self.document.getroot()

		# getting the width and height attributes of the canvas
		canvas_width  = self.unittouu(svg.get('width'))
		canvas_height = self.unittouu(svg.attrib['height'])

		# If a selected object exists, set guides to that object.
		# Otherwise, use document center guides
		if (target == "selection"):

			# If there is no selection, quit with message
			if not self.options.ids:
				inkex.errormsg(_("Please select at least one object first"))
				exit()

			else:
				q = {}
				q = self.selection_bounding_box(self.options.ids)

			# get width, height, center of bounding box
			obj_width = q['width']
			obj_height = q['height']
			center_x = q['x'] + obj_width/2
			center_y = ( canvas_height - q['y'] - obj_height ) + obj_height/2

		else:

			# Pick document center
			center_x = canvas_width/2
			center_y = canvas_height/2

		# call the function. Output.
		guidetools.drawGuide(center_x, "vertical", namedview)
		guidetools.drawGuide(center_y, "horizontal", namedview)


# APPLY
# Create effect instance and apply it. Taking in SVG, changing it, and then outputing SVG
effect = addCenteredGuides()
effect.affect()
