/*
* Copyright (c) 2007, TUBITAK/UEKAE
*
* This program is free software; you can redistribute it and/or modify it
* under the terms of the GNU General Public License as published by the
* Free Software Foundation; either version 2 of the License, or (at your
* option) any later version. Please read the COPYING file.
*/

#include <Python.h>
#include <libx86.h>

#include "vbe.h"
#include "vesamode.h"

#define TIMING(x, y, z) Py_BuildValue("iii", x, y, z)

int
is_valid(struct vbe_edid1_info *edid)
{
	char sum = 0;
	int i = 128;

	while (i--)
		sum += *((char *)edid + i);

	return sum == 0;
}

/* Strips the 13-bytes buffer */
void
strip(char *s)
{
	char *ps;

	s[12] = 0;
	for (ps = s + strlen(s) - 1; ps >= s; ps--)
		if (isspace(*ps))
			*ps = 0;
		else
			break;
}

PyObject *
get_established_timings(struct vbe_edid1_info *edid)
{
	PyObject *timings[16];
	int i = 0, j;

	if(edid->established_timings.timing_720x400_70)
		timings[i++] = TIMING(720, 400, 70);
	if(edid->established_timings.timing_720x400_88)
		timings[i++] = TIMING(720, 400, 88);
	if(edid->established_timings.timing_640x480_60)
		timings[i++] = TIMING(640, 480, 60);
	if(edid->established_timings.timing_640x480_67)
		timings[i++] = TIMING(640, 480, 67);
	if(edid->established_timings.timing_640x480_72)
		timings[i++] = TIMING(640, 480, 72);
	if(edid->established_timings.timing_640x480_75)
		timings[i++] = TIMING(640, 480, 75);
	if(edid->established_timings.timing_800x600_56)
		timings[i++] = TIMING(800, 600, 56);
	if(edid->established_timings.timing_800x600_60)
		timings[i++] = TIMING(800, 600, 60);
	if(edid->established_timings.timing_800x600_72)
		timings[i++] = TIMING(800, 600, 72);
	if(edid->established_timings.timing_800x600_75)
		timings[i++] = TIMING(800, 600, 75);
	if(edid->established_timings.timing_832x624_75)
		timings[i++] = TIMING(832, 624, 75);
	/*if(edid->established_timings.timing_1024x768_87i)
		timings[i++] = "1024x768@87i";*/
	if(edid->established_timings.timing_1024x768_60)
		timings[i++] = TIMING(1024, 768, 60);
	if(edid->established_timings.timing_1024x768_70)
		timings[i++] = TIMING(1024, 768, 70);
	if(edid->established_timings.timing_1024x768_75)
		timings[i++] = TIMING(1024, 768, 75);
	if(edid->established_timings.timing_1280x1024_75)
		timings[i++] = TIMING(1280, 1024, 75);

	PyObject *established_timings = PyTuple_New(i);
	for (j = 0; j < i; j++)
		PyTuple_SetItem(established_timings, j, timings[j]);

	return established_timings;
}

PyObject *
get_standard_timings(struct vbe_edid1_info *edid)
{
	PyObject *timings[8];
	int i, j;

	for(i = j = 0; j < 8; j++) {
		double aspect = 1;
		unsigned int x, y;
		unsigned char xres, vfreq;
		xres = edid->standard_timing[j].xresolution;
		vfreq = edid->standard_timing[j].vfreq;
		if((xres != vfreq) ||
		   ((xres != 0) && (xres != 1)) ||
		   ((vfreq != 0) && (vfreq != 1))) {
			switch(edid->standard_timing[j].aspect) {
				case 0: aspect = 0.625; break; /*undefined*/
				case 1: aspect = 0.750; break;
				case 2: aspect = 0.800; break;
				case 3: aspect = 0.5625; break;
			}
			x = xres * 8 + 248;
			y = x * aspect;
			timings[i++] = TIMING(x, y, (vfreq & 0x3f) + 60);
		}
	}
	
	PyObject *standard_timings = PyTuple_New(i);
	for (j = 0; j < i; j++)
		PyTuple_SetItem(standard_timings, j, timings[j]);

	return standard_timings;
}

