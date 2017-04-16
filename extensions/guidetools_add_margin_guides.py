#!/usr/bin/env python
'''
Add margin guides,
by Samuel Dellicour,

The extension adds document margin guides - guides at a certain distance
from the borders of the document (or the bounding box of a selected object).

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

# To show debugging output or error messages, use: inkex.debug( _(str(string)) )

# CLASS

class addMarginGuides(inkex.Effect):

	def __init__(self):
		"""
		Constructor.
		Defines options of the script.
		"""
		# Call the base class constructor.
		inkex.Effect.__init__(self)

		self.OptionParser.add_option("--tab",
				action="store", type="string",
				dest="tab", default="columns",
				help="")

		# Define string option "--unit"
		self.OptionParser.add_option('--unit',
				action="store", type="string",
				dest="unit", default="mm",
				help="The unit of the values")

		# Define string option "--target"
		self.OptionParser.add_option('--target',
				action="store", type="string",
				dest="target", default="document",
				help="Target: document or selection")

		# Define boolean option "--same_margins"
		self.OptionParser.add_option('--same_margins',
				action = 'store', type = 'inkbool',
				dest = 'same_margins', default = False,
				help = 'Same margins on all four sides')

		# Define string option "--top_margin"
		self.OptionParser.add_option('--top_margin',
				action = 'store',type = 'string',
				dest = 'top_margin',default = 'centered',
				help = 'Top margin, distance from top border')

		# Define string option "--right_margin"
		self.OptionParser.add_option('--right_margin',
				action = 'store',type = 'string',
				dest = 'right_margin',default = 'centered',
				help = 'Right margin, distance from right border')

		# Define string option "--bottom_margin"
		self.OptionParser.add_option('--bottom_margin',
				action = 'store',type = 'string',
				dest = 'bottom_margin',default = 'centered',
				help = 'Bottom margin, distance from bottom border')

		# Define string option "--left_margin"
		self.OptionParser.add_option('--left_margin',
				action = 'store',type = 'string',
				dest = 'left_margin',default = 'centered',
				help = 'Left margin, distance from left border')

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

		# Get script's options values.

		# Factor to multiply in order to get user units (pixels)
		factor = self.unittouu('1' + self.options.unit)

		# document or selection
		target = self.options.target

		# boolean
		same_margins = self.options.same_margins

		# convert string to integer, in user units (pixels)
		top_margin = float(self.options.top_margin) * factor
		right_margin = float(self.options.right_margin) * factor
		bottom_margin = float(self.options.bottom_margin) * factor
		left_margin = float(self.options.left_margin) * factor

		# getting parent tag of the guides
		namedview = self.document.xpath('/svg:svg/sodipodi:namedview',
										namespaces=inkex.NSS)[0]

		# getting the main SVG document element (canvas)
		svg = self.document.getroot()

		# if same margins, set them all to same value
		if same_margins:
			right_margin = top_margin
			bottom_margin = top_margin
			left_margin = top_margin

		# getting the width and height attributes of the canvas
		canvas_width  = self.unittouu(svg.get('width'))
		canvas_height = self.unittouu(svg.get('height'))

		# If selection, draw around selection. Otherwise use document.
		if (target == "selection"):

			# If there is no selection, quit with message
			if not self.options.ids:
				inkex.errormsg(_("Please select at least one object first"))
				exit()

			else:
				q = {}
				q = self.selection_bounding_box(self.options.ids)

			# get center of bounding box
			obj_width = q['width']
			obj_height = q['height']
			obj_x = q['x'] + obj_width/2
			obj_y = ( canvas_height - q['y'] - obj_height ) + obj_height/2

			# start position of guides
			# (not sure why I need to add the last half width/height)
			top_pos = obj_y - top_margin + obj_height/2
			right_pos = obj_x + obj_width - right_margin - obj_width/2
			bottom_pos = obj_y - obj_height + bottom_margin + obj_height/2
			left_pos = obj_x + left_margin - obj_width/2

			# Draw the four margin guides
			# TODO: only draw if not on border
			guidetools.drawGuide(top_pos, "horizontal", namedview)
			guidetools.drawGuide(right_pos, "vertical", namedview)
			guidetools.drawGuide(bottom_pos, "horizontal", namedview)
			guidetools.drawGuide(left_pos, "vertical", namedview)

		else:

			# draw margin guides (if not zero)
			if same_margins:
				right_margin = top_margin
				bottom_margin = top_margin
				left_margin = top_margin

			# start position of guides
			top_pos = canvas_height - top_margin
			right_pos = canvas_width - right_margin
			bottom_pos = bottom_margin
			left_pos = left_margin

			# Draw the four margin guides (if margin exists)
			if top_pos != canvas_height: guidetools.drawGuide(top_pos, "horizontal", namedview)
			if right_pos != canvas_width: guidetools.drawGuide(right_pos, "vertical", namedview)
			if bottom_pos != 0: guidetools.drawGuide(bottom_pos, "horizontal", namedview)
			if left_pos != 0: guidetools.drawGuide(left_pos, "vertical", namedview)


# APPLY

# Create effect instance and apply it. Taking in SVG, changing it, and then outputing SVG
effect = addMarginGuides()
effect.affect()