PyObject *
get_detailed_timing_info(struct vbe_edid1_info *edid)
{
	PyObject *flags = NULL;
	
	int	i,
		pixel_clock = 0,
		horizontal_active = 0,
		horizontal_blanking = 0,
		vertical_active = 0,
		vertical_blanking = 0,
		hsync_offset = 0,
		hsync_pulse_width = 0,
		vsync_offset = 0,
		vsync_pulse_width = 0,
		himage_size = 0,
		vimage_size = 0,

		hsync_min = 0,
		hsync_max = 0,
		vref_min = 0,
		vref_max = 0;

	char	serial[13] = {0};
	char	ascii[13] = {0};
	char	name[13] = {0};

	for(i = 0; i < 4; i++) {
		struct vbe_edid_monitor_descriptor *monitor = NULL;
		struct vbe_edid_detailed_timing *timing = NULL;

		timing = &edid->monitor_details.detailed_timing[i];
		monitor = &edid->monitor_details.monitor_descriptor[i];

		if (timing->pixel_clock && (monitor->zero_flag_1 || monitor->zero_flag_2)) {
			pixel_clock = VBE_EDID_DETAILED_TIMING_PIXEL_CLOCK(*timing);
			horizontal_active = VBE_EDID_DETAILED_TIMING_HORIZONTAL_ACTIVE(*timing);
			horizontal_blanking = VBE_EDID_DETAILED_TIMING_HORIZONTAL_BLANKING(*timing);
			vertical_active = VBE_EDID_DETAILED_TIMING_VERTICAL_ACTIVE(*timing);
			vertical_blanking = VBE_EDID_DETAILED_TIMING_VERTICAL_BLANKING(*timing);
			hsync_offset = VBE_EDID_DETAILED_TIMING_HSYNC_OFFSET(*timing);
			hsync_pulse_width = VBE_EDID_DETAILED_TIMING_HSYNC_PULSE_WIDTH(*timing);
			vsync_offset = VBE_EDID_DETAILED_TIMING_VSYNC_OFFSET(*timing);
			vsync_pulse_width = VBE_EDID_DETAILED_TIMING_VSYNC_PULSE_WIDTH(*timing);
			himage_size = VBE_EDID_DETAILED_TIMING_HIMAGE_SIZE(*timing);
			vimage_size = VBE_EDID_DETAILED_TIMING_VIMAGE_SIZE(*timing);
			flags = Py_BuildValue("{s:O,s:O,s:O,s:O,s:O,s:i}",
				"interlaced",	PyBool_FromLong(timing->flags.interlaced),
				"stereo",	PyBool_FromLong(timing->flags.stereo),
				"separate_sync",	PyBool_FromLong(timing->flags.separate_sync),
				"hsync_positive",	PyBool_FromLong(timing->flags.hsync_positive),
				"vsync_positive",	PyBool_FromLong(timing->flags.vsync_positive),
				"stereo_mode",	timing->flags.stereo_mode
			);

		} else if (monitor->type == vbe_edid_monitor_descriptor_serial) {
			memcpy(serial, monitor->data.string, 13);
			strip(serial);

		} else if (monitor->type == vbe_edid_monitor_descriptor_ascii) {
			memcpy(ascii, monitor->data.string, 13);
			strip(ascii);

		} else if (monitor->type == vbe_edid_monitor_descriptor_name) {
			memcpy(name, monitor->data.string, 13);
			strip(name);

		} else if (monitor->type == vbe_edid_monitor_descriptor_range) {
			hsync_min = monitor->data.range_data.horizontal_min;
			hsync_max = monitor->data.range_data.horizontal_max;
			vref_min = monitor->data.range_data.vertical_min;
			vref_max = monitor->data.range_data.vertical_max;
		}
	}

	if (flags == NULL) {
		Py_INCREF(Py_None);
		flags = Py_None;
	}

	return Py_BuildValue(
		"{s:i,"		/* pixel_clock */
		"s:i,"		/* horizontal_active */
		"s:i,"		/* horizontal_blanking */
		"s:i,"		/* vertical_active */
		"s:i,"		/* vertical_blanking */
		"s:i,"		/* hsync_offset */
		"s:i,"		/* hsync_pulse_width */
		"s:i,"		/* vsync_offset */
		"s:i,"		/* vsync_pulse_width */
		"s:i,"		/* horizontal_image_size */
		"s:i,"		/* vertical_image_size */
		"s:s,"		/* serial_number */
		"s:s,"		/* ascii_string */
		"s:s,"		/* name */
		"s:(i,i),"	/* hsync_range */
		"s:(i,i),"	/* vref_range */
		"s:O}",		/* flags */

		"pixel_clock", pixel_clock,
		"horizontal_active", horizontal_active,
		"horizontal_blanking", horizontal_blanking,
		"vertical_active", vertical_active,
		"vertical_blanking", vertical_blanking,
		"hsync_offset", hsync_offset,
		"hsync_pulse_width", hsync_pulse_width,
		"vsync_offset", vsync_offset,
		"vsync_pulse_width", vsync_pulse_width,
		"horizontal_image_size", himage_size,
		"vertical_image_size", vimage_size,
		"serial_number", serial,
		"ascii_string", ascii,
		"name", name,
		"hsync_range", hsync_min, hsync_max,
		"vref_range", vref_min, vref_max,
		"flags", flags
	);
}

PyDoc_STRVAR(vbeInfo__doc__,
	"vbeInfo()\n"
	"\n"
	"Get VBE info\n");

PyObject*
ddc_vbeInfo(PyObject *self, PyObject *args)
{
	PyObject *ret;
	struct vbe_info *vbe_info = NULL;
	
	const char *vendor_name = NULL;
	const char *product_name = NULL;
	const char *product_revision = NULL;

	unsigned int mode_count;
	u_int16_t *mode_list = NULL;
	PyObject *modes;
	
	vbe_info = vbe_get_vbe_info();
	if(vbe_info == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	if(vbe_info->version[1] >= 3) {
		vendor_name = vbe_info->vendor_name.string;
		product_name = vbe_info->product_name.string;
		product_revision = vbe_info->product_revision.string;
	}

	mode_count = 0;
	for (mode_list = vbe_info->mode_list.list; *mode_list != 0xffff; mode_list++)
		mode_count++;

	modes = PyTuple_New(mode_count);
	mode_list = vbe_info->mode_list.list;

	int i = 0;
	for (mode_list = vbe_info->mode_list.list; *mode_list != 0xffff; mode_list++) {
		int j;
		for (j = 0; known_vesa_modes[j].x; j++) {
			if (known_vesa_modes[j].number == *mode_list) {
				PyTuple_SetItem(modes, i++, PyString_FromString(known_vesa_modes[j].text));
			}
		}
	}
	
	ret = Py_BuildValue(
		"{s:s#,"	/* signature */
		"s:(i,i),"	/* version */
		"s:s,"		/* oem_name */
		"s:s,"		/* vendor_name */
		"s:s,"		/* product_name */
		"s:s,"		/* product_revision */
		"s:i,"		/* memory_size */
		"s:O}",		/* mode_list */

		"signature", vbe_info->signature, 4,
		"version", vbe_info->version[1], vbe_info->version[0],
		"oem_name", vbe_info->oem_name,
		"vendor_name", vendor_name,
		"product_name", product_name,
		"product_revision", product_revision,
		"memory_size", vbe_info->memory_size,
		"mode_list", modes
	);

	free(vbe_info);
	return ret;
}


PyDoc_STRVAR(query__doc__,
	"query(adapter)\n"
	"\n"
	"Query DDC and return a dict object including EDID infos\n");

PyObject*
ddc_query(PyObject *self, PyObject *args)
{
	PyObject *ret;
	int adapter;
	struct vbe_edid1_info *edid;
	
	unsigned char hmin, hmax, vmin, vmax;
	char eisa_id[8] = {0};
	char manufacturer[4];

	if (!PyArg_ParseTuple(args, "i", &adapter))
		return NULL;

	if (!vbe_get_edid_supported(adapter)) {
		Py_INCREF(Py_None);
		return Py_None;
	}
	
	if ((edid = vbe_get_edid_info(adapter)) == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	if (!is_valid(edid)) {
		free(edid);
		Py_INCREF(Py_None);
		return Py_None;
	}

	if (edid->version == 255 && edid->revision == 255) {
		free(edid);
		Py_INCREF(Py_None);
		return Py_None;
	}

	manufacturer[0] = edid->manufacturer_name.char1 + 'A' - 1;
	manufacturer[1] = edid->manufacturer_name.char2 + 'A' - 1;
	manufacturer[2] = edid->manufacturer_name.char3 + 'A' - 1;
	manufacturer[3] = '\0';
	snprintf(eisa_id, 8, "%s%04x", manufacturer, edid->product_code);

	if(edid->serial_number != 0xffffffff) {
		if(strcmp(manufacturer, "MAG") == 0) {
			edid->serial_number -= 0x7000000;
		}
		if(strcmp(manufacturer, "OQI") == 0) {
			edid->serial_number -= 456150000;
		}
		if(strcmp(manufacturer, "VSC") == 0) {
			edid->serial_number -= 640000000;
		}
	}

	ret = Py_BuildValue(
		"{s:i,"		/* version */
		"s:i,"		/* revision */
		"s:i,"		/* serial_number */
		"s:i,"		/* week */
		"s:i,"		/* year */
		"s:O,"		/* input_separate_sync */
		"s:O,"		/* input_composite_sync */
		"s:O,"		/* input_sync_on_green */
		"s:O,"		/* input_digital */
		"s:i,"		/* max_size_horizontal */
		"s:i,"		/* max_size_vertical */
		"s:f,"		/* gamma */
		"s:O,"		/* dpms_active_off */
		"s:O,"		/* dpms_suspend */
		"s:O,"		/* dpms_standby */
		"s:O,"		/* established_timings */
		"s:O,"		/* standard_timings */
		"s:O,"		/* detailed_timing */
		"s:s}",		/* eisa_id */

		"version", edid->version,
		"revision", edid->revision,
		"serial_number", edid->serial_number,
		"week", edid->week,
		"year", edid->year + 1990,
		"input_separate_sync", PyBool_FromLong(edid->video_input_definition.separate_sync),
		"input_composite_sync", PyBool_FromLong(edid->video_input_definition.composite_sync),
		"input_sync_on_green", PyBool_FromLong(edid->video_input_definition.sync_on_green),
		"input_digital", PyBool_FromLong(edid->video_input_definition.digital),
		"max_size_horizontal", edid->max_size_horizontal,
		"max_size_vertical", edid->max_size_vertical,
		"gamma", edid->gamma / 100.0 + 1,
		"dpms_active_off", PyBool_FromLong(edid->feature_support.active_off),
		"dpms_suspend", PyBool_FromLong(edid->feature_support.suspend),
		"dpms_standby", PyBool_FromLong(edid->feature_support.standby),
		"established_timings", get_established_timings(edid),
		"standard_timings", get_standard_timings(edid),
		"detailed_timing", get_detailed_timing_info(edid),
		"eisa_id", eisa_id
	);

	free(edid);
	return ret;
}

static PyMethodDef ddc_methods[] = {
	{"vbeInfo", (PyCFunction)ddc_vbeInfo, METH_NOARGS, vbeInfo__doc__},
	{"query", (PyCFunction)ddc_query, METH_VARARGS, query__doc__},
	{NULL, NULL}
};

PyMODINIT_FUNC
initddc(void)
{
	PyObject *m;

	m = Py_InitModule("ddc", ddc_methods);

	return;
}
